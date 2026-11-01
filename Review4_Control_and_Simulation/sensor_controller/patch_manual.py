"""Sixth patch of the single digital twin (run AFTER patch_ux.py; safe to re-run): manual entry for ALL six sensors.
 - typed number box beside every slider (cloud, temperature, humidity, soil, wind), two-way
 - pyranometer (W/m2) and PAR (umol/m2/s) can be typed directly: they replace the simulated reading until switched off
 - rain sensor toggle inside the sensor panel
python patch_manual.py"""
import os, shutil
here = os.path.dirname(os.path.abspath(__file__)); root = os.path.abspath(os.path.join(here, '..', '..'))
tw = os.path.join(root, 'Review3_Digital_Twin', 'results', 'live_twin', 'SRMC_Digital_Twin.html')
bkd = os.path.join(root, '_archive', 'backups_of_files_before_the_final_update', 'manual_patch'); os.makedirs(bkd, exist_ok=True); bk = os.path.join(bkd, 'SRMC_Digital_Twin_before_manual.html')
cur = open(tw, encoding='utf8').read()
if 'MANUAL_PATCHED' not in cur:                                             # twin was just rebuilt by patch_ux.py: save it as the new starting point
    assert 'UX_PATCHED' in cur, 'run patch_ux.py first'; shutil.copy(tw, bk)
s = open(bk, encoding='utf8').read()
def rep(old, new, cnt=1):
    global s
    assert old in s, 'MISSING: ' + old[:80]
    s = s.replace(old, new, cnt)
css = """
/*MANUAL_PATCHED*/
.mnum{width:74px;margin-left:8px;background:var(--panel2);color:var(--tx);border:1px solid var(--line);border-radius:6px;padding:2px 6px;font:inherit;font-size:13px}
#man-box{border:1px solid #4a6a2a;background:#14200d;border-radius:10px;padding:8px 12px;margin:10px 0}#man-box h5{margin:0 0 4px;font-size:13px;color:#b8d9a0}
#man-box .r{display:flex;align-items:center;gap:8px;margin:5px 0;font-size:13px}#man-box .r span{flex:1}
.man-on{outline:2px solid #FFB84D}
"""
rep("</style>\n</head>", css + "</style>\n</head>")
box = """<div id="man-box"><h5>TYPE THE SENSOR VALUES YOURSELF</h5>
        <div class="hint" style="margin:0 0 6px">Every sensor has a number box. Sunlight and plant light are normally worked out from the sun and the cloud slider; tick the box to type them instead. The controller then sees exactly your numbers.</div>
        <label style="display:inline;font-size:13px"><input type="checkbox" id="man-on"> <b>Manual pyranometer and PAR</b></label>
        <div class="r"><span>Pyranometer, sunlight (W/m²)</span><input class="mnum" type="number" id="man-ghi" min="0" max="1200" step="10" value="800"></div>
        <div class="r"><span>PAR above the canopy (µmol/m²/s)</span><input class="mnum" type="number" id="man-par" min="0" max="2400" step="20" value="1640"></div>
        <div class="r"><span>Rain sensor</span><button class="b" id="man-rain">dry (press to wet it)</button></div>
        <div id="man-state" class="hint"></div></div>
        <div id="sens-trace" """
rep('<div id="sens-trace" ', box)
# manual pyranometer: replaces the simulated / live reading
rep("irr.ghi = lv.ghi; } }\n  if (!lv && !SENS.manualSoil)", "irr.ghi = lv.ghi; } }\n  if (SENS.man && SENS.man.on) { const k = SENS.man.ghi / Math.max(irr.ghi, 1); irr.dni *= k; irr.dhi *= k; irr.ghi = SENS.man.ghi; }\n  if (!lv && !SENS.manualSoil)")
rep("const T = SENS.temp, RH = SENS.rh, ws = clim.wind ? clim.wind[m] : 2, rain = lv ? lv.rain : st.rain, night = irr.ghi < 20 || sun.sz < .02,", "const T = SENS.temp, RH = SENS.rh, ws = clim.wind ? clim.wind[m] : 2, rain = lv ? lv.rain : st.rain, night = irr.ghi < 20 || (sun.sz < .02 && !(SENS.man && SENS.man.on)),")
rep("if (lv && lv.par != null) { parUm = lv.par; lsr = parUm / SRMC_SC.UM_PER_W / Math.max(irr.ghi, 1); } }", "if (lv && lv.par != null) { parUm = lv.par; lsr = parUm / SRMC_SC.UM_PER_W / Math.max(irr.ghi, 1); } if (SENS.man && SENS.man.on) { parUm = SENS.man.par; lsr = parUm / SRMC_SC.UM_PER_W / Math.max(irr.ghi, 1); } }")
js = r"""
/* ---------------- Manual entry for every sensor ---------------- */
function manInit() {
  SENS.man = { on: false, ghi: 800, par: 1640 };
  const pairs = [['sens-cloud', 'v-sens-cloud'], ['sens-temp', 'v-sens-temp'], ['sens-rh', 'v-sens-rh'], ['sens-soil', 'v-sens-soil'], ['sens-wind', 'v-sens-wind']];
  pairs.forEach(([id]) => { const sl = $('#' + id); if (!sl || $('#n-' + id)) return; const nb = document.createElement('input'); nb.type = 'number'; nb.className = 'mnum'; nb.id = 'n-' + id; nb.min = sl.min; nb.max = sl.max; nb.step = sl.step; nb.value = sl.value;
    nb.addEventListener('change', () => { const v = Math.max(+sl.min, Math.min(+sl.max, +nb.value)); nb.value = v; uxSet('#' + id, v); }); sl.insertAdjacentElement('afterend', nb); });
  const on = $('#man-on'), g = $('#man-ghi'), p = $('#man-par'), rb = $('#man-rain');
  const apply = () => { SENS.man.on = on.checked; SENS.man.ghi = Math.max(0, Math.min(1200, +g.value || 0)); SENS.man.par = Math.max(0, Math.min(2400, +p.value || 0)); $('#sens-card').classList.toggle('man-on', SENS.man.on); try { senseDecide(true); scene3d.refresh(true); } catch (e) { } };
  on.onchange = apply; g.onchange = apply; p.onchange = apply;
  g.addEventListener('input', () => { if (on.checked) apply(); }); p.addEventListener('input', () => { if (on.checked) apply(); });
  rb.onclick = () => { const U = window.SRMC_UI; uxRain(!U.st.rain); };
  const rs = $('#sens-reset'); if (rs) rs.addEventListener('click', () => { on.checked = false; apply(); });
  setInterval(() => {
    pairs.forEach(([id]) => { const sl = $('#' + id), nb = $('#n-' + id); if (sl && nb && document.activeElement !== nb && nb.value !== sl.value) nb.value = sl.value; });
    const U = window.SRMC_UI; if (U) { rb.textContent = U.st.rain ? 'WET (press to dry it)' : 'dry (press to wet it)'; rb.style.background = U.st.rain ? '#1f4a7a' : ''; }
    const L = SENS.last; $('#man-state').textContent = SENS.man.on ? 'MANUAL: the controller reads ' + SENS.man.ghi + ' W/m² and PAR ' + SENS.man.par + ' µmol/m²/s from you.' : 'Sunlight and PAR are simulated from the sun, the cloud slider and the panel angle' + (L ? ' (now ' + Math.round(L.ghi) + ' W/m², PAR ' + Math.round(L.par) + ').' : '.');
  }, 400);
}
"""
k = s.index('/* ---------------- Tab: mechanism'); s = s[:k] + js + '\n' + s[k:]
rep("uxInit();", "uxInit(); manInit();")
open(tw, 'w', encoding='utf8').write(s); print('manual patched', len(s) // 1024, 'KB')
