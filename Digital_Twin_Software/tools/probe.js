const ctx = require('./load')(process.argv[2]); const S = ctx.SRMC, D = ctx.SRMC_DATA;
const clim = D.climates.find(c => c.id === 'tce_madurai'), soil = D.soils.find(s => s.id === 'red_sandy_loam');
console.log(Object.keys(clim), clim.kt, clim.wind);
const t0 = Date.now(); const R = S.run({ clim, soil, crops: D.crops, params: {}, zoneCrops: [] }); console.log('run ms', Date.now() - t0);
console.log(Object.keys(R.wb), R.wb.theta.length, R.wb.theta[0].length, R.wb.rain.slice(0, 5), Object.keys(R.P).join(' '));
console.log(Object.keys(soil), R.zones.map(z => z.crop.id + ' kc:' + JSON.stringify(z.crop.kc)));
const SC = ctx.SRMC_SC.make(S, { P: R.P, clim, zones: R.zones, w: 0.5 }); const n = 105, sun = S.sunVec(clim.lat, n, 12), irr = S.irradiance(sun.sz, n, clim.kt[3]);
let t1 = Date.now(); for (let i = 0; i < 100; i++) SC.evalAngle(30, sun, irr, 30, 1, 0, 2); console.log('evalAngle ms', (Date.now() - t1) / 100, irr);
