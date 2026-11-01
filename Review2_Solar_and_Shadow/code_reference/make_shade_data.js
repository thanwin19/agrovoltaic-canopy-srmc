// Ground light map data for the crop-shade heat map:  node make_shade_data.js
// For four days, hours 6-18 and tilts 3,15..60,90 it stores the light on the ground (fraction of open-field sunlight) at 40 points across one 2.5 m row pitch,
// the panel power, and the angle the six-sensor controller would pick in clear sky with ideal sensors.  2-D model (rows of infinite length), reference site.
const fs = require('fs'), path = require('path');
const ROOT = path.join(__dirname, '..', '..');
const S = require(path.join(ROOT, 'Review3_Digital_Twin', 'code_reference', 'srmc_engine.js')), SC = require(path.join(ROOT, 'Review4_Control_and_Simulation', 'sensor_controller', 'sensor_controller.js'));
const DD = path.join(ROOT, 'Review1_Design_and_CAD', 'results', 'design'), L = f => JSON.parse(fs.readFileSync(path.join(DD, f)));
const clim = L('climates.json')[0], soil = L('soils.json')[0], crops = L('crops.json'), D = L('design.json'), dp = D.presets[D.active], pw = +(dp.panelPitch - dp.panelGap).toFixed(4);
const params = { bayLen: dp.bayLen, pitch: dp.panelPitch, panelW: pw, height: dp.clearanceLowestEdge + pw / 2 * Math.sin(dp.maxTiltDeg * Math.PI / 180), tankM3: dp.cistern.m3, rainSlope: dp.rainSlopeDeg, stops: Array.from({ length: Math.round((dp.stopsDeg[1] - dp.stopsDeg[0]) / 5) + 1 }, (_, i) => dp.stopsDeg[0] + 5 * i) };
const R = S.run({ clim, soil, crops, params }), P = R.P, ctl = SC.make(S, { P, clim, zones: R.zones, w: 0.5, maxStep: 90, guard: true });
const DAYS = [[80, '21 Mar'], [172, '21 Jun'], [266, '23 Sep'], [355, '21 Dec']], HOURS = [], TILTS = [3, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 90];
for (let h = 6; h <= 18; h += 0.5) HOURS.push(h);
const monthOf = n => { let m = 0; for (let i = 0; i < 12; i++) if (n > S.CUM[i]) m = i; return m; };
const out = { site: clim.name, lat: clim.lat, pitch: P.pitch, panelW: P.panelW, height: P.height, ns: S.NS, days: DAYS.map(d => d[1]), hours: HOURS, tilts: TILTS, data: {}, ctrl: {}, note: 'light = ground irradiance divided by open-field global horizontal irradiance; clear-sky day of the month; 2-D model' };
for (const [n, name] of DAYS) {
  const m = monthOf(n); ctl.setDay(n); out.data[name] = {}; out.ctrl[name] = {};
  for (const h of HOURS) {
    const sun = S.sunVec(clim.lat, n, h); if (sun.sz < 0.05) continue; const irr = S.irradiance(sun.sz, n, clim.kt[m]);
    out.data[name][h] = TILTS.map(a => { const Q = Object.assign({}, P, { tiltMode: 'fixed', tilt: a }), g = S.groundLightHour(Q, sun, irr, a), pv = S.panelPower(Q, sun, irr, a, clim.tmean[m] + 4, 2).p; return { l: g.map(x => +(x / Math.max(irr.ghi, 1)).toFixed(3)), pv: +pv.toFixed(1) }; });
    out.ctrl[name][h] = ctl.search(sun, irr, clim.tmean[m] + 4, 1, 0, 2).best.a;
  }
}
fs.writeFileSync(path.join(ROOT, 'Review2_Solar_and_Shadow', 'results', 'shadow_heatmap', 'shade_data.json'), JSON.stringify(out)); console.log('ok', Object.keys(out.data), JSON.stringify(out.ctrl['21 Mar']));
