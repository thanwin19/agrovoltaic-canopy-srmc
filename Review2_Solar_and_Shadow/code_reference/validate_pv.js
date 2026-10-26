// Validate the engine's open-field PV and irradiation against PVGIS (ERA5, horizontal, 14 % losses) for the TCE site
const fs = require('fs'), S = require('../engine/srmc_engine.js');
const clim = JSON.parse(fs.readFileSync('data/climates.json')).find(c => c.id === 'tce_madurai');
const pv = JSON.parse(fs.readFileSync('out/physics/pvgis_PVGIS-ERA5.json'));
clim.wind = clim.wind; const P = Object.assign({}, S.DEFAULTS, { pitch: 60, panelW: 2.5, tiltMode: 'fixed', tilt: 0 });
const a = S.annualLight(P, clim);
const ref = pv.outputs.monthly.fixed, rows = [];
let sE = 0, sH = 0, rE = 0, rH = 0;
for (let m = 0; m < 12; m++) {
  const eng = a.months[m].pvKWhPerM2Day * S.DIM[m] / P.eff, engH = a.months[m].ghiKWhPerM2Day * S.DIM[m], r = ref[m];
  rows.push({ month: S.MNAME[m], pvgisE: r.E_m, engE: eng, pvgisH: r['H(i)_m'], engH }); sE += eng; sH += engH; rE += r.E_m; rH += r['H(i)_m'];
}
console.log('month   PVGIS kWh/kWp  engine   | PVGIS kWh/m2  engine   | energy diff');
rows.forEach(r => console.log(r.month.padEnd(6), r.pvgisE.toFixed(0).padStart(8), r.engE.toFixed(0).padStart(9), '   |', r.pvgisH.toFixed(0).padStart(8), r.engH.toFixed(0).padStart(9), '   |', ((r.engE / r.pvgisE - 1) * 100).toFixed(1) + ' %'));
console.log('YEAR  ', rE.toFixed(0).padStart(8), sE.toFixed(0).padStart(9), '   |', rH.toFixed(0).padStart(8), sH.toFixed(0).padStart(9), '   |', ((sE / rE - 1) * 100).toFixed(1) + ' % energy,', ((sH / rH - 1) * 100).toFixed(1) + ' % irradiation');
fs.writeFileSync('out/physics/pv_validation.csv', 'month,pvgis_kWh_per_kWp,engine_kWh_per_kWp,pvgis_H_kWh_m2,engine_H_kWh_m2\n' + rows.map(r => [r.month, r.pvgisE, r.engE.toFixed(1), r.pvgisH, r.engH.toFixed(1)].join(',')).join('\n'));
