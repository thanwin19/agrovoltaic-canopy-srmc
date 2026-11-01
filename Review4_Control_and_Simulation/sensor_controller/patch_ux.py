"""Fifth patch of the single digital twin (run AFTER patch_wow.py; safe to re-run): a judge-friendly layer.
 - Start page (what it is, live plain-language status, eight one-click scenarios, a map of the tabs, how far to trust it)
 - plain tab names, sensor panel beside the 3D view (not below it), a live status bar on every tab, design controls hidden until asked for, honesty bar
python patch_ux.py"""
import os, shutil
here = os.path.dirname(os.path.abspath(__file__)); root = os.path.abspath(os.path.join(here, '..', '..'))
tw = os.path.join(root, 'Review3_Digital_Twin', 'results', 'live_twin', 'SRMC_Digital_Twin.html')
bkd = os.path.join(root, '_archive', 'backups_of_files_before_the_final_update', 'ux_patch'); os.makedirs(bkd, exist_ok=True); bk = os.path.join(bkd, 'SRMC_Digital_Twin_before_ux.html')
if not os.path.exists(bk):
    cur = open(tw, encoding='utf8').read(); assert 'UX_PATCHED' not in cur and 'WOW_PATCHED' in cur, 'run patch_wow.py first'; shutil.copy(tw, bk)
s = open(bk, encoding='utf8').read()
def rep(old, new, cnt=1):
    global s
    assert old in s, 'MISSING: ' + old[:80]
    s = s.replace(old, new, cnt)
css = """
/*UX_PATCHED*/
body:not(.adv) aside{display:none}body:not(.adv) .wrap{grid-template-columns:1fr}
#honest{background:#2a2410;color:#f0d98a;font-size:12px;padding:6px 24px;border-bottom:1px solid var(--line)}
#ux-strip{position:sticky;top:0;z-index:20;background:rgba(14,11,8,.94);backdrop-filter:blur(6px);border-bottom:1px solid var(--line);padding:7px 24px;font-size:13px;display:flex;gap:10px;align-items:center;flex-wrap:wrap}#ux-strip span{color:var(--mute)}
#ux-toggle{margin-left:auto}body.tab-guide #kpis,body.tab-guide #checks{display:none}
.tabs{gap:6px}.tab{min-width:0}.tab small{font-size:10px}
.hero .lead{font-size:15px;line-height:1.7;max-width:980px}
.flow{display:flex;gap:8px;align-items:stretch;flex-wrap:wrap;margin-top:12px}.flow div{flex:1;min-width:170px;background:var(--panel2);border:1px solid var(--line);border-radius:10px;padding:10px 12px}.flow b{display:block;color:var(--g);margin-bottom:3px}.flow span{font-size:12px;color:var(--mute)}.flow i{align-self:center;font-style:normal;color:var(--mute);font-size:22px}
.live{display:flex;gap:10px;flex-wrap:wrap;align-items:stretch}.big{background:var(--panel2);border:2px solid var(--line);border-radius:12px;padding:8px 18px;min-width:150px}.big span{display:block;font-size:11px;color:var(--mute);text-transform:uppercase;letter-spacing:.06em}.big b{font-size:30px}
.say{flex:1;min-width:260px;background:var(--panel2);border-left:5px solid var(--g);border-radius:8px;padding:10px 14px;font-size:15px}.say span{font-size:12px;color:var(--mute)}
.rd{width:100%;margin-top:10px;font-size:13px;border-collapse:collapse}.rd td{padding:4px 8px;border-bottom:1px solid var(--line)}.rd td:first-child{color:var(--mute);width:42%}
.scen{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:10px;margin-top:10px}
.sc{text-align:left;background:var(--panel2);color:var(--tx);border:1px solid var(--line);border-radius:10px;padding:10px 12px;cursor:pointer;font:inherit}.sc:hover{border-color:var(--g);background:#1f2a14}.sc i{font-style:normal;font-size:22px;float:right}.sc b{display:block;font-size:14px;margin-bottom:2px}.sc span{font-size:12px;color:var(--mute)}
.plain{margin:8px 0 0 18px;line-height:1.7;font-size:13px}
.watch{background:#17240f;border:1px solid #2e4a1a;border-radius:10px;padding:9px 14px;margin-bottom:12px;font-size:13px}.watch span{display:block;color:#b8d9a0;margin-top:2px}
#pane-twin{display:grid;grid-template-columns:minmax(0,1.55fr) minmax(330px,1fr);gap:14px;align-items:start}
#pane-twin>#ux-watch{grid-column:1/3}#pane-twin>#three,#pane-twin>.bar{grid-column:1}
#pane-twin>#sens-card{grid-column:2;grid-row:2 / span 3;position:sticky;top:48px;max-height:calc(100vh - 60px);overflow:auto}
#pane-twin>.note{grid-column:1/3}
@media(max-width:1100px){#pane-twin{display:block}#pane-twin>#sens-card{position:static;max-height:none}}
"""
rep("</style>\n</head>", css + "</style>\n</head>")
rep("</header>", '<button class="b" id="ux-toggle">Show design controls</button></header>\n<div id="honest"><b>Simulation study.</b> Sensor values are simulated unless a real board is connected; prices, farmer share and crop values are assumptions; accuracy is measured against the controller\'s own goal, not against a field trial. Start with the first tab.</div>\n<div id="ux-strip"><span>starting...</span></div>')
tabs = '''    <button class="tab on" data-t="guide">Start here<small>1-minute tour</small></button>
    <button class="tab" data-t="twin">Live 3D demo<small>move the sensors</small></button>
    <button class="tab" data-t="light">Sun and shade<small>through the day</small></button>
    <button class="tab" data-t="gmap">Shade map<small>red / yellow / green</small></button>
    <button class="tab" data-t="mech">How it tilts<small>motor and wire</small></button>
    <button class="tab" data-t="tilt">Best angle<small>electricity or crop?</small></button>
    <button class="tab" data-t="water">Rain and water<small>tank, irrigation</small></button>
    <button class="tab" data-t="crops">Crops and soil<small>what grows where</small></button>
    <button class="tab" data-t="eco">Money<small>farmer and investor</small></button>
    <button class="tab" data-t="acc">How accurate<small>score vs the best</small></button>
    <button class="tab" data-t="struct">Strength<small>wind, stress</small></button>
    <button class="tab" data-t="dex">Design explorer<small>computer search</small></button>
    <button class="tab" data-t="edge">ESP32 and attack<small>cheap board, hacked sensor</small></button>
    <button class="tab" data-t="method">Limits<small>read this</small></button>
'''
i = s.index('    <button class="tab on" data-t="twin">'); j = s.index('  </div>', s.index('data-t="method"', i))
s = s[:i] + tabs + s[j:]
rep('  <section class="pane" id="pane-twin">', open(os.path.join(here, 'ux_pane.html'), encoding='utf8').read() + '  <section class="pane" id="pane-twin" style="display:none">\n    <div id="ux-watch" class="watch">Press a scenario on the <b>Start here</b> tab, or move a slider in the sensor panel on the right: the panels, shadows and numbers change at once.</div>')
rep("day: 105, hour: 9.5, tab: 'twin',", "day: 105, hour: 9.5, tab: 'guide',")
k = s.index('/* ---------------- Tab: mechanism'); s = s[:k] + open(os.path.join(here, 'ux_block.js'), encoding='utf8').read() + '\n' + s[k:]
rep("if (st.tab === 'twin') { scene3d.resize(); hud(); }", "document.body.classList.toggle('tab-guide', st.tab === 'guide' || st.tab === 'twin'); if (st.tab === 'guide') uxLive(); else if (st.tab === 'twin') { scene3d.resize(); hud(); }")
rep("$('#live-connect').onclick = liveConnect;", "$('#live-connect').onclick = liveConnect; uxInit();")
rep('<h4>SIX-SENSOR CONTROLLER: pyranometer, PAR, DHT11, soil moisture, rain sensor and anemometer decide the panel angle</h4>', '<h4>SENSOR PANEL: change the six sensors like a real day would, and watch the panels react</h4><div class="hint" style="margin:-4px 0 8px">Sunlight (pyranometer) and light under the panels (PAR) follow the cloud slider; the rain sensor is the "Rain mode" button under the 3D view.</div>')
rep('SENS.last = { lsr, target: d.target,', 'SENS.last = { lsr, angle: d.angle, mode: d.mode, target: d.target,')
open(tw, 'w', encoding='utf8').write(s); print('ux patched', len(s) // 1024, 'KB')
