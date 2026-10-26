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
add('SC v2 ideal sensors', { ideal: true, guard: true });
add('SC v1 noisy (1 reading)', { ns: 1, K: 1, guard: false }); add('SC v2 noisy (median of 5 + guard)', { ns: 1, K: K, guard: true });
for (const ns of [0.5, 2, 3]) { add('v1 noise x' + ns, { ns, K: 1, guard: false, sweep: true }); add('v2 noise x' + ns, { ns, K: K, guard: true, sweep: true }); }
for (const [fn, f] of [['PAR dirty (x0.35)', par => par * .35], ['PAR reflection (x1.9)', par => par * 1.9], ['PAR dead (0)', par => 0]]) { add('v1 fault: ' + fn, { ns: 1, K: 1, guard: false, fault: f, fault_name: fn }); add('v2 fault: ' + fn, { ns: 1, K: K, guard: true, fault: f, fault_name: fn }); }
add('SC v2 stress relax 0 (full crop light)', { ns: 1, K: K, guard: true, ctl: cR0, money_only: true }); add('SC v2 stress relax 0.15', { ns: 1, K: K, guard: true, ctl: cR15, money_only: true });
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
      const addAcc = (name, a) => { const r = score(a), c = acc[name]; c.pv += r.pv * wgt; c.pvO += pm * wgt; c.crop += hw * (cm > 1e-6 ? r.crop / cm : 1) * wgt; c.J += hw * r.J * wgt; c.Jo += hw * Jo * wgt; c.w += hw * wgt; c.sq += (a - o.best.a) ** 2 * wgt; c.n += wgt; };
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
      rowsOut.push([S.MNAME[m], skyName, soilName, hh, o.best.a, st['SC v2 noisy (median of 5 + guard)'].angle, st['SC v1 noisy (1 reading)'].angle, sch]);
      [['Monthly schedule (SRMC-DT)', sch], ['Fixed 45 deg', 45], ['Fixed 15 deg (PV-max)', 15], ['Sun tracking (E-W)', trk]].forEach(([nm, a]) => { addAcc(nm, a); keep(nm, a); });
    }
  }
  console.error('month', S.MNAME[m], ((Date.now() - t0) / 1000).toFixed(0), 's');
}
const fin = name => { const a = acc[name]; return { strategy: name, pv_pct: +(100 * a.pv / a.pvO).toFixed(1), crop_pct: +(100 * a.crop / a.w).toFixed(1), J_pct: +(100 * a.J / a.Jo).toFixed(1), angle_rmse_deg: +Math.sqrt(a.sq / a.n).toFixed(1) }; };
const all = Object.keys(acc).map(fin);
// yield and money ---------------------------------------------------------------------------------------------
const money = {};
for (const [name, s] of Object.entries(sched)) {
  const P2 = Object.assign({}, P, { tiltMode: 'smart', schedule: s }), annual = S.annualLight(P2, clim), zm = [0, 1, 2, 3].map(z => annual.months.map(r => r.strip[z]));
  const zones = R.zones.map((z, k) => Object.assign({}, z, { light: zm[k] })), wb = S.waterBalance(P2, clim, soil, zones, P.tankM3), eco = S.economics(P2, clim, annual, wb, P.tankM3, zones);
  money[name] = { strategy: name, pv_kWh_m2: +annual.pvKWhPerM2.toFixed(1), crop_light_pct: +(100 * annual.meanLight).toFixed(1), crop_net_lakh: +(eco.cropNet / 1e5).toFixed(2), solar_net_lakh: +((eco.solarRev - eco.om) / 1e5).toFixed(2), farmer_inr_month: Math.round(eco.farmerMonthlyAvg || eco.farmerAnnual / 12) };
  money[name].total_lakh = +(money[name].crop_net_lakh + money[name].solar_net_lakh).toFixed(2);
}
const orT = money['Oracle (perfect knowledge)'].total_lakh, orC = money['Oracle (perfect knowledge)'].crop_net_lakh, orP = money['Oracle (perfect knowledge)'].pv_kWh_m2;
Object.values(money).forEach(r => { r.total_pct_of_oracle = +(100 * r.total_lakh / orT).toFixed(1); r.pv_pct_of_oracle = +(100 * r.pv_kWh_m2 / orP).toFixed(1); r.crop_pct_of_oracle = +(100 * r.crop_net_lakh / orC).toFixed(1); });
const od = path.join(__dirname, 'results'); fs.mkdirSync(od, { recursive: true });
const get = n => all.find(x => x.strategy === n);
const main = ['SC v2 ideal sensors', 'SC v2 noisy (median of 5 + guard)', 'SC v1 noisy (1 reading)', 'Monthly schedule (SRMC-DT)', 'Fixed 45 deg', 'Fixed 15 deg (PV-max)', 'Sun tracking (E-W)'].map(get);
const noise = [0.5, 1, 2, 3].map(ns => ({ noise_x: ns, v1: ns === 1 ? get('SC v1 noisy (1 reading)') : get('v1 noise x' + ns), v2: ns === 1 ? get('SC v2 noisy (median of 5 + guard)') : get('v2 noise x' + ns) }));
const faults = ['PAR dirty (x0.35)', 'PAR reflection (x1.9)', 'PAR dead (0)'].map(fn => ({ fault: fn, v1: get('v1 fault: ' + fn), v2: get('v2 fault: ' + fn) }));
fs.writeFileSync(path.join(od, 'accuracy_v2.json'), JSON.stringify({ weights: { energy: W, crop: 1 - W }, readings_per_decision_v2: K, main, noise, faults, money: Object.values(money) }, null, 1));
const csv = (head, rows) => head.join(',') + '\n' + rows.map(r => r.join(',')).join('\n');
fs.writeFileSync(path.join(od, 'T11_accuracy_v2.csv'), csv(['strategy', 'electricity % of best', 'crop light value % of best', 'combined score %', 'angle RMSE vs best (deg)'], main.map(r => [r.strategy, r.pv_pct, r.crop_pct, r.J_pct, r.angle_rmse_deg])));
fs.writeFileSync(path.join(od, 'T12_noise_sweep.csv'), csv(['noise x base', 'v1 combined %', 'v2 combined %', 'v1 angle RMSE', 'v2 angle RMSE'], noise.map(r => [r.noise_x, r.v1.J_pct, r.v2.J_pct, r.v1.angle_rmse_deg, r.v2.angle_rmse_deg])));
fs.writeFileSync(path.join(od, 'T13_fault_test.csv'), csv(['fault', 'v1 combined %', 'v2 combined %', 'v1 angle RMSE', 'v2 angle RMSE'], faults.map(r => [r.fault, r.v1.J_pct, r.v2.J_pct, r.v1.angle_rmse_deg, r.v2.angle_rmse_deg])));
fs.writeFileSync(path.join(od, 'T14_yield_and_money.csv'), csv(['strategy', 'PV kWh/m2', 'crop light %', 'crop net INR lakh', 'solar net INR lakh', 'total INR lakh', 'total % of best', 'PV % of best', 'crop income % of best'], Object.values(money).map(r => [r.strategy, r.pv_kWh_m2, r.crop_light_pct, r.crop_net_lakh, r.solar_net_lakh, r.total_lakh, r.total_pct_of_oracle, r.pv_pct_of_oracle, r.crop_pct_of_oracle])));
fs.writeFileSync(path.join(od, 'angles_by_hour_v2.csv'), 'month,sky,soil,hour,oracle_deg,sensor_v2_deg,sensor_v1_deg,schedule_deg\n' + rowsOut.map(r => r.join(',')).join('\n'));
console.log(JSON.stringify({ main, noise: noise.map(r => [r.noise_x, r.v1.J_pct, r.v2.J_pct]), faults: faults.map(r => [r.fault, r.v1.J_pct, r.v2.J_pct]), money: Object.values(money).map(r => [r.strategy, r.total_lakh, r.crop_net_lakh, r.pv_kWh_m2, r.total_pct_of_oracle]) }, null, 1)); console.error('total', ((Date.now() - t0) / 1000).toFixed(0), 's');
