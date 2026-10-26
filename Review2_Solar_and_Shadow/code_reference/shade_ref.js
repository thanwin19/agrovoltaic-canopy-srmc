// Engine-side direct-beam lit fraction per zone strip for a set of (hour, tilt) cases -> out/physics/shade_cases.json
const fs = require('fs'), S = require('../engine/srmc_engine.js');
const B = JSON.parse(fs.readFileSync('out/blender_inputs.json')), P = Object.assign({}, S.DEFAULTS, { pitch: B.design.panelPitch, panelW: B.design.panelW, height: B.design.pivotHeight });
const lat = B.sun.lat, day = B.sun.day, cases = [];
for (const hour of [7, 9, 12, 15, 17]) for (const tilt of [15, 30, 45, 60]) {
  const sun = S.sunVec(lat, day, hour), segs = S.segments(P, tilt, S.rowsFor(P, sun)), strips = [0, 0, 0, 0], NS = S.NS;
  for (let i = 0; i < NS; i++) { const x = (i + .5) / NS * P.pitch; if (!S.rayBlocked(x, 0, sun.sx, sun.sz, segs, null)) strips[Math.floor(i / (NS / 4))] += 1 / (NS / 4); }
  cases.push({ hour, tilt, sx: sun.sx, sy: sun.sy, sz: sun.sz, engine: strips });
}
fs.mkdirSync('out/physics', { recursive: true }); fs.writeFileSync('out/physics/shade_cases.json', JSON.stringify({ design: B.design, cases }));
console.log('cases', cases.length);
