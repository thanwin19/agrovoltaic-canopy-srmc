// Tests of the controller safety layer: sensor-failure fallbacks (rain, soil), motor wear count, limits on how often the panels may move.
//   node test_safety.js   -> results/safety_tests.md, results/safety_flicker.csv
const fs = require('fs'), path = require('path');
const ROOT = path.join(__dirname, '..', '..');
const S = require(path.join(ROOT, 'Review3_Digital_Twin', 'code_reference', 'srmc_engine.js')), SC = require('./sensor_controller.js');
const DD = path.join(ROOT, 'Review1_Design_and_CAD', 'results', 'design'), L = f => JSON.parse(fs.readFileSync(path.join(DD, f)));
const clim = L('climates.json')[0], soil = L('soils.json')[0], crops = L('crops.json'), D = L('design.json'), dp = D.presets[D.active], pw = +(dp.panelPitch - dp.panelGap).toFixed(4);
const params = { bayLen: dp.bayLen, pitch: dp.panelPitch, panelW: pw, height: dp.clearanceLowestEdge + pw / 2 * Math.sin(dp.maxTiltDeg * Math.PI / 180), tankM3: dp.cistern.m3, rainSlope: dp.rainSlopeDeg, stops: Array.from({ length: Math.round((dp.stopsDeg[1] - dp.stopsDeg[0]) / 5) + 1 }, (_, i) => dp.stopsDeg[0] + 5 * i) };
const R = S.run({ clim, soil, crops, params }), P = R.P, ctl = SC.make(S, { P, clim, zones: R.zones, w: 0.5, maxStep: 6, guard: true });
const ctl0 = SC.make(S, { P, clim, zones: R.zones, w: 0.5, maxStep: 6, guard: true, hyst: 0 });
const out = ['# Controller safety tests', '', 'Fallbacks for the rain and soil sensors, a motor wear count and limits on how often the panels may move (`makeSafe` in sensor_controller.js). Run: `node test_safety.js`.', ''];
const DAY = 285, N = DAY; // 12 Oct (crop in season)
const base = (hour, extra) => { const sun = S.sunVec(clim.lat, N, hour), irr = S.irradiance(sun.sz, N, clim.kt[9]); return Object.assign({ ghi: irr.ghi, parUm: 2.05 * 0.4 * irr.ghi, T: 31, RH: 55, soil: 60, rain: false, wind: 3, day: N, hour }, extra || {}); };
const T = []; const check = (name, ok, detail) => { T.push([name, ok, detail]); };
// 1. rain sensor stuck wet in dry sunny air, 09:00 to 12:00, 5 min steps
{ const safe = ctl.makeSafe(), st = safe.fresh(30), st0 = { angle: 30 }; let flatMin = 0, flat0 = 0, firstOk = null, note = '';
  for (let m = 0; m < 180; m += 5) { const sen = base(9 + m / 60, { rain: true, RH: 40 }), d = safe.step(sen, st), d0 = ctl.decide(sen, st0); st0.angle = d0.angle; if (d.mode === 'RAIN') flatMin += 5; else if (firstOk == null) { firstOk = m; note = d.safety.notes.join('; '); } if (d0.mode === 'RAIN') flat0 += 5; }
  check('Rain sensor stuck wet (dry sunny air, 3 h)', flatMin < 60 && st.fallbackRain > 0, 'without the guard the panels stay flat for ' + flat0 + ' min; with it for ' + flatMin + ' min (fault declared after 30 min). ' + note); }
// 2. rain sensor dead dry while it is really raining (forecast + saturated air + dark sky)
{ const safe = ctl.makeSafe(), st = safe.fresh(30); const sen = base(14.5, { rain: false, RH: 96, ghi: 0.1 * S.irradiance(S.sunVec(clim.lat, N, 14.5).sz, N, 0.85).ghi, rainForecast: true, parUm: 5 }), d = safe.step(sen, st);
  check('Rain sensor dead (reads dry in real rain)', d.mode === 'RAIN', 'forecast + RH 96 % + dark sky gives mode ' + d.mode + ' (angle ' + d.angle + ' deg); without the fallback the panels would stay tilted: ' + ctl.decide(sen, { angle: 30 }).mode); }
// 3. soil probe faults
{ const safe = ctl.makeSafe(), st = safe.fresh(30); let d = safe.step(base(10, { soil: NaN, soilModel: 55 }), st); check('Soil probe unplugged (no reading)', d.safety.soilFallbacks === 1 && /water-balance model/.test(d.safety.notes.join()), d.safety.notes[0]);
  const s2 = ctl.makeSafe(), st2 = s2.fresh(30); s2.step(base(9, { soil: 60 }), st2); d = s2.step(base(9.5, { soil: 5 }), st2); check('Soil probe glitch (60 % to 5 % in 30 min)', d.safety.soilFallbacks === 1, d.safety.notes[0]);
  const s3 = ctl.makeSafe(), st3 = s3.fresh(30); let flagged = null; for (let m = 0; m < 300; m += 10) { const dd = s3.step(base(9 + m / 60, { soil: 12, soilRaw: 2800, soilModel: 62 }), st3); if (dd.safety.soilFallbacks && flagged == null) flagged = m; } check('Soil probe stuck at 12 % for 5 h', flagged != null && flagged >= 170, 'declared stuck after ' + flagged + ' min (limit 180 min), then the model value is used');
  const s4 = ctl.makeSafe(), st4 = s4.fresh(30); d = s4.step(base(10, { soil: 140 }), st4); check('Soil probe out of range (140 %)', d.safety.soilFallbacks === 1, d.safety.notes[0]); }
// 4. cloud flicker: 1-minute steps, 10:00 to 12:00, cloud factor jumping between clear and heavy cloud
function flicker(limit, cc) {
  cc = cc || ctl;
  let seed = 5; const rnd = () => (seed = (seed * 1664525 + 1013904223) % 4294967296) / 4294967296; const safe = cc.makeSafe(limit ? {} : { minHoldS: 0, maxMovesPerHour: 1e9, maxTravelPerDay: 1e9 }), st = safe.fresh(30); let Jsum = 0, wsum = 0; const rows = []; let d;
  for (let m = 0; m < 120; m++) { const hour = 10 + m / 60, cloud = rnd() < 0.5 ? 1 : 0.25 + 0.3 * rnd(), sun = S.sunVec(clim.lat, N, hour), irr0 = S.irradiance(sun.sz, N, clim.kt[9] * cloud), tr = ctl.evalAngle(Math.min(st.angle, 60), sun, irr0, 31, 1, 0, 2);
    const sen = { ghi: irr0.ghi, parUm: 2.05 * tr.lsr * irr0.ghi, T: 31, RH: 55, soil: 60, rain: false, wind: 3, day: N, hour, t: (N * 24 + hour) * 3600 }; cc.setDay(N); d = safe.step(sen, st);
    const o = ctl.search(sun, irr0, 31, 1, 0, 2), ev = o.ev, pm = Math.max(...ev.map(x => x.pv), 1e-9), cm = Math.max(...ev.map(x => x.crop), 1e-9), Jof = x => 0.5 * x.pv / pm + 0.5 * (cm > 1e-6 ? x.crop / cm : 1), q = ctl.evalAngle(Math.min(st.angle, 60), sun, irr0, 31, 1, 0, 2); Jsum += Jof(q) / Jof(o.best) * irr0.ghi; wsum += irr0.ghi; rows.push([m, cloud.toFixed(2), irr0.ghi.toFixed(0), d.angle, o.best.a]); }
  return { J: 100 * Jsum / wsum, safety: d.safety, rows }; }
const fN = flicker(false, ctl0), fH = flicker(false, ctl), fL = flicker(true, ctl0); fs.mkdirSync(path.join(__dirname, 'results'), { recursive: true });
fs.writeFileSync(path.join(__dirname, 'results', 'safety_flicker.csv'), 'minute,cloud,ghi,angle_with_limits,best_angle\n' + fL.rows.map(r => r.join(',')).join('\n'));
const fmt = f => f.safety.moves + ' moves, ' + f.safety.travelDeg.toFixed(0) + ' deg of panel travel, ' + f.safety.wireM.toFixed(1) + ' m of wire (score vs best angle ' + f.J.toFixed(1) + ' %)';
check('Cloud flicker: panels may not hunt', fL.safety.moves <= fN.safety.moves / 2 && fL.safety.movesLastHour <= 12, 'two hours of 1-minute clear/cloud flicker. No protection: ' + fmt(fN) + '. Hysteresis only (the controller default): ' + fmt(fH) + '. Limits without hysteresis: ' + fmt(fL) + ' with ' + fL.safety.heldMoves + ' moves held.');
// 5. normal clear day wear (5 min steps, 05:30 to 18:30)
{ const safe = ctl.makeSafe(), st = safe.fresh(15); let d; for (let m = 0; m < 14 * 60; m += 5) { const hour = 5 + m / 60, sun = S.sunVec(clim.lat, N, hour), irr = S.irradiance(sun.sz, N, clim.kt[9]), tr = ctl.evalAngle(Math.min(st.angle, 60), sun, irr, 31, 1, 0, 2); d = safe.step({ ghi: irr.ghi, parUm: 2.05 * tr.lsr * irr.ghi, T: 31, RH: 55, soil: 60, rain: false, wind: 3, day: N, hour, t: (N * 24 + hour) * 3600 }, st); }
  const w = d.safety; check('Wear on a normal clear day', w.moves > 0 && w.moves <= 80, w.moves + ' moves, ' + w.travelDeg.toFixed(0) + ' deg of panel travel, ' + w.wireM.toFixed(1) + ' m of drive wire, ' + w.drumTurns.toFixed(1) + ' drum turns, ' + w.reversals + ' reversals in one day; about ' + Math.round(w.drumTurns * 365) + ' drum turns and ' + Math.round(w.moves * 365) + ' motor starts per year'); }
out.push('| Test | Result | What happened |', '|---|---|---|', ...T.map(r => '| ' + r[0] + ' | ' + (r[1] ? 'PASS' : 'FAIL') + ' | ' + r[2].replace(/\|/g, '/') + ' |'), '', 'Limits (defaults): minimum 120 s between moves, at most 12 moves per hour, at most 900 deg of panel travel per day; rain flat-roof, storm stow and night park are never blocked. Soil probe fault rules: no reading, outside 0 to 100 %, jump above 40 points in an hour (unless it rained or irrigation ran), or the same raw value for 3 daytime hours. Rain sensor rules: wet for 30 min in dry sunny air (RH under 65 %, sun above 60 % of clear sky) is ignored; a dry reading with a rain forecast, RH of 90 % or more and a dark sky counts as rain.', '', 'Wear numbers use the 0.44 m offset lever arm (wire travel = arm x change of sin(angle - 45 deg)) and a 120 mm drum.', '');
fs.writeFileSync(path.join(__dirname, 'results', 'safety_tests.md'), out.join('\n')); console.log(out.join('\n'));
