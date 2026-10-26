const load = require('./load'), ctx = load('SRMC_Digital_Twin_original_copy.html', ['src/srmc_vp.js']);
const S = ctx.SRMC, D = ctx.SRMC_DATA, clim = D.climates.find(c => c.id === 'tce_madurai'), soil = D.soils.find(s => s.id === 'red_sandy_loam');
let t = Date.now(); const R = S.run({ clim, soil, crops: D.crops, params: {}, zoneCrops: [] }); console.log('engine', Date.now() - t, 'ms');
const day = +(process.argv[2] || 105), fault = process.argv[3] || 'none', seed = +(process.argv[4] || 1);
t = Date.now(); const sim = ctx.SRMC_VP.create({ S, SC: ctx.SRMC_SC, R, clim, soil, day, seed, fault, storm: process.argv[5] === "storm", ideal: process.argv[6] === "ideal", instant: process.argv[7] === "instant" }); const M = sim.runAll(); console.log('day sim', Date.now() - t, 'ms');
console.log(JSON.stringify({ ...M, hidden: undefined, calib: undefined }, (k, v) => typeof v === 'number' ? +v.toFixed(3) : v, 1).slice(0, 4000));
