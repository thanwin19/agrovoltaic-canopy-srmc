// Training and test data for distilling the six-sensor controller into a small neural network that fits an ESP32.
//   node make_dataset.js [nTrain] [nTest]   -> train.bin / test.bin (float32) and meta.json
// Each sample is one daylight hour at the reference site with random day, hour, sky (clearness), temperature, humidity, soil moisture, a light model mismatch m
// (true crop light = model light x m; the controller can only see it through the PAR sensor), and the angle the panels are at now (prev).
// Inputs are NOISY sensor readings (same noise as the accuracy study).  Target = the best angle for the TRUE state (the oracle).
// Also stored per sample: the electricity and crop value of every angle 15..60 in 0.5 deg steps under the TRUE state, so that any strategy can be scored, and
// the angle the full optimiser (single readings, no filter) would pick from the same noisy readings.
// Layout of one record (float32): 10 features, oracle angle, optimiser angle, month plan angle, 91 pv values, 91 crop values.
const fs = require('fs'), path = require('path');
const ROOT = path.join(__dirname, '..', '..', '..');
const S = require(path.join(ROOT, 'Review3_Digital_Twin', 'code_reference', 'srmc_engine.js')), SC = require(path.join(__dirname, '..', 'sensor_controller.js'));
const DD = path.join(ROOT, 'Review1_Design_and_CAD', 'results', 'design'), L = f => JSON.parse(fs.readFileSync(path.join(DD, f)));
const clim = L('climates.json')[0], soil = L('soils.json')[0], crops = L('crops.json'), D = L('design.json'), dp = D.presets[D.active], pw = +(dp.panelPitch - dp.panelGap).toFixed(4);
const params = { bayLen: dp.bayLen, pitch: dp.panelPitch, panelW: pw, height: dp.clearanceLowestEdge + pw / 2 * Math.sin(dp.maxTiltDeg * Math.PI / 180), tankM3: dp.cistern.m3, rainSlope: dp.rainSlopeDeg, stops: Array.from({ length: Math.round((dp.stopsDeg[1] - dp.stopsDeg[0]) / 5) + 1 }, (_, i) => dp.stopsDeg[0] + 5 * i) };
const R = S.run({ clim, soil, crops, params }), P = R.P, ctl = SC.make(S, { P, clim, zones: R.zones, w: 0.5, maxStep: 90, guard: true, hyst: 0 });
function rng(seed) { let a = seed >>> 0; return () => { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
const gauss = r => { let u = 0; while (!u) u = r(); const v = r(); return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v); };
const ANG = Array.from({ length: 91 }, (_, i) => 15 + 0.5 * i), NF = 10, REC = NF + 3 + 91 * 2;
const monthOf = n => { let m = 0; for (let i = 0; i < 12; i++) if (n > S.CUM[i]) m = i; return m; };
function make(N, seed, file) {
  const r = rng(seed), buf = new Float32Array(N * REC); let k = 0;
  while (k < N) {
    const n = 1 + Math.floor(r() * 365), m = monthOf(n), hour = 5.5 + r() * 13, sun = S.sunVec(clim.lat, n, hour); if (sun.sz < 0.08) continue;
    const kf = 0.25 + 0.75 * r(), irr = S.irradiance(sun.sz, n, clim.kt[m] * kf), T = clim.tmean[m] + clim.trange[m] / 2 * Math.sin(2 * Math.PI * (hour - 9) / 24) + 2 * gauss(r), RH = Math.max(15, Math.min(98, clim.rh[m] - 12 * Math.cos(2 * Math.PI * (hour - 15) / 24) + 5 * gauss(r))), soilV = 8 + 34 * r(), mm = 0.75 + 0.5 * r();
    ctl.setDay(n); const ws = clim.wind ? clim.wind[m] : 2, stress = ctl.stressOf(T, RH, soilV).s;
    const ev = ANG.map(a => ctl.evalAngle(a, sun, irr, T, mm, stress, ws)), pm = Math.max(...ev.map(x => x.pv), 1e-9), cm = Math.max(...ev.map(x => x.crop), 1e-9);
    const J = ev.map(x => 0.5 * x.pv / pm + 0.5 * (cm > 1e-6 ? x.crop / cm : 1)); let bi = 0; J.forEach((v, i) => { if (v > J[bi] + 1e-12) bi = i; });
    const oracle = ANG[bi], prev = Math.max(15, Math.min(60, Math.round((r() < 0.2 ? 15 + 45 * r() : oracle + 8 * gauss(r)) * 2) / 2));   // mostly near the best angle (slow changes), sometimes far (cold start, passing cloud)
    const tr = ctl.evalAngle(prev, sun, irr, T, mm, stress, ws), q = 1;                       // light under the panels at the angle now in use, true state
    const ghiM = irr.ghi * (1 + .05 * q * gauss(r)), parM = 2.05 * tr.lsr * irr.ghi * (1 + .05 * q * gauss(r)), TM = T + 1.2 * q * gauss(r), RHM = Math.max(5, Math.min(100, RH + 3 * q * gauss(r))), soilM = soilV + 1.8 * q * gauss(r);
    const g0 = 1361 * (1 + 0.033 * Math.cos(2 * Math.PI * n / 365)), ktM = ghiM / (g0 * sun.sz), lsrM = parM / 2.05 / Math.max(ghiM, 1);
    const dec = ctl.decide({ ghi: ghiM, parUm: parM, T: TM, RH: RHM, soil: soilM, rain: false, day: n, hour }, { angle: prev });
    const sch = P.schedule ? P.schedule[m][S.winIndex(P, hour)] : 45;
    const f = [sun.sz, sun.sx, ktM, TM, RHM, soilM, lsrM, prev, Math.sin(2 * Math.PI * n / 365), Math.cos(2 * Math.PI * n / 365)];
    const o = k * REC; f.forEach((v, i) => buf[o + i] = v); buf[o + NF] = oracle; buf[o + NF + 1] = dec.angle; buf[o + NF + 2] = sch; ev.forEach((x, i) => { buf[o + NF + 3 + i] = x.pv; buf[o + NF + 3 + 91 + i] = x.crop; });
    k++; if (k % 2000 === 0) console.error(file, k, '/', N);
  }
  fs.writeFileSync(path.join(__dirname, file), Buffer.from(buf.buffer));
}
const nTrain = +process.argv[2] || 40000, nTest = +process.argv[3] || 6000;
make(nTrain, 11, 'train.bin'); make(nTest, 97, 'test.bin');
fs.writeFileSync(path.join(__dirname, 'meta.json'), JSON.stringify({ NF, REC, angles: [15, 60, 0.5], features: ['sz', 'sx', 'kt', 'T', 'RH', 'soil', 'lsr', 'prev', 'sin_doy', 'cos_doy'], lat: clim.lat, nTrain, nTest }));
console.log('done');
