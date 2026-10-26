"""Third patch of the final twin (run AFTER patch_twin.py and patch_mech.py): fault-injection menu for the safety layer, water link (soil probe decides irrigation, water saved), HUD.   python patch_safety_water.py"""
import os, json
here = os.path.dirname(os.path.abspath(__file__)); root = os.path.abspath(os.path.join(here, '..', '..'))
tw = os.path.join(root, 'Review3_Digital_Twin', 'results', 'live_twin', 'SRMC_Digital_Twin.html')
s = open(tw, encoding='utf8').read()
assert 'SAFETY_WATER_PATCHED' not in s, 'already patched; run patch_twin.py and patch_mech.py first'
def rep(old, new, cnt=1):
    global s
    assert old in s, 'MISSING: ' + old[:80]
    s = s.replace(old, new, cnt)
mod = open(os.path.join(here, 'irrigation.js'), encoding='utf8').read()
study = json.load(open(os.path.join(here, 'results', 'irrigation_study.json'), encoding='utf8'))['rows']
rep('<script>window.SRMC_DATA=', '<script>\n' + mod + '\n</script>\n<script>window.SRMC_IRRSTUDY=' + json.dumps(study) + ';/*SAFETY_WATER_PATCHED*/</script>\n<script>window.SRMC_DATA=')
# replace the first HUD water block by the water-link version
a = s.index('  function hudWater(P) {'); b = s.index('  function hud() {')
s = s[:a] + s[b:]                       # remove the first HUD water function (it sits inside the scene scope)
k = s.index('/* ---------------- Tab: mechanism'); s = s[:k] + open(os.path.join(here, 'twin_water_block.js'), encoding='utf8').read() + '\n' + s[k:]      # app scope: water link and the new HUD water text
rep('<div class="card"><h4>Cistern sizing</h4>', '<div class="card"><h4>WATER LINK: the soil probe decides when irrigation runs (and how much water it saves)</h4><canvas id="wl-chart"></canvas><div class="note" id="wl-note"></div><table id="wl-table" style="font-size:12px"></table><div class="note">Compared with a timer (every 4 days in the season, fixed depth). A probe that sticks or dies is caught by the fallback (stuck 3 days or no reading: run the timer schedule). Borewell top-up is assumed to deliver the demand when the cistern is empty. Simulated soil, rain and ET0 from the NASA POWER climate; not field measurements.</div></div>\n    <div class="card"><h4>Cistern sizing</h4>')
rep("else if (st.tab === 'water') tabWater();", "else if (st.tab === 'water') { tabWater(); tabWaterLink(); }")
rep('<div class="hint" style="margin-top:8px"><b>Real board (optional):</b>', '<div class="hint" style="margin-top:8px"><b>Inject a sensor fault (safety demo):</b> <select id="sens-fault"><option value="none">none</option><option value="rainWet">rain sensor stuck WET (dry sunny air)</option><option value="rainDead">rain sensor dead (ignores real rain)</option><option value="soilStuck">soil probe stuck at 12 %</option><option value="soilDead">soil probe unplugged</option><option value="soilGlitch">soil probe glitch (reads 3 %)</option></select></div><div class="hint" style="margin-top:8px"><b>Real board (optional):</b>')
rep("$('#live-connect').onclick = liveConnect;", "$('#live-connect').onclick = liveConnect; $('#sens-fault').onchange = e => { SENS.fault = e.target.value; SENS.ctlR = null; scene3d.refresh(true); };")
open(tw, 'w', encoding='utf8').write(s); print('safety + water link patched', len(s))
# ---- URL parameters for screenshots and demos: ?tab=acc&day=106&hour=9.5
s = open(tw, encoding='utf8').read()
old = "$('#live-connect').onclick = liveConnect;"
assert old in s
s = s.replace(old, old + " (function () { const q = new URLSearchParams(location.search), set = (id, v) => { const el = $(id); if (el && v != null) { el.value = v; el.dispatchEvent(new Event('input')); } }; set('#t-day', q.get('day')); set('#t-hour', q.get('hour')); if (q.get('tab')) setTimeout(() => { const b = document.querySelector('[data-t=\"' + q.get('tab') + '\"]'); if (b) b.click(); }, 700); })();", 1)
open(tw, 'w', encoding='utf8').write(s); print('url params added')
