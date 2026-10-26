const ctx = require('./load')(process.argv[2]); const S = ctx.SRMC, D = ctx.SRMC_DATA;
const clim = D.climates.find(c => c.id === 'tce_madurai'), P = Object.assign({}, S.DEFAULTS, { tiltMode: 'fixed', tilt: 30 });
const n = 105, sun = S.sunVec(clim.lat, n, 10.3);
const a = { ghi: 0, dni: 500, dhi: 0 }, b = { ghi: 0, dni: 0, dhi: 200 }, ab = { ghi: 0, dni: 500, dhi: 200 };
const ga = S.groundLightHour(P, sun, a, 30), gb = S.groundLightHour(P, sun, b, 30), gab = S.groundLightHour(P, sun, ab, 30);
console.log('lin err', Math.max(...gab.map((v, i) => Math.abs(v - ga[i] - gb[i]))), gab.slice(0, 5));
let t = Date.now(); for (let i = 0; i < 200; i++) S.groundLightHour(P, sun, ab, 30); console.log('gl ms', (Date.now() - t) / 200);
t = Date.now(); for (let i = 0; i < 200; i++) S.panelPower(P, sun, ab, 30, 30, 2); console.log('pv ms', (Date.now() - t) / 200, S.panelPower(P, sun, ab, 30, 30, 2));
