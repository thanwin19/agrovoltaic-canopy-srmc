// Writes results/accuracy_cases.json: a grid of truth states with the sensor readings the controller saw and the JS decisions,
// so MATLAB (srmc_sc_accuracy.m) can repeat the decisions from the SAME readings and score them with its own physics.
const fs = require('fs'), path = require('path');
const ROOT = path.join(__dirname, '..', '..');
const S = require(path.join(ROOT, 'Review3_Digital_Twin', 'code_reference', 'srmc_engine.js')), SC = require('./sensor_controller.js');
const DD = path.join(ROOT, 'Review1_Design_and_CAD', 'results', 'design'), L = f => JSON.parse(fs.readFileSync(path.join(DD, f)));
const clim = L('climates.json')[0], soil = L('soils.json')[0], crops = L('crops.json'), D = L('design.json'), dp = D.presets[D.active], pw = +(dp.panelPitch - dp.panelGap).toFixed(4);
const params = { bayLen: dp.bayLen, pitch: dp.panelPitch, panelW: pw, height: dp.clearanceLowestEdge + pw / 2 * Math.sin(dp.maxTiltDeg * Math.PI / 180), tankM3: dp.cistern.m3, rainSlope: dp.rainSlopeDeg, stops: Array.from({ length: Math.round((dp.stopsDeg[1] - dp.stopsDeg[0]) / 5) + 1 }, (_, i) => dp.stopsDeg[0] + 5 * i) };
const R = S.run({ clim, soil, crops, params }), K = 5, W = 0.5;
const ctl = SC.make(S, { P: R.P, clim, zones: R.zones, w: W, maxStep: 90, guard: true }), ctl1 = SC.make(S, { P: R.P, clim, zones: R.zones, w: W, maxStep: 90, guard: false });
function rng(seed) { let a = seed >>> 0; return () => { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
const gauss = r => { let u = 0; while (!u) u = r(); const v = r(); return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v); };
const cases = [], SKY = [['clear', 1], ['partly cloudy', .65], ['overcast', .3]], SOIL = [26, 15], MONTHS = [0, 3, 6, 9], HOURS = [6, 8, 10, 12, 14, 16];
let id = 0;
for (const m of MONTHS) for (const [sk, kf] of SKY) for (const sv of SOIL) {
  const r = rng(31 * m + 7 * sv + sk.length), n = S.MID[m]; let a1 = null, a2 = null;
  for (let hh = 5; hh < 20; hh++) {
    const hour = hh + .5, sun = S.sunVec(clim.lat, n, hour); if (sun.sz < .02) continue; if (S.irradiance(sun.sz, n, clim.kt[m] * kf).ghi < 20) continue;
    const irr = S.irradiance(sun.sz, n, clim.kt[m] * kf), T = clim.tmean[m] + clim.trange[m] / 2 * Math.sin(2 * Math.PI * (hour - 9) / 24), RH = Math.max(15, Math.min(98, clim.rh[m] - 12 * Math.cos(2 * Math.PI * (hour - 15) / 24)));
    ctl.setDay(n); ctl1.setDay(n); const stress = ctl.stressOf(T, RH, sv).s, one = a => { const tr = ctl.evalAngle(a == null ? 15 : a, sun, irr, T, 1, stress, 2); return { ghi: irr.ghi * (1 + .05 * gauss(r)), parUm: SC.UM_PER_W * tr.lsr * irr.ghi * (1 + .05 * gauss(r)), T: T + 1.2 * gauss(r), RH: Math.max(5, Math.min(100, RH + 3 * gauss(r))), soil: sv + 1.8 * gauss(r), rain: false, wind: 3, day: n, hour }; };
    const list = []; for (let k = 0; k < K; k++) list.push(one(a2)); const single = one(a1), d2 = ctl.decide(ctl.fuse(list), { angle: a2 }), d1 = ctl1.decide(single, { angle: a1 });
    const prev1 = a1 == null ? 15 : a1, prev2 = a2 == null ? 15 : a2; a1 = d1.angle; a2 = d2.angle;
    if (!HOURS.includes(hh)) continue;
    cases.push({ id: ++id, month: m + 1, sky: sk, soilPct: sv, day: n, hour, kt: clim.kt[m] * kf, T, RH, truthStress: stress, prev1, prev2, single, list, js: { v1: d1.angle, v2: d2.angle, mode1: d1.mode, mode2: d2.mode } });
  }
}
const out = { lat: clim.lat, wEnergy: W, zones: R.zones.map(z => ({ id: z.crop.id, lmin: z.crop.lmin, lopt: z.crop.lopt, ym: z.crop.ym, price: z.crop.price })), monthW: ctl.seasonWeights, cases };
fs.writeFileSync(path.join(__dirname, 'results', 'accuracy_cases.json'), JSON.stringify(out)); console.log('accuracy cases', cases.length);
