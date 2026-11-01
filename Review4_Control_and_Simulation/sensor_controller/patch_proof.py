"""Eighth patch of the single digital twin (run AFTER patch_mech.py; safe to re-run): the Review 0 sensors and proof in the twin.
 - sensor panel names the six real devices (SP-110, SQ-110, DHT11, SEN0193, YL-83/FC-37, Adafruit 1733) and shows the signal each would output
 - 'datasheet sensor errors' switch (the controller sees readings wrong by realistic amounts) and a CSV recorder
 - new tab 'Sensors and proof': datasheet table with links, the Jinko panel with a live I-V / P-V curve and array power, where the sunlight comes from and the model-vs-data check,
   the accuracy comparison, cost if real, what else is needed
python patch_proof.py"""
import os, shutil, base64, io
from PIL import Image
here = os.path.dirname(os.path.abspath(__file__)); root = os.path.abspath(os.path.join(here, '..', '..'))
tw = os.path.join(root, 'Review3_Digital_Twin', 'results', 'live_twin', 'SRMC_Digital_Twin.html')
bkd = os.path.join(root, '_archive', 'backups_of_files_before_the_final_update', 'proof_patch'); os.makedirs(bkd, exist_ok=True); bk = os.path.join(bkd, 'SRMC_Digital_Twin_before_proof.html')
cur = open(tw, encoding='utf8').read()
if 'PROOF_PATCHED' not in cur:
    assert 'MECHCTL_PATCHED' in cur, 'run patch_mech.py first'; shutil.copy(tw, bk)
s = open(bk, encoding='utf8').read()
def rep(old, new, cnt=1):
    global s
    assert old in s, 'MISSING: ' + old[:80]
    s = s.replace(old, new, cnt)
def b64(path, w=1000):
    im = Image.open(path).convert('RGB'); im.thumbnail((w, w)); buf = io.BytesIO(); im.save(buf, 'JPEG', quality=88); return 'data:image/jpeg;base64,' + base64.b64encode(buf.getvalue()).decode()
IMG = os.path.join(root, 'Review0_Prototype_Demo', 'ppt', '_img2'); GH = 'https://github.com/thanwin19/agrovoltaic-canopy-srmc/blob/main/Proof/10_Review0_Sensors_and_Panels/'
fig_acc = b64(os.path.join(IMG, 'poster_accuracy.png'), 1100); fig_trust = b64(os.path.join(IMG, 'poster_trust.png'), 800)
L = lambda f, t=None: '<a href="%s%s" target="_blank" rel="noopener">%s</a>' % (GH, f, t or f.split('/')[-1])

css = """
/*PROOF_PATCHED*/
.pt{width:100%;border-collapse:collapse;font-size:13px;margin:6px 0}.pt th{background:#1f3a5f;color:#fff;text-align:left;padding:6px 8px}.pt td{padding:5px 8px;border-bottom:1px solid var(--line);vertical-align:top}.pt tr:nth-child(even) td{background:rgba(255,255,255,.03)}
.pt a,.plinks a{color:#9ad0ff}.pgrid{display:grid;grid-template-columns:1fr 1fr;gap:14px}@media(max-width:1000px){.pgrid{display:block}}
.pbig{display:flex;gap:10px;flex-wrap:wrap;margin:8px 0}.pbig div{background:var(--panel2);border:1px solid var(--line);border-radius:10px;padding:8px 14px;min-width:150px}.pbig b{display:block;font-size:26px;color:#72B830}.pbig span{font-size:12px;color:var(--mute)}
#px-box{border:1px solid #2e4a6a;background:#101c2a;border-radius:10px;padding:8px 12px;margin:10px 0;font-size:13px}#px-box h5{margin:0 0 4px;font-size:13px;color:#9ad0ff}#px-sig td{padding:2px 6px;font-size:12.5px}#px-sig td:first-child{color:var(--mute)}
.warnbox{background:#2a2410;border:1px solid #6a5a20;color:#f0d98a;border-radius:8px;padding:8px 12px;font-size:13px}
"""
rep("</style>\n</head>", css + "</style>\n</head>")

# ---- sensor card: real device names + signals ----
rep("<div><b>1 Pyranometer (GHI):</b> ${irr.ghi.toFixed(0)} W/m² ${night ? '(night)' : ''}", "<div><b>1 Apogee SP-110 pyranometer:</b> ${irr.ghi.toFixed(0)} W/m² (${(0.2 * irr.ghi).toFixed(0)} mV) ${night ? '(night)' : ''}")
rep("<div><b>2 PAR sensor under the canopy:</b> ${parUm.toFixed(0)} µmol/m²/s →", "<div><b>2 Apogee SQ-110 PAR sensor:</b> ${parUm.toFixed(0)} µmol/m²/s (${(0.2 * parUm).toFixed(0)} mV) →")
rep("<div><b>3 DHT11:</b> ${T.toFixed(1)} °C, ${RH} % RH →", "<div><b>3 DHT11:</b> ${T.toFixed(1)} °C (±2), ${RH} % RH (±5) →")
rep("<div><b>4 Soil moisture (plant-available water):</b> ${SENS.soil} %", "<div><b>4 DFRobot SEN0193 soil moisture:</b> ${SENS.soil} % (${(2.5 - SENS.soil / 100 * 1.3).toFixed(2)} V)")
rep("<div><b>5 Rain sensor:</b> ${rain ? '<span style=\"color:#9ad0ff\">WET</span>", "<div><b>5 YL-83 / FC-37 rain sensor:</b> ${rain ? '<span style=\"color:#9ad0ff\">WET (pin LOW)</span>")
rep("<div><b>6 Anemometer (wind):</b> reads ${WW.read.toFixed(1)} m/s", "<div><b>6 Adafruit 1733 anemometer:</b> reads ${WW.read.toFixed(1)} m/s (${(0.4 + 1.6 * WW.read / 32.4).toFixed(2)} V)")
rep('<h4>SENSOR PANEL: change the six sensors like a real day would, and watch the panels react</h4>', '<h4>SENSOR PANEL: six real devices, simulated. Change them by hand and watch the panels react</h4>')
# datasheet error switch: the controller sees readings wrong by datasheet-sized amounts
rep("const d = SENS.safe.step({ ghi: irr.ghi, parUm, T, RH, soil: soilRead,", "const d = SENS.safe.step({ ghi: pxErr(irr.ghi, 'ghi'), parUm: pxErr(parUm, 'par'), T: pxErr(T, 'T'), RH: pxErr(RH, 'RH'), soil: pxErr(soilRead, 'soil'),")
rep("pvRel: d.pvRel == null ? 0 : d.pvRel, cropRel: d.cropRel == null ? 0 : d.cropRel };", "pvRel: d.pvRel == null ? 0 : d.pvRel, cropRel: d.cropRel == null ? 0 : d.cropRel, wind: SENS.wind, soil: SENS.soil };\n  if (apply && SENS.recOn) pxRec(n, hr, d);")
box = """<div id="px-box"><h5>WHAT EACH REAL DEVICE WOULD OUTPUT RIGHT NOW</h5>
        <table id="px-sig"></table>
        <label style="display:inline;font-size:13px"><input type="checkbox" id="px-err"> <b>Add datasheet sensor errors</b></label> <span class="hint">the controller then sees sunlight and PAR wrong by up to about 5 %, DHT11 by 2 °C and 5 % RH, soil by 3 %</span><br>
        <button class="b" id="px-rec">Record sensors ●</button> <button class="b" id="px-dl">Download CSV</button> <span id="px-recn" class="hint"></span>
        <div class="hint" style="margin-top:4px">Proof and datasheets: open the <b>Sensors and proof</b> tab.</div></div>
        <div id="sens-trace" """
rep('<div id="sens-trace" ', box)

# ---- new tab ----
rep('<button class="tab" data-t="method">', '<button class="tab" data-t="proof">Sensors and proof<small>datasheets, data, trust</small></button>\n    <button class="tab" data-t="method">')
rep("document.body.classList.toggle('tab-guide', st.tab === 'guide' || st.tab === 'twin');", "document.body.classList.toggle('tab-guide', st.tab === 'guide' || st.tab === 'twin' || st.tab === 'proof');")
sens_rows = [
 ('1', 'Sunlight', 'Apogee SP-110 pyranometer', '0-2000 W/m²', '±5 %', '0.20 mV per W/m²', '01_pyranometer_ApogeeSP110_manual.pdf'),
 ('2', 'Plant light (PAR)', 'Apogee SQ-110 quantum sensor', '0-4000 µmol/m²/s', '±5 %', '0.20 mV per µmol', '02_PAR_ApogeeSQ110_manual.pdf'),
 ('3', 'Air temperature', 'DHT11', '0-50 °C', '±2 °C', 'digital', '03-04_airTemp_and_humidity_DHT11_datasheet.pdf'),
 ('4', 'Air humidity', 'DHT11 (same chip)', '20-90 % RH', '±5 % RH', 'digital', '03-04_airTemp_and_humidity_DHT11_datasheet.pdf'),
 ('5', 'Soil moisture', 'DFRobot SEN0193 v1.2 capacitive', '2.5 V dry to 1.2 V wet', 'needs dry/wet calibration', 'analog 1.2-2.5 V', '05_soilMoisture_DFRobotSEN0193_product_page.html'),
 ('6', 'Rain', 'YL-83 / FC-37 + LM393', 'wet / dry', 'trimmer threshold', 'digital, LOW = wet', '06_rain_YL83_FC37_vendor_page.html'),
 ('7', 'Wind speed', 'Adafruit 1733 anemometer', '0.5-32.4 m/s', '±1 m/s worst case', 'analog 0.4-2.0 V', '07_wind_Adafruit1733_datasheet_C2192.pdf')]
rows = ''.join('<tr><td>%s</td><td>%s</td><td><b>%s</b></td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' % (a, b, c, d, e, f, L('sensor_datasheets/' + g, 'datasheet')) for a, b, c, d, e, f, g in sens_rows)
pane = '''  <section class="pane" id="pane-proof" style="display:none">
    <div class="card"><h4>The six sensors: simulated after real devices, with the datasheets as proof</h4>
      <div class="warnbox"><b>Honest status:</b> the sensors are software models of these real devices. The readings are calculated or typed by you, not measured. No field trial yet.</div>
      <table class="pt"><tr><th>#</th><th>Reading</th><th>Real device</th><th>Range</th><th>Accuracy</th><th>Signal</th><th>Proof</th></tr>''' + rows + '''</table>
      <div class="note">Each datasheet file was downloaded and checked: SP-110 and SQ-110 sensitivity 0.20 mV per unit and ±5 %; DHT11 ±5 % RH and ±2 °C; the Adafruit wind formula speed = (V − 0.4) / 1.6 × 32.4. Not verified: the rain sensor has no official datasheet (vendor page only). Files: ''' + L('sensor_datasheets/', 'sensor_datasheets folder') + '''.</div></div>
    <div class="card"><h4>The solar panel: 8 × JinkoSolar Tiger Pro JKM550M-72HL4-V, with a live I-V curve</h4>
      <div class="pgrid"><div><table class="pt"><tr><th>Item</th><th>Value (official datasheet)</th></tr><tr><td>Model</td><td>JKM550M-72HL4-V, monocrystalline</td></tr><tr><td>Panels</td><td>8 (2 rows × 4) = 4.4 kWp</td></tr><tr><td>Pmax (test conditions)</td><td>550 Wp</td></tr><tr><td>Vmp / Imp</td><td>40.90 V / 13.45 A</td></tr><tr><td>Voc / Isc</td><td>49.62 V / 14.03 A</td></tr><tr><td>Efficiency</td><td>21.33 %</td></tr><tr><td>Size / weight</td><td>2274 × 1134 × 35 mm / 28.9 kg</td></tr></table>
        <div id="px-ivread" class="note"></div><div class="note">Datasheet: ''' + L('sensor_datasheets/P1_panel_JinkoSolar_JKM550M-72HL4-V_datasheet.pdf', 'Jinko datasheet (PDF)') + '''. The curve uses a single-diode model through these five numbers with typical temperature coefficients (not from this datasheet); sunlight on the panel plane is approximated by the horizontal sunlight.</div></div>
      <div><canvas id="px-iv"></canvas></div></div></div>
    <div class="card"><h4>Where the sunlight comes from, and why to trust it</h4>
      <div class="note" style="margin-top:0;font-size:14px">Nobody measured it. The twin <b>calculates</b> it: sun position from astronomy for TCE (9.88 N, 78.08 E), the solar constant 1361 W/m² corrected for the day, times a monthly clearness index from <b>NASA POWER</b> for this site, split into direct and diffuse light (Erbs). PAR is 45 % of the sunlight (4.57 µmol per joule).</div>
      <div class="pgrid"><div><table class="pt"><tr><th>15 April, TCE, flat ground</th><th>Wh/m² per day</th></tr><tr><td>Our model, typical clear day</td><td>6502</td></tr><tr><td>NASA POWER, actual day (2023)</td><td>6539</td></tr><tr><td>NASA POWER, perfect clear sky</td><td>7144</td></tr><tr><td>PVGIS-ERA5, April 2020 mean day</td><td>6337</td></tr></table>
        <div class="note">Daily energy within 0.6 % of NASA's actual day and 2.6 % above PVGIS. Plant-light share: NASA POWER 0.444, model 0.45. The model's noon peak (837 W/m²) is below a perfectly cloudless day (986). Yearly electricity against PVGIS: +5.0 %. These are satellite and reanalysis data, not a sensor on the TCE roof. Files: ''' + L('sunlight_datasets/', 'sunlight_datasets folder') + ''' and ''' + L('WHERE_SUNLIGHT_COMES_FROM_AND_WHY_TRUST_IT.md', 'explanation') + '''.</div></div>
      <div><img src="''' + fig_trust + '''" style="width:100%;border-radius:8px;background:#fff"></div></div></div>
    <div class="card"><h4>Accuracy of the co-optimisation: what we obtained against ordinary designs</h4>
      <div class="pbig"><div><b>99.6 %</b><span>our controller, share of the best possible score</span></div><div><b>91.2 %</b><span>fixed 45°</span></div><div><b>84.0 %</b><span>sun tracking</span></div><div><b>80.0 %</b><span>fixed 15° (maximum power)</span></div><div><b>4.8°</b><span>angle error (fixed 45°: 16.3°)</span></div></div>
      <img src="''' + fig_acc + '''" style="width:100%;max-width:1000px;border-radius:8px;background:#fff">
      <div class="note">864 noisy test cases (sensor noise: sunlight and PAR 5 %, DHT11 ±2 °C and ±5 % RH, soil ±3 %). The score is half electricity and half crop light, against the best angle found by trying every angle from 15° to 60°. Simulation, against the controller's own goal, not real crop yield. File: Proof/05_Controller_and_Accuracy/T11_accuracy_v2.csv. Try it live: tick <b>Add datasheet sensor errors</b> in the sensor panel.</div></div>
    <div class="card"><h4>Cost if the sensors were real (indicative, INR, not quotes)</h4>
      <table class="pt"><tr><th>Item</th><th>Research-grade kit</th><th>Low-cost kit</th></tr><tr><td>Sunlight sensor (Apogee SP-110 / reference cell)</td><td>28,000</td><td>1,500</td></tr><tr><td>PAR sensor (Apogee SQ-110 / reference cell)</td><td>28,000</td><td>1,500</td></tr><tr><td>Anemometer (Adafruit 1733)</td><td>6,500</td><td>6,500</td></tr><tr><td>DHT11 + soil + rain sensor</td><td>700</td><td>700</td></tr><tr><td>ESP32 + ADC</td><td>1,400</td><td>1,400</td></tr><tr><td>Amplifier, enclosure, cables</td><td>3,000</td><td>1,500</td></tr><tr><td><b>Total sensing and control kit</b></td><td><b>67,600</b></td><td><b>13,100</b></td></tr></table>
      <div class="note">8 panels at an assumed INR 16 per Wp: about INR 70,000. This simulation costs nothing. Prices are my estimates (Apogee about US$ 250-300 each plus duty and GST); replace them with quotes.</div></div>
    <div class="card"><h4>What else the twin needs (next steps)</h4>
      <div class="pgrid"><div><b>Added now</b><ul class="plain"><li>Real device names, signals and datasheet proof for every sensor</li><li>Switch for datasheet-sized sensor errors</li><li>Record the sensor readings and decisions, download as CSV</li><li>Live I-V curve and array power for the real panel</li></ul></div>
      <div><b>Still needed</b><ul class="plain"><li>Real SP-110, SQ-110 and wind sensors on a roof, logged for a month, then replayed in the twin</li><li>Replay of NASA POWER hourly weather for any chosen date</li><li>Wind-tunnel or CFD run to settle the storm stow (flat or 90°)</li><li>Crop-light and yield measurement to test the crop model</li></ul></div></div></div>
    <div class="card plinks"><h4>All proof files</h4><div class="note" style="margin-top:0">Everything is in the repository folder ''' + L('', 'Proof/10_Review0_Sensors_and_Panels') + ''': datasheets, NASA POWER and PVGIS data, figures, the Evidence Book (Word) for the judges, and a SHA-256 checksum for every file in Proof/MANIFEST.csv.</div></div>
  </section>
'''
rep('  <section class="pane method" id="pane-method"', pane + '  <section class="pane method" id="pane-method"')

js = r"""
/* ---------------- Sensors and proof: datasheet errors, recorder, signals, I-V curve ---------------- */
function pxRnd() { let t = (SENS.pxSeed = ((SENS.pxSeed || 12345) + 0x6D2B79F5) | 0); t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }
function pxGauss() { let u = 0, v = 0; while (u === 0) u = pxRnd(); v = pxRnd(); return Math.max(-2, Math.min(2, Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v))); }
function pxErr(v, k) {                                     // sigma = half of the datasheet limit; one new draw per decision
  if (!SENS.dsErr || v == null || isNaN(v)) return v; const z = pxGauss();
  if (k === 'ghi' || k === 'par') return Math.max(0, v * (1 + 0.025 * z)); if (k === 'T') return v + 1.0 * z; if (k === 'RH') return Math.max(0, Math.min(100, v + 2.5 * z)); if (k === 'soil') return Math.max(0, Math.min(100, v + 1.5 * z)); return v;
}
function pxRec(n, hr, d) {
  const L = SENS.last; (SENS.rec = SENS.rec || []).push([n, hr.toFixed(2), L.ghi.toFixed(0), L.par.toFixed(0), L.T.toFixed(1), L.RH, L.soil, L.rain ? 1 : 0, SENS.wind, d.mode, d.angle.toFixed(1), (+L.pvRel).toFixed(3), (+L.cropRel).toFixed(3), SENS.dsErr ? 1 : 0]);
  if (SENS.rec.length > 20000) SENS.rec.shift();
}
function pxIV(G, Tc) {
  const Isc = 14.03, Voc = 49.62, Imp = 13.45, Vmp = 40.90, aI = 0.0005, bV = -0.0027;
  const f = a => Imp / Isc - (1 - (Math.exp(Vmp / a) - 1) / (Math.exp(Voc / a) - 1)); let lo = 0.5, hi = 20; for (let i = 0; i < 60; i++) { const mid = (lo + hi) / 2; if (f(lo) * f(mid) <= 0) hi = mid; else lo = mid; } const a0 = (lo + hi) / 2;
  const Iph = Isc * G / 1000 * (1 + aI * (Tc - 25)), a = a0 * (Tc + 273.15) / 298.15, VocT = Voc * (1 + bV * (Tc - 25)), I0 = Iph / (Math.exp(VocT / a) - 1), pts = []; let best = { P: 0, V: 0, I: 0 };
  for (let i = 0; i <= 200; i++) { const V = VocT * i / 200, I = Math.max(0, Iph - I0 * (Math.exp(V / a) - 1)), P = V * I; pts.push([V, I, P]); if (P > best.P) best = { P, V, I }; } return { pts, best, VocT, Iph };
}
function pxDraw() {
  const cvEl = $('#px-iv'); if (!cvEl || st.tab !== 'proof') return; const L = SENS.last; const G = L ? Math.max(0, L.ghi) : 0, ws = Math.max(0.5, SENS.wind || 2), T = L ? L.T : 30, Tc = T + G * Math.exp(-3.473 - 0.0594 * ws);
  const o = pxIV(G, Tc), { g, w, h } = cv(cvEl, 300); const mx = 50, my = 14, pw = w - mx - 56, ph = h - my - 36, Vm = 60, Im = 15, Pm = 620;
  g.fillStyle = '#0f1620'; g.fillRect(0, 0, w, h); g.strokeStyle = GRID; g.lineWidth = 1; g.fillStyle = TXT; g.font = '11px system-ui'; g.textAlign = 'center';
  for (let v = 0; v <= 60; v += 10) { const x = mx + pw * v / Vm; g.beginPath(); g.moveTo(x, my); g.lineTo(x, my + ph); g.stroke(); g.fillText(v, x, my + ph + 14); } g.fillText('module voltage (V)', mx + pw / 2, h - 6);
  g.textAlign = 'right'; for (let i = 0; i <= 15; i += 5) { const y = my + ph - ph * i / Im; g.beginPath(); g.moveTo(mx, y); g.lineTo(mx + pw, y); g.stroke(); g.fillText(i, mx - 4, y + 4); } g.save(); g.translate(12, my + ph / 2); g.rotate(-Math.PI / 2); g.textAlign = 'center'; g.fillText('current (A)', 0, 0); g.restore();
  g.textAlign = 'left'; for (let p = 0; p <= 600; p += 200) { const y = my + ph - ph * p / Pm; g.fillText(p, mx + pw + 6, y + 4); } g.fillStyle = '#e0a030'; g.fillText('power (W)', mx + pw - 40, my + 10);
  g.strokeStyle = '#72B830'; g.lineWidth = 2.5; g.beginPath(); o.pts.forEach((q, i) => { const x = mx + pw * q[0] / Vm, y = my + ph - ph * q[1] / Im; i ? g.lineTo(x, y) : g.moveTo(x, y); }); g.stroke();
  g.strokeStyle = '#e0a030'; g.beginPath(); o.pts.forEach((q, i) => { const x = mx + pw * q[0] / Vm, y = my + ph - ph * q[2] / Pm; i ? g.lineTo(x, y) : g.moveTo(x, y); }); g.stroke();
  if (o.best.P > 1) { const x = mx + pw * o.best.V / Vm, y = my + ph - ph * o.best.P / Pm; g.fillStyle = '#ff5a4a'; g.beginPath(); g.arc(x, y, 5, 0, 7); g.fill(); }
  $('#px-ivread').innerHTML = G < 20 ? 'Night or no sunlight: no power.' : `Now: sunlight ${G.toFixed(0)} W/m², cell about ${Tc.toFixed(0)} °C. One module at its maximum power point: <b>${o.best.V.toFixed(1)} V × ${o.best.I.toFixed(2)} A = ${o.best.P.toFixed(0)} W</b>. All 8 modules: <b>${(8 * o.best.P / 1000).toFixed(2)} kW</b> DC (green = current, amber = power, red dot = maximum power point).`;
}
function pxInit() {
  const eb = $('#px-err'); if (!eb) return; eb.onchange = () => { SENS.dsErr = eb.checked; try { senseDecide(true); } catch (e) { } };
  $('#px-rec').onclick = () => { SENS.recOn = !SENS.recOn; $('#px-rec').textContent = SENS.recOn ? 'Recording ● (press to stop)' : 'Record sensors ●'; if (SENS.recOn) SENS.rec = SENS.rec || []; };
  $('#px-dl').onclick = () => { const head = 'day,solar_hour,pyranometer_Wm2,PAR_umol,temp_C,RH_pct,soil_pct,rain,wind_ms,mode,angle_deg,pv_vs_best,crop_vs_best,datasheet_errors_on', rows = (SENS.rec || []).map(r => r.join(',')); const blob = new Blob([head + '\n' + rows.join('\n') + '\n'], { type: 'text/csv' }), a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = 'srmc_twin_sensor_log.csv'; document.body.appendChild(a); a.click(); a.remove(); };
  setInterval(() => {
    const L = SENS.last; $('#px-recn').textContent = SENS.recOn ? (SENS.rec || []).length + ' rows recorded' : ((SENS.rec || []).length ? (SENS.rec.length + ' rows ready to download') : '');
    if (L) { const rows = [['Apogee SP-110', L.ghi.toFixed(0) + ' W/m²  →  ' + (0.2 * L.ghi).toFixed(0) + ' mV'], ['Apogee SQ-110 (under canopy)', L.par.toFixed(0) + ' µmol/m²/s  →  ' + (0.2 * L.par).toFixed(0) + ' mV'], ['DHT11', L.T.toFixed(1) + ' °C, ' + L.RH + ' % RH  →  digital word'], ['SEN0193 soil', SENS.soil + ' %  →  ' + (2.5 - SENS.soil / 100 * 1.3).toFixed(2) + ' V'], ['YL-83 rain', L.rain ? 'WET  →  pin LOW' : 'dry  →  pin HIGH'], ['Adafruit 1733', SENS.wind + ' m/s  →  ' + (0.4 + 1.6 * SENS.wind / 32.4).toFixed(2) + ' V']]; $('#px-sig').innerHTML = rows.map(r => '<tr><td>' + r[0] + '</td><td>' + r[1] + '</td></tr>').join(''); }
  }, 500);
  setInterval(pxDraw, 700);
}
"""
k = s.index('/* ---------------- Tab: mechanism'); s = s[:k] + js + '\n' + s[k:]
rep("uxInit(); manInit(); mechCtlInit();", "uxInit(); manInit(); mechCtlInit(); pxInit();")
open(tw, 'w', encoding='utf8').write(s); print('proof patched', len(s) // 1024, 'KB')
