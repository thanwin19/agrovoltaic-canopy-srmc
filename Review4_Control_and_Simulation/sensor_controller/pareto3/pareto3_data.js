// Energy and crop value of every FIXED tilt angle at the reference site, from the engine (one year, per hectare, assumed prices).
//   node pareto3_data.js  -> pareto3_fixed_tilt.json
const fs = require('fs'), path = require('path');
const ROOT = path.join(__dirname, '..', '..', '..');
const S = require(path.join(ROOT, 'Review3_Digital_Twin', 'code_reference', 'srmc_engine.js'));
const DD = path.join(ROOT, 'Review1_Design_and_CAD', 'results', 'design'), L = f => JSON.parse(fs.readFileSync(path.join(DD, f)));
const clim = L('climates.json')[0], soil = L('soils.json')[0], crops = L('crops.json'), D = L('design.json'), dp = D.presets[D.active], pw = +(dp.panelPitch - dp.panelGap).toFixed(4);
const params = { bayLen: dp.bayLen, pitch: dp.panelPitch, panelW: pw, height: dp.clearanceLowestEdge + pw / 2 * Math.sin(dp.maxTiltDeg * Math.PI / 180), tankM3: dp.cistern.m3, rainSlope: dp.rainSlopeDeg, stops: Array.from({ length: Math.round((dp.stopsDeg[1] - dp.stopsDeg[0]) / 5) + 1 }, (_, i) => dp.stopsDeg[0] + 5 * i) };
const R = S.run({ clim, soil, crops, params }), P = R.P;
function valueOf(sched) {
  const P2 = Object.assign({}, P, { tiltMode: 'smart', schedule: sched }), annual = S.annualLight(P2, clim), zm = [0, 1, 2, 3].map(z => annual.months.map(r => r.strip[z]));
  const zones = R.zones.map((z, k) => Object.assign({}, z, { light: zm[k] })), wb = S.waterBalance(P2, clim, soil, zones, P.tankM3), eco = S.economics(P2, clim, annual, wb, P.tankM3, zones);
  return { pv_kWh_m2: +annual.pvKWhPerM2.toFixed(2), mean_light_pct: +(100 * annual.meanLight).toFixed(2), crop_net_lakh: +(eco.cropNet / 1e5).toFixed(3), solar_net_lakh: +((eco.solarRev - eco.om) / 1e5).toFixed(3) };
}
const out = [];
for (const a of [3, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60]) { const sched = Array.from({ length: 12 }, () => new Array(14).fill(a)); out.push(Object.assign({ tilt: a }, valueOf(sched))); }
fs.writeFileSync(path.join(__dirname, 'pareto3_fixed_tilt.json'), JSON.stringify({ site: clim.name, note: 'one year, per hectare, assumed prices (tariff INR 3/kWh); fixed tilt held all year', rows: out }, null, 1));
console.log(out.map(r => [r.tilt, r.pv_kWh_m2, r.mean_light_pct, r.crop_net_lakh, r.solar_net_lakh].join('\t')).join('\n'));
