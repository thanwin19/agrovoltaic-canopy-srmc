// Evaluates one agrivoltaic design per input line with the digital-twin engine (one year, per hectare, assumed prices).
// stdin: JSON {gcr, clearance, tiltMax, w} per line; stdout: JSON {solar, crop, steel_t, rainfed, pv, light} per line.   Used by nsga.py
const fs = require('fs'), path = require('path'), readline = require('readline');
const ROOT = path.join(__dirname, '..', '..', '..');
const S = require(path.join(ROOT, 'Review3_Digital_Twin', 'code_reference', 'srmc_engine.js'));
const DD = path.join(ROOT, 'Review1_Design_and_CAD', 'results', 'design'), L = f => JSON.parse(fs.readFileSync(path.join(DD, f)));
const clim = L('climates.json')[0], soil = L('soils.json')[0], crops = L('crops.json'), D = L('design.json'), dp = D.presets[D.active], PW = 2.497;
function steelPerHa(pitch, pivotH) {                       // screening mass of one 25 x 25 m unit (columns, tubes, ropes), scaled to a hectare
  const nrow = Math.floor(25 / pitch), cols = 36 * (pivotH + 1.15 + 0.4) * 36.5, tubes = nrow * 25 * 10.85, ropes = 149 + 340 * (pivotH / 5.58);
  return 16 * (cols + tubes + ropes) / 1000;                // tonnes per hectare
}
function evalDesign(d) {
  const pitch = PW / d.gcr, top = Math.round(d.tiltMax / 5) * 5, stops = []; for (let a = 15; a <= top; a += 5) stops.push(a);
  const height = d.clearance + PW / 2 * Math.sin(top * Math.PI / 180);
  const params = { bayLen: dp.bayLen, pitch, panelW: PW, height, tankM3: dp.cistern.m3, rainSlope: dp.rainSlopeDeg, stops, energyWeight: d.w };
  const R = S.run({ clim, soil, crops, params }), e = R.eco;
  return { solar: +((e.solarRev - e.om) / 1e5).toFixed(3), crop: +(e.cropNet / 1e5).toFixed(3), steel_t: +steelPerHa(pitch, height).toFixed(2), rainfed: +(100 * R.wb.supplied / Math.max(R.wb.demand, 1)).toFixed(2), pv: +R.annual.pvKWhPerM2.toFixed(1), light: +(100 * R.annual.meanLight).toFixed(2), pitch: +pitch.toFixed(2), height: +height.toFixed(2) };
}
if (require.main === module) {
  const rl = readline.createInterface({ input: process.stdin });
  rl.on('line', l => { try { process.stdout.write(JSON.stringify(evalDesign(JSON.parse(l))) + '\n'); } catch (err) { process.stdout.write(JSON.stringify({ error: String(err) }) + '\n'); } });
}
module.exports = { evalDesign };
