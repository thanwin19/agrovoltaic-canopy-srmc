"""Seventh patch of the single digital twin (run AFTER patch_manual.py; safe to re-run): "DRIVE IT YOURSELF" card at the top of the How-it-tilts tab.
 - hold-to-tilt buttons and a slider: you are the motor
 - FOLLOW THE LIVE CONTROLLER: the mechanism moves exactly as the six-sensor controller commands (change a sensor, the wire, arms and panels move)
 - scenario buttons that set the sensors without leaving the tab
 - a live cause-and-effect chain: sensors -> decision -> motor -> wire travel -> panel angle
python patch_mech.py"""
import os, shutil
here = os.path.dirname(os.path.abspath(__file__)); root = os.path.abspath(os.path.join(here, '..', '..'))
tw = os.path.join(root, 'Review3_Digital_Twin', 'results', 'live_twin', 'SRMC_Digital_Twin.html')
bkd = os.path.join(root, '_archive', 'backups_of_files_before_the_final_update', 'mech_patch'); os.makedirs(bkd, exist_ok=True); bk = os.path.join(bkd, 'SRMC_Digital_Twin_before_mech.html')
cur = open(tw, encoding='utf8').read()
if 'MECHCTL_PATCHED' not in cur:
    assert 'MANUAL_PATCHED' in cur, 'run patch_manual.py first'; shutil.copy(tw, bk)
s = open(bk, encoding='utf8').read()
def rep(old, new, cnt=1):
    global s
    assert old in s, 'MISSING: ' + old[:80]
    s = s.replace(old, new, cnt)
css = """
/*MECHCTL_PATCHED*/
#mc-card{border:2px solid #4a6a2a}#mc-card .mcrow{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin:8px 0}
#mc-card .mcbig{font-size:18px;padding:10px 18px}#mc-card .mcon{background:#2d5a14;border-color:#72B830}
#mc-chain{display:flex;gap:6px;flex-wrap:wrap;align-items:stretch;margin-top:8px}#mc-chain div{flex:1;min-width:150px;background:var(--panel2);border:1px solid var(--line);border-radius:10px;padding:8px 10px;font-size:12px;color:var(--mute)}#mc-chain div b{display:block;color:var(--g);font-size:13px;margin-bottom:2px}#mc-chain div span{display:block;color:var(--tx);font-size:14px}#mc-chain i{align-self:center;font-style:normal;color:var(--mute)}
"""
rep("</style>\n</head>", css + "</style>\n</head>")
card = """<div class="card" id="mc-card"><h4>DRIVE IT YOURSELF: make the panels tilt and see why</h4>
      <div class="note" style="margin-top:0;font-size:14px">Two ways. <b>(1) You are the motor:</b> hold a tilt button and watch the drum, the red wire, the lever arms and the panels all move together. <b>(2) Follow the controller:</b> press a weather button; the six sensors change, the controller decides, and the mechanism below moves in real time.</div>
      <div class="mcrow"><button class="b mcbig" id="mc-less">&#9660; less tilt (hold)</button><button class="b mcbig" id="mc-more">&#9650; more tilt (hold)</button><span style="color:var(--mute)">or</span><button class="b mcbig" id="mc-follow">Follow the live controller: OFF</button></div>
      <div class="mcrow"><span style="color:var(--mute)">Weather (sets the sensors):</span><button class="b" data-mcs="clear">&#9728; Clear noon</button><button class="b" data-mcs="cloud">&#9925; Clouds</button><button class="b" data-mcs="hot">&#128293; Hot and dry</button><button class="b" data-mcs="rain">&#127783; Rain</button><button class="b" data-mcs="storm">&#127786; Storm</button><button class="b" data-mcs="night">&#127769; Night</button></div>
      <div class="mcrow"><label style="display:inline;margin:0">Wind sensor <b id="mc-wv">3 m/s</b></label><input type="range" id="mc-wind" min="0" max="25" step="0.5" value="3" style="max-width:220px"><label style="display:inline;margin:0 0 0 12px">Cloud <b id="mc-cv">0 %</b></label><input type="range" id="mc-cloud" min="0" max="100" step="5" value="0" style="max-width:220px"></div>
      <div id="mc-chain"></div></div>
    """
rep('<div class="card"><h4>STEP A. Close-up', card + '<div class="card"><h4>STEP A. Close-up')
# follow mode inside the animation loop
rep("const e = MECH.target - MECH.cur, mv = 22 * dt;", "if (MECH.follow) mechFollow(dt);\n  if (MECH.hold2) { MECH.target = Math.max(3, Math.min(90, MECH.target + MECH.hold2 * 30 * dt)); MECH.cur = MECH.cur; }\n  const e = MECH.target - MECH.cur, mv = 22 * dt;")
js = r"""
/* ---------------- Drive it yourself (How it tilts tab) ---------------- */
function mechFollow(dt) {
  MECH.auto = false; MECH.fT = (MECH.fT || 0) + dt;
  if (MECH.fT > .5) { MECH.fT = 0; try { senseDecide(true); } catch (e) { } }
  const L = SENS.last; if (L) MECH.target = ['STOW', 'RAIN', 'NIGHT'].includes(L.mode) && L.angle != null ? L.angle : SENS.cmd;
}
function mechCtlInit() {
  const fb = $('#mc-follow'); if (!fb) return;
  const setFollow = on => { MECH.follow = on; fb.textContent = 'Follow the live controller: ' + (on ? 'ON' : 'OFF'); fb.classList.toggle('mcon', on); if (on) { MECH.auto = false; $('#mech-auto').checked = false; if (!SENS.on) { $('#sens-on').checked = true; $('#sens-on').dispatchEvent(new Event('change')); } } };
  fb.onclick = () => setFollow(!MECH.follow);
  const hold = (id, dir) => { const b = $(id); const dn = e => { e.preventDefault(); setFollow(false); MECH.auto = false; $('#mech-auto').checked = false; MECH.hold2 = dir; }, up = () => { MECH.hold2 = 0; }; b.addEventListener('pointerdown', dn); ['pointerup', 'pointerleave', 'pointercancel'].forEach(ev => b.addEventListener(ev, up)); };
  hold('#mc-more', 1); hold('#mc-less', -1);
  const off = () => setFollow(false); $('#mech-slider').addEventListener('input', off); $$('[data-mech]').forEach(b => b.addEventListener('click', off));
  $$('[data-mcs]').forEach(b => b.onclick = () => { const sc = UX_SCEN.find(x => x.id === b.dataset.mcs); $('#sens-reset') && $('#sens-reset').click(); uxFault('none'); uxRain(false); uxSet('#sens-wind', 3); const so = $('#sens-on'); so.checked = true; so.dispatchEvent(new Event('change')); sc.set(); setFollow(true); const w = $('#ux-watch'); if (w) w.innerHTML = `<b>${sc.icon} ${sc.name}:</b> ${sc.what} <span>What to watch: ${sc.watch}</span>`; });
  $('#mc-wind').oninput = e => { uxSet('#sens-wind', e.target.value); setFollow(true); }; $('#mc-cloud').oninput = e => { uxSet('#sens-cloud', e.target.value); setFollow(true); };
  setInterval(() => {
    if (st.tab !== 'mech') return; const L = SENS.last, cur = MECH.cur, tgt = MECH.target, Lr = .44, OFF = 45 * D2R, tipx = th => Lr * Math.sin(OFF - th * D2R), dmm = Math.round(1000 * (tipx(cur) - tipx(3)));
    const run = Math.abs(tgt - cur) > .3, dir = tgt > cur ? 'winding the wire in' : 'letting the wire out';
    $('#mc-wv').textContent = SENS.wind + ' m/s'; $('#mc-cv').textContent = SENS.cloud + ' %'; if (document.activeElement !== $('#mc-wind')) $('#mc-wind').value = SENS.wind; if (document.activeElement !== $('#mc-cloud')) $('#mc-cloud').value = SENS.cloud;
    const c = (t, h, x) => `<div><b>${t}</b><span>${h}</span>${x || ''}</div>`;
    $('#mc-chain').innerHTML = c('1 Sensors', L ? Math.round(L.ghi) + ' W/m² sun, wind ' + SENS.wind + ' m/s, ' + (st.rain ? 'RAIN' : 'dry') : '-', L ? SENS.temp + ' °C, ' + SENS.rh + ' % RH, soil ' + SENS.soil + ' %' : '') + '<i>&rarr;</i>' +
      c('2 Controller decides', L ? L.mode.replace('OPTIMISE', 'tracking the sun') + ' &rarr; ' + (['STOW', 'RAIN', 'NIGHT'].includes(L.mode) ? L.angle : SENS.cmd).toFixed(1) + '°' : '-', MECH.follow ? 'following it' : 'you are in control') + '<i>&rarr;</i>' +
      c('3 Motor and drum', run ? 'running: ' + dir : 'stopped, brake on', 'target ' + tgt.toFixed(1) + '°') + '<i>&rarr;</i>' +
      c('4 Wire moves', Math.abs(dmm) + ' mm', 'at the lever-arm tip, from flat') + '<i>&rarr;</i>' +
      c('5 Panels tilt', cur.toFixed(1) + '°', 'all arms together');
  }, 300);
}
"""
k = s.index('/* ---------------- Tab: mechanism'); s = s[:k] + js + '\n' + s[k:]
rep("uxInit(); manInit();", "uxInit(); manInit(); mechCtlInit();")
open(tw, 'w', encoding='utf8').write(s); print('mech patched', len(s) // 1024, 'KB')
