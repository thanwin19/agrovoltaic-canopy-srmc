"""Builds make_dxf_final.py from make_dxf.py (the original generator) with the final design: 6 mm drive wire, 45 deg offset lever arm, anemometer mast and storm-stow panel,
M24 turnbuckles, anchors, 10 kN winch, six sensors.  Then run:  python make_dxf_final.py   (writes ../results/cad_drawings/SRMC_feasible_*.dxf, .png and the BOM)"""
import os
here = os.path.dirname(os.path.abspath(__file__)); s = open(os.path.join(here, 'make_dxf.py'), encoding='utf-8').read()
def rep(old, new, cnt=1):
    global s
    assert old in s, 'MISSING: ' + old[:80]
    s = s.replace(old, new, cnt)
# ---- inputs from the design file instead of out/blender_inputs.json
rep("ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))\nCFG = json.load(open(os.path.join(ROOT, 'out', 'blender_inputs.json'))); D = CFG['design']\nOUT = os.path.join(ROOT, 'out', 'cad'); os.makedirs(OUT, exist_ok=True)",
    "ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))\n_dz = json.load(open(os.path.join(ROOT, '_project_core', 'design', 'design.json'), encoding='utf-8')); _p = _dz['presets'][_dz['active']]\n_pw = _p['panelPitch'] - _p['panelGap']\nD = dict(name=_dz['active'], field=_p['field'], nPanels=int(round(_p['field']['width'] / _p['panelPitch'])), panelPitch=_p['panelPitch'], panelW=_pw, pivotHeight=_p['clearanceLowestEdge'] + _pw / 2 * math.sin(math.radians(_p['maxTiltDeg'])), bayLen=_p['bayLen'], columnSize=_p['columnSize'], maxTiltDeg=_p['maxTiltDeg'], rainSlopeDeg=_p['rainSlopeDeg'], clearanceLowestEdge=_p['clearanceLowestEdge'], gutter=_p['gutter'], cistern=_p['cistern'], sagRatio=_p['sagRatio'], tube=_p['tube'], wires=_p['wires'])\nCFG = {'design': D, 'tilt': 27}\nOUT = os.path.join(ROOT, 'Review1_Design_and_CAD', 'results', 'cad_drawings'); os.makedirs(OUT, exist_ok=True)")
TITLE = 'AGROVOLTAIC CANOPY FOR PROTECTION AND SUSTAINABLE FARMING'
rep("'SRMC AGRIVOLTAIC CANOPY - PLAN'", "'%s - PLAN'" % TITLE); rep("'SRMC AGRIVOLTAIC CANOPY - ELEVATION (looking north)'", "'%s - ELEVATION (looking north)'" % TITLE)
# ---- plan: anemometer mast and sensor box
rep("gap = PITCH / 4\nfor k in range(N):", "d.circle(mm(HALF + 2.2), mm(-LZ / 2 + 2.5), 150, 'DRIVE'); d.circle(mm(HALF + 2.2), mm(-LZ / 2 + 2.5), 40, 'DRIVE'); d.text(mm(HALF + 2.5), mm(-LZ / 2 + 2.3), 130, 'ANEMOMETER MAST (storm stow at 15 m/s)', 'TEXT')\ngap = PITCH / 4\nfor k in range(N):")
# ---- elevation: storm stow panel and anemometer mast
rep("panel(-HALF + 3 * PITCH / 2, 45, 'HIDDEN');", "panel(-HALF + 3 * PITCH / 2, 90, 'HIDDEN'); d.text(mm(-HALF + 3 * PITCH / 2) - 300, mm(H + PW / 2) + 150, 140, 'STORM STOW 90 deg (anemometer >= 15 m/s)', 'TEXT');")
rep("cxx = HALF + 4.5; d.rect(", "mx_ = HALF + 2.2; d.line(mm(mx_), 0, mm(mx_), mm(H + 3.2), 'DRIVE'); d.circle(mm(mx_), mm(H + 3.35), 150, 'DRIVE'); d.line(mm(mx_ - .35), mm(H + 3.35), mm(mx_ + .35), mm(H + 3.35), 'DRIVE'); d.text(mm(mx_) + 250, mm(H + 3.2), 130, 'CUP ANEMOMETER ON 3 m MAST (WIND SENSOR)', 'TEXT')\ncxx = HALF + 4.5; d.rect(")
rep("wire ropes SS316 (carrier %d mm, drive %d mm)'", "wire ropes SS316 (carrier %d mm, drive %d mm); six sensors: pyranometer, PAR, DHT11, soil, rain, wind'")
# ---- section: offset lever arm
rep("ax, az = rot(0, -440); d.line(tx, tz, ax, az, 'DRIVE'); d.circle(ax, az, 22, 'DRIVE'); d.text(ax + 80, az - 40, 100, 'DRIVE WIRE %d mm SS316 (via lever-arm tip)' % D['wires']['driveDiaMm'], 'TEXT')",
    "ax, az = rot(440 * math.sin(math.radians(45)), -440 * math.cos(math.radians(45))); d.line(tx, tz, ax, az, 'DRIVE'); d.circle(ax, az, 22, 'DRIVE'); d.text(ax + 80, az - 40, 100, 'DRIVE WIRE %d mm SS316 (via lever-arm tip)' % D['wires']['driveDiaMm'], 'TEXT'); d.text(ax + 80, az - 190, 90, 'LEVER ARM 440 mm, FIXED 45 deg OFFSET (lever >= 311 mm up to the 90 deg stow)', 'TEXT')")
# ---- wire drive: offset arm positions (working 27 deg, rest 0 deg, stow 90 deg)
rep("tipx = xc + LA * math.sin(math.radians(TILT)); d.line(mm(xc), 0, mm(xc), mm(-LA), 'STRUCT'); pts.append((mm(tipx), mm(-LA * math.cos(math.radians(TILT)))))",
    "tipx = xc + LA * math.sin(math.radians(TILT - 45)); d.line(mm(xc), 0, mm(tipx), mm(-LA * math.cos(math.radians(TILT - 45))), 'STRUCT'); pts.append((mm(tipx), mm(-LA * math.cos(math.radians(TILT - 45)))))\n    if k == N - 1:\n        for ang_, nm_ in ((0, 'REST'), (90, 'STOW')): d.circle(mm(xc + LA * math.sin(math.radians(ang_ - 45))), mm(-LA * math.cos(math.radians(ang_ - 45))), 40, 'HIDDEN'); d.text(mm(xc + LA * math.sin(math.radians(ang_ - 45))) - 100, mm(-LA * math.cos(math.radians(ang_ - 45))) - 220, 100, nm_ + ' ' + str(ang_) + ' deg', 'TEXT')")
rep("'SS316 %d mm 7x7, min breaking load >= 13 kN, working load <= 2.6 kN; encoder 0.5 deg; fail-safe brake' % D['wires']['driveDiaMm']", "'SS316 %d mm 7x19, min breaking load >= 20 kN, working load <= 4.1 kN (54 km/h wind, 60 deg); 10 kN winch; offset arm 45 deg; encoder 0.5 deg; fail-safe brake' % D['wires']['driveDiaMm']")
# ---- BOM
rep("('Ground anchor block', 2 * len(colY) + 2 * len(colX), 'nos', 'concrete 1.0 x 0.8 x 0.35 m'),", "('Ground anchor (screw/rock anchor or about 1.6 m3 buried concrete; soil test)', 2 * len(colY) + 2 * len(colX), 'nos', 'pull-out >= 38 kN each'),")
rep("('Turnbuckle M16 SS316', 2 * len(colY) + 2 * len(colX), 'nos', 'stay pre-tension'),", "('Turnbuckle M24 SS316 (>= 72 kN breaking)', 2 * len(colY) + 2 * len(colX), 'nos', 'stay pre-tension'),")
rep("('Lever arm SS316 150-250 mm', N, 'nos', 'one per panel'),", "('Lever arm SS316, 0.44 m, fixed 45 deg offset', N, 'nos', 'one per panel; keeps a lever at the 90 deg stow'),")
rep("('Drive wire SS316 %d mm 7x7' % D['wires']['driveDiaMm'], round(drive, 1), 'm', 'motor -> tips -> tensioner'),", "('Drive wire SS316 %d mm 7x19' % D['wires']['driveDiaMm'], round(drive, 1), 'm', 'motor -> tips -> tensioner'),")
rep("('Gearmotor winch, IP66, >= 3 kN, encoder 0.5 deg', 1, 'nos', 'single motor for run <= 30 m'),", "('Gearmotor winch, IP66, >= 10 kN (about 0.25 kW worm gear), encoder 0.5 deg', 1, 'nos', 'single motor for run <= 30 m'),")
rep("('Sensors: pyranometer x1 reference + 4 zone, rain gauge, T/RH, soil moisture x4, panel IR', 1, 'set', 'ESP32 controller'),", "('Sensors: pyranometer, PAR (under canopy), DHT11 T/RH, soil moisture, rain sensor', 1, 'set', 'ESP32 controller'),\n    ('Cup anemometer on a 3 m mast (wind sensor)', 1, 'nos', 'storm stow at 15 m/s, resume below 12 m/s'),")
open(os.path.join(here, 'make_dxf_final.py'), 'w', encoding='utf-8').write(s); print('make_dxf_final.py written')
