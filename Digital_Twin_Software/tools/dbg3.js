const load = require('./load'), ctx = load('SRMC_Digital_Twin_original_copy.html', ['src/srmc_vp.js']);
const S = ctx.SRMC, D = ctx.SRMC_DATA, clim = D.climates.find(c => c.id === 'tce_madurai'), soil = D.soils.find(s => s.id === 'red_sandy_loam');
const R = S.run({ clim, soil, crops: D.crops, params: {}, zoneCrops: [] });
const sim = ctx.SRMC_VP.create({ S, SC: ctx.SRMC_SC, R, clim, soil, day: 15, seed: 1, ideal: true, hyst: 0, instant: true, noParCal: true });
let k = 0; while (!sim.done()) { const r = sim.stepMinute(); const d = sim.state.decision; if (r.reason && k++ < 80 && r.t % 10 === 0) console.log(sim.fmtT(r.t), 'tgt', d.target, 'cmd', r.cmd, 'o', r.oAngle, 'm', r.mAngle, d.mode, 'ghi', r.ghi.toFixed(0), r.e_ghi.toFixed(0)); }
