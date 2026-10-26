// Paper evaluation of the software digital twin (Monte Carlo).  node tools/run_paper_eval.js <shard> <nShards>   then  node tools/merge_eval.js
// Same code as the browser twin (engine, controller and SRMC_VP loaded from the HTML / src).
const fs = require('fs'), path = require('path'), load = require('./load');
const ROOT = path.join(__dirname, '..'), ctx = load(path.join(ROOT, 'SRMC_Digital_Twin_original_copy.html'), [path.join(ROOT, 'src/srmc_vp.js')]);
const S = ctx.SRMC, D = ctx.SRMC_DATA, clim = D.climates.find(c => c.id === 'tce_madurai'), soil = D.soils.find(s => s.id === 'red_sandy_loam');
const shard = +(process.argv[2] || 0), nSh = +(process.argv[3] || 1);
const R = S.run({ clim, soil, crops: D.crops, params: {}, zoneCrops: [] });
const MID = S.MID, jobs = [];
for (const d of MID) for (const seed of [1, 2, 3]) jobs.push({ group: 'normal', day: d, seed });                 // 12 months x 3 weather/sensor seeds
for (const d of MID) jobs.push({ group: 'ideal', day: d, seed: 1, ideal: true });                                  // error budget: perfect sensors
for (const f of ['pyrDrift', 'parDirty', 'dhtDrop', 'soilStuck', 'rainStuck', 'windStuck']) for (const d of [17, 105, 288]) jobs.push({ group: 'fault', day: d, seed: 1, fault: f });
const rainy = []; for (let i = 0; i < 365 && rainy.length < 4; i++) if ((R.wb.rain[i] || 0) >= 8 && i > 250) rainy.push(i + 1);
for (const d of rainy) jobs.push({ group: 'storm', day: d, seed: 1, storm: true });                               // rain + gust front
const out = [];
jobs.forEach((j, k) => { if (k % nSh !== shard) return; const t = Date.now();
  const M = ctx.SRMC_VP.create(Object.assign({ S, SC: ctx.SRMC_SC, R, clim, soil }, j)).runAll(); M.group = j.group; delete M.hidden;
  out.push(M); console.log(k, j.group, j.day, j.fault || '', 'J', M.strat[0].Jpct.toFixed(1), ((Date.now() - t) / 1000).toFixed(1) + ' s'); });
fs.mkdirSync(path.join(ROOT, 'results/raw'), { recursive: true }); fs.writeFileSync(path.join(ROOT, 'results/raw/shard_' + shard + '.json'), JSON.stringify(out));
