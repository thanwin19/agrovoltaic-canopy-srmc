const load = require('./load'), ctx = load('SRMC_Digital_Twin_original_copy.html', ['src/srmc_vp.js']);
const S0 = ctx.SRMC, D = ctx.SRMC_DATA, clim = D.climates.find(c => c.id === 'tce_madurai'), soil = D.soils.find(s => s.id === 'red_sandy_loam');
const R = S0.run({ clim, soil, crops: D.crops, params: { tiltMode: 'fixed' }, zoneCrops: [] }), S = ctx.SRMC_VP.fastEngine(S0);
const ctl = ctx.SRMC_SC.make(S, { P: R.P, clim, zones: R.zones }); const n = 15;
for (const [h, a] of [[9, 30], [12, 45], [12, 15], [15, 60]]) {
  const sun = S0.sunVec(clim.lat, n, h), irr = S0.irradiance(sun.sz, n, 0.55), Q = Object.assign({}, R.P, { tiltMode: 'fixed', tilt: a }), gl = S.groundLightHour(Q, sun, irr, a);
  const zl = [0, 1, 2, 3].map(z => gl.slice(z * 10, z * 10 + 10).reduce((p, q) => p + q, 0) / 10 / irr.ghi);
  const ev = ctl.evalAngle(a, sun, ctl.irrFrom(irr.ghi, sun, n), 30, 1, 0, 2);
  console.log(h, a, 'truth lsr', (zl.reduce((p, q) => p + q) / 4).toFixed(4), 'model lsr', ev.lsr.toFixed(4), 'zl', zl.map(v => v.toFixed(2)).join(' '), gl.length);
}
