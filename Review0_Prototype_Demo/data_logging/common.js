// Shared helpers for the real-data logging pipeline (fake week generator and week scorer).
const fs = require('fs'), path = require('path');
const ROOT = path.join(__dirname, '..', '..');
const S = require(path.join(ROOT, 'Review3_Digital_Twin', 'code_reference', 'srmc_engine.js'));
const SC = require(path.join(ROOT, 'Review4_Control_and_Simulation', 'sensor_controller', 'sensor_controller.js'));
const DD = path.join(ROOT, 'Review1_Design_and_CAD', 'results', 'design'), L = f => JSON.parse(fs.readFileSync(path.join(DD, f)));
function setup(opts = {}) {
  const clim = L('climates.json')[0], soil = L('soils.json')[0], crops = L('crops.json'), D = L('design.json'), dp = D.presets[D.active], pw = +(dp.panelPitch - dp.panelGap).toFixed(4);
  const params = { bayLen: dp.bayLen, pitch: dp.panelPitch, panelW: pw, height: dp.clearanceLowestEdge + pw / 2 * Math.sin(dp.maxTiltDeg * Math.PI / 180), tankM3: dp.cistern.m3, rainSlope: dp.rainSlopeDeg, stops: Array.from({ length: Math.round((dp.stopsDeg[1] - dp.stopsDeg[0]) / 5) + 1 }, (_, i) => dp.stopsDeg[0] + 5 * i) };
  const R = S.run({ clim, soil, crops, params });
  const ctl = SC.make(S, { P: R.P, clim, zones: R.zones, w: 0.5, maxStep: opts.maxStep || 6, guard: true });
  return { S, SC, clim, soil, R, P: R.P, ctl };
}
// local clock (with UTC offset in the ISO string) -> day of year and solar hour for the site
function solarTime(iso, lon) {
  const d = new Date(iso), start = Date.UTC(d.getUTCFullYear(), 0, 0), n = Math.floor((Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate()) - start) / 864e5);
  const B = 2 * Math.PI * (n - 81) / 364, eot = 9.87 * Math.sin(2 * B) - 7.53 * Math.cos(B) - 1.5 * Math.sin(B);     // minutes
  const utcH = d.getUTCHours() + d.getUTCMinutes() / 60 + d.getUTCSeconds() / 3600;
  return { day: n, hour: (utcH + lon / 15 + eot / 60 + 24) % 24 };
}
function monthOfDay(n) { let m = 0; for (let i = 0; i < 12; i++) if (n > S.CUM[i]) m = i; return m; }
function parseCsv(file) {
  const lines = fs.readFileSync(file, 'utf8').split(/\r?\n/).filter(l => l.trim() && !l.startsWith('#')); const head = lines[0].split(',').map(s => s.trim());
  return lines.slice(1).map(l => { const p = l.split(','), o = {}; head.forEach((h, i) => { const v = (p[i] || '').trim(); o[h] = v === '' ? null : (isNaN(+v) ? v : +v); }); return o; });
}
module.exports = { S, SC, setup, solarTime, monthOfDay, parseCsv, ROOT };
