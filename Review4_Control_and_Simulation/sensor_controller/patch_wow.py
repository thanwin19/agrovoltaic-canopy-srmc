"""Fourth patch of the single digital twin (run AFTER patch_twin, patch_mech and patch_safety_water; safe to re-run): adds
 - Ground map tab (3-D ray-cast light map under the canopy, any day, hour and tilt)
 - Structure tab (3-objective trade-off, stow-angle check, finite element check of the lever arm)
 - Design explorer tab (many-objective NSGA-III search of the whole canopy)
 - Edge AI tab (the controller distilled into a small neural network for an ESP32, optional steering in the 3D twin; sensor-attack test of the anemometer)
 - three anemometer attack options in the fault selector, with a drive-wire-tension monitor.
python patch_wow.py"""
import base64, csv, io, json, os, shutil, zlib
from PIL import Image
here = os.path.dirname(os.path.abspath(__file__)); root = os.path.abspath(os.path.join(here, '..', '..'))
tw = os.path.join(root, 'Review3_Digital_Twin', 'results', 'live_twin', 'SRMC_Digital_Twin.html')
bkd = os.path.join(root, '_archive', 'backups_of_files_before_the_final_update', 'wow_patch'); os.makedirs(bkd, exist_ok=True); bk = os.path.join(bkd, 'SRMC_Digital_Twin_before_wow.html')
if not os.path.exists(bk):
    cur = open(tw, encoding='utf8').read(); assert 'WOW_PATCHED' not in cur, 'the twin is already patched and no backup exists'; shutil.copy(tw, bk)
s = open(bk, encoding='utf8').read()                       # always start from the saved version without these tabs
def rep(old, new, cnt=1):
    global s
    assert old in s, 'MISSING: ' + old[:80]
    s = s.replace(old, new, cnt)
def jpg(path, maxw=1300, q=84):
    im = Image.open(path).convert('RGB'); im.thumbnail((maxw, maxw * 2)); b = io.BytesIO(); im.save(b, 'JPEG', quality=q); return base64.b64encode(b.getvalue()).decode()
R2 = os.path.join(root, 'Review2_Solar_and_Shadow', 'results'); R4 = here; R1 = os.path.join(root, 'Review1_Design_and_CAD', 'fea')
# ---------------- data
meta = json.load(open(os.path.join(R2, 'ground_heatmap', 'meta.json'))); sd = json.load(open(os.path.join(R2, 'shadow_heatmap', 'shade_data.json')))
gm = dict(keys=meta['keys'], ny=meta['ny'], nx=meta['nx'], res=meta['res'], x0=meta['x0'], y0=meta['y0'], stats=meta['stats'], days=sd['days'], tilts=sd['tilts'], ctrl={d: {str(float(h)).rstrip('0').rstrip('.') if float(h) % 1 else str(int(float(h))): a for h, a in v.items()} for d, v in sd['ctrl'].items()})
fea = json.load(open(os.path.join(R1, 'fea_results.json')))
par = []
with open(os.path.join(R4, 'pareto3', 'T23_pareto3_designs.csv'), encoding='utf8') as f:
    for r in csv.DictReader(f):
        if r['load model'] == 'B': par.append(dict(name=r['design'], pv=float(r['energy kWh/m2/yr']), crop=float(r['crop net INR lakh/ha/yr']), load=float(r['structural demand index at 140 km/h']), front=r['on Pareto front'] == 'yes'))
dex = json.load(open(os.path.join(R4, 'design_explorer', 'design_explorer.json')))
nn = dict(model=json.load(open(os.path.join(R4, 'esp32_model', 'model.json'))), results=json.load(open(os.path.join(R4, 'esp32_model', 'results.json'))))
cls = os.path.join(R4, 'esp32_model', 'closed_loop_summary.json')
if os.path.exists(cls): nn['closed'] = json.load(open(cls))['reference_site']
atk = json.load(open(os.path.join(R4, 'results', 'attack_test.json')))
def _dom(o, r): return o['solar'] >= r['solar'] and o['crop'] >= r['crop'] and o['steel_t'] <= r['steel_t'] and o['rainfed'] >= r['rainfed'] and (o['solar'] > r['solar'] or o['crop'] > r['crop'] or o['steel_t'] < r['steel_t'] or o['rainfed'] > r['rainfed'])
dex['dominating_final'] = sum(_dom(o, dex['reference']) for o in dex['all']); dex['n_eval'] = len(dex['all'])
W = dict(gm=gm, str=dict(fea=dict(cases=fea['cases'], tube=fea['tube'], validation=fea['validation']), pareto=par), dex=dict(front=dex['front'], reference=dex['reference'], evaluated=dex['n_eval'], dominating=dex['dominating_final']), nn=nn, atk=atk)
gm_b64 = base64.b64encode(open(os.path.join(R2, 'ground_heatmap', 'maps.bin.z'), 'rb').read()).decode()
# ---------------- insert
block = open(os.path.join(here, 'wow_block.js'), encoding='utf8').read(); panes = open(os.path.join(here, 'wow_panes.html'), encoding='utf8').read()
panes = panes.replace('{{IMG_PARETO}}', jpg(os.path.join(R4, 'pareto3', 'fig_pareto3_load.png'))).replace('{{IMG_FEA}}', jpg(os.path.join(R1, 'fig_arm_stress.png'), 1100))
rep('<script>window.SRMC_DATA=', '<script>window.SRMC_WOW=' + json.dumps(W, separators=(',', ':')) + ';/*WOW_PATCHED*/</script>\n<script>window.SRMC_GM_B64="' + gm_b64 + '";</script>\n<script>window.SRMC_DATA=')
k = s.index('/* ---------------- Tab: mechanism'); s = s[:k] + block + '\n' + s[k:]
rep('    <button class="tab" data-t="method">', '    <button class="tab" data-t="gmap">Ground map<small>shade · red/yellow/green</small></button>\n    <button class="tab" data-t="struct">Structure<small>3 goals · stress</small></button>\n    <button class="tab" data-t="dex">Design explorer<small>NSGA-III</small></button>\n    <button class="tab" data-t="edge">Edge AI<small>ESP32 · attack test</small></button>\n    <button class="tab" data-t="method">')
rep('  <section class="pane method" id="pane-method"', panes + '  <section class="pane method" id="pane-method"')
rep("else if (st.tab === 'acc') tabAcc();", "else if (st.tab === 'acc') tabAcc(); else if (st.tab === 'gmap') tabGmap(); else if (st.tab === 'struct') tabStruct(); else if (st.tab === 'dex') tabDex(); else if (st.tab === 'edge') tabEdge();")
# anemometer attacks in the fault menu
rep('<option value="soilGlitch">soil probe glitch (reads 3 %)</option>', '<option value="soilGlitch">soil probe glitch (reads 3 %)</option><option value="windZero">ATTACK: anemometer spoofed to read 0</option><option value="windReplay">ATTACK: anemometer replays a calm recording</option><option value="windRamp">ATTACK: anemometer drifts 6 m/s low</option>')
rep("const stt = apply ? SENS.st : cloneSt(SENS.st);", "const WW = wowWind(fl, SENS.wind, SENS.cmd); const stt = apply ? SENS.st : cloneSt(SENS.st);")
rep("wind: SENS.wind, day: n,", "wind: WW.used, day: n,")
rep("if (apply) SENS.cmd = d.angle;", "if (SENS.useNN === undefined) SENS.useNN = false; SENS.useNN = !!($('#ed-use') && $('#ed-use').checked); if (SENS.useNN && d.mode === 'OPTIMISE' && WOW.nn) { const a0 = wowNN(sun, irr, T, RH, SENS.soil, parUm, SENS.cmd, n); d.angle = Math.max(SENS.cmd - 6, Math.min(SENS.cmd + 6, a0)); d.reason = 'DISTILLED NETWORK (ESP32 model) picks ' + a0.toFixed(1) + '°; ' + d.reason; } if (apply) SENS.cmd = d.angle;")
rep("<div><b>6 Anemometer (wind):</b> ${SENS.wind.toFixed(1)} m/s → ${SENS.wind >= 15 ? '<span style=\"color:#ffb3a8\">STORM: panels edge-on at 90°</span>' : 'normal (stow at 15 m/s = 54 km/h, resume below 12 m/s)'}</div>",
    "<div><b>6 Anemometer (wind):</b> reads ${WW.read.toFixed(1)} m/s${fl.startsWith('wind') ? ' <span style=\"color:#ffb3a8\">(ATTACKED: the real wind is ' + SENS.wind.toFixed(1) + ' m/s)</span>' : ''} → ${WW.used >= 15 ? '<span style=\"color:#ffb3a8\">STORM: panels edge-on at 90°</span>' : 'normal (stow at 15 m/s = 54 km/h, resume below 12 m/s)'}<br><span style=\"color:#9fc7e8\">Wire-tension monitor (load cell on the winch): wire force ${WW.F.toFixed(1)} kN → wind ${WW.vEst.toFixed(1)} m/s ${WW.flagged ? '<b style=\"color:#ffb3a8\">ANEMOMETER FAULT: stowed on the tension reading, reset by the operator</b>' : (WW.monitor ? '(consistent)' : '(monitor switched off)')}</span></div>")
open(tw, 'w', encoding='utf8').write(s); print('wow tabs added', len(s) // 1024, 'KB')
