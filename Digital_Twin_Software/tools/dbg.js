const load = require('./load'), ctx = load('SRMC_Digital_Twin_original_copy.html', ['src/srmc_vp.js']);
const S = ctx.SRMC, D = ctx.SRMC_DATA, clim = D.climates.find(c => c.id === 'tce_madurai'), soil = D.soils.find(s => s.id === 'red_sandy_loam');
const R = S.run({ clim, soil, crops: D.crops, params: {}, zoneCrops: [] });
console.log(R.zones.map(z => z.crop.id), JSON.stringify(ctx.SRMC_SC.make(S, { P: R.P, clim, zones: R.zones }).seasonWeights.map(a => a.map(v => +v.toFixed(2)))));
const sim = ctx.SRMC_VP.create({ S, SC: ctx.SRMC_SC, R, clim, soil, day: +process.argv[2] || 105, seed: 1, ideal: true });
while (!sim.done()) { const r = sim.stepMinute(); if (r.t % 30 === 0 && r.crop != null) console.log(sim.fmtT(r.t), r.mode, 'cmd', r.cmd, 'ang', r.angle.toFixed(1), 'o', r.oAngle, 'm', r.mAngle, 'ghi', r.ghi.toFixed(0), 'pv', r.pv.toFixed(0), r.pvO.toFixed(0), r.pv15.toFixed(0), 'crop', r.crop.toFixed(0), r.cropO.toFixed(0), r.cropM.toFixed(0), 'e_ghi', r.e_ghi.toFixed(0), 'T', r.T.toFixed(1), r.e_T.toFixed(1), 'soil', r.soil.toFixed(0), r.e_soil.toFixed(0), (r.reason||'').slice(0,90)); }
