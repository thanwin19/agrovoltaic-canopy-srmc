const load = require('./load'), ctx = load('SRMC_Digital_Twin_original_copy.html', ['src/srmc_vp.js']);
const S = ctx.SRMC, D = ctx.SRMC_DATA, clim = D.climates.find(c => c.id === 'tce_madurai'), soil = D.soils.find(s => s.id === 'red_sandy_loam');
const R = S.run({ clim, soil, crops: D.crops, params: {}, zoneCrops: [] });
for (const v of JSON.parse(process.argv[2])) { const M = ctx.SRMC_VP.create(Object.assign({ S, SC: ctx.SRMC_SC, R, clim, soil, day: 15, seed: 1 }, v)).runAll();
  console.log(JSON.stringify(v), M.strat.map(s => s.name.slice(0, 12) + ' ' + s.Jpct.toFixed(1) + '/' + s.cropPct.toFixed(1)).join(' | '), 'moves', M.moves); }
