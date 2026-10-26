// General accuracy study (site-independent):  node eval_general.js [sites|ablation|seeds|all]
//  1. sites    : the six-sensor controller and baselines at seven climates (9.9 to 30.9 deg N), noisy sensors, 864 cases each
//  2. ablation : what each sensor is worth. The true crop light is the model light times a mismatch m (0.8, 1.0, 1.2: dirt, shading error, different canopy);
//                the controller can only learn m from the PAR sensor. Variants: full, no PAR sensor, no DHT11 and soil stress, single readings with no guard.
//  3. seeds    : 8 independent noise draws at the reference site -> mean, standard deviation, 95 % interval
// Writes results/T20_multisite.csv, T21_ablation.csv, T22_seeds.csv and general_study.json
const fs = require('fs'), path = require('path');
const ROOT = path.join(__dirname, '..', '..');
const S = require(path.join(ROOT, 'Review3_Digital_Twin', 'code_reference', 'srmc_engine.js')), SC = require('./sensor_controller.js');
const DD = path.join(ROOT, 'Review1_Design_and_CAD', 'results', 'design'), L = f => JSON.parse(fs.readFileSync(path.join(DD, f)));
const CLIM = L('climates.json'), SOILS = L('soils.json'), crops = L('crops.json'), D = L('design.json'), dp = D.presets[D.active], pw = +(dp.panelPitch - dp.panelGap).toFixed(4);
const params = { bayLen: dp.bayLen, pitch: dp.panelPitch, panelW: pw, height: dp.clearanceLowestEdge + pw / 2 * Math.sin(dp.maxTiltDeg * Math.PI / 180), tankM3: dp.cistern.m3, rainSlope: dp.rainSlopeDeg, stops: Array.from({ length: Math.round((dp.stopsDeg[1] - dp.stopsDeg[0]) / 5) + 1 }, (_, i) => dp.stopsDeg[0] + 5 * i) };
function rng(seed) { let a = seed >>> 0; return () => { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
const gauss = r => { let u = 0; while (!u) u = r(); const v = r(); return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v); };
const SKY = [['clear', 1.0, .5], ['partly cloudy', .65, .3], ['overcast', .3, .2]], SOILC = [['normal', 26, .7], ['dry', 15, .3]];
const W = 0.5;
// variant: { name, K, guard, relax, noPar, base }  ; base strategies: 'plan', 'fix45', 'fix15', 'track'
function runSite(clim, variants, opt) {
  opt = Object.assign({ mism: 1, seed: 1, ns: 1 }, opt || {});
  const soil = SOILS.find(s => s.id === clim.suggest_soil) || SOILS[0], R = S.run({ clim, soil, crops, params }), P = R.P;
  const mk = o => SC.make(S, Object.assign({ P, clim, zones: R.zones, w: W, maxStep: 90, guard: true }, o)), cG = mk({});
  const ctls = {}; variants.forEach(v => { if (!v.base) ctls[v.name] = mk({ guard: v.guard !== false, relax: v.relax }); });
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
          const d = ctl.decide(sen, sk); sk.angle = d.angle; add(v.name, d.angle);
        }
      }
    }
  }
  const out = {}; for (const [k, a] of Object.entries(acc)) out[k] = { elec: 100 * a.pv / a.pvO, crop: 100 * a.crop / a.w, J: 100 * a.J / a.Jo, rmse: Math.sqrt(a.sq / a.n) };
  return out;
}
const f1 = x => +x.toFixed(1), csv = (head, rows) => head.join(',') + '\n' + rows.map(r => r.join(',')).join('\n');
const FULL = { name: 'Six-sensor controller', K: 5, guard: true }, SINGLE = { name: 'Single readings, no guard', K: 1, guard: false }, NOPAR = { name: 'No PAR sensor', K: 5, guard: true, noPar: true }, NOSTR = { name: 'No DHT11 or soil stress', K: 5, guard: true, relax: 0 };
const BASES = [{ name: 'Monthly plan', base: 'plan' }, { name: 'Fixed 45 deg', base: 'fix45' }, { name: 'Fixed 15 deg', base: 'fix15' }, { name: 'Sun tracking', base: 'track' }];
const what = process.argv[2] || 'all', res = {}, od = path.join(__dirname, 'results');
if (what === 'sites' || what === 'all') {
  res.sites = CLIM.map(c => { const r = runSite(c, [FULL].concat(BASES)); console.error('site', c.id); return { site: c.name, lat: c.lat, soil: c.suggest_soil, r }; });
  fs.writeFileSync(path.join(od, 'T20_multisite.csv'), csv(['site', 'latitude', 'strategy', 'electricity %', 'crop light %', 'combined %', 'tilt RMSE deg'], res.sites.flatMap(s => Object.entries(s.r).map(([k, v]) => [JSON.stringify(s.site), s.lat, k, f1(v.elec), f1(v.crop), f1(v.J), f1(v.rmse)]))));
}
if (what === 'ablation' || what === 'all') {
  res.ablation = [0.8, 1.0, 1.2].map(mm => { const per = CLIM.map(c => runSite(c, [FULL, NOPAR, NOSTR, SINGLE, BASES[0]], { mism: mm })); console.error('ablation mismatch', mm); const agg = {}; Object.keys(per[0]).forEach(k => agg[k] = { J: per.reduce((a, r) => a + r[k].J, 0) / per.length, elec: per.reduce((a, r) => a + r[k].elec, 0) / per.length, crop: per.reduce((a, r) => a + r[k].crop, 0) / per.length, rmse: per.reduce((a, r) => a + r[k].rmse, 0) / per.length, minJ: Math.min(...per.map(r => r[k].J)) }); return { mism: mm, agg }; });
  fs.writeFileSync(path.join(od, 'T21_ablation.csv'), csv(['light mismatch m', 'variant', 'combined % (mean of 7 sites)', 'worst site combined %', 'electricity %', 'crop light %', 'tilt RMSE deg'], res.ablation.flatMap(a => Object.entries(a.agg).map(([k, v]) => [a.mism, k, f1(v.J), f1(v.minJ), f1(v.elec), f1(v.crop), f1(v.rmse)]))));
}
if (what === 'seeds' || what === 'all') {
  const J = [], E = [], C = []; for (let s = 1; s <= 8; s++) { const r = runSite(CLIM[0], [FULL], { seed: s })[FULL.name]; J.push(r.J); E.push(r.elec); C.push(r.crop); console.error('seed', s, r.J.toFixed(2)); }
  const st = a => { const m = a.reduce((x, y) => x + y, 0) / a.length, sd = Math.sqrt(a.reduce((x, y) => x + (y - m) ** 2, 0) / (a.length - 1)); return { mean: m, sd, lo: m - 2.365 * sd / Math.sqrt(a.length), hi: m + 2.365 * sd / Math.sqrt(a.length), min: Math.min(...a), max: Math.max(...a) }; };
  res.seeds = { combined: st(J), electricity: st(E), crop: st(C) };
  fs.writeFileSync(path.join(od, 'T22_seeds.csv'), csv(['metric', 'mean %', 'sd', '95% interval low', '95% interval high', 'min', 'max'], Object.entries(res.seeds).map(([k, v]) => [k, v.mean.toFixed(2), v.sd.toFixed(3), v.lo.toFixed(2), v.hi.toFixed(2), v.min.toFixed(2), v.max.toFixed(2)])));
}
const jf = path.join(od, 'general_' + what + '.json'); let old = {}; try { old = JSON.parse(fs.readFileSync(jf)); } catch (e) { }
fs.writeFileSync(jf, JSON.stringify(Object.assign(old, res), null, 1)); console.log('done', Object.keys(res));
