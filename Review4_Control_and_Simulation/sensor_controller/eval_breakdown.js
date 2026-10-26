// Accuracy study v2:  node eval_accuracy_v2.js      (about 1 min)
//  (1) how close the controller gets to the best possible electricity and crop light, (2) angle error in degrees,
//  (3) accuracy versus sensor noise (x0.5 ... x3), (4) accuracy with a faulty PAR sensor, v1 (single reading, no guard) versus v2 (median of 5 readings + fault guard),
//  (5) yield and rupees: each strategy's hourly angles run through the engine's crop, water and economics model for a year.
const fs = require('fs'), path = require('path');
const ROOT = path.join(__dirname, '..', '..');
const S = require(path.join(ROOT, 'Review3_Digital_Twin', 'code_reference', 'srmc_engine.js')), SC = require('./sensor_controller.js');
const DD = path.join(ROOT, 'Review1_Design_and_CAD', 'results', 'design'), L = f => JSON.parse(fs.readFileSync(path.join(DD, f)));
const clim = L('climates.json')[0], soil = L('soils.json')[0], crops = L('crops.json'), D = L('design.json'), dp = D.presets[D.active], pw = +(dp.panelPitch - dp.panelGap).toFixed(4);
const params = { bayLen: dp.bayLen, pitch: dp.panelPitch, panelW: pw, height: dp.clearanceLowestEdge + pw / 2 * Math.sin(dp.maxTiltDeg * Math.PI / 180), tankM3: dp.cistern.m3, rainSlope: dp.rainSlopeDeg, stops: Array.from({ length: Math.round((dp.stopsDeg[1] - dp.stopsDeg[0]) / 5) + 1 }, (_, i) => dp.stopsDeg[0] + 5 * i) };
const R = S.run({ clim, soil, crops, params }), P = R.P, W = 0.5, K = 5;
const cR0 = SC.make(S, { P, clim, zones: R.zones, w: W, maxStep: 90, guard: true, relax: 0 }), cR15 = SC.make(S, { P, clim, zones: R.zones, w: W, maxStep: 90, guard: true, relax: 0.15 }), cG = SC.make(S, { P, clim, zones: R.zones, w: W, maxStep: 90, guard: true }), cN = SC.make(S, { P, clim, zones: R.zones, w: W, maxStep: 90, guard: false });
function rng(seed) { let a = seed >>> 0; return () => { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
const gauss = r => { let u = 0; while (!u) u = r(); const v = r(); return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v); };
const SKY = [['clear', 1.0, .5], ['partly cloudy', .65, .3], ['overcast', .3, .2]], SOIL = [['normal soil 26 %', 26, .7], ['dry soil 15 %', 15, .3]];
// strategies --------------------------------------------------------------------------------------------------
const strat = [];
const add = (name, o) => strat.push(Object.assign({ name, ns: 1, K: 1, guard: false, fault: null, ideal: false }, o));

add('SC v2 noisy (median of 5 + guard)', { ns: 1, K: K, guard: true });



const base = ['Monthly schedule (SRMC-DT)', 'Fixed 45 deg', 'Fixed 15 deg (PV-max)', 'Sun tracking (E-W)'];
const acc = {}; [...strat.map(s => s.name), ...base].forEach(n => acc[n] = { pv: 0, pvO: 0, crop: 0, J: 0, Jo: 0, w: 0, sq: 0, n: 0 });
const sched = {}; ['Oracle (perfect knowledge)', ...strat.filter(s => ['SC v1 noisy (1 reading)', 'SC v2 noisy (median of 5 + guard)', 'SC v2 ideal sensors', 'SC v2 stress relax 0 (full crop light)', 'SC v2 stress relax 0.15'].includes(s.name)).map(s => s.name), ...base].forEach(n => sched[n] = Array.from({ length: 12 }, () => new Array(14).fill(15)));
const rowsOut = [];
const t0 = Date.now();
for (let m = 0; m < 12; m++) {
  const n = S.MID[m];
  for (const [skyName, kf, skyW] of SKY) for (const [soilName, soilV, soilW] of SOIL) {
    const wgt = S.DIM[m] * skyW * soilW, st = {}, rg = {}; strat.forEach((s, i) => { st[s.name] = { angle: null }; rg[s.name] = rng(7919 * m + 104729 * i + skyName.length * 31 + soilV); });
    for (let hh = 5; hh < 20; hh++) {
      const hour = hh + 0.5, sun = S.sunVec(clim.lat, n, hour); if (sun.sz < 0.02) continue;
      const irr = S.irradiance(sun.sz, n, clim.kt[m] * kf), T = clim.tmean[m] + clim.trange[m] / 2 * Math.sin(2 * Math.PI * (hour - 9) / 24), RH = Math.max(15, Math.min(98, clim.rh[m] - 12 * Math.cos(2 * Math.PI * (hour - 15) / 24)));
      [cG, cN, cR0, cR15].forEach(c => c.setDay(n)); const ws = clim.wind ? clim.wind[m] : 2, stress = cG.stressOf(T, RH, soilV).s, o = cG.search(sun, irr, T, 1, stress, ws), ev = o.ev;
      const pm = Math.max(...ev.map(x => x.pv), 1e-9), cm = Math.max(...ev.map(x => x.crop), 1e-9), cRel = x => cm > 1e-6 ? x.crop / cm : 1, Jof = x => W * x.pv / pm + (1 - W) * cRel(x), Jo = Jof(o.best), hw = irr.ghi, wi = hh - 5;
      const score = a => { const x = cG.evalAngle(a, sun, irr, T, 1, stress, ws); return { J: Jof(x), pv: x.pv, crop: x.crop }; };
      const addAcc = (name, a) => { const r = score(a); for (const key of [name, name + '|sky:' + skyName, name + '|soil:' + soilName, name + '|season:' + (m<2||m==11?'Dec-Feb':m<5?'Mar-May':m<9?'Jun-Sep':'Oct-Nov')]) { if (!acc[key]) acc[key] = { pv: 0, pvO: 0, crop: 0, J: 0, Jo: 0, w: 0, sq: 0, n: 0 }; const c = acc[key]; c.pv += r.pv * wgt; c.pvO += pm * wgt; c.crop += hw * (cm > 1e-6 ? r.crop / cm : 1) * wgt; c.J += hw * r.J * wgt; c.Jo += hw * Jo * wgt; c.w += hw * wgt; c.sq += (a - o.best.a) ** 2 * wgt; c.n += wgt; } };
      const keep = (name, a) => { if (sched[name] && skyName === 'clear' && soilV === 26) sched[name][m][wi] = a; };
      keep('Oracle (perfect knowledge)', o.best.a);
      for (const s of strat) {
        const ctl = s.ctl || (s.guard ? cG : cN), sk = st[s.name], r = rg[s.name], aPrev = sk.angle == null ? P.stops[0] : sk.angle, tr = cG.evalAngle(aPrev, sun, irr, T, 1, stress, ws);
        const reading = () => { if (s.ideal) return { ghi: irr.ghi, parUm: SC.UM_PER_W * tr.lsr * irr.ghi, T, RH, soil: soilV, rain: false, day: n, hour }; const q = s.ns;
          let par = SC.UM_PER_W * tr.lsr * irr.ghi * (1 + .05 * q * gauss(r)); if (s.fault) par = s.fault(par);
          return { ghi: irr.ghi * (1 + .05 * q * gauss(r)), parUm: par, T: T + 1.2 * q * gauss(r), RH: Math.max(5, Math.min(100, RH + 3 * q * gauss(r))), soil: soilV + 1.8 * q * gauss(r), rain: false, day: n, hour }; };
        let sen; if (s.K > 1) { const l = []; for (let k = 0; k < s.K; k++) l.push(reading()); sen = ctl.fuse(l); } else sen = reading();
        const d = ctl.decide(sen, sk); sk.angle = d.angle; addAcc(s.name, d.angle); keep(s.name, d.angle);
      }
      const wi2 = S.winIndex(P, hour), sch = P.schedule ? P.schedule[m][wi2] : 45, trk = Math.max(15, Math.min(60, Math.abs(Math.atan2(sun.sx, sun.sz) * 180 / Math.PI)));
      rowsOut.push([S.MNAME[m], skyName, soilName, hh, o.best.a, st['SC v2 noisy (median of 5 + guard)'].angle, sch]);
      [['Monthly schedule (SRMC-DT)', sch], ['Fixed 45 deg', 45], ['Fixed 15 deg (PV-max)', 15], ['Sun tracking (E-W)', trk]].forEach(([nm, a]) => { addAcc(nm, a); keep(nm, a); });
    }
  }
  console.error('month', S.MNAME[m], ((Date.now() - t0) / 1000).toFixed(0), 's');
}
const fin = name => { const a = acc[name]; return { group: name, electricity_pct: +(100 * a.pv / a.pvO).toFixed(1), crop_light_pct: +(100 * a.crop / a.w).toFixed(1), combined_pct: +(100 * a.J / a.Jo).toFixed(1), tilt_rmse_deg: +Math.sqrt(a.sq / a.n).toFixed(1) }; };
const out = Object.keys(acc).filter(k => /^(SC v2 noisy|Monthly|Fixed 45)/.test(k)).sort().map(fin);
fs.writeFileSync(path.join(__dirname, 'results', 'accuracy_breakdown.json'), JSON.stringify(out, null, 1));
console.log(out.map(r => [r.group, r.electricity_pct, r.crop_light_pct, r.combined_pct, r.tilt_rmse_deg].join(' | ')).join(String.fromCharCode(10)));
