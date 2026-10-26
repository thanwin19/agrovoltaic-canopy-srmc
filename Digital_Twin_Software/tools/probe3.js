const ctx = require('./load')(process.argv[2]); const S = ctx.SRMC, D = ctx.SRMC_DATA;
const clim = D.climates.find(c => c.id === 'tce_madurai'), P = Object.assign({}, S.DEFAULTS, { tiltMode: 'fixed', tilt: 30 });
const b = { ghi: 0, dni: 0, dhi: 200 };
const g1 = S.groundLightHour(P, S.sunVec(clim.lat, 105, 8), b, 30), g2 = S.groundLightHour(P, S.sunVec(clim.lat, 200, 14.5), b, 30);
console.log('diffuse sun-dependence', Math.max(...g1.map((v, i) => Math.abs(v - g2[i]))));
console.log(S.sunVec(clim.lat, 105, 8));
