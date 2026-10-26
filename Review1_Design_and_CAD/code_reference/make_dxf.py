"""AutoCAD drawings (DXF R12, units = millimetres) + bill of materials, generated from design.json (via out/blender_inputs.json).
usage: node tools/export_blender.js <preset> ...   then   python tools/make_dxf.py
Writes: out/cad/SRMC_<preset>_{plan,elevation,section,wire_drive}.dxf, SRMC_<preset>_BOM.csv, and PNG previews."""
import json, math, os, sys, csv
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
CFG = json.load(open(os.path.join(ROOT, 'out', 'blender_inputs.json'))); D = CFG['design']
OUT = os.path.join(ROOT, 'out', 'cad'); os.makedirs(OUT, exist_ok=True)
mm = lambda v: v * 1000.0
LZ = D['field']['length']; N = D['nPanels']; PITCH = D['panelPitch']; PW = D['panelW']; H = D['pivotHeight']; BAY = D['bayLen']; CS = D['columnSize']; HALF = N * PITCH / 2
MAXT = D['maxTiltDeg']; SLOPE = D['rainSlopeDeg']; CLR = D['clearanceLowestEdge']; TILT = CFG['tilt']

class DXF:
    COL = {'STRUCT': 7, 'PANELS': 5, 'WIRES': 3, 'DRIVE': 1, 'WATER': 4, 'DIM': 2, 'TEXT': 7, 'SITE': 8, 'CROP': 94, 'HIDDEN': 8}
    def __init__(s): s.e = []
    def line(s, x1, y1, x2, y2, layer='STRUCT'): s.e.append(f"0\nLINE\n8\n{layer}\n10\n{x1:.2f}\n20\n{y1:.2f}\n30\n0\n11\n{x2:.2f}\n21\n{y2:.2f}\n31\n0\n")
    def circle(s, x, y, r, layer='STRUCT'): s.e.append(f"0\nCIRCLE\n8\n{layer}\n10\n{x:.2f}\n20\n{y:.2f}\n30\n0\n40\n{r:.2f}\n")
    def text(s, x, y, h, t, layer='TEXT', rot=0): s.e.append(f"0\nTEXT\n8\n{layer}\n10\n{x:.2f}\n20\n{y:.2f}\n30\n0\n40\n{h:.2f}\n1\n{t}\n50\n{rot}\n")
    def poly(s, pts, layer='STRUCT', closed=False):
        for a, b in zip(pts, pts[1:]): s.line(a[0], a[1], b[0], b[1], layer)
        if closed: s.line(pts[-1][0], pts[-1][1], pts[0][0], pts[0][1], layer)
    def rect(s, x0, y0, x1, y1, layer='STRUCT'): s.poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], layer, True)
    def dim_h(s, x1, x2, y, label, off=600, th=180):                       # manual horizontal dimension
        yy = y - off; s.line(x1, y, x1, yy - 100, 'DIM'); s.line(x2, y, x2, yy - 100, 'DIM'); s.line(x1, yy, x2, yy, 'DIM')
        for xx, d in ((x1, 1), (x2, -1)): s.line(xx, yy, xx + d * 150, yy + 60, 'DIM'); s.line(xx, yy, xx + d * 150, yy - 60, 'DIM')
        s.text((x1 + x2) / 2 - len(label) * th * .28, yy + 60, th, label, 'DIM')
    def dim_v(s, y1, y2, x, label, off=600, th=180):
        xx = x - off; s.line(x, y1, xx - 100, y1, 'DIM'); s.line(x, y2, xx - 100, y2, 'DIM'); s.line(xx, y1, xx, y2, 'DIM')
        for yy, d in ((y1, 1), (y2, -1)): s.line(xx, yy, xx + 60, yy + d * 150, 'DIM'); s.line(xx, yy, xx - 60, yy + d * 150, 'DIM')
        s.text(xx - 80, (y1 + y2) / 2 - len(label) * th * .28, th, label, 'DIM', 90)
    def write(s, path):
        layers = list(s.COL)
        h = "0\nSECTION\n2\nHEADER\n9\n$ACADVER\n1\nAC1009\n9\n$INSUNITS\n70\n4\n0\nENDSEC\n"
        t = "0\nSECTION\n2\nTABLES\n0\nTABLE\n2\nLTYPE\n70\n1\n0\nLTYPE\n2\nCONTINUOUS\n70\n0\n3\nSolid line\n72\n65\n73\n0\n40\n0.0\n0\nENDTAB\n"
        t += f"0\nTABLE\n2\nLAYER\n70\n{len(layers)}\n" + ''.join(f"0\nLAYER\n2\n{l}\n70\n0\n62\n{s.COL[l]}\n6\nCONTINUOUS\n" for l in layers) + "0\nENDTAB\n0\nENDSEC\n"
        open(path, 'w', encoding='ascii', errors='replace').write(h + t + "0\nSECTION\n2\nENTITIES\n" + ''.join(s.e) + "0\nENDSEC\n0\nEOF\n")
    def preview(s, path, title):
        import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(13, 8)); col = {7: 'k', 5: '#1b3a82', 3: '#555', 1: '#c0392b', 4: '#1c8fd0', 2: '#b8860b', 8: '#999', 94: '#3a7d1e'}
        for e in s.e:
            f = e.split('\n'); L = f[3]
            if f[1] == 'LINE': ax.plot([float(f[5]), float(f[11])], [float(f[7]), float(f[13])], color=col[s.COL[L]], lw=.8)
            elif f[1] == 'CIRCLE': ax.add_patch(plt.Circle((float(f[5]), float(f[7])), float(f[11]), fill=False, color=col[s.COL[L]], lw=.8))
            elif f[1] == 'TEXT': ax.text(float(f[5]), float(f[7]), f[13], fontsize=max(4, float(f[11]) / 70), rotation=float(f[15]), color=col[s.COL[L]])
        ax.set_aspect('equal'); ax.set_title(title); ax.axis('off'); fig.savefig(path, dpi=130, bbox_inches='tight'); plt.close(fig)

colX = [-HALF + i * BAY for i in range(int(round(2 * HALF / BAY)) + 1)]; NLINE = max(2, int(round(LZ / BAY))); colY = [-LZ / 2 + i * LZ / NLINE for i in range(NLINE + 1)]; SAG = D.get('sagRatio', 0.0256); TUBE = D.get('tube', {'D': 60.3, 't': 3})
def title(d, x, y, name, sub): d.text(x, y, 400, name, 'TEXT'); d.text(x, y - 520, 200, sub, 'TEXT')

# ---------------- PLAN ----------------
d = DXF(); gw = D['gutter']['width']; cs_side = D['cistern']['side']; cx = HALF + 4.5; zW = LZ / 2 - .525
d.rect(mm(-HALF), mm(-LZ / 2), mm(HALF), mm(LZ / 2), 'SITE')
for k in range(N):
    xc = -HALF + k * PITCH + PITCH / 2; d.rect(mm(xc - PW / 2), mm(-LZ / 2), mm(xc + PW / 2), mm(LZ / 2), 'PANELS'); d.line(mm(xc), mm(-LZ / 2), mm(xc), mm(LZ / 2), 'PANELS')
    if k % 2 == 0: d.text(mm(xc) - 250, mm(LZ / 2) + 250, 160, 'P%02d' % (k + 1), 'TEXT')
for x in colX:
    for y in colY: d.rect(mm(x - CS / 2), mm(y - CS / 2), mm(x + CS / 2), mm(y + CS / 2), 'STRUCT'); d.rect(mm(x - .45), mm(y - .45), mm(x + .45), mm(y + .45), 'HIDDEN')
for y in colY: d.line(mm(-HALF), mm(y), mm(HALF), mm(y), 'WIRES')
for x in colX: d.line(mm(x), mm(-LZ / 2), mm(x), mm(LZ / 2), 'WIRES')
for sx in (-1, 1):
    for y in colY: d.line(mm(sx * HALF), mm(y), mm(sx * (HALF + 6.5)), mm(y), 'WIRES'); d.rect(mm(sx * (HALF + 6.5) - .5), mm(y - .4), mm(sx * (HALF + 6.5) + .5), mm(y + .4), 'HIDDEN')
d.line(mm(-HALF), mm(zW), mm(HALF + .3), mm(zW), 'DRIVE'); d.rect(mm(HALF + .45), mm(zW - .25), mm(HALF + 1.2), mm(zW + .25), 'DRIVE'); d.text(mm(HALF + 1.3), mm(zW), 150, 'DRIVE MOTOR + WINCH', 'TEXT')
d.rect(mm(HALF), mm(-LZ / 2), mm(HALF + gw), mm(zW - 1.2), 'WATER'); d.circle(mm(HALF + .2), 0, 60, 'WATER'); d.line(mm(HALF + .2), 0, mm(cx - cs_side / 2), 0, 'WATER')
d.rect(mm(cx - cs_side / 2), mm(-cs_side / 2), mm(cx + cs_side / 2), mm(cs_side / 2), 'WATER'); d.text(mm(cx) - 900, 0, 220, 'CISTERN %d m3' % D['cistern']['m3'], 'WATER')
d.rect(mm(cx - .5), mm(-cs_side / 2 - 1.8), mm(cx + .5), mm(-cs_side / 2 - .8), 'WATER'); d.text(mm(cx) - 300, mm(-cs_side / 2 - 2.4), 160, 'PUMP', 'WATER')
d.line(mm(-HALF), mm(-LZ / 2 - .6), mm(cx), mm(-LZ / 2 - .6), 'WATER'); d.line(mm(cx), mm(-cs_side / 2 - .8), mm(cx), mm(-LZ / 2 - .6), 'WATER')
gap = PITCH / 4
for k in range(N):
    for z in range(4): lx = -HALF + k * PITCH + z * gap + gap / 2; d.line(mm(lx), mm(-LZ / 2), mm(lx), mm(LZ / 2 - .2), 'CROP')
d.dim_h(mm(-HALF), mm(HALF), mm(-LZ / 2), 'OVERALL WIDTH %d mm' % round(mm(2 * HALF)), 1700)
for i in range(len(colX) - 1): d.dim_h(mm(colX[i]), mm(colX[i + 1]), mm(-LZ / 2), 'BAY %d' % round(mm(BAY)), 700)
d.dim_h(mm(-HALF), mm(-HALF + PITCH), mm(LZ / 2), 'PANEL PITCH %d' % round(mm(PITCH)), -900)
d.dim_v(mm(-LZ / 2), mm(LZ / 2), mm(-HALF), 'WIRE RUN LENGTH %d mm' % round(mm(LZ)), 1500)
d.line(mm(-HALF - 3), mm(LZ / 2 + 2), mm(-HALF - 3), mm(LZ / 2 + 4.5), 'TEXT'); d.line(mm(-HALF - 3), mm(LZ / 2 + 4.5), mm(-HALF - 3.3), mm(LZ / 2 + 3.7), 'TEXT'); d.line(mm(-HALF - 3), mm(LZ / 2 + 4.5), mm(-HALF - 2.7), mm(LZ / 2 + 3.7), 'TEXT'); d.text(mm(-HALF - 3) - 80, mm(LZ / 2 + 4.8), 250, 'N', 'TEXT')
title(d, mm(-HALF), mm(LZ / 2 + 7), 'SRMC AGRIVOLTAIC CANOPY - PLAN', 'Preset: %s | %d panels x %.3f m | pivot height %.2f m | all dimensions in mm' % (D['name'], N, PW, H))
d.write(os.path.join(OUT, 'SRMC_%s_plan.dxf' % D['name'])); d.preview(os.path.join(OUT, 'SRMC_%s_plan.png' % D['name']), 'PLAN')

# ---------------- ELEVATION ----------------
d = DXF(); sag = lambda span: SAG * span; topY = H - .1
d.line(mm(-HALF - 9), 0, mm(HALF + 14), 0, 'SITE')
for x in colX:
    d.rect(mm(x - CS / 2), mm(-.4), mm(x + CS / 2), mm(H + .75), 'STRUCT'); d.rect(mm(x - .45), mm(-.5), mm(x + .45), mm(-.2), 'HIDDEN')
for i in range(len(colX) - 1):
    a, b = colX[i], colX[i + 1]; pts = [(mm(a + (b - a) * u / 20), mm(topY - 4 * sag(b - a) * (u / 20) * (1 - u / 20))) for u in range(21)]; d.poly(pts, 'WIRES')
for sx in (-1, 1): d.line(mm(sx * HALF), mm(H + .7), mm(sx * (HALF + 6.5)), mm(-.35), 'WIRES'); d.rect(mm(sx * (HALF + 6.5) - .5), mm(-.45), mm(sx * (HALF + 6.5) + .5), mm(-.1), 'HIDDEN')
def panel(xc, ang, layer):
    t = math.radians(ang); dx = PW / 2 * math.cos(t); dz = PW / 2 * math.sin(t); d.line(mm(xc - dx), mm(H + dz), mm(xc + dx), mm(H - dz), layer)
for k in range(N):
    xc = -HALF + k * PITCH + PITCH / 2; panel(xc, SLOPE, 'PANELS'); d.circle(mm(xc), mm(H), 60, 'STRUCT')
    u = ((xc + HALF) % BAY) / BAY; d.line(mm(xc), mm(topY - 4 * sag(BAY) * u * (1 - u)), mm(xc), mm(H - .05), 'WIRES')
panel(-HALF + PITCH / 2, MAXT, 'HIDDEN'); panel(-HALF + 3 * PITCH / 2, 45, 'HIDDEN'); d.text(mm(-HALF + PITCH / 2) - 300, mm(H + PW / 2 * math.sin(math.radians(MAXT))) + 150, 140, 'MAX TILT %d deg' % MAXT, 'TEXT')
d.rect(mm(-HALF + BAY / 2 - 1.5), 0, mm(-HALF + BAY / 2 + 1.5), mm(4.1), 'HIDDEN'); d.text(mm(-HALF + BAY / 2) - 600, mm(2.0), 150, 'COMBINE HARVESTER 3.0 x 4.1 m', 'TEXT')
cxx = HALF + 4.5; d.rect(mm(cxx - cs_side / 2), mm(-D['cistern']['depth']), mm(cxx + cs_side / 2), 0, 'WATER'); d.text(mm(cxx) - 900, mm(-1.5), 200, 'UNDERGROUND CISTERN', 'WATER')
d.rect(mm(HALF), mm(H - .5), mm(HALF + gw), mm(H - .2), 'WATER'); d.line(mm(HALF + .2), mm(H - .5), mm(HALF + .2), mm(-.6), 'WATER'); d.line(mm(HALF + .2), mm(-.6), mm(cxx - cs_side / 2), mm(-.6), 'WATER')
d.dim_v(0, mm(H), mm(-HALF - 1), 'PIVOT HEIGHT %d' % round(mm(H)), 800); lowest = H - PW / 2 * math.sin(math.radians(MAXT))
d.dim_v(0, mm(lowest), mm(-HALF + 2.2), 'LOWEST EDGE %d' % round(mm(lowest)), 700); d.dim_h(mm(colX[0]), mm(colX[-1]), 0, 'COLUMN SPAN %d  (bays of %d)' % (round(mm(colX[-1] - colX[0])), round(mm(BAY))), 1500)
d.dim_h(mm(-HALF), mm(-HALF + PITCH), mm(H + 2), 'PITCH %d' % round(mm(PITCH)), -500)
title(d, mm(-HALF), mm(H + 4), 'SRMC AGRIVOLTAIC CANOPY - ELEVATION (looking north)', 'Required lowest-edge clearance %.2f m at max tilt %d deg; rain mode %d deg fall to gutter; wire ropes SS316 (carrier %d mm, drive %d mm)' % (CLR, MAXT, SLOPE, D['wires']['carrierDiaMm'], D['wires']['driveDiaMm']))
d.write(os.path.join(OUT, 'SRMC_%s_elevation.dxf' % D['name'])); d.preview(os.path.join(OUT, 'SRMC_%s_elevation.png' % D['name']), 'ELEVATION')

# ---------------- SECTION DETAIL (one panel, full scale) ----------------
d = DXF(); t = math.radians(TILT if TILT else 27); c, s_ = math.cos(t), math.sin(t); hw = mm(PW) / 2
def rot(x, z): return (x * c + z * s_, -x * s_ + z * c)
def prect(x0, z0, x1, z1, layer):
    pts = [rot(x0, z0), rot(x1, z0), rot(x1, z1), rot(x0, z1)]; d.poly(pts, layer, True)
prect(-hw, 60, hw, 110, 'PANELS'); prect(-hw - 20, 50, -hw + 20, 140, 'STRUCT'); prect(hw - 20, 50, hw + 20, 140, 'STRUCT')
tx, tz = rot(0, 0); d.circle(tx, tz, TUBE['D'] / 2, 'STRUCT'); d.circle(tx, tz, TUBE['D'] / 2 - TUBE['t'], 'STRUCT')
for sgn in (-1, 1): ex, ez = rot(sgn * (hw + 12), 90); d.circle(ex, ez, 16, 'STRUCT')
ax, az = rot(0, -440); d.line(tx, tz, ax, az, 'DRIVE'); d.circle(ax, az, 22, 'DRIVE'); d.text(ax + 80, az - 40, 100, 'DRIVE WIRE %d mm SS316 (via lever-arm tip)' % D['wires']['driveDiaMm'], 'TEXT')
d.line(0, -60, 0, -420, 'WIRES'); d.circle(0, -480, 40, 'WIRES'); d.text(100, -520, 100, 'CARRIER WIRE ROPE %d mm' % D['wires']['carrierDiaMm'], 'TEXT'); d.text(100, -380, 100, 'HANGER', 'TEXT')
d.text(tx + 90, tz + 120, 100, 'PIVOT TUBE %.1f OD x %.1f' % (TUBE['D'], TUBE['t']), 'TEXT'); d.text(-hw, 250, 100, 'PV PANEL %.3f m wide, 30-40 mm frame' % PW, 'TEXT'); d.text(hw - 300, 250 - 130, 100, 'EPDM BULB SEAL 10 mm', 'TEXT')
d.line(-hw * 1.2, 0, hw * 1.2, 0, 'HIDDEN'); d.text(-hw * 1.2, -80, 90, 'PIVOT AXIS HEIGHT ABOVE GROUND = %d mm' % round(mm(H)), 'TEXT')
title(d, -hw, 700, 'SECTION A-A - PANEL, PIVOT AND DRIVE WIRE (full scale)', 'Panel shown at %.1f deg (tilt mode); east edge down; seals meet at flat mode' % (TILT if TILT else 27))
d.write(os.path.join(OUT, 'SRMC_%s_section.dxf' % D['name'])); d.preview(os.path.join(OUT, 'SRMC_%s_section.png' % D['name']), 'SECTION')

# ---------------- WIRE DRIVE (plan along the wire) ----------------
d = DXF(); LA = .44
d.text(mm(-HALF), mm(2.2), 220, 'Wire path: motor drum -> lever-arm tips (series) -> turnbuckle tensioner', 'TEXT')
d.rect(mm(HALF + .1), mm(-.5), mm(HALF + 1.2), mm(.5), 'DRIVE'); d.circle(mm(HALF + .4), 0, mm(.14), 'DRIVE'); d.text(mm(HALF) + 100, mm(.7), 140, 'MOTOR', 'TEXT')
d.rect(mm(-HALF - .8), mm(-.2), mm(-HALF - .1), mm(.2), 'DRIVE'); d.text(mm(-HALF - 1.0), mm(.55), 140, 'TENSIONER', 'TEXT')
pts = [(mm(HALF), 0)]
for k in range(N - 1, -1, -1):
    xc = -HALF + k * PITCH + PITCH / 2; tipx = xc + LA * math.sin(math.radians(TILT)); d.line(mm(xc), 0, mm(xc), mm(-LA), 'STRUCT'); pts.append((mm(tipx), mm(-LA * math.cos(math.radians(TILT)))))
    d.circle(mm(xc), 0, 60, 'STRUCT'); d.text(mm(xc) - 150, mm(.35), 120, 'P%02d' % (k + 1), 'TEXT')
pts.append((mm(-HALF), 0)); d.poly(pts, 'DRIVE'); d.circle(mm(HALF), 0, 80, 'STRUCT'); d.circle(mm(-HALF), 0, 80, 'STRUCT')
d.dim_h(mm(-HALF), mm(HALF), mm(-.6), 'WIRE RUN %d mm  (%d panels, single motor <= 30 m / 20 panels)' % (round(mm(2 * HALF)), N), 500)
title(d, mm(-HALF), mm(3.5), 'WIRE-DRIVE LAYOUT', 'SS316 %d mm 7x7, min breaking load >= 13 kN, working load <= 2.6 kN; encoder 0.5 deg; fail-safe brake' % D['wires']['driveDiaMm'])
d.write(os.path.join(OUT, 'SRMC_%s_wire_drive.dxf' % D['name'])); d.preview(os.path.join(OUT, 'SRMC_%s_wire_drive.png' % D['name']), 'WIRE DRIVE')

# ---------------- BILL OF MATERIALS ----------------
ncol = len(colX) * len(colY); span_len = lambda sp: sp * (1 + 8 * (sag(sp) / sp) ** 2 / 3)
carrier = sum(span_len(colX[i + 1] - colX[i]) for i in range(len(colX) - 1)) * len(colY); longw = sum(2 * 0 + (colY[j + 1] - colY[j]) * (1 + 8 * SAG ** 2 / 3) for j in range(len(colY) - 1)) * len(colX)
stay = 2 * len(colY) * math.hypot(6.5, H + 1.05) + 2 * len(colX) * math.hypot(6.5, H + 1.05); hang = N * len(colY) * .25
drive = 2 * HALF + N * .8
rows = [
    ('Column, GI RHS %d x %d mm, %.2f m long' % (round(CS * 1000), round(CS * 1000), H + 1.15), ncol, 'nos', 'S355 hot-dip galvanised; pile or pad foundation'),
    ('Foundation pad 0.9 x 0.9 m', ncol, 'nos', 'concrete M20'),
    ('Carrier wire rope SS316 %d mm 7x19' % D['wires']['carrierDiaMm'], round(carrier, 1), 'm', 'catenary, E-W spans'),
    ('Longitudinal wire rope SS316 %d mm' % D['wires']['carrierDiaMm'], round(longw, 1), 'm', 'N-S catenaries at column tops'),
    ('Stay wire rope SS316 %d mm 7x7' % D['wires']['braceDiaMm'], round(stay, 1), 'm', 'to ground anchors'),
    ('Ground anchor block', 2 * len(colY) + 2 * len(colX), 'nos', 'concrete 1.0 x 0.8 x 0.35 m'),
    ('Turnbuckle M16 SS316', 2 * len(colY) + 2 * len(colX), 'nos', 'stay pre-tension'),
    ('PV panel %.3f x %.1f m (pivoting)' % (PW, LZ), N, 'nos', 'framed, ~%.0f kWp total at STC 0.21 efficiency' % (N * PW * LZ * 0.21)),
    ('Pivot tube S355 galv CHS %.1f x %.1f mm, %.1f m' % (TUBE['D'], TUBE['t'], LZ), N, 'nos', 'one per panel'),
    ('Pivot bearing block, self-aligning, IP65', N * len(colY), 'nos', 'one per carrier line'),
    ('Hanger rod / wire, carrier to bearing', round(hang, 1), 'm', 'N x carrier lines'),
    ('Lever arm SS316 150-250 mm', N, 'nos', 'one per panel'),
    ('Drive wire SS316 %d mm 7x7' % D['wires']['driveDiaMm'], round(drive, 1), 'm', 'motor -> tips -> tensioner'),
    ('Guide pulley SS316 80 mm', 2, 'nos', 'column ends'),
    ('Gearmotor winch, IP66, >= 3 kN, encoder 0.5 deg', 1, 'nos', 'single motor for run <= 30 m'),
    ('EPDM bulb seal 10 mm', round(2 * N * LZ, 1), 'm', 'both long edges of every panel'),
    ('Rain gutter %.2f x %.2f m' % (gw, D['gutter']['depth']), round(LZ - 1.2, 1), 'm', 'east edge, 1:100 fall'),
    ('Downpipe 75 mm + underground pipe', round(H + 5, 1), 'm', 'HDPE / SS316'),
    ('First-flush diverter 20 L per 100 m2', max(1, round(N * PW * LZ / 100)), 'nos', ''),
    ('Underground cistern', D['cistern']['m3'], 'm3', 'RCC / HDPE, %.0f x %.0f m, %.1f m deep' % (cs_side, cs_side, D['cistern']['depth'])),
    ('Pump + header + drip laterals', 1, 'set', '%d laterals' % (N * 4)),
    ('Sensors: pyranometer x1 reference + 4 zone, rain gauge, T/RH, soil moisture x4, panel IR', 1, 'set', 'ESP32 controller'),
    ('Inverter + transformer + overhead line to industry', 1, 'set', 'sized to ~%.0f kWp' % (N * PW * LZ * 0.21))]
with open(os.path.join(OUT, 'SRMC_%s_BOM.csv' % D['name']), 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.writer(f); w.writerow(['Item', 'Qty', 'Unit', 'Note']); [w.writerow(r) for r in rows]
print('wrote', sorted(os.listdir(OUT)))
