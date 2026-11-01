// Closed-loop accuracy of the distilled network in the 864-case test of the paper (noisy single readings; its own previous angle is fed back):  node closed_loop_eval.js
const fs = require('fs'), path = require('path');
const ROOT = path.join(__dirname, '..', '..', '..');
const S = require(path.join(ROOT, 'Review3_Digital_Twin', 'code_reference', 'srmc_engine.js')), SC = require('../sensor_controller.js');
const DD = path.join(ROOT, 'Review1_Design_and_CAD', 'results', 'design'), L = f => JSON.parse(fs.readFileSync(path.join(DD, f)));
const CLIM = L('climates.json'), SOILS = L('soils.json'), crops = L('crops.json'), D = L('design.json'), dp = D.presets[D.active], pw = +(dp.panelPitch - dp.panelGap).toFixed(4);
const params = { bayLen: dp.bayLen, pitch: dp.panelPitch, panelW: pw, height: dp.clearanceLowestEdge + pw / 2 * Math.sin(dp.maxTiltDeg * Math.PI / 180), tankM3: dp.cistern.m3, rainSlope: dp.rainSlopeDeg, stops: Array.from({ length: Math.round((dp.stopsDeg[1] - dp.stopsDeg[0]) / 5) + 1 }, (_, i) => dp.stopsDeg[0] + 5 * i) };
function rng(seed) { let a = seed >>> 0; return () => { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
const gauss = r => { let u = 0; while (!u) u = r(); const v = r(); return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v); };
const SKY = [['clear', 1.0, .5], ['partly cloudy', .65, .3], ['overcast', .3, .2]], SOILC = [['normal', 26, .7], ['dry', 15, .3]];
const W = 0.5;
// variant: { name, K, guard, relax, noPar, base }  ; base strategies: 'plan', 'fix45', 'fix15', 'track'

const MODEL = JSON.parse(fs.readFileSync(path.join(__dirname, 'model.json')));
function nnAngle(sen, prev, n, hour, sun) {                // exactly the computation done on the ESP32 (see srmc_nn.h)
  const g0 = 1361 * (1 + 0.033 * Math.cos(2 * Math.PI * n / 365)), kt = sen.ghi / (g0 * sun.sz), lsr = sen.parUm / 2.05 / Math.max(sen.ghi, 1);
  const f = [sun.sz, sun.sx, kt, sen.T, sen.RH, sen.soil, lsr, prev, Math.sin(2 * Math.PI * n / 365), Math.cos(2 * Math.PI * n / 365)];
  let h = f.map((v, i) => (Math.fround(v) - MODEL.mu[i]) / MODEL.sd[i]);
  MODEL.layers.forEach((L, li) => { const o = L.b.map((b, j) => { let s = b; for (let i = 0; i < h.length; i++) s += L.w[j][i] * h[i]; return s; }); h = li < 2 ? o.map(Math.tanh) : o; });
  return Math.max(15, Math.min(60, Math.round((h[0] * 22.5 + 37.5) * 2) / 2));
}
function runSite(clim, variants, opt) {
  opt = Object.assign({ mism: 1, seed: 1, ns: 1 }, opt || {});
  const soil = SOILS.find(s => s.id === clim.suggest_soil) || SOILS[0], R = S.run({ clim, soil, crops, params }), P = R.P;
  const mk = o => SC.make(S, Object.assign({ P, clim, zones: R.zones, w: W, maxStep: 90, guard: true }, o)), cG = mk({});
  const ctls = {}; variants.forEach(v => { if (!v.base) ctls[v.name] = mk({ guard: v.guard !== false, relax: v.relax, hyst: v.hyst }); });
  const acc = {}; variants.forEach(v => acc[v.name] = { pv: 0, pvO: 0, crop: 0, J: 0, Jo: 0, w: 0, sq: 0, n: 0 });
  const stt = {}, rg = {};
  for (let m = 0; m < 12; m++) {
    const n = S.MID[m];
    for (const [skyName, kf, skyW] of SKY) for (const [soilName, soilV, soilW] of SOILC) {
      const wgt = S.DIM[m] * skyW * soilW; variants.forEach((v, i) => { stt[v.name] = { angle: null }; rg[v.name] = rng(7919 * m + 104729 * i + 31 * skyName.length + soilV + 100003 * opt.seed); });
      for (let hh = 5; hh < 20; hh++) {
        const hour = hh + 0.5, sun = S.sunVec(clim.lat, n, hour); if (sun.sz < 0.02) continue;
        const irr = S.irradiance(sun.sz, n, clim.kt[m] * kf), T = clim.tmean[m] + clim.trange[m] / 2 * Math.sin(2 * Math.PI * (hour - 9) / 24), RH = Math.max(15, Math.min(98, clim.rh[m] - 12 * Math.cos(2 * Math.PI * (hour - 15) / 24)));
        Object.values(ctls).concat([cG]).forEach(c => c.setDay(n)); const ws = clim.wind ? clim.wind[m] : 2, stress = cG.stressOf(T, RH, soilV).s, mm = opt.mism;
        const o = cG.search(sun, irr, T, mm, stress, ws), ev = o.ev, pm = Math.max(...ev.map(x => x.pv), 1e-9), cm = Math.max(...ev.map(x => x.crop), 1e-9), Jof = x => W * x.pv / pm + (1 - W) * (cm > 1e-6 ? x.crop / cm : 1), Jo = Jof(o.best), hw = irr.ghi;
        const add = (name, a) => { const x = cG.evalAngle(a, sun, irr, T, mm, stress, ws), c = acc[name]; c.pv += x.pv * wgt; c.pvO += pm * wgt; c.crop += hw * (cm > 1e-6 ? x.crop / cm : 1) * wgt; c.J += hw * Jof(x) * wgt; c.Jo += hw * Jo * wgt; c.w += hw * wgt; c.sq += (a - o.best.a) ** 2 * wgt; c.n += wgt; };
        const sch = P.schedule ? P.schedule[m][S.winIndex(P, hour)] : 45, trk = Math.max(P.stops[0], Math.min(P.stops[P.stops.length - 1], Math.abs(Math.atan2(sun.sx, sun.sz) * 180 / Math.PI)));
        for (const v of variants) {
          if (v.base) { add(v.name, v.base === 'plan' ? sch : v.base === 'fix45' ? 45 : v.base === 'fix15' ? 15 : trk); continue; }
          const ctl = ctls[v.name], sk = stt[v.name], r = rg[v.name], aPrev = sk.angle == null ? P.stops[0] : sk.angle, tr = cG.evalAngle(aPrev, sun, irr, T, mm, stress, ws), q = opt.ns;
          const reading = () => ({ ghi: irr.ghi * (1 + .05 * q * gauss(r)), parUm: v.noPar ? NaN : SC.UM_PER_W * tr.lsr * mm * irr.ghi * (1 + .05 * q * gauss(r))   /* the PAR sensor sees the true light, model light x mismatch */, T: T + 1.2 * q * gauss(r), RH: Math.max(5, Math.min(100, RH + 3 * q * gauss(r))), soil: soilV + 1.8 * q * gauss(r), rain: false, day: n, hour });
          let sen; if (v.K > 1) { const l = []; for (let k = 0; k < v.K; k++) l.push(reading()); sen = ctl.fuse(l); } else sen = reading();
          let ang; if (v.nn) { ang = nnAngle(sen, sk.angle == null ? P.stops[0] : sk.angle, n, hour, sun); } else { const d = ctl.decide(sen, sk); ang = d.angle; } sk.angle = ang; add(v.name, ang);
        }
      }
    }
  }
  const out = {}; for (const [k, a] of Object.entries(acc)) out[k] = { elec: 100 * a.pv / a.pvO, crop: 100 * a.crop / a.w, J: 100 * a.J / a.Jo, rmse: Math.sqrt(a.sq / a.n) };
  return out;
}

const VARS = [{ name: 'Distilled network (single readings)', K: 1, nn: true }, { name: 'Optimiser, single readings, no hysteresis', K: 1, guard: false, hyst: 0 }, { name: 'Full controller (median of 5, guard, hysteresis)', K: 5, guard: true }, { name: 'Monthly plan', base: 'plan' }, { name: 'Fixed 45 deg', base: 'fix45' }];
const out = CLIM.map(c => ({ site: c.id, r: runSite(c, VARS) }));
const rows = []; out.forEach(o => Object.entries(o.r).forEach(([k, v]) => rows.push([o.site, k, v.elec.toFixed(1), v.crop.toFixed(1), v.J.toFixed(1), v.rmse.toFixed(1)].join(','))));
fs.writeFileSync(path.join(__dirname, 'closed_loop_results.csv'), ['site,strategy,electricity %,crop light %,combined %,tilt RMSE deg'].concat(rows).join(String.fromCharCode(10)));
const mean = k => ({ J: out.reduce((a, o) => a + o.r[k].J, 0) / out.length, elec: out.reduce((a, o) => a + o.r[k].elec, 0) / out.length, crop: out.reduce((a, o) => a + o.r[k].crop, 0) / out.length, rmse: out.reduce((a, o) => a + o.r[k].rmse, 0) / out.length });
const ref = {}; VARS.forEach(v => ref[v.name] = out[0].r[v.name]);
fs.writeFileSync(path.join(__dirname, 'closed_loop_summary.json'), JSON.stringify({ reference_site: ref, mean_over_sites_note: 'the network was trained at the reference site only; other sites use the same weights with the site latitude not changed, so only the reference site is a fair test', mean_all_sites: Object.fromEntries(VARS.map(v => [v.name, mean(v.name)])) }, null, 1));
console.log(JSON.stringify(ref, null, 1));
