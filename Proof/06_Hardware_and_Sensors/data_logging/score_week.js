// Scores a logged week (fake or real) with the six-sensor controller.
//   node score_week.js week.csv [--dry 3200 --wet 1300] [--out folder]
// For every daytime reading: the controller decides from the (median-filtered) sensors; the decision is scored against the best possible angle for that reading
// (same 50 % electricity + 50 % crop light score as the accuracy study). It also scores the angle that was actually logged (if the panels were moving),
// a fixed 45 deg panel, a fixed 15 deg panel and the monthly plan, estimates the week's electricity, and checks the sensors for faults.
const fs = require('fs'), path = require('path'), { setup, solarTime, monthOfDay, parseCsv } = require('./common.js');
const argv = process.argv.slice(2), file = argv.find(a => !a.startsWith('--') && !/^\d+$/.test(a)), opt = k => { const i = argv.indexOf('--' + k); return i >= 0 ? argv[i + 1] : null; };
if (!file) { console.error('usage: node score_week.js week.csv [--dry 3200 --wet 1300] [--out folder]'); process.exit(1); }
const DRY = +(opt('dry') || 3200), WET = +(opt('wet') || 1300), outDir = opt('out') || path.join(path.dirname(file), 'score_' + path.basename(file, '.csv'));
const { S, SC, clim, P, ctl } = setup(), rows = parseCsv(file), W = 0.5; fs.mkdirSync(outDir, { recursive: true });
const times = rows.map(r => Date.parse(r.timestamp)); const dts = times.slice(1).map((t, i) => (t - times[i]) / 1000).filter(x => x > 0).sort((a, b) => a - b), dtS = dts.length ? dts[Math.floor(dts.length / 2)] : 300, dtH = dtS / 3600;
const fuse = (list) => ctl.fuse(list);
let prevAngle = 15, lastT = 28, lastRH = 60; const win = [], out = [], flags = { dht: 0, par: 0, ghiHigh: 0, gaps: 0, rainRows: 0, stow: 0 }, flagDays = {};
const acc = ['controller', 'logged angle', 'fixed 45 deg', 'fixed 15 deg', 'monthly plan'].reduce((o, k) => (o[k] = { pv: 0, pvO: 0, crop: 0, J: 0, Jo: 0, w: 0, sq: 0, n: 0, kwh: 0 }, o), {}); let kwhOracle = 0, nDay = 0, changes = 0, lastCtl = null;
const soilHist = [];
rows.forEach((r, i) => {
  const st = solarTime(r.timestamp, clim.lon), n = st.day, m = monthOfDay(n), sun = S.sunVec(clim.lat, n, st.hour), up = sun.sz > 0.02 && (r.ghi || 0) >= 20, dayKey = String(r.timestamp).slice(0, 10);
  if (i > 0 && (times[i] - times[i - 1]) / 1000 > 3 * dtS) { flags.gaps++; (flagDays[dayKey] = flagDays[dayKey] || new Set()).add('data gap'); }
  const dhtOk = r.tempC != null && r.tempC > -100 && r.rh != null && r.rh >= 0 && r.rh <= 100; if (!dhtOk) { flags.dht++; (flagDays[dayKey] = flagDays[dayKey] || new Set()).add('DHT11 read failures'); } else { lastT = r.tempC; lastRH = r.rh; }
  const soil = Math.max(0, Math.min(100, 100 * (DRY - r.soilRaw) / (DRY - WET))); soilHist.push({ day: dayKey, raw: r.soilRaw, up });
  const rain = !!r.rain, wind = r.wind == null ? 0 : r.wind; if (rain) flags.rainRows++; if (wind >= 15) flags.stow++;
  const logged = r.angleDeg != null ? Math.min(90, r.angleDeg) : null, aNow = logged != null ? logged : prevAngle;
  let par = r.par; if (par == null && up) { ctl.setDay(n); const irr0 = S.irradiance(sun.sz, n, Math.min(.85, r.ghi / (1361 * Math.max(sun.sz, .05)))); par = SC.UM_PER_W * ctl.evalAngle(Math.min(aNow, 60), sun, { ghi: r.ghi, dni: irr0.dni * r.ghi / Math.max(irr0.ghi, 1), dhi: irr0.dhi * r.ghi / Math.max(irr0.ghi, 1) }, lastT, 1, 0, 2).lsr * r.ghi; }
  let parRatio = null; if (up && r.par != null) { const irrR = ctl.irrFrom(r.ghi, sun, n), mod = ctl.evalAngle(Math.min(aNow, 60), sun, irrR, lastT, 1, 0, 2).lsr; if (mod > 0.01) parRatio = (r.par / SC.UM_PER_W / r.ghi) / mod; }
  const reading = { ghi: r.ghi || 0, parUm: par || 0, parRatio, T: dhtOk ? r.tempC : lastT, RH: dhtOk ? r.rh : lastRH, soil, rain, wind, day: n, hour: st.hour };
  win.push(reading); if (win.length > 5) win.shift();
  ctl.setDay(n); const d = ctl.decide(fuse(win), { angle: aNow }); prevAngle = d.angle; if (lastCtl != null && d.angle !== lastCtl) changes++; lastCtl = d.angle; if (d.fault) { flags.par++; (flagDays[dayKey] = flagDays[dayKey] || new Set()).add('PAR sensor implausible'); }
  const row = { timestamp: r.timestamp, solarHour: +st.hour.toFixed(2), ghi: r.ghi, par: r.par, tempC: reading.T, rh: reading.RH, soilPct: +soil.toFixed(1), rain: rain ? 1 : 0, wind, angleLogged: logged, angleController: d.angle, mode: d.mode, angleBest: '', Jctl: '', fault: d.fault || '' };
  if (up && !rain && wind < 15) {
    nDay++; const clear = S.irradiance(sun.sz, n, 0.85).ghi; if (r.ghi > 1.15 * clear) { flags.ghiHigh++; (flagDays[dayKey] = flagDays[dayKey] || new Set()).add('pyranometer above clear-sky'); }
    const irr = ctl.irrFrom(r.ghi, sun, n), stress = ctl.stressOf(reading.T, reading.RH, soil).s, ws = clim.wind ? clim.wind[m] : 2, o = ctl.search(sun, irr, reading.T, 1, stress, ws), ev = o.ev;
    const pm = Math.max(...ev.map(x => x.pv), 1e-9), cm = Math.max(...ev.map(x => x.crop), 1e-9), cRel = x => cm > 1e-6 ? x.crop / cm : 1, Jof = x => W * x.pv / pm + (1 - W) * cRel(x), Jo = Jof(o.best), hw = r.ghi;
    const sc = a => { const x = ctl.evalAngle(Math.min(a, 60), sun, irr, reading.T, 1, stress, ws); return { x, J: Jof(x) }; };
    const add = (k, a) => { if (a == null) return; const q = sc(a), c = acc[k]; c.pv += q.x.pv * hw; c.pvO += pm * hw; c.crop += hw * cRel(q.x); c.J += hw * q.J; c.Jo += hw * Jo; c.w += hw; c.sq += (a - o.best.a) ** 2; c.n++; c.kwh += q.x.pv * dtH / 1000; return q; };
    const qc = add('controller', d.angle); add('logged angle', logged); add('fixed 45 deg', 45); add('fixed 15 deg', 15); add('monthly plan', P.schedule ? P.schedule[m][S.winIndex(P, st.hour)] : 45); kwhOracle += o.best.pv * dtH / 1000;
    row.angleBest = o.best.a; row.Jctl = +(100 * qc.J / Jo).toFixed(1);
    if (r.par != null) { const model = ctl.evalAngle(Math.min(aNow, 60), sun, irr, reading.T, 1, stress, ws).lsr * r.ghi * SC.UM_PER_W; if (model > 5 && (r.par / model < 0.5 || r.par / model > 1.6)) (flagDays[dayKey] = flagDays[dayKey] || new Set()).add('PAR/pyranometer ratio implausible'); }
  }
  out.push(row);
});
// stuck soil probe: same raw value for 3 h of daytime
const byDay = {}; soilHist.forEach(h => { (byDay[h.day] = byDay[h.day] || []).push(h); }); const need = Math.round(3 * 3600 / dtS); let stuck = 0;
Object.entries(byDay).forEach(([dk, arr]) => { let run = 1; for (let i = 1; i < arr.length; i++) { run = arr[i].raw === arr[i - 1].raw ? run + 1 : 1; if (run === need) { stuck++; (flagDays[dk] = flagDays[dk] || new Set()).add('soil probe stuck for 3 h'); } } });
const pct = (a, b) => b > 0 ? +(100 * a / b).toFixed(1) : null, res = {};
for (const [k, c] of Object.entries(acc)) res[k] = c.n ? { electricity_pct: pct(c.pv, c.pvO), crop_pct: pct(c.crop, c.w), J_pct: pct(c.J, c.Jo), angle_rmse_deg: +Math.sqrt(c.sq / c.n).toFixed(1), kWh_per_m2_week: +c.kwh.toFixed(2) } : null;
const days = [...new Set(out.map(r => String(r.timestamp).slice(0, 10)))], summary = { file: path.basename(file), rows: rows.length, days: days.length, interval_s: dtS, daytime_scored_rows: nDay, soil_calibration: { dry_raw: DRY, wet_raw: WET },
  scores: res, kWh_per_m2_week_best_possible: +kwhOracle.toFixed(2), controller_angle_changes: changes, data_quality: { complete_pct: pct(rows.length, Math.round((times[times.length - 1] - times[0]) / 1000 / dtS) + 1), dht11_failures: flags.dht, dht11_failure_pct: pct(flags.dht, rows.length), par_guard_triggers: flags.par, pyranometer_above_clearsky: flags.ghiHigh, data_gaps: flags.gaps, stuck_soil_events: stuck, rain_rows: flags.rainRows, storm_rows_wind_ge_15: flags.stow }, flagged_days: Object.fromEntries(Object.entries(flagDays).map(([k, v]) => [k, [...v]])) };
fs.writeFileSync(path.join(outDir, 'week_summary.json'), JSON.stringify(summary, null, 1));
fs.writeFileSync(path.join(outDir, 'week_scores.csv'), Object.keys(out[0]).join(',') + '\n' + out.map(r => Object.values(r).map(v => v == null ? '' : v).join(',')).join('\n'));
const c = res['controller'], L = res['logged angle'], f45 = res['fixed 45 deg'], f15 = res['fixed 15 deg'], pl = res['monthly plan'];
const md = ['# Week score: ' + path.basename(file), '', `${rows.length} readings over ${days.length} days (every ${dtS} s), ${nDay} daytime readings scored.`, '', '## How close to the best possible (100 % = best angle for each reading)', '', '| Strategy | Electricity % | Crop light % | Combined score % | Tilt error (deg) | Week electricity (kWh/m2 panel) |', '|---|---|---|---|---|---|',
  ...Object.entries(res).filter(([k, v]) => v).map(([k, v]) => `| ${k} | ${v.electricity_pct} | ${v.crop_pct} | ${v.J_pct} | ${v.angle_rmse_deg} | ${v.kWh_per_m2_week} |`), `| best possible | 100 | 100 | 100 | 0 | ${summary.kWh_per_m2_week_best_possible} |`, '',
  c ? `The controller scored ${c.J_pct} % of the best combined score` + (f45 ? ` (fixed 45 deg: ${f45.J_pct} %, fixed 15 deg: ${f15.J_pct} %, monthly plan: ${pl.J_pct} %).` : '.') : 'No daytime readings to score.', L ? `The angle that was actually logged scored ${L.J_pct} %.` : 'No angle column in the log, so the as-built angle was not scored.', '', '## Data quality', '',
  ...Object.entries(summary.data_quality).map(([k, v]) => `- ${k.replace(/_/g, ' ')}: ${v}`), '', '## Flagged days', '', ...(Object.keys(summary.flagged_days).length ? Object.entries(summary.flagged_days).map(([d, f]) => `- ${d}: ${f.join('; ')}`) : ['- none']), '', 'Files: week_scores.csv (every reading), week_summary.json. Scores use the logged sensor values as truth, so a faulty sensor lowers confidence in them; check the flagged days first.', ''].join('\n');
fs.writeFileSync(path.join(outDir, 'week_report.md'), md); console.log(md);
