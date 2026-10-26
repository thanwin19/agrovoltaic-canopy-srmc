// Year-long evaluation of the five-sensor controller (SRMC-SC) against an oracle and simple strategies.
//   node eval_sensor_controller.js [quick]     -> results/*.csv, *.json, summary.md
// Truth: 12 representative days x 3 sky states x 2 soil states x 14 daylight hours.  Sensors = truth + noise (pyranometer 5 %, PAR 5 %,
// DHT11 +-2 C / +-5 % RH, soil +-3 %).  Oracle = same objective with perfect knowledge and a fine angle search.
const fs = require('fs'), path = require('path');
const ROOT = path.join(__dirname, '..', '..');
const S = require(path.join(ROOT, 'Review3_Digital_Twin', 'code_reference', 'srmc_engine.js'));
const SC = require('./sensor_controller.js');
const DD = path.join(ROOT, 'Review1_Design_and_CAD', 'results', 'design');
const L = f => JSON.parse(fs.readFileSync(path.join(DD, f))), clim = L('climates.json')[0], soil = L('soils.json')[0], crops = L('crops.json');
const D = L('design.json'), dp = D.presets[D.active], pw = +(dp.panelPitch - dp.panelGap).toFixed(4);
const params = { bayLen: dp.bayLen, pitch: dp.panelPitch, panelW: pw, height: dp.clearanceLowestEdge + pw / 2 * Math.sin(dp.maxTiltDeg * Math.PI / 180), tankM3: dp.cistern.m3, rainSlope: dp.rainSlopeDeg, stops: Array.from({ length: Math.round((dp.stopsDeg[1] - dp.stopsDeg[0]) / 5) + 1 }, (_, i) => dp.stopsDeg[0] + 5 * i) };
const R = S.run({ clim, soil, crops, params }); const P = R.P;
const W = 0.5, quick = process.argv[2] === 'quick';
const ctrl = SC.make(S, { P, clim, zones: R.zones, w: W, maxStep: 90, hyst: process.env.HYST ? +process.env.HYST : undefined });
function rng(seed) { let a = seed >>> 0; return () => { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
const gauss = r => { let u = 0, v = 0; while (!u) u = r(); v = r(); return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v); };
const SKY = [['clear', 1.0, .5], ['partly cloudy', .65, .3], ['overcast', .3, .2]], SOIL = [['normal soil 26 %', 26, .7], ['dry soil 15 %', 15, .3]];
const months = quick ? [0, 3, 6, 9] : [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11];
const NREP = quick ? 1 : 2;
const rows = [];   // per (month, sky, soil, hour)
const acc = {};    // strategy -> {pv, pvO, cropRelW, ghiW, J, Jo, n, w}
const strategies = ['SRMC-SC (noisy sensors)', 'SRMC-SC (ideal sensors)', 'Monthly schedule (SRMC-DT)', 'Fixed 45 deg', 'Fixed 15 deg (PV-max)', 'Sun tracking (E-W)'];
strategies.forEach(s => acc[s] = { pv: 0, pvO: 0, crop: 0, cropO: 0, J: 0, Jo: 0, w: 0, hrs: 0 });
const bySky = {}, byMonth = {};
const t0 = Date.now(); let nState = 0;
for (const m of months) {
  const n = S.MID[m];
  for (const [skyName, kf, skyW] of SKY) for (const [soilName, soilV, soilW] of SOIL) {
    const wgt = S.DIM[m] * skyW * soilW; let prevN = null, prevI = null; const seeds = [];
    for (let rep = 0; rep < NREP; rep++) seeds.push(rng(1000 * m + 10 * rep + (skyName.length) + soilV));
    const stN = seeds.map(() => ({ angle: null })), stI = { angle: null };
    for (let hh = 5; hh < 20; hh++) {
      const hour = hh + 0.5, sun = S.sunVec(clim.lat, n, hour); if (sun.sz < 0.02) continue;
      const irr = S.irradiance(sun.sz, n, clim.kt[m] * kf), T = clim.tmean[m] + clim.trange[m] / 2 * Math.sin(2 * Math.PI * (hour - 9) / 24), RH = Math.max(15, Math.min(98, clim.rh[m] - 12 * Math.cos(2 * Math.PI * (hour - 15) / 24)));
      const ws = clim.wind ? clim.wind[m] : 2, stress = ctrl.stressOf(T, RH, soilV).s;
      // oracle: fine search with truth
      const o = ctrl.search(sun, irr, T, 1, stress, ws), ev = o.ev, pm = Math.max(...ev.map(x => x.pv), 1e-9), cm = Math.max(...ev.map(x => x.crop), 1e-9);
      const Jof = x => W * x.pv / pm + (1 - W) * x.crop / cm, Jo = Jof(o.best);
      const score = a => { const x = ctrl.evalAngle(a, sun, irr, T, 1, stress, ws); return { x, J: Jof(x), pv: x.pv, crop: x.crop }; };
      const g = ghiW => ghiW;                                    // hour weight = sunlight in that hour
      const add = (name, r, hw) => { const a = acc[name]; a.pv += r.pv * wgt; a.pvO += pm * wgt; a.crop += hw * r.crop / cm * wgt; a.cropO += hw * wgt; a.J += hw * r.J * wgt; a.Jo += hw * Jo * wgt; a.w += hw * wgt; a.hrs += wgt; };
      const hw = irr.ghi;
      // ideal sensors
      const dI = ctrl.decide({ ghi: irr.ghi, parUm: SC.UM_PER_W * ctrl.evalAngle(stI.angle == null ? P.stops[0] : stI.angle, sun, irr, T, 1, stress, ws).lsr * irr.ghi, T, RH, soil: soilV, rain: false, day: n, hour }, stI); stI.angle = dI.angle; add('SRMC-SC (ideal sensors)', score(dI.angle), hw);
      // noisy sensors (average over repetitions)
      let sNoisy = { pv: 0, crop: 0, J: 0 };
      seeds.forEach((r, k) => {
        const aPrev = stN[k].angle == null ? P.stops[0] : stN[k].angle, tr = ctrl.evalAngle(aPrev, sun, irr, T, 1, stress, ws);
        const sen = { ghi: irr.ghi * (1 + .05 * gauss(r)), parUm: SC.UM_PER_W * tr.lsr * irr.ghi * (1 + .05 * gauss(r)), T: T + 1.2 * gauss(r), RH: Math.max(5, Math.min(100, RH + 3 * gauss(r))), soil: soilV + 1.8 * gauss(r), rain: false, day: n, hour };
        const d = ctrl.decide(sen, stN[k]); stN[k].angle = d.angle; const sc = score(d.angle); sNoisy.pv += sc.pv / NREP; sNoisy.crop += sc.crop / NREP; sNoisy.J += sc.J / NREP;
      });
      add('SRMC-SC (noisy sensors)', sNoisy, hw);
      // baselines
      const wi = S.winIndex(P, hour), sched = P.schedule ? P.schedule[m][wi] : 45;
      add('Monthly schedule (SRMC-DT)', score(sched), hw); add('Fixed 45 deg', score(45), hw); add('Fixed 15 deg (PV-max)', score(15), hw);
      const trk = Math.max(15, Math.min(60, Math.abs(Math.atan2(sun.sx, sun.sz) * 180 / Math.PI))); add('Sun tracking (E-W)', score(trk), hw);
      rows.push({ month: S.MNAME[m], sky: skyName, soil: soilName, hour: hh, oracle: o.best.a, noisy: stN[0].angle, ideal: stI.angle, schedule: sched, stress: +stress.toFixed(2) });
      nState++;
    }
  }
  console.error('month', S.MNAME[m], 'done', ((Date.now() - t0) / 1000).toFixed(0), 's');
}
const out = [];
for (const s of strategies) { const a = acc[s]; out.push({ strategy: s, pv_index_pct: +(100 * a.pv / a.pvO).toFixed(1), crop_index_pct: +(100 * a.crop / a.cropO).toFixed(1), J_efficiency_pct: +(100 * a.J / a.Jo).toFixed(1), pv_kWh_m2_yr: +(a.pv / 1000).toFixed(1) }); }
const od = path.join(__dirname, 'results'); fs.mkdirSync(od, { recursive: true });
fs.writeFileSync(path.join(od, quick ? 'accuracy_quick.json' : 'accuracy_summary.json'), JSON.stringify({ weights: { energy: W, crop: 1 - W }, noise: 'pyranometer 5 %, PAR 5 %, DHT11 +-2 C +-5 % RH, soil +-3 %', states: nState, results: out }, null, 1));
const csv = 'strategy,PV index % of best,crop index % of best,objective J efficiency %,PV kWh/m2 panel/yr (weighted)\n' + out.map(o => [o.strategy, o.pv_index_pct, o.crop_index_pct, o.J_efficiency_pct, o.pv_kWh_m2_yr].join(',')).join('\n');
fs.writeFileSync(path.join(od, quick ? 'accuracy_quick.csv' : 'accuracy_table.csv'), csv);
fs.writeFileSync(path.join(od, quick ? 'angles_quick.csv' : 'angles_by_hour.csv'), 'month,sky,soil,hour,oracle_deg,sensor_noisy_deg,sensor_ideal_deg,schedule_deg,stress\n' + rows.map(r => [r.month, r.sky, r.soil, r.hour, r.oracle, r.noisy, r.ideal, r.schedule, r.stress].join(',')).join('\n'));
console.log(csv); console.error('total', ((Date.now() - t0) / 1000).toFixed(0), 's, states', nState);
