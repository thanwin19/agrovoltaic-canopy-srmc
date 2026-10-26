// Three extra honesty studies:  node eval_gaps.js
//  A. rupee view: sweep the electricity weight w from 0 (crop only) to 1 (PV only) and run each schedule through the engine's yield and money model
//  B. water baselines: probe against timers of different quality (every 2, 4, 7 days) so the saving is not just against one timer
//  C. year-long hourly run WITH wind and rain: random rain days and a few storms; storm stow on or off (no anemometer)
// -> results/T17_weight_sweep.csv, T18_water_baselines.csv, T19_year_wind_rain.csv + gaps_study.json
const fs = require('fs'), path = require('path');
const ROOT = path.join(__dirname, '..', '..');
const S = require(path.join(ROOT, 'Review3_Digital_Twin', 'code_reference', 'srmc_engine.js')), SC = require('./sensor_controller.js'), IRR = require('./irrigation.js');
const DD = path.join(ROOT, 'Review1_Design_and_CAD', 'results', 'design'), L = f => JSON.parse(fs.readFileSync(path.join(DD, f)));
const clim = L('climates.json')[0], soil = L('soils.json')[0], crops = L('crops.json'), D = L('design.json'), dp = D.presets[D.active], pw = +(dp.panelPitch - dp.panelGap).toFixed(4);
const params = { bayLen: dp.bayLen, pitch: dp.panelPitch, panelW: pw, height: dp.clearanceLowestEdge + pw / 2 * Math.sin(dp.maxTiltDeg * Math.PI / 180), tankM3: dp.cistern.m3, rainSlope: dp.rainSlopeDeg, stops: Array.from({ length: Math.round((dp.stopsDeg[1] - dp.stopsDeg[0]) / 5) + 1 }, (_, i) => dp.stopsDeg[0] + 5 * i) };
const R = S.run({ clim, soil, crops, params }), P = R.P, outDir = path.join(__dirname, 'results');
const csv = (head, rows) => head.join(',') + '\n' + rows.map(r => r.join(',')).join('\n');
function rng(seed) { let a = seed >>> 0; return () => { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
const out = {};
// ------------------------------------------------------------------ A. weight sweep in rupees
function moneyOf(sched) {
  const P2 = Object.assign({}, P, { tiltMode: 'smart', schedule: sched }), annual = S.annualLight(P2, clim), zm = [0, 1, 2, 3].map(z => annual.months.map(r => r.strip[z]));
  const zones = R.zones.map((z, k) => Object.assign({}, z, { light: zm[k] })), wb = S.waterBalance(P2, clim, soil, zones, P.tankM3), eco = S.economics(P2, clim, annual, wb, P.tankM3, zones);
  return { pv: annual.pvKWhPerM2, light: 100 * annual.meanLight, crop: eco.cropNet / 1e5, solar: (eco.solarRev - eco.om) / 1e5, farmer: Math.round(eco.farmerMonthlyAvg || eco.farmerAnnual / 12) };
}
const W = [0, 0.2, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0], sweep = [];
for (const w of W) {
  const ctl = SC.make(S, { P, clim, zones: R.zones, w, maxStep: 90, guard: true }), sched = Array.from({ length: 12 }, () => new Array(14).fill(15));
  for (let m = 0; m < 12; m++) { const n = S.MID[m]; ctl.setDay(n); const st = { angle: null };
    for (let hh = 5; hh < 20; hh++) { const hour = hh + 0.5, sun = S.sunVec(clim.lat, n, hour); if (sun.sz < 0.02) continue;
      const irr = S.irradiance(sun.sz, n, clim.kt[m]), T = clim.tmean[m] + clim.trange[m] / 2 * Math.sin(2 * Math.PI * (hour - 9) / 24), RH = Math.max(15, Math.min(98, clim.rh[m] - 12 * Math.cos(2 * Math.PI * (hour - 15) / 24)));
      const tr = ctl.evalAngle(st.angle == null ? P.stops[0] : st.angle, sun, irr, T, 1, 0, 2), d = ctl.decide({ ghi: irr.ghi, parUm: SC.UM_PER_W * tr.lsr * irr.ghi, T, RH, soil: 26, rain: false, day: n, hour }, st);
      st.angle = d.angle; sched[m][hh - 5] = d.angle; } }
  const r = moneyOf(sched); sweep.push({ w, pv: +r.pv.toFixed(1), light: +r.light.toFixed(1), crop: +r.crop.toFixed(2), solar: +r.solar.toFixed(2), total: +(r.crop + r.solar).toFixed(2), farmer: r.farmer }); console.error('w', w);
}
const pvMax = Math.max(...sweep.map(r => r.pv)), cMax = Math.max(...sweep.map(r => r.crop));
sweep.forEach(r => { r.pv_pct_of_max = +(100 * r.pv / pvMax).toFixed(1); r.crop_pct_of_max = +(100 * r.crop / cMax).toFixed(1); });
fs.writeFileSync(path.join(outDir, 'T17_weight_sweep.csv'), csv(['electricity weight w', 'PV kWh/m2/yr', 'crop light %', 'crop net INR lakh', 'solar net INR lakh', 'total INR lakh', 'farmer INR/month', 'PV % of best', 'crop income % of best'], sweep.map(r => [r.w, r.pv, r.light, r.crop, r.solar, r.total, r.farmer, r.pv_pct_of_max, r.crop_pct_of_max])));
out.weight_sweep = sweep;
// ------------------------------------------------------------------ B. water baselines
const ctx = { P, clim, soil, zones: R.zones.map((z, i) => Object.assign({}, z, { light: R.zoneMonthly ? R.zoneMonthly[i] : z.light })), tankM3: P.tankM3 };
const wrows = []; const probe = IRR.simulate(S, ctx, { type: 'probe' });
const row = (name, r, ref) => ({ name, applied: Math.round(r.appliedM3), events: r.events, stress: +r.stressDays.toFixed(1), yield_: +r.relYield.toFixed(3), perc: Math.round(r.percMm), saved_vs_this: ref ? +(100 * (ref.appliedM3 - probe.appliedM3) / ref.appliedM3).toFixed(1) : '' });
[2, 4, 7].forEach(iv => { const t = IRR.simulate(S, ctx, { type: 'timer', interval: iv }); wrows.push(row('Timer every ' + iv + ' days', t, t)); });
wrows.push(Object.assign(row('Soil probe decides (ideal)', probe, null), { saved_vs_this: '' }));
fs.writeFileSync(path.join(outDir, 'T18_water_baselines.csv'), csv(['strategy', 'applied water m3/ha/yr', 'irrigation events', 'water-stress days', 'relative yield from water', 'percolation loss mm', 'probe saves vs this %'], wrows.map(r => [r.name, r.applied, r.events, r.stress, r.yield_, r.perc, r.saved_vs_this])));
out.water = wrows; console.error('water done');
// ------------------------------------------------------------------ C. year-long hourly run with wind and rain
function yearRun(useWind, seed) {
  const r = rng(seed), ctl = SC.make(S, { P, clim, zones: R.zones, w: 0.5, maxStep: 90, guard: true }), safe = ctl.makeSafe(), st = safe.fresh(P.stops[0]);
  const storms = new Set(); while (storms.size < 4) storms.add(Math.floor(r() * 365)); const stormDays = [...storms];          // 4 storm days a year (assumption)
  const stormStart = {}; stormDays.forEach(d => stormStart[d] = 12 + Math.floor(r() * 6));
  const tot = { pvAct: 0, pvFree: 0, hRain: 0, hStow: 0, hStormWindows: 0, hStormUnprotected: 0, hNight: 0, hours: 0 };
  let wprev = 2, lastSafety = null;
  for (let d = 0; d < 365; d++) {
    const n = d + 1; let m = 0; for (let i = 0; i < 12; i++) if (n > S.CUM[i]) m = i; ctl.setDay(n);
    const rainDay = r() < clim.raindays[m] / S.DIM[m], rainStart = 8 + Math.floor(r() * 10), rainLen = 2 + Math.floor(r() * 4), sky = r(), kf = rainDay ? 0.3 : sky < 0.5 ? 1 : sky < 0.8 ? 0.65 : 0.3, stormDay = stormDays.includes(d), sStart = stormStart[d];
    for (let hh = 0; hh < 24; hh++) {
      const hour = hh + 0.5, sun = S.sunVec(clim.lat, n, hour), irr = sun.sz < 0.02 ? { ghi: 0, dni: 0, dhi: 0 } : S.irradiance(sun.sz, n, clim.kt[m] * kf);
      const T = clim.tmean[m] + clim.trange[m] / 2 * Math.sin(2 * Math.PI * (hour - 9) / 24), RH = rainDay ? 94 : Math.max(15, Math.min(98, clim.rh[m] - 12 * Math.cos(2 * Math.PI * (hour - 15) / 24)));
      let u = -Math.log(1 - r() * 0.999999); const wmean = clim.wind[m] * (1 + 0.35 * Math.sin(2 * Math.PI * (hour - 9) / 24)), wind0 = wmean / 0.886 * Math.sqrt(u);
      let wind = 0.6 * wprev + 0.4 * wind0; wprev = wind; if (stormDay && hh >= sStart && hh < sStart + 4) wind = 15 + 9 * r();
      const rain = rainDay && hh >= rainStart && hh < rainStart + rainLen, tr = ctl.evalAngle(Math.min(st.angle == null ? P.stops[0] : st.angle, 60), sun, irr, T, 1, 0, 2);
      const sen = { ghi: irr.ghi, parUm: SC.UM_PER_W * tr.lsr * irr.ghi, T, RH, soil: 26, rain, wind: useWind ? wind : 0, day: n, hour, t: (n * 24 + hour) * 3600 };
      const dd = safe.step(sen, st), a = dd.angle; lastSafety = dd.safety;
      // electricity this hour at the angle used (stow = 90 deg), against the same hour with no storm and no rain interruption
      const pvAt = (ang) => irr.ghi > 0 ? S.panelPower(Object.assign({}, P, { tiltMode: 'fixed', tilt: ang }), sun, irr, ang, T, 2).p : 0;
      tot.pvAct += pvAt(a); const free = irr.ghi > 0 ? ctl.search(sun, irr, T, 1, 0, 2).best.a : 15; tot.pvFree += pvAt(free); tot.hours++;
      if (dd.mode === 'RAIN') tot.hRain++; if (dd.mode === 'STOW') tot.hStow++; if (wind >= 15) { tot.hStormWindows++; if (a < 90) tot.hStormUnprotected++; }
    }
  }
  return Object.assign(tot, { moves: lastSafety.moves, travelDeg: lastSafety.travelDeg, wireM: lastSafety.wireM, drumTurns: lastSafety.drumTurns, stormDays });
}
const w1 = yearRun(true, 11), w0 = yearRun(false, 11);
const rows = [['With anemometer (storm stow at 15 m/s)', w1], ['Anemometer missing or dead (never stows)', w0]].map(([nm, x]) => [nm, x.hStormWindows, x.hStormUnprotected, x.hStow, x.hRain, +(100 * x.pvAct / x.pvFree).toFixed(2), x.moves, Math.round(x.travelDeg), +x.wireM.toFixed(0), +x.drumTurns.toFixed(0)]);
fs.writeFileSync(path.join(outDir, 'T19_year_wind_rain.csv'), csv(['case', 'storm hours (wind >= 15 m/s)', 'storm hours NOT stowed', 'hours stowed', 'hours flat for rain', 'electricity % of the same year without storms or rain stops', 'moves', 'panel travel deg', 'drive wire m', 'drum turns'], rows));
out.year = rows.map(r => ({ case: r[0], storm_hours: r[1], storm_hours_not_stowed: r[2], hours_stowed: r[3], hours_rain_flat: r[4], pv_pct: r[5], moves: r[6], travel_deg: r[7], wire_m: r[8], drum_turns: r[9] }));
fs.writeFileSync(path.join(outDir, 'gaps_study.json'), JSON.stringify(out, null, 1));
console.log(JSON.stringify(out, null, 1));
