"""Patch the final digital twin: retitle, make the six-sensor controller (SRMC-SC) the default controller.  python patch_twin.py"""
import os, shutil
here = os.path.dirname(os.path.abspath(__file__)); root = os.path.abspath(os.path.join(here, '..', '..'))
tw = os.path.join(root, 'Review3_Digital_Twin', 'results', 'live_twin', 'SRMC_Digital_Twin.html')
bk = os.path.join(os.path.dirname(tw), '_old'); os.makedirs(bk, exist_ok=True)
bkf = os.path.join(bk, 'SRMC_Digital_Twin_before_sensor_controller.html')
if not os.path.exists(bkf): shutil.copy(tw, bkf)
s = open(bkf, encoding='utf8').read()            # always patch from the saved original so the script can be re-run
def rep(old, new, cnt=1):
    global s
    assert old in s, 'MISSING: ' + old[:70]
    s = s.replace(old, new, cnt)
mod = open(os.path.join(here, 'sensor_controller.js'), encoding='utf8').read()
rep('<script>window.SRMC_DATA=', '<script>\n' + mod + '\n</script>\n<script>window.SRMC_DATA=')
rep('<title>SRMC Digital Twin</title>', '<title>Agrovoltaic Canopy: Digital Twin</title>')
rep('<h1>SRMC <span>Digital Twin</span></h1>', '<h1>Agrovoltaic Canopy for Protection and Sustainable Farming <span>Digital Twin</span></h1>')
rep('<div class="sub">Soil Regeneration Microclimatic Chamber · wire-tension agrivoltaic canopy with rain harvesting · ground visual: Thiagarajar College of Engineering, Madurai</div>',
    '<div class="sub">Six sensors (pyranometer, PAR, DHT11, soil moisture, rain, anemometer) tilt the panels to optimise both crop light and electricity · rain-harvesting gutter · wire-tension canopy · ground visual: Thiagarajar College of Engineering, Madurai</div>')
rep('SRMC-DT controller: flat in rain, tilt stop chosen 3×/day (spec + novelty)', 'Hourly plan (planner and sensor-failure fallback); the six-sensor controller below overrides it')
i = s.index('/* ---------------- Sensor feedback controller'); j = s.index('/* ---------------- Tab: mechanism')
new = open(os.path.join(here, 'twin_sens_block.js'), encoding='utf8').read()
s = s[:i] + new + '\n' + s[j:]
rep('<h4>SENSOR PLAYGROUND: the five real sensors decide the panel angle</h4>', '<h4>SIX-SENSOR CONTROLLER: pyranometer, PAR, DHT11, soil moisture, rain sensor and anemometer decide the panel angle</h4>')
rep('<input type="checkbox" id="sens-on"> <b>Use the sensor feedback controller</b> (pyranometer, PAR, DHT11, soil moisture, rain sensor)', '<input type="checkbox" id="sens-on" checked> <b>Six-sensor controller ON</b> (untick to see the hourly plan only)')
i = s.index('<div class="note">Rule: <b>keep just enough light'); j = s.index('</div>', i) + 6
s = s[:i] + open(os.path.join(here, 'twin_sens_note.html'), encoding='utf8').read() + s[j:]
rep('<div id="sens-box" style="display:none">', '<div id="sens-box">')
rep('<button class="b" id="sens-reset">reset sliders</button></div>', '<button class="b" id="sens-reset">reset sliders</button></div><div class="hint" style="margin-top:8px"><b>Real board (optional):</b> <select id="live-board"><option value="esp8266">NodeMCU ESP8266</option><option value="esp32">ESP32</option></select> <button class="b" id="live-connect">Connect board (USB)</button> <span id="live-status">not connected: DHT11, soil and rain would come from your board, pyranometer and PAR stay simulated</span></div>')
rep("window.SRMC_UI = { st, SENS,", "$('#live-connect').onclick = liveConnect; window.SRMC_UI = { st, SENS, liveLine, liveConnect,")
rep('<div class="hint">Rain sensor = the "Rain mode" button above.', '<label>Anemometer wind speed <b id="v-sens-wind">3 m/s</b></label><input type="range" id="sens-wind" min="0" max="25" step="0.5" value="3"><div class="hint">Rain sensor = the "Rain mode" button above.')
rep("['soil', 'soil', v => v + ' %', v => +v]]", "['soil', 'soil', v => v + ' %', v => +v], ['wind', 'wind', v => v + ' m/s', v => +v]]")
rep("${row('★ Rain sensor', flat ? 'WET' : 'dry', flat ? 'FLAT→gutter' : '')}", "${row('★ Rain sensor', flat ? 'WET' : 'dry', flat ? 'FLAT→gutter' : '')}${row('★ Anemometer (wind)', fmt(SENS.wind, 1) + ' m/s', SENS.wind >= 15 ? 'STOW 90°' : 'ok')}")
import json as _json
_v2 = _json.load(open(os.path.join(here, 'results', 'accuracy_v2.json'), encoding='utf-8')); _mt = _json.load(open(os.path.join(here, 'results', 'accuracy_matlab.json'), encoding='utf-8'))
ACC = {'main': _v2['main'], 'noise': _v2['noise'], 'faults': _v2['faults'], 'money': _v2['money'], 'matlab': _mt}
rep('<script>window.SRMC_DATA=', '<script>window.SRMC_ACC=' + _json.dumps(ACC) + ';</script>\n<script>window.SRMC_DATA=')
s = s.replace(s[s.index('/* ---------------- Tab: mechanism'):s.index('/* ---------------- Tab: mechanism')], '')
k = s.index('/* ---------------- Tab: mechanism'); s = s[:k] + open(os.path.join(here, 'twin_acc_block.js'), encoding='utf8').read() + '\n' + s[k:]
rep('    <button class="tab" data-t="method">', '    <button class="tab" data-t="acc">Accuracy<small>both goals · test</small></button>\n    <button class="tab" data-t="method">')
rep('  <section class="pane method" id="pane-method"', open(os.path.join(here, 'twin_acc_pane.html'), encoding='utf8').read() + '  <section class="pane method" id="pane-method"')
rep("else if (st.tab === 'method') tabMethod();", "else if (st.tab === 'method') tabMethod(); else if (st.tab === 'acc') tabAcc();")
rep("$('#live-connect').onclick = liveConnect;", "$('#live-connect').onclick = liveConnect; $('#acc-run').onclick = runLiveAcc; $('#acc-noise-in').oninput = e => { $('#v-acc-noise-in').textContent = 'x' + e.target.value; };")
rep('<label>Soil moisture sensor <b id="v-sens-soil">26 %</b></label><input type="range" id="sens-soil" min="5" max="45" step="1" value="26">', '<label>Soil moisture sensor, plant-available water (follows the water-balance model until you move it) <b id="v-sens-soil">26 %</b></label><input type="range" id="sens-soil" min="0" max="100" step="1" value="26">')
rep("if (id === 'temp' || id === 'rh') SENS.manualTH = true;", "if (id === 'temp' || id === 'rh') SENS.manualTH = true; if (id === 'soil') SENS.manualSoil = true;")
rep("SENS.manualTH = false; SENS.cloud = 0; SENS.soil = 26; $('#sens-cloud').value = 0; $('#v-sens-cloud').textContent = '0 %'; $('#sens-soil').value = 26; $('#v-sens-soil').textContent = '26 %';", "SENS.manualTH = false; SENS.manualSoil = false; SENS.cloud = 0; $('#sens-cloud').value = 0; $('#v-sens-cloud').textContent = '0 %';")
rep("soilTxt = SENS.on ? SENS.soil + ' %' :", "soilTxt = SENS.on ? SENS.soil + ' % ' + (SENS.manualSoil ? '(slider)' : '(water-balance model)') :")
rep("${row('★ Rain sensor', flat ?", "${row('Irrigation (drip, from the cistern)', R.wb.irrSeries[st.day] > 0.5 ? fmt(R.wb.irrSeries[st.day], 0) + ' m³ today' : 'off today', 'cistern ' + fmt(R.wb.tankSeries[st.day], 0) + ' m³')}${row('★ Rain sensor', flat ?")
rep("</style>\n</head>", ".hb{display:inline-block;width:44px;height:7px;background:rgba(255,255,255,.15);border-radius:4px;vertical-align:middle;overflow:hidden}.hb i{display:block;height:100%}.pulse{display:inline-block;width:9px;height:9px;border-radius:50%;background:#4fd1ff;margin-right:5px;animation:hudp 1s infinite}@keyframes hudp{0%{box-shadow:0 0 0 0 rgba(79,209,255,.8)}100%{box-shadow:0 0 0 9px rgba(79,209,255,0)}}\n</style>\n</head>")
rep("Cistern ${fmt(R.wb.tankSeries[st.day], 0)} / ${fmt(P.tankM3)} m³<br>", "${hudWater(P)}")
rep("  function hud() {", """  function hudWater(P) {          // live soil moisture per zone, irrigation and cistern (from the water-balance model, or the real board when connected)
    const so = DATA.soils.find(x => x.id === st.soilId), th = R.wb.theta.map(a => a[st.day]), av = th.map(v => Math.max(0, Math.min(100, 100 * (v - so.wp) / (so.fc - so.wp)))), irr = R.wb.irrSeries[st.day], tank = R.wb.tankSeries[st.day], rain = R.wb.rain[st.day];
    const col = v => v < 20 ? '#ff8a5c' : v < 35 ? '#f0c24a' : '#6fe07c', bar = v => `<span class="hb"><i style="width:${v}%;background:${col(v)}"></i></span>`;
    const live = typeof SENS !== 'undefined' && SENS.live && Date.now() - SENS.live.t < 5000 ? SENS.live : null;
    return `Soil moisture (plant-available water): ${av.map((v, i) => 'Z' + (i + 1) + ' ' + bar(v) + ' ' + fmt(v, 0) + '%').join(' &nbsp;')}${live ? '<br><span style="color:#9ad0ff">real probe: ' + fmt(live.soil, 0) + ' %</span>' : ''}<br>` +
      (irr > 0.5 ? `<span class="pulse"></span><b style="color:#4fd1ff">IRRIGATING</b> ${fmt(irr, 0)} m³ today (drip)` : 'Irrigation: off today') + ` · rain ${fmt(rain, 0)} mm<br>Cistern ${bar(100 * tank / P.tankM3)} ${fmt(tank, 0)} / ${fmt(P.tankM3)} m³<br>`;
  }
  function hud() {""")
fi = s.index('"feasible":{'); fe = s.index('"source"', fi)          # embedded design: drive wire 4 -> 6 mm in the checked preset
blk = s[fi:fe]; assert '"driveDiaMm":4' in blk
s = s[:fi] + blk.replace('"driveDiaMm":4', '"driveDiaMm":6') + s[fe:]
open(tw, 'w', encoding='utf8').write(s); print('twin patched', len(s))
