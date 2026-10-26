// Writes results/crosscheck_cases.json: sensor states + the JS controller's answer, for the MATLAB cross-check (srmc_sc_crosscheck.m)
const fs = require('fs'), path = require('path');
const ROOT = path.join(__dirname, '..', '..');
const S = require(path.join(ROOT, 'Review3_Digital_Twin', 'code_reference', 'srmc_engine.js')), SC = require('./sensor_controller.js');
const DD = path.join(ROOT, 'Review1_Design_and_CAD', 'results', 'design'), L = f => JSON.parse(fs.readFileSync(path.join(DD, f)));
const clim = L('climates.json')[0], soil = L('soils.json')[0], crops = L('crops.json'), D = L('design.json'), dp = D.presets[D.active], pw = +(dp.panelPitch - dp.panelGap).toFixed(4);
const params = { bayLen: dp.bayLen, pitch: dp.panelPitch, panelW: pw, height: dp.clearanceLowestEdge + pw / 2 * Math.sin(dp.maxTiltDeg * Math.PI / 180), tankM3: dp.cistern.m3, rainSlope: dp.rainSlopeDeg, stops: Array.from({ length: Math.round((dp.stopsDeg[1] - dp.stopsDeg[0]) / 5) + 1 }, (_, i) => dp.stopsDeg[0] + 5 * i) };
const R = S.run({ clim, soil, crops, params }), ctl = SC.make(S, { P: R.P, clim, zones: R.zones, w: 0.5, maxStep: 6 });
let seed = 7; const rnd = () => (seed = (seed * 1664525 + 1013904223) % 4294967296) / 4294967296;
const cases = [];
for (let i = 0; i < 40; i++) {
  const m = Math.floor(rnd() * 12), hour = 5.5 + Math.floor(rnd() * 14), n = S.MID[m], sun = S.sunVec(clim.lat, n, hour), kf = [1, .65, .3][Math.floor(rnd() * 3)];
  const irr = S.irradiance(sun.sz, n, clim.kt[m] * kf), T = +(24 + rnd() * 16).toFixed(1), RH = Math.round(25 + rnd() * 60), soilv = Math.round(10 + rnd() * 30), rain = i % 13 === 5, prev0 = +(15 + Math.floor(rnd() * 90) * 0.5).toFixed(1), prev = i % 11 === 4 ? 90 : prev0, wind = +((i % 7 === 3 ? 9 + rnd() * 12 : rnd() * 10)).toFixed(1);
  ctl.setDay(n); const st = ctl.stressOf(T, RH, soilv), par0 = irr.ghi > 20 ? SC.UM_PER_W * ctl.evalAngle(Math.min(prev, 60), sun, irr, T, 1, st.s, 2).lsr * irr.ghi : 0, par = i % 9 === 2 ? par0 * 0.3 : par0;
  const sen = { ghi: irr.ghi, parUm: par, T, RH, soil: soilv, rain, wind, day: n, hour }, d = ctl.decide(sen, { angle: prev });
  cases.push({ sen, prev, js: { mode: d.mode, angle: d.angle, stress: d.stress, corr: d.corr, target: d.target } });
}
const out = { lat: clim.lat, wEnergy: 0.5, maxStep: 6, zones: R.zones.map(z => ({ id: z.crop.id, lmin: z.crop.lmin, lopt: z.crop.lopt, ym: z.crop.ym, price: z.crop.price })), monthW: ctl.seasonWeights, P: { pitch: R.P.pitch, panelW: R.P.panelW, height: R.P.height, stops: R.P.stops, rainSlope: R.P.rainSlope, eff: R.P.eff, sysLoss: R.P.sysLoss }, cases };
fs.mkdirSync(path.join(__dirname, 'results'), { recursive: true }); fs.writeFileSync(path.join(__dirname, 'results', 'crosscheck_cases.json'), JSON.stringify(out, null, 1)); console.log('cases', cases.length, 'modes', [...new Set(cases.map(c => c.js.mode))].join(','));
