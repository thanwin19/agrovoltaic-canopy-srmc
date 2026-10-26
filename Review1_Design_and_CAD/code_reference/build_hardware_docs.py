"""8-panel (4.4 kWp) hardware pack for the final design: component strength table, installation spec (HTML), easy guide + cost (DOCX).
Final design = after the strength check: 10 kN winch, 6 mm SS316 drive wire, M24 turnbuckles, anchors sized for 26 kN uplift each.
Run:  python build_hardware_docs.py      (writes into ../documents)"""
import os, math, html
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.section import WD_ORIENT
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, '..', 'documents'); os.makedirs(OUT, exist_ok=True)
G = 9.80665; TITLE = 'Agrovoltaic Canopy for Protection and Sustainable Farming'
# ---------------- inputs ----------------
NMOD, PWP, MOD_L, MOD_W, MOD_KG = 8, 550, 2.278, 1.134, 27.5
ROWS, PER_ROW, PITCH, BAY, CLEAR, TMAX = 2, 4, 2.5, 5.0, 4.5, 60
RHO_S, RHO_C, K = 7850, 2400, 0.00381          # steel, concrete kg/m3; rope kg/m = K d^2 (fitted to supplier 8-16 mm listings)
mbl = lambda d: .568 * d * d                    # kN breaking load (fitted to 16 mm supplier value 145.5 kN)
vz = 39 * .98; pz = .6 * vz ** 2 / 1000; wdn = 1.35 * .2 + 1.5 * pz; wup = 1.5 * pz * 1.3 - .9 * .2
H = CLEAR + MOD_L / 2 * math.sin(math.radians(TMAX)); COLH = H + 1.15; Lt = PER_ROW * MOD_W + (PER_ROW - 1) * .02 + .10
# structure checks (same formulas as matlab/structural_check.m)
D, t = 114.3, 4.0; Z = math.pi * (D ** 4 - (D - 2 * t) ** 4) / (32 * D); MRd = Z * 355 / 1e6
wT = wdn * MOD_L; Mt = wT * Lt ** 2 / 8; ut_tube = Mt / MRd
P = wT * Lt / 2; a = (BAY - PITCH) / 2; s = BAY / 12; Hh = (P * BAY / 2 - P * (BAY / 2 - a)) / s; Tw = math.hypot(Hh, P)
ut_rope = Tw / (mbl(16) / 2)
th = math.atan2(H + 1.05, 6.5); Ts = Hh / math.cos(th); Vs = Ts * math.sin(th); ut_stay = Ts / (mbl(20) / 2); stay_len = math.hypot(H + 1.05, 6.5)
anch_kN = 1.5 * Vs; anch_m3 = anch_kN / (RHO_C * G / 1000); uplift = wup * NMOD * MOD_L * MOD_W
# drive: wire force at 60 deg tilt (worst), two rows; the lever arm is offset 45 deg, so the moment arm is 0.44 cos(tilt - 45 deg) and stays >= 0.31 m up to the 90 deg stow
arm = .44 * math.cos(math.radians(60 - 45)); A = MOD_L * PER_ROW * MOD_W; e = .25 * MOD_L; row_kg = PER_ROW * MOD_KG + 12 + 53.7; grav = row_kg * G * .05
Fw = lambda V: 2 * (.6 * V * V * A * e + grav) / arm / 1000
F0, F10, F15 = Fw(0), Fw(10), Fw(15)
F4 = F15 / (mbl(4) / 2)
V_ok3 = math.sqrt(max(0, (3000 * arm / 2 - grav) / (.6 * A * e)))            # wind (m/s) at which a 3 kN winch is at its limit
# ---------------- bill of materials ----------------
def sec(item, qty, unit, kgu, note, src): return [item, qty, unit, round(kgu, 3), round(qty * kgu, 1), note, src]
tube_kg = math.pi / 4 * (D ** 2 - (D - 2 * t) ** 2) * 1e-6 * RHO_S * Lt * 1.05
col_kg = 4656e-6 * RHO_S * COLH * 1.05 + 12
Lc = 2 * (BAY * (1 + 8 / 3 * (1 / 12) ** 2) + 1.2); stay_m = 4 * (stay_len + .8)
bom = [sec('Monocrystalline module 550 Wp, 2278 x 1134 x 35 mm', NMOD, 'nos', MOD_KG, '2 rows x 4, landscape across the tube', 'cited listings 26.9 to 27.5 kg'),
       sec('Module rails, clamps, fasteners', NMOD, 'set', 3.0, 'assumed', 'assumption'),
       sec('Pivot tube S355 CHS 114.3 x 4.0, galvanised', ROWS, 'nos (%.2f m)' % Lt, tube_kg, '10.9 kg/m + 5 % zinc', 'calculated'),
       sec('Bearing block, self-aligning, IP65, 50 mm', 4, 'nos', 2.5, 'tube rotates in these, hung from the carrier ropes', 'catalogue typical'),
       sec('Column RHS 200 x 200 x 6, %.2f m' % COLH, 4, 'nos', col_kg, '36.5 kg/m + zinc + base plate', 'calculated'),
       sec('Carrier rope SS316 16 mm 7x19', round(Lc, 1), 'm', K * 256, '2 lines, 5 m span, sag L/12', 'supplier 0.975 kg/m'),
       sec('Longitudinal rope SS316 16 mm 7x19', round(Lc, 1), 'm', K * 256, 'ties column tops N-S', 'supplier 0.975 kg/m'),
       sec('Stay rope SS316 20 mm', round(stay_m, 1), 'm', K * 400, 'one per column, %.2f m slope' % stay_len, 'derived 0.00381 d^2'),
       sec('Turnbuckle M24 SS316 (>= 72 kN breaking)', 4, 'nos', 1.8, 'stay pre-tension (M16 would be too weak)', 'assumption'),
       sec('Drive wire SS316 6 mm 7x19', 12, 'm', K * 36, 'loop through both lever-arm tips', 'derived 0.00381 d^2'),
       sec('Lever arm SS316, 0.44 m, fixed 45 deg offset from the panel normal', ROWS, 'nos', 1.5, 'one per tube; the offset keeps a lever at the 90 deg stow', 'assumption'),
       sec('Guide pulley SS316 80 mm', 2, 'nos', .8, 'column ends', 'assumption'),
       sec('Thimbles, swaged terminals, clamps', 1, 'set', 4.0, '', 'assumption'),
       sec('Gearmotor winch 10 kN, IP66, worm gear about 0.25 kW, encoder 0.5 deg', 1, 'nos', 25.0, 'one motor tilts both rows', 'catalogue typical'),
       sec('Controller + 5 sensors (pyranometer, PAR, DHT11, soil, rain) + cable', 1, 'set', 4.0, 'ESP32', 'assumption'),
       sec('Cup anemometer on a 3 m mast (wind sensor)', 1, 'nos', 2.0, 'storm stow at 15 m/s (54 km/h), resume below 12 m/s', 'assumption (catalogue)'),
       sec('Inverter 5 kW + protection', 1, 'set', 18.0, '', 'assumption')]
conc = [sec('Column pad 0.9 x 0.9 x 0.6 m M20', 4, 'nos', .9 * .9 * .6 * RHO_C, 'depth assumed, soil test needed', 'assumption'),
        sec('Ground anchor, buried concrete %.2f m3 each (or a screw/rock anchor rated %.0f kN)' % (anch_m3, anch_kN), 4, 'nos', anch_m3 * RHO_C, 'sized for %.0f kN stay uplift x 1.5' % Vs, 'calculated')]
above = sum(r[4] for r in bom); concrete = sum(r[4] for r in conc); conc_m3 = 4 * .9 * .9 * .6 + 4 * anch_m3
import csv
with open(os.path.join(OUT, '8panel_BOM.csv'), 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.writer(f); w.writerow(['Item', 'Qty', 'Unit', 'kg per unit', 'Total kg', 'Note', 'Source']); w.writerows(bom + conc)
# ---------------- strength table rows ----------------
rows = [
 ('Carrier rope SS316 16 mm 7x19', 'holds the tubes (5 m span)', '%.1f kN at 140 km/h wind' % Tw, '%.1f kN (145.5 breaking / 2)' % (mbl(16) / 2), '%.2f' % ut_rope, 'GOOD', 'Breaking load from the supplier listing.'),
 ('Stay rope SS316 20 mm', 'keeps the columns from being pulled in', '%.1f kN at 140 km/h wind' % Ts, '%.0f kN (indicative)' % (mbl(20) / 2), '%.2f' % ut_stay, 'GOOD', ''),
 ('Rope end fittings (swaged)', 'rope to turnbuckle and column', '%.1f kN' % Ts, 'about 90 % of rope breaking load', '0.2 (est.)', 'GOOD if swaged', 'Factory swages, not U-clips.'),
 ('Turnbuckle M24 SS316 (changed from M16)', 'tensions the stay', '%.1f kN' % Ts, 'select one rated >= 72 kN breaking', '0.5', 'GOOD (after change)', 'M16 working loads are only a few kN, so it was too weak.'),
 ('Pivot tube CHS 114.3 x 4, S355', 'turns with the panels', '%.1f kNm' % Mt, '%.2f kNm' % MRd, '%.2f' % ut_tube, 'GOOD', 'Tube length %.1f m between carrier lines. Do not lengthen.' % Lt),
 ('Bearing block (rotating joint) 50 mm', 'lets the tube rotate under the rope', '%.1f kN down / %.1f kN up' % (P, uplift / 4), 'about 23 kN static (typical 50 mm block)', '%.2f' % (P / 23), 'GOOD', 'Typical catalogue value; confirm with the chosen bearing.'),
 ('Column RHS 200 x 200 x 6', 'holds everything up', '%.1f kN + %.1f kN uplift' % (P, uplift / 4), '802 kN buckling (0.6 Pcr)', '0.05', 'VERY STRONG', 'A smaller column would also work.'),
 ('Column pad 0.9 x 0.9 x 0.6 m', 'ties the column to the ground', '%.1f kN uplift' % (uplift / 4), 'pad weight %.1f kN' % (.9 * .9 * .6 * RHO_C * G / 1000), '%.2f' % ((uplift / 4) / (.9 * .9 * .6 * RHO_C * G / 1000)), 'OK', 'Needs a soil test.'),
 ('Ground anchor (changed)', 'holds the stay down', '%.1f kN uplift (x 1.5 = %.0f kN)' % (Vs, anch_kN), 'buried concrete %.2f m3 each, or screw/rock anchor >= %.0f kN' % (anch_m3, anch_kN), '<= 1.0 by design', 'GOOD (after change)', 'The old block 1.0 x 0.8 x 0.35 m resisted only 6.6 kN.'),
 ('Drive wire SS316 6 mm 7x19 (changed from 4 mm)', 'pulls the lever arms', '%.1f / %.1f / %.1f kN (calm / 36 km/h / 54 km/h wind)' % (F0, F10, F15), '%.1f kN (%.1f breaking / 2)' % (mbl(6) / 2, mbl(6)), '%.2f / %.2f / %.2f' % (F0 / (mbl(6) / 2), F10 / (mbl(6) / 2), F15 / (mbl(6) / 2)), 'GOOD to 54 km/h', 'At 60 degrees tilt, the worst angle, panels held. The old 4 mm wire would be at %.2f of its limit at 54 km/h: too tight.' % F4),
 ('Cup anemometer + mast (new)', 'measures wind for the storm stow', '15 m/s trigger (54 km/h)', 'typical cup anemometer 0 to 40 m/s', '< 0.5', 'GOOD', 'The stow moves the panels edge-on to 90 degrees; resume below 12 m/s.'),
 ('Lever arm SS316 (0.44 m, 45 deg offset)', 'turns the tube', '%.0f Nm per row at 36 km/h' % (.6 * 100 * A * e + grav), 'arm plate: well above this', 'below 0.5 (est.)', 'GOOD', 'Check the weld and the clamp to the tube.'),
 ('Gearmotor winch 10 kN (changed from 3 kN)', 'winds the drive wire', '%.1f / %.1f / %.1f kN' % (F0, F10, F15), '10 kN', '%.2f / %.2f / %.2f' % (F0 / 10, F10 / 10, F15 / 10), 'GOOD to 54 km/h', 'The old 3 kN winch reaches its limit at about %.0f km/h wind and is at %.2f of its limit at 54 km/h.' % (V_ok3 * 3.6, F15 / 3)),
]
# ---------------- cost ----------------
rate = dict(mod=(20, 25, 30), steel=(70, 85, 100), r16=(650, 850, 1100), r20=(1000, 1300, 1700), r6=(120, 160, 220), conc=(6500, 7500, 9000))
st_kg = bom[2][4] + bom[4][4]; r16 = bom[5][1] + bom[6][1]; st_m = bom[7][1]; dm = bom[9][1]
items = [('Monocrystalline modules 8 x 550 Wp', '4,400 Wp', *[4400 * x for x in rate['mod']]), ('Pivot tubes + columns, galvanised steel', '%.0f kg' % st_kg, *[st_kg * x for x in rate['steel']]),
         ('SS316 16 mm rope (carrier + longitudinal)', '%.1f m' % r16, *[r16 * x for x in rate['r16']]), ('SS316 20 mm stay rope', '%.1f m' % st_m, *[st_m * x for x in rate['r20']]),
         ('SS316 6 mm drive wire', '%.0f m' % dm, *[dm * x for x in rate['r6']]), ('M24 turnbuckles, thimbles, clamps, pulleys, lever arms (SS316)', 'set', 20000, 28000, 40000),
         ('Bearing blocks x4, module rails and clamps', 'set', 14000, 20000, 30000), ('Gearmotor winch 10 kN with encoder and limit switches', '1', 35000, 55000, 85000),
         ('Controller + 5 sensors + cabling', 'set', 25000, 40000, 70000), ('Cup anemometer with mast', 'nos', 6000, 9000, 15000), ('Inverter 5 kW, DC/AC protection, earthing', 'set', 30000, 42000, 60000),
         ('Concrete: 4 pads + 4 anchors (%.1f m3, with steel and labour)' % conc_m3, '%.1f m3' % conc_m3, *[conc_m3 * x for x in rate['conc']]), ('Soil test, drawings, engineer check', 'lump sum', 15000, 25000, 50000)]
sub = [sum(i[2 + k] for i in items) for k in range(3)]
extra = [('Transport and handling (4 %)', .04), ('Installation labour, crane (15 %)', .15), ('Contingency (10 %)', .10)]
extra_rows = [(n, *[x * p for x in sub]) for n, p in extra]; tot = [sub[k] + sum(r[1 + k] for r in extra_rows) for k in range(3)]
fmt = lambda v: f'{v:,.0f}'
yield_kwh = 1134 * 4.4; sales = yield_kwh * 3.0
# ---------------- docx helpers ----------------
def newdoc(land=False):
    d = Document(); s0 = d.sections[0]
    if land: s0.orientation = WD_ORIENT.LANDSCAPE; s0.page_width, s0.page_height = s0.page_height, s0.page_width
    for s_ in d.sections: s_.left_margin = s_.right_margin = Inches(.6 if land else .9); s_.top_margin = s_.bottom_margin = Inches(.6)
    d.styles['Normal'].font.name = 'Calibri'; d.styles['Normal'].font.size = Pt(10.5); return d
def table(d, head, data, size=9):
    t = d.add_table(rows=1, cols=len(head)); t.style = 'Light Grid Accent 1'
    for j, h in enumerate(head):
        t.rows[0].cells[j].text = h
        for p in t.rows[0].cells[j].paragraphs:
            for r in p.runs: r.bold = True; r.font.size = Pt(size)
    for row in data:
        c = t.add_row().cells
        for j, v in enumerate(row):
            c[j].text = str(v)
            for p in c[j].paragraphs:
                for r in p.runs:
                    r.font.size = Pt(size)
                    if head[j] == 'Verdict': r.bold = True; r.font.color.rgb = RGBColor(0x1f, 0x7a, 0x2e) if v.startswith(('GOOD', 'VERY', 'OK')) else RGBColor(0xb0, 0x30, 0x20)
    d.add_paragraph()
# ================= 1. strength table docx =================
d = newdoc(True); d.add_heading('Strength of wire, joints, poles and motor: ' + TITLE, 0)
p = d.add_paragraph(); p.add_run('Will it give good output? ').bold = True
p.add_run('Yes, for the final design. At 140 km/h (panels held) every rope, tube, bearing and pole is within its limit. The first parts list had weak items, now changed: M16 turnbuckles, undersized anchor blocks, a 4 mm drive wire (too tight) and a 3 kN winch (limit at about %.0f km/h wind), and no wind sensor or stow arm. The final design adds a cup anemometer and a 45 degree offset lever arm for the 90 degree storm stow.' % (V_ok3 * 3.6))
table(d, ['Part', 'What it does', 'Load on it', 'What it can carry', 'Load / capacity', 'Verdict', 'Note'], rows)
d.add_heading('Motor and drive numbers', 1)
for x in ['Each row of 4 panels weighs about %.0f kg; an assumed 5 cm centre-of-mass offset gives about %.0f Nm per row.' % (row_kg, grav),
          'Wind torque per row = 0.6 V^2 x area (%.1f m2) x offset (%.2f m), flat-plate coefficient 1.0 (conservative).' % (A, e),
          'The lever arm is fixed with a 45 degree offset, so the useful lever is 0.44 m x cos(tilt - 45 deg): %.2f m at 60 degrees and still 0.31 m at the 90 degree stow. Wire force = torque of 2 rows / %.2f m: %.1f kN calm, %.1f kN at 36 km/h, %.1f kN at 54 km/h.' % (arm, arm, F0, F10, F15),
          'Speed: 15 to 60 degrees needs 0.27 m of wire in 45 s (6 mm/s). Mechanical power is only about 30 W at 5 kN, so a 0.25 kW worm-gear motor is ample.',
          'Wind stow: the anemometer trips the stow at 15 m/s (54 km/h) and releases below 12 m/s; edge-on panels (90 degrees) carry very little wind torque.']:
    d.add_paragraph(x, style='List Bullet')
d.add_heading('Honest limits', 1)
for x in ['Screening-level hand calculation (IS 875 style), not a certified design.', 'Bearing, turnbuckle, winch and lever-arm capacities are typical catalogue values or estimates; confirm with the datasheets of the parts you buy.', 'Wind torque uses a flat-plate coefficient of 1.0 and a centre of pressure a quarter of the panel width from the axis.']:
    d.add_paragraph(x, style='List Bullet')
d.save(os.path.join(OUT, 'SRMC_Component_Strength_Table.docx'))
# ================= 2. guide + cost docx =================
d = newdoc(); d.add_heading(TITLE, 0); d.add_paragraph('8-panel set (4.4 kWp): easy guide, weights, installation and cost estimate', style='Intense Quote')
def B(*ts):
    for x in ts: d.add_paragraph(x, style='List Bullet')
def N(*ts):
    for x in ts: d.add_paragraph(x, style='List Number')
d.add_heading('1. The idea in one page', 1)
d.add_paragraph('Solar panels sit 4.5 m above a farm on stainless steel wire ropes with crops below. Six sensors (pyranometer, PAR, DHT11, soil moisture, rain and wind) tell the controller what the sun, the crop and the weather are doing. It tilts the panels to the angle that gives the best mix of crop light and electricity. In rain the panels become a flat roof with a 3 degree slope and the water runs through a gutter into a tank for irrigation. In a storm (15 m/s) they turn edge-on to 90 degrees. The electricity is sold to a nearby industry, so the farmer earns a monthly income. Heat and dry air are protected against by extra shade.')
d.add_heading('2. What each sensor does', 1)
table(d, ['Sensor', 'What it measures', 'What the controller does'], [('Pyranometer', 'total sunlight (W/m2)', 'day or night, how bright; basis for the electricity estimate'), ('PAR sensor (under the panels)', 'light the plants can use', 'corrects the model: shows how much light really reaches the crop'), ('DHT11', 'air temperature and humidity', 'hot, dry air = plant stress = accept more shade'), ('Soil moisture', 'water in the root zone', 'dry soil = more shade and irrigation ON'), ('Rain sensor', 'wet or dry', 'wet = flat roof 3 degrees, rain to the gutter and tank'), ('Anemometer', 'wind speed (m/s)', 'at 15 m/s (54 km/h) or more: storm stow, panels edge-on at 90 degrees')])
d.add_paragraph('Rule: every step the controller tries every angle from 15 to 60 degrees in 0.5 degree steps and picks the one with the best combined score = 50 % electricity + 50 % crop light value. Year-long simulation with noisy sensors: 99.6 % of the best possible combined score (79 % of the best electricity, 95 % of the best crop light value).')
d.add_heading('3. Words you need to know', 1)
table(d, ['Word', 'Simple meaning'], [('kWp', 'Power in perfect test sunlight. 8 x 550 Wp = 4.4 kWp.'), ('SS316', 'Stainless steel with molybdenum; resists rust, rain and salt.'), ('7x19 rope', '7 strands of 19 wires: flexible, good for pulleys.'), ('Pivot tube', 'The tube the panels are bolted to; it turns with them.'), ('Carrier rope', 'The main rope between two columns; the tubes hang from it.'), ('Sag', 'How much a rope droops. We use span/12 = 0.42 m on 5 m.'), ('Stay', 'A slanted rope to the ground that stops the column being pulled over.'), ('Anchor', 'Buried concrete or a screw that the stay is tied to.'), ('Lever arm', 'A short arm on each tube; the drive wire pulls its tip.'), ('MBL', 'Minimum breaking load; we use half of it.'), ('Utilisation', 'Load divided by capacity. Above 1 means failure.'), ('PAR', 'The part of sunlight plants use.'), ('VPD', 'How thirsty the air is; high VPD stresses plants.')])
d.add_heading('4. Layout', 1)
table(d, ['Item', 'Value'], [('Modules', '8 x 550 Wp monocrystalline, 2.278 x 1.134 x 0.035 m, about 27.5 kg each'), ('Arrangement', '2 rows x 4 modules, row pitch 2.5 m, tube %.2f m each' % Lt), ('Columns', '4 x RHS 200x200x6, %.2f m, on a 5 m x 5 m grid' % COLH), ('Pivot height', '%.2f m (lowest edge 4.5 m)' % H), ('Ropes', '2 carrier + 2 longitudinal 16 mm; 4 stays 20 mm; drive wire 6 mm (all SS316)'), ('Motor', '10 kN gearmotor winch, about 0.25 kW, encoder 0.5 degree'), ('Footprint', 'about 25 m2 plus anchors')])
d.add_heading('5. SS316 wire rope weight', 1)
table(d, ['Diameter', 'kg per metre', 'Breaking load kN'], [('6 mm', '%.3f (derived)' % (K * 36), '%.1f (derived)' % mbl(6)), ('8 mm', '0.2438', '36.4'), ('10 mm', '0.381', '56.8'), ('12 mm', '0.5486', '81.8'), ('16 mm', '0.9754', '145.5'), ('20 mm', '%.2f (derived)' % (K * 400), '%.0f (derived)' % mbl(20))])
d.add_paragraph('Supplier listing for 7x19 SS316 (GS Products). Rule fitted to the listed sizes: weight (kg/m) = 0.00381 x d x d (d in mm); breaking load (kN) = 0.568 x d x d. Values for 6 and 20 mm are derived, not listed; confirm with the supplier.')
d.add_heading('6. Parts list and weights', 1)
table(d, ['Item', 'Qty', 'Unit', 'kg each', 'Total kg', 'Note', 'Source'], bom + conc, 8)
d.add_paragraph('Above-ground weight about %s kg (modules 220 kg). Concrete about %.1f t.' % (fmt(above), concrete / 1000)).runs[0].bold = True
d.add_heading('7. Strength check (summary)', 1)
table(d, ['Part', 'Load / capacity', 'Verdict'], [(r[0], r[4], r[5]) for r in rows])
d.add_heading('8. Installation steps', 1)
N('Soil test and survey. The anchors carry the wind uplift, so this is essential.', 'Mark the 5 m x 5 m column grid and the stay anchors 6.5 m outward at 45 degrees.', 'Cast 4 column pads and 4 anchors (or install screw anchors). Cure 7 days.', 'Stand the 4 columns plumb and hold them with temporary guys.', 'Hang the 16 mm carrier ropes, set sag 0.42 m, add the longitudinal ropes.', 'Fit the 20 mm stays and tension them equally with the M24 turnbuckles.', 'Hang the bearing blocks, place the two pivot tubes, fix the lever arms at the same angle.', 'Clamp the 8 modules to the rails, earth the frames, connect the strings to the inverter.', 'Fix the lever arms with the 45 degree offset, install the 10 kN winch, drum, guide pulleys and 6 mm drive wire through both lever-arm tips; set limit switches at 15 and 60 degrees and a stow stop at 90 degrees.', 'Fit the sensors: pyranometer in open sun, PAR under the panels, DHT11 in a shaded vent box, soil probe in the root zone, rain sensor at the panel edge, cup anemometer on a 3 m mast above the canopy. Load the controller code.', 'Test calm-weather motion, rain-flat mode and the sensor responses; log data for a month and compare with the digital twin.')
d.add_paragraph('Safety: harness and helmet; never stand under a suspended tube; use a crane or chain block.').runs[0].bold = True
d.add_heading('9. Cost estimate (indicative)', 1)
d.add_paragraph('Rates are assumptions; module and SS rope price levels come from web searches, the rest are typical-market guesses. Replace them with quotes.').runs[0].italic = True
table(d, ['Item', 'Quantity', 'Low INR', 'Mid INR', 'High INR'], [(n, q, fmt(a_), fmt(b_), fmt(c_)) for n, q, a_, b_, c_ in items] + [('Subtotal', '', fmt(sub[0]), fmt(sub[1]), fmt(sub[2]))] + [(n, '', fmt(a_), fmt(b_), fmt(c_)) for n, a_, b_, c_ in extra_rows] + [('TOTAL', '', fmt(tot[0]), fmt(tot[1]), fmt(tot[2]))])
d.add_paragraph('Total about INR %.1f lakh (mid), range %.1f to %.1f lakh, about INR %s per kWp. The model used INR 60,000 per kWp for a large field; a 4.4 kWp tilting set on tall columns costs several times more per kWp.' % (tot[1] / 1e5, tot[0] / 1e5, tot[2] / 1e5, fmt(tot[1] / 4.4))).runs[0].bold = True
d.add_paragraph('Earnings: 4.4 kWp x 1,134 kWh/kWp = %s kWh a year, about INR %s at INR 3/kWh (assumed). The farmer gets 30 percent plus crop income. Payback of INR %.1f lakh from this is very long, so the 8-panel set is a demonstration, not a business case.' % (fmt(yield_kwh), fmt(sales), tot[1] / 1e5))
d.add_heading('10. Learning exercises', 1)
for x in ['Q1. Weight of 20 m of 16 mm SS316 rope?  A: 0.975 x 20 = 19.5 kg.', 'Q2. Why use a sag of span/12?  A: A tighter rope pulls much harder on the columns and stays.', 'Q3. What does utilisation 0.76 mean?  A: 76 percent of the safe load is used.', 'Q4. Why change the 3 kN winch?  A: At 54 km/h wind the drive wire needs about %.1f kN, which is %.1f times the 3 kN winch. The 10 kN winch has margin.' % (F15, F15 / 3), 'Q5. Why does the controller tilt differently when the soil is dry?  A: Dry soil lowers the light the crop needs, so the panels take more of the sun.', 'Q6. Weight of the 8 modules?  A: 8 x 27.5 = 220 kg.']:
    d.add_paragraph(x)
d.add_heading('11. References', 1)
B('GS Products, 316 stainless 7x19 rope weights and breaking loads. https://www.gsproducts.co.uk/16mm-7x19-stainless-steel-wire-rope-cable/', 'Astronergy Astro 5 550 W, 26.9 kg. https://mm.mmem.com.au/astchsm72m-hc-550sf', 'JA Solar 555 W, 27.3 kg. https://autosolar.es/panel-solar-24-voltios/panel-solar-555w-ja-solar-monocristalino', 'BM Steel CHS sizes. https://www.bmsteel.co.uk/1143-x-5mm-75m-circular-hollow-section-bsen10219/p2570', 'EN 10219-1. https://store.sfs.fi/SFS-EN-10219-1', 'GreentechLead solar panel prices 2026. https://greentechlead.com/solar/solar-panel-prices-2026-china-at-0-11-w-vs-india-at-0-14-0-25-w-and-us-at-0-30-w-55213', 'Project files: Review1 results/structure/structural_report.txt, Review4 sensor_controller results.')
d.add_heading('12. Honest limits', 1)
B('Screening-level design, not certified; a structural engineer must check it.', '4 mm-class derived rope values, motor, inverter and bearing weights are assumptions.', 'Prices are indicative, real quotes can differ by 30 percent or more.', 'No field measurements exist yet.')
d.save(os.path.join(OUT, 'SRMC_8Panel_Guide_and_Cost.docx'))
# ================= 3. installation spec html =================
def tb(head, data): return '<table><tr>' + ''.join('<th>%s</th>' % html.escape(h) for h in head) + '</tr>' + ''.join('<tr>' + ''.join('<td>%s</td>' % html.escape(str(c)) for c in r) + '</tr>' for r in data) + '</table>'
page = ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>8-panel installation spec</title><style>body{margin:0;background:#f4f8ef;color:#1d221d;font:15px/1.5 Calibri,Segoe UI,sans-serif}header{background:#1f4d2b;color:#fff;padding:16px 22px}h1{margin:0;font-size:24px}main{max-width:1100px;margin:auto;padding:12px}h2{color:#1f4d2b}table{width:100%%;border-collapse:collapse;background:#fff;margin:6px 0}th,td{padding:5px 8px;border-bottom:1px solid #ccc;text-align:left;font-size:13.5px}th{background:#72b830}.w{background:#fff;border-left:6px solid #b03020;padding:8px 14px}</style></head><body><header><h1>' + TITLE + '</h1><div>8-panel (4.4 kWp) installation and weight estimate, final design</div></header><main>'
        '<h2>Strength check</h2>' + tb(['Part', 'What it does', 'Load', 'Capacity', 'Load/capacity', 'Verdict', 'Note'], rows) +
        '<h2>Parts and weights</h2>' + tb(['Item', 'Qty', 'Unit', 'kg/unit', 'Total kg', 'Note', 'Source'], bom + conc) +
        '<p><b>Above-ground weight about %s kg; concrete about %.1f t.</b></p>' % (fmt(above), concrete / 1000) +
        '<div class="w">Wind: 39 m/s (140 km/h) design speed, panels held. Screening level, not certified. Foundation and anchor sizes need a soil test. Source files: documents/8panel_BOM.csv and code_reference/build_hardware_docs.py.</div></main></body></html>')
open(os.path.join(OUT, 'SRMC_8Panel_Installation_Spec.html'), 'w', encoding='utf-8').write(page)
print('above %.0f kg, concrete %.1f t, cost mid %.2f lakh, F %.2f/%.2f/%.2f kN, anchor %.2f m3, V3kN %.1f m/s' % (above, concrete / 1000, tot[1] / 1e5, F0, F10, F15, anch_m3, V_ok3))
