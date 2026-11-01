"""Ninth patch of the single digital twin (run AFTER patch_proof.py; safe to re-run): replay a REAL day of weather and a monthly model-vs-data check.
 - 15 real days of NASA POWER hourly data for TCE (2023): the 15th of every month, the rainiest, the windiest and the sunniest day
   -> the twin's sunlight, temperature, humidity, wind and rain come from the data instead of the model
 - 'Sensors and proof' tab gets the 12-month model-vs-NASA/PVGIS check
python patch_replay.py"""
import os, shutil, base64, io, json, csv
from PIL import Image
here = os.path.dirname(os.path.abspath(__file__)); root = os.path.abspath(os.path.join(here, '..', '..'))
tw = os.path.join(root, 'Review3_Digital_Twin', 'results', 'live_twin', 'SRMC_Digital_Twin.html')
P10 = os.path.join(root, 'Proof', '10_Review0_Sensors_and_Panels')
bkd = os.path.join(root, '_archive', 'backups_of_files_before_the_final_update', 'replay_patch'); os.makedirs(bkd, exist_ok=True); bk = os.path.join(bkd, 'SRMC_Digital_Twin_before_replay.html')
cur = open(tw, encoding='utf8').read()
if 'REPLAY_PATCHED' not in cur:
    assert 'PROOF_PATCHED' in cur, 'run patch_proof.py first'; shutil.copy(tw, bk)
s = open(bk, encoding='utf8').read()
def rep(old, new, cnt=1):
    global s
    assert old in s, 'MISSING: ' + old[:80]
    s = s.replace(old, new, cnt)
def b64(path, w=1000):
    im = Image.open(path).convert('RGB'); im.thumbnail((w, w)); buf = io.BytesIO(); im.save(buf, 'JPEG', quality=88); return 'data:image/jpeg;base64,' + base64.b64encode(buf.getvalue()).decode()
days = json.load(open(os.path.join(P10, 'sunlight_datasets', 'NASA_POWER_replay_days_for_twin.json'), encoding='utf8'))
mrows = list(csv.reader(open(os.path.join(P10, 'MONTHLY_sunlight_model_vs_NASA_PVGIS.csv'), encoding='utf8')))[1:]
fig_m = b64(os.path.join(P10, 'TRUST_monthly_sunlight_model_vs_NASA_PVGIS.png'), 1100)
GH = 'https://github.com/thanwin19/agrovoltaic-canopy-srmc/blob/main/Proof/10_Review0_Sensors_and_Panels/'

css = """
/*REPLAY_PATCHED*/
#rp-box{border:1px solid #2e6a4a;background:#0f2018;border-radius:10px;padding:8px 12px;margin:10px 0;font-size:13px}#rp-box h5{margin:0 0 4px;font-size:13px;color:#8fe0b0}#rp-box select{background:var(--panel2);color:var(--tx);border:1px solid var(--line);border-radius:6px;padding:3px 6px;font:inherit;max-width:100%}
#rp-box.on{outline:2px solid #72B830}
"""
rep("</style>\n</head>", css + "</style>\n</head>")
opts = ''.join('<option value="%d">%s</option>' % (i, d['label']) for i, d in enumerate(days))
box = '''<div id="rp-box"><h5>REPLAY A REAL DAY: NASA POWER weather for TCE, 2023</h5>
        <select id="rp-sel">''' + opts + '''</select><br>
        <label style="display:inline;font-size:13px"><input type="checkbox" id="rp-on"> <b>Use this day's real weather</b></label> <span class="hint">sunlight, temperature, humidity, wind and rain come from the data instead of the model</span>
        <div id="rp-read" class="hint" style="margin-top:4px"></div></div>
        <div id="px-box">'''
rep('<div id="px-box">', box)

# hooks in the sensor step
rep("  const T = SENS.temp, RH = SENS.rh, ws = clim.wind ? clim.wind[m] : 2, rain = lv ? lv.rain : st.rain,", "  rpApply(irr, hr);\n  const T = SENS.temp, RH = SENS.rh, ws = clim.wind ? clim.wind[m] : 2, rain = lv ? lv.rain : (SENS.rp && SENS.rp.on && SENS.rp.rain != null ? SENS.rp.rain : st.rain),")

# proof tab: monthly validation card, and the lists
mt = ''.join('<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s %%</td><td>%s %%</td></tr>' % (r[0], r[1], r[2], r[3], r[4], r[5]) for r in mrows)
card = '''<div class="card"><h4>Is the sunlight model right in every month? Model against NASA POWER 2023 and PVGIS 2020</h4>
      <div class="pgrid"><div><table class="pt"><tr><th>Month</th><th>Model Wh/m²/day</th><th>NASA 2023</th><th>PVGIS 2020</th><th>vs NASA</th><th>vs PVGIS</th></tr>''' + mt + '''</table></div>
      <div><img src="''' + fig_m + '''" style="width:100%;border-radius:8px;background:#fff"></div></div>
      <div class="note"><b>Result:</b> against NASA POWER 2023 the year average is +2.0 % (monthly differences from −6.9 % to +9.9 %; hourly shape RMSE 40 to 91 W/m², mean 67). Against PVGIS-ERA5 of the single year 2020 the model is +7.9 % on average and about +16 to +26 % in June to September and December: one reanalysis year differs a lot from the long-term climate, and the earlier multi-year comparison with PVGIS gave +5.0 %. So the model is a good typical year, not a prediction of one particular year. Real hourly wind at TCE in 2023 never exceeded 10.9 m/s (hourly means at 10 m, gusts not included), so the 15 m/s storm stow never triggered in that year's data. Files: ''' + '<a href="%sMONTHLY_sunlight_model_vs_NASA_PVGIS.csv" target="_blank" rel="noopener">monthly table</a>, <a href="%ssunlight_datasets/NASA_POWER_hourly_2023_full_year_TCE.json" target="_blank" rel="noopener">NASA hourly 2023</a>' % (GH, GH) + '''.</div></div>
    <div class="card"><h4>Accuracy of the co-optimisation: what we obtained against ordinary designs</h4>'''
rep('<div class="card"><h4>Accuracy of the co-optimisation: what we obtained against ordinary designs</h4>', card)
rep("<li>Live I-V curve and array power for the real panel</li>", "<li>Live I-V curve and array power for the real panel</li><li>Replay of real NASA POWER weather days (15 days of 2023) in the sensor panel</li><li>Month-by-month check of the sunlight model against NASA POWER and PVGIS</li>")
rep("<li>Replay of NASA POWER hourly weather for any chosen date</li>", "<li>Replay of logged data from our own sensors (CSV import)</li>")

RP = json.dumps(days, separators=(',', ':'))
js = "window.SRMC_REPLAY = " + RP + r""";
function rpApply(irr, hr) {
  const R = SENS.rp; if (!R || !R.on) return; const D = window.SRMC_REPLAY[R.idx]; if (!D) return;
  const x = Math.max(0, Math.min(22.999, hr - 0.5)), i0 = Math.floor(x), f = x - i0, at = a => a[i0] * (1 - f) + a[Math.min(23, i0 + 1)] * f;
  const g = Math.max(0, at(D.ghi)); if (g < 1) { irr.ghi = 0; irr.dni = 0; irr.dhi = 0; } else if (irr.ghi > 1) { const k = g / irr.ghi; irr.dni *= k; irr.dhi *= k; irr.ghi = g; } else { irr.ghi = g; irr.dni = 0; irr.dhi = g; }
  SENS.temp = +at(D.T).toFixed(1); SENS.rh = Math.round(at(D.RH)); SENS.wind = Math.round(at(D.ws) * 10) / 10; const pr = at(D.rain); R.rain = pr >= 0.5; R.txt = `${D.label}, solar hour ${hr.toFixed(1)}: sunlight ${g.toFixed(0)} W/m², ${SENS.temp} °C, ${SENS.rh} % RH, wind ${SENS.wind} m/s (10 m), rain ${pr.toFixed(1)} mm/h`;
  [['#sens-temp', '#v-sens-temp', SENS.temp, ' °C'], ['#sens-rh', '#v-sens-rh', SENS.rh, ' %'], ['#sens-wind', '#v-sens-wind', SENS.wind, ' m/s']].forEach(([a, b, v, u]) => { const e = $(a); if (e) { e.value = v; $(b).textContent = v + u; } });
  const st2 = window.SRMC_UI && window.SRMC_UI.st; if (st2 && !!st2.rain !== R.rain) uxRain(R.rain);
}
function rpInit() {
  const on = $('#rp-on'), sel = $('#rp-sel'); if (!on) return; SENS.rp = { on: false, idx: 0, rain: null, txt: '' };
  const setDay = () => { const D = window.SRMC_REPLAY[SENS.rp.idx]; uxSet('#t-day', D.doy - 1); };
  on.onchange = () => { SENS.rp.on = on.checked; $('#rp-box').classList.toggle('on', on.checked); if (on.checked) { SENS.manualTH = true; setDay(); } else { SENS.manualTH = false; SENS.rp.rain = null; } try { senseDecide(true); scene3d.refresh(true); } catch (e) { } };
  sel.onchange = () => { SENS.rp.idx = +sel.value; if (on.checked) { setDay(); try { senseDecide(true); scene3d.refresh(true); } catch (e) { } } };
  setInterval(() => { $('#rp-read').textContent = SENS.rp.on ? SENS.rp.txt : 'Off: the twin uses its own sun, sky and weather model.'; }, 500);
}
"""
k = s.index('/* ---------------- Tab: mechanism'); s = s[:k] + js + '\n' + s[k:]
rep("mechCtlInit(); pxInit();", "mechCtlInit(); pxInit(); rpInit();")
open(tw, 'w', encoding='utf8').write(s); print('replay patched', len(s) // 1024, 'KB')
