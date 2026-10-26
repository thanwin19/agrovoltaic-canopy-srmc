// Water link study: soil probe vs timer irrigation, probe faults and fallback.   node irrigation_study.js  -> results/T16_irrigation_probe_vs_timer.csv, irrigation_study.json, fig_irrigation_probe_vs_timer.png via make_irrigation_fig.py
const fs = require('fs'), path = require('path');
const ROOT = path.join(__dirname, '..', '..');
const S = require(path.join(ROOT, 'Review3_Digital_Twin', 'code_reference', 'srmc_engine.js')), IRR = require('./irrigation.js');
const DD = path.join(ROOT, 'Review1_Design_and_CAD', 'results', 'design'), L = f => JSON.parse(fs.readFileSync(path.join(DD, f)));
const clim = L('climates.json')[0], soil = L('soils.json')[0], crops = L('crops.json'), D = L('design.json'), dp = D.presets[D.active], pw = +(dp.panelPitch - dp.panelGap).toFixed(4);
const params = { bayLen: dp.bayLen, pitch: dp.panelPitch, panelW: pw, height: dp.clearanceLowestEdge + pw / 2 * Math.sin(dp.maxTiltDeg * Math.PI / 180), tankM3: dp.cistern.m3, rainSlope: dp.rainSlopeDeg, stops: Array.from({ length: Math.round((dp.stopsDeg[1] - dp.stopsDeg[0]) / 5) + 1 }, (_, i) => dp.stopsDeg[0] + 5 * i) };
const R = S.run({ clim, soil, crops, params }), ctx = { P: R.P, clim, soil, zones: R.zones.map(z => Object.assign({}, z, { light: R.zoneMonthly ? R.zoneMonthly[R.zones.indexOf(z)] : z.light })), tankM3: R.P.tankM3 };
const cmp = IRR.compare(S, ctx), engine = R.wb;
const out = { site: clim.name, soil: soil.name, crops: R.zones.map(z => z.crop.name), engine_reference: { supplied_m3: Math.round(engine.supplied), borewell_m3: Math.round(engine.borewellM3), demand_m3: Math.round(engine.demand) }, rows: cmp.rows };
fs.mkdirSync(path.join(__dirname, 'results'), { recursive: true });
fs.writeFileSync(path.join(__dirname, 'results', 'irrigation_study.json'), JSON.stringify(out, null, 1));
const head = ['strategy', 'applied water m3/ha/yr', 'from cistern m3', 'borewell m3', 'irrigation events', 'water-stress days (mean zone)', 'relative yield from water (1 = none lost)', 'percolation loss mm', 'water saved vs timer m3', 'water saved vs timer %'];
fs.writeFileSync(path.join(__dirname, 'results', 'T16_irrigation_probe_vs_timer.csv'), head.join(',') + '\n' + cmp.rows.map(r => [r.name, r.applied_m3_ha, r.cistern_m3, r.borewell_m3, r.events, r.stress_days, r.relative_yield_from_water, r.percolation_loss_mm, r.water_saved_vs_timer_m3, r.water_saved_vs_timer_pct].join(',')).join('\n'));
console.log('engine reference', out.engine_reference); console.table(cmp.rows);
// daily series for the figure
const t = cmp.timer, p = cmp.sims[1][1]; fs.writeFileSync(path.join(__dirname, 'results', 'irrigation_daily.csv'), 'day,rain_mm,timer_m3,probe_m3,probe_avail_z1,tank_probe\n' + Array.from({ length: 365 }, (_, d) => [d + 1, (engine.rain[d]).toFixed(1), t.irrSeries[d].toFixed(1), p.irrSeries[d].toFixed(1), p.availSeries[0][d].toFixed(1), p.tankSeries[d].toFixed(1)].join(',')).join('\n'));
