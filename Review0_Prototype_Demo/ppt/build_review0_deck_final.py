"""Review 0 presentation (16:9) -> Review0_Presentation.pptx.   python build_review0_deck_final.py"""
import os, qrcode
from review0_ppt_common import *
p = new_pres(12191695, 6858000); TOTAL = 17; N = [0]
LOGO = os.path.join(IMG2, 'poster_02.png')

def frame(title, sub=None):
    s = blank(p); N[0] += 1; c = Canvas(s, 'in')
    c.rect(0, 0, 13.333, 1.0, fill=NAVY); c.rect(0, 1.0, 13.333, 0.06, fill=AMBER)
    c.text(0.5, 0.1, 11.2, 0.8, title, size=30, color=WHITE, bold=True, anchor='m')
    c.rect(12.15, 0.13, 0.75, 0.75, fill=WHITE); c.pic(LOGO, 12.2, 0.17, w=0.65)
    if sub: c.text(0.5, 1.15, 12.3, 0.4, sub, size=15, color=MUTED)
    c.text(0.5, 7.1, 10, 0.3, 'TCE  EEE  Project III, Review 0   |   Agrovoltaic Canopy for Protection and Sustainable Farming', size=10, color=MUTED)
    c.text(12.3, 7.1, 0.6, 0.3, str(N[0]), size=11, color=MUTED, align='r')
    return s, c

def card(c, x, y, w, h, title, body, tcol=NAVY, accent=GREEN, size=13, tsize=16, fill=LIGHT):
    c.rect(x, y, w, h, fill=fill, line=LINE); c.rect(x, y, 0.09, h, fill=accent)
    c.text(x + 0.25, y + 0.1, w - 0.4, 0.4, title, size=tsize, color=tcol, bold=True)
    if body: c.text(x + 0.25, y + 0.52, w - 0.4, h - 0.6, body, size=min(16, size * 1.12), color=INK, spacing=5, line=0.98)

def table(c, x, y, colw, rows, rowh=0.42, hsize=12, size=12, head=NAVY, zebra=True, bold_first=False, aligns=None):
    tw = sum(colw); shp = c.s.shapes.add_table(len(rows), len(colw), c.e(x), c.e(y), c.e(tw), c.e(rowh * len(rows))); t = shp.table
    tblPr = shp._element.graphic.graphicData.tbl.tblPr; tblPr.set('firstRow', '0'); tblPr.set('bandRow', '0')
    for j, w in enumerate(colw): t.columns[j].width = c.e(w)
    for i, row in enumerate(rows):
        t.rows[i].height = c.e(rowh)
        for j, v in enumerate(row):
            cell = t.cell(i, j); cell.margin_left = cell.margin_right = c.e(0.07); cell.margin_top = cell.margin_bottom = c.e(0.03); cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.fill.solid(); cell.fill.fore_color.rgb = rgb(head if i == 0 else (LIGHT if (zebra and i % 2 == 0) else WHITE))
            tf = cell.text_frame; tf.word_wrap = True; para = tf.paragraphs[0]; para.alignment = PP_ALIGN.CENTER if (aligns and aligns[j] == 'c') else (PP_ALIGN.RIGHT if (aligns and aligns[j] == 'r') else PP_ALIGN.LEFT)
            r = para.add_run(); r.text = str(v); f = r.font; f.name = FONT; f.size = Pt(hsize if i == 0 else size); f.bold = (i == 0) or (bold_first and j == 0); f.color.rgb = rgb(WHITE if i == 0 else INK)
    return t

# ============ 1 title ============
s = blank(p); N[0] += 1; c = Canvas(s, 'in')
c.gradient(0, 0, 13.333, 7.5, DEEP, NAVY, angle=315)
c.rect(8.6, -2.2, 6.4, 6.4, fill=SUN, shape=MSO_SHAPE.OVAL, alpha=0.14); c.rect(10.0, -0.9, 3.9, 3.9, fill=AMBER, shape=MSO_SHAPE.OVAL, alpha=0.18)
for k in range(6):
    sh = c.rect(9.0 + k * 0.62, 5.3 + (k % 2) * 0.1, 0.55, 0.12, fill='8FB4E8', alpha=0.55); sh.rotation = -32 + k * 13
c.rect(0.6, 0.55, 1.3, 1.3, fill=WHITE, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.08); c.pic(LOGO, 0.68, 0.63, w=1.14)
c.text(2.2, 0.62, 10, 0.9, ['THIAGARAJAR COLLEGE OF ENGINEERING, MADURAI  625 015', 'Department of Electrical and Electronics Engineering'], size=17, color=SUN, bold=True, spacing=2)
c.text(0.6, 2.2, 11.6, 1.9, 'AGROVOLTAIC CANOPY FOR PROTECTION AND SUSTAINABLE FARMING', size=40, color=WHITE, bold=True, line=0.95)
c.rect(0.6, 4.05, 1.6, 0.06, fill=AMBER)
c.text(0.6, 4.2, 11, 0.5, 'Review 0: prototype demonstration, six-sensor smart tilt controller (computer simulation)', size=20, color=SUN, italic=True)
c.text(0.6, 5.2, 7.2, 1.5, ['Thanwin S S (2303917710521118)', 'Chandru P M (2303917710521304)', 'Kuberaeshwaran S (2303917710521307)', 'Mukilan A (2303917710521311)'], size=15, color='D9E4F2', spacing=1)
c.text(0.6, 6.55, 8, 0.4, 'Guide: Dr. M. Meenakshi Devi, Assistant Professor, EEE   |   Academic year 2026-27, Semester VII', size=13, color='B8C8DC')

# ============ 2 problem ============
s, c = frame('Problem and Need', 'Land, water and income are in conflict for small and marginal farmers')
card(c, 0.5, 1.7, 4.0, 1.5, 'Water scarcity and cost', ['38 % of surveyed farmers named water scarcity and 25 % high farming cost as the top problem.'], size=13)
card(c, 0.5, 3.35, 4.0, 1.5, 'Solar takes farmland', ['Ground-mounted solar removes land from cultivation.'], size=13)
card(c, 0.5, 5.0, 4.0, 1.9, 'Fixed agrivoltaics cannot adapt', ['They cannot react to sun, cloud, heat, wind or rain, so they waste energy or shade the crop.'], size=13)
c.pic(os.path.join(IMG2, 'poster_13.png'), 4.8, 1.7, w=3.9); c.pic(os.path.join(IMG2, 'poster_14.png'), 8.9, 1.7, w=4.0)
c.text(4.8, 4.1, 8.1, 0.4, 'Field survey, Viluppuram district: 38 % water, 25 % cost, 22 % climate, 15 % electricity', size=12, color=MUTED, italic=True)
c.rect(4.8, 4.65, 8.1, 2.2, fill=PALEGREEN, line=GREEN)
c.text(5.05, 4.75, 7.7, 2.0, [[('The need', {'bold': True, 'color': GREEN, 'size': 17})], 'A low-cost canopy that chooses the panel angle from sensors, so that the crop gets the light it needs and the panels still make electricity, harvests rain for irrigation and stays safe in storms.', [('Review 0 question: ', {'bold': True, 'color': NAVY}), ('can six sensors choose the angle accurately, and can we show it before building hardware?', {})]], size=14, spacing=5)

# ============ 3 objectives and rubric ============
s, c = frame('Objectives and What Review 0 Delivers', 'Everything runs on the computer: no board, no wiring')
card(c, 0.5, 1.7, 6.0, 5.1, 'Objectives of Review 0', ['1  Simulate six sensors from real, named datasheets, each adjustable by hand', '2  Decide the panel angle from the sensors: safety, then water, then energy and crop light', '3  Show the result live in a MATLAB dashboard with plain-word explanations', '4  Measure the accuracy of the co-optimisation against the best possible angle', '5  Prove every number: datasheets, NASA POWER and PVGIS data, tests, checksums', '6  Estimate the cost if the sensors were real'], size=14, accent=AMBER)
table(c, 6.8, 1.75, [3.1, 1.0, 2.0], [['Review rubric', 'Marks', 'Where in this deck'], ['Prototype demonstration', '20', 'slides 8, 9, 10'], ['Testing and validation evidence', '10', 'slides 11, 12, 13'], ['Feasibility', '5', 'slides 14, 15'], ['SDG and cost', '5', 'slides 14, 15'], ['Time management', '5', 'slide 16'], ['Questions', '5', 'slide 17']], rowh=0.5, size=13, aligns=['l', 'c', 'l'])
c.rect(6.8, 5.45, 6.1, 1.35, fill=PALEGREEN, line=GREEN); c.text(7.0, 5.5, 5.8, 1.25, [[('Honest status: ', {'bold': True, 'color': GREEN}), ('a validated computer simulation. The sensor readings are generated or typed, not measured. No field trial yet.', {})]], size=14, anchor='m')

# ============ 4 idea and system ============
s, c = frame('The Idea and the System', 'Sensors in, best angle out: electricity for sale, light for the crop, rain for the tank')
c.pic(os.path.join(IMG2, 'poster_19.png'), 0.5, 1.6, w=7.6)
card(c, 8.7, 1.7, 4.2, 2.3, 'How it works', ['1  Six sensors read sun, plant light, air, soil, rain, wind', '2  The controller picks the tilt every step', '3  A motor and wire tilt all panels together'], size=13)
card(c, 8.7, 4.15, 4.2, 2.65, 'Why it is new', ['The angle balances electricity and crop light (half and half, adjustable).', 'Plant stress (hot, dry air or soil) is used as an input.', 'Every decision is explained in plain words.'], size=13, accent=AMBER)
c.text(0.5, 6.55, 7.9, 0.5, 'Site: TCE Madurai (9.88 N, 78.08 E). Panels: 8 x 550 Wp. Tilt range 15-60 deg; rain 3 deg; storm 90 deg.', size=12.5, color=MUTED, italic=True)

# ============ 5 sensors ============
s, c = frame('The Six Sensors: Simulated After Real Devices', 'Each reading follows the device datasheet; the datasheet files are downloaded as proof')
rows = [['#', 'Reading', 'Real device simulated', 'Range', 'Accuracy', 'Output signal'],
        ['1', 'Sunlight', 'Apogee SP-110 pyranometer', '0-2000 W/m2', '+-5 %', '0.20 mV per W/m2'], ['2', 'Plant light (PAR)', 'Apogee SQ-110 quantum sensor', '0-4000 umol/m2/s', '+-5 %', '0.20 mV per umol'],
        ['3', 'Air temperature', 'DHT11', '0-50 deg C', '+-2 deg C', 'digital'], ['4', 'Air humidity', 'DHT11 (same chip)', '20-90 % RH', '+-5 % RH', 'digital'],
        ['5', 'Soil moisture', 'DFRobot SEN0193 v1.2', '2.5 V dry to 1.2 V wet', 'needs dry/wet calibration', 'analog 1.2-2.5 V'], ['6', 'Rain', 'YL-83 / FC-37 + LM393', 'wet / dry', 'trimmer threshold', 'digital, LOW = wet'],
        ['7', 'Wind speed', 'Adafruit 1733 anemometer', '0.5-32.4 m/s', '+-1 m/s worst case', 'analog 0.4-2.0 V']]
table(c, 0.5, 1.7, [0.45, 1.9, 3.3, 2.4, 2.4, 1.95], rows, rowh=0.52, size=13, hsize=13, aligns=['c', 'l', 'l', 'l', 'l', 'l'])
c.text(0.5, 6.0, 12.4, 0.9, [[('How a simulated reading works: ', {'bold': True, 'color': NAVY}), ('the slider is the physical quantity and the dashboard also shows the signal the real device would output (837 W/m2 on the SP-110 is 167 mV; 20 m/s on the Adafruit 1733 is 1.39 V). Every sensor can be set by hand.', {})]], size=13.5)

# ============ 6 panels ============
s, c = frame('The Solar Panels: 8 x JinkoSolar Tiger Pro 550 Wp', 'Real module, values read from the official datasheet we downloaded')
table(c, 0.5, 1.7, [3.2, 3.6], [['Item', 'Value'], ['Model', 'JKM550M-72HL4-V (mono)'], ['Maximum power (STC)', '550 Wp'], ['Vmp / Imp', '40.90 V / 13.45 A'], ['Voc / Isc', '49.62 V / 14.03 A'], ['Efficiency', '21.33 %'], ['Size / weight', '2274 x 1134 x 35 mm / 28.9 kg'], ['Our array', '8 panels = 4.4 kWp']], rowh=0.5, size=13.5, bold_first=True)
c.text(0.5, 5.85, 6.8, 1.0, 'The tilt controller moves all panels together by one wire. 40.90 V x 13.45 A = 550 W.', size=13, color=MUTED, italic=True)
c.rect(7.8, 1.7, 5.1, 5.05, fill=LIGHT, line=LINE); c.text(8.0, 1.78, 4.8, 0.4, 'The array: 2 rows x 4 modules (landscape)', size=15, color=NAVY, bold=True)
for rI in range(2):
    for cI in range(4):
        c.rect(8.15 + cI * 1.12, 2.5 + rI * 1.55, 1.02, 1.35, fill='1F4E9E', line='9DB7E0', lw=1.2); c.text(8.15 + cI * 1.12, 2.5 + rI * 1.55, 1.02, 1.35, '550 Wp', size=11, color=WHITE, bold=True, align='c', anchor='m')
c.text(8.0, 5.7, 4.8, 1.0, ['Series string voltage at maximum power: 4 x 40.9 = 163.6 V per row', 'Total 8 x 550 = 4,400 Wp'], size=12.5, color=INK, spacing=3)

# ============ 7 control logic ============
s, c = frame('How the Controller Decides', 'Safety first, then water, then energy and crop light')
c.pic(os.path.join(IMG2, 'poster_23.png'), 0.5, 1.7, h=4.6)
card(c, 5.9, 1.7, 7.0, 2.2, 'Priority rules', [[('1  Wind 15 m/s or more: ', {'bold': True}), ('stow edge-on at 90 deg', {})], [('2  Rain sensor wet: ', {'bold': True}), ('3 deg slope, rain runs to the tank', {})], [('3  Night: ', {'bold': True}), ('park at 15 deg', {})]], size=14, accent=RED)
card(c, 5.9, 4.05, 7.0, 2.75, 'Otherwise: co-optimise', ['Try every angle from 15 to 60 deg (0.5 deg steps) and pick the best of', [('J(a) = w x Electricity(a) + (1 - w) x CropLight(a)', {'bold': True, 'color': GREEN, 'size': 15})], 'w = 0.5 by default (slider). Hot, dry air or dry soil lowers the light the crop needs, so the panels give more shade. Pump on below 35 % soil water, off above 55 %.'], size=13.5, accent=GREEN)

# ============ 8 dashboard ============
s, c = frame('Prototype: the MATLAB Dashboard', 'Seven readings from six devices, all adjustable by hand, with the decision explained in words')
pc, w_, h_ = c.pic(os.path.join(RES, 'dashboard_tab_sensors_day.png'), 0.5, 1.65, w=8.2, border=LINE)
card(c, 8.95, 1.65, 3.95, 5.15, 'What the judges can do', ['Move a slider or type a value for any sensor (MANUAL tag)', 'Press a weather preset: clear noon, cloud, hot dry, rain, storm, night', 'Press RAIN: panels go flat', 'Set wind to 20 m/s: panels stow at 90 deg', 'Read the decision in plain words', 'Open the four graph tabs'], size=13, accent=AMBER)

# ============ 9 live demo ============
s, c = frame('Live Demo: Change a Sensor, the Panels React', 'Five steps, about two minutes')
steps = [('1', 'Clear noon', 'preset: panels settle at 43 deg for the best mix'), ('2', 'Drag sunlight or PAR', 'the angle changes with the light'), ('3', 'Hot, dry preset', 'crop is stressed: more shade'), ('4', 'Press RAIN', 'panels flat at 3 deg, tank fills'), ('5', 'Wind to 20 m/s', 'stow edge-on at 90 deg')]
for i, (n_, a, b) in enumerate(steps):
    y = 1.7 + i * 0.98; c.rect(0.5, y, 5.6, 0.86, fill=LIGHT, line=LINE); c.rect(0.5, y, 0.7, 0.86, fill=GREEN); c.text(0.5, y, 0.7, 0.86, n_, size=24, color=WHITE, bold=True, align='c', anchor='m')
    c.text(1.35, y + 0.05, 4.7, 0.8, [[(a, {'bold': True, 'size': 15, 'color': NAVY})], [(b, {'size': 12.5})]], line=0.95)
c.pic(os.path.join(RES, 'dashboard_rain_manual.png'), 6.4, 1.7, w=3.2, border=LINE); c.pic(os.path.join(RES, 'dashboard_storm_manual_wind.png'), 9.75, 1.7, w=3.2, border=LINE)
c.text(6.4, 3.4, 3.2, 0.4, 'Rain: 3 deg', size=12, color=MUTED, align='c', italic=True); c.text(9.75, 3.4, 3.2, 0.4, 'Wind 20 m/s: 90 deg', size=12, color=MUTED, align='c', italic=True)
c.rect(6.4, 3.95, 6.55, 2.85, fill=PALEGREEN, line=GREEN)
c.text(6.6, 4.05, 6.2, 2.65, [[('Each graph says what it shows', {'bold': True, 'color': GREEN, 'size': 16})], 'Under every graph there is a one-line explanation in plain words, so a judge can read the dashboard without help.', [('Tip: ', {'bold': True, 'color': NAVY}), ('open the dashboard once before the review and press every preset.', {})]], size=13.5, spacing=5)

# ============ 10 graphs ============
s, c = frame('What the Graphs Show', 'Sensors through a day, and the panel angle and output against a fixed 45 deg panel')
c.pic(os.path.join(RES, 'dashboard_tab_sensors_day.png'), 0.5, 1.65, w=6.2, border=LINE); c.pic(os.path.join(RES, 'dashboard_tab_angle_output.png'), 6.9, 1.65, w=6.0, border=LINE)
card(c, 0.5, 4.8, 6.2, 2.0, 'Sensors through a day', ['Sunlight and PAR rise and fall with the sun; temperature and humidity move together; soil dries until the valve opens; wind stays below the 15 m/s storm limit.'], size=12.5, accent=AMBER)
card(c, 6.9, 4.8, 6.0, 2.0, 'Angle and output', ['The controller changes the angle through the day (blue) while a fixed panel cannot. On this hot, clear April day it makes about +5 % electricity and +8 % crop light against fixed 45 deg.'], size=12.5)

# ============ 11 accuracy ============
s, c = frame('Result: Accuracy of the Co-Optimisation', 'How close the chosen angle is to the best possible angle (half electricity, half crop light)')
c.pic(os.path.join(IMG2, 'poster_accuracy.png'), 0.5, 1.65, w=8.3)
table(c, 0.5, 5.1, [2.6, 1.55, 1.55, 1.55, 1.1], [['Design', 'Score', 'Electricity', 'Crop light', 'Error'], ['Fixed 45 deg', '91.2 %', '81.0 %', '84.6 %', '16.3 deg'], ['Our controller', '99.6 %', '82.1 %', '97.7 %', '4.8 deg']], rowh=0.5, size=13, aligns=['l', 'c', 'c', 'c', 'c'], bold_first=True)
card(c, 9.1, 1.65, 3.8, 5.15, 'What we obtained', [[('99.6 %', {'bold': True, 'color': GREEN, 'size': 28})], 'of the best possible score over 864 noisy test cases, with datasheet-sized sensor errors.', 'Ordinary designs reach 80 to 91 % and give up either crop light or electricity.', [('Simulation: ', {'bold': True, 'color': RED}), ('measured against the controller\'s own goal, not real crop yield.', {})]], size=13, accent=GREEN)

# ============ 12 testing ============
s, c = frame('Testing and Validation', '29 of 29 software tests pass; the sunlight model is checked against NASA POWER and PVGIS')
card(c, 0.5, 1.7, 4.2, 5.1, 'Checks done', ['Review 0 tests: 16 of 16 pass (decision rules, sensor errors, physics, explanation)', 'Sensor and tracker tests: 13 of 13 pass', 'Yearly electricity vs PVGIS: +5.0 %', 'Shadow model vs Blender 3-D: mean difference 0.010', 'Web twin and MATLAB model: identical results', 'Sunlight vs NASA POWER and PVGIS (right)'], size=13, accent=GREEN)
c.pic(os.path.join(IMG2, 'poster_trust.png'), 4.95, 1.7, w=5.6)
table(c, 10.7, 1.8, [1.3, 1.0], [['15 April', 'Wh/m2'], ['Our Clear day', '6502'], ['NASA actual', '6539'], ['PVGIS mean', '6337']], rowh=0.5, size=12.5, hsize=12, aligns=['l', 'c'], bold_first=True)
c.rect(4.95, 5.05, 7.95, 1.75, fill=PALEGREEN, line=GREEN)
c.text(5.15, 5.1, 7.6, 1.65, [[('Dashboard Clear day = a typical clear April day: ', {'bold': True, 'color': GREEN}), ('daily energy within 0.6 % of NASA POWER actual day and 2.6 % above PVGIS April mean. Plant-light share: NASA 0.444, dashboard 0.45. Noon peak is below a perfectly cloudless day (837 vs 986 W/m2). These are satellite data, not a sensor on the TCE roof.', {})]], size=13, anchor='m')

# ============ 13 proof ============
s, c = frame('Proof: Datasheets, Data and Checks', 'Every file is in the Proof folder (Proof/10_Review0_Sensors_and_Panels) and on GitHub')
rows = [['What we can show', 'File', 'It proves'],
        ['Pyranometer manual', '01_pyranometer_ApogeeSP110_manual.pdf', '0.20 mV per W/m2, +-5 %, 0-2000 W/m2'], ['PAR manual', '02_PAR_ApogeeSQ110_manual.pdf', '0.20 mV per umol, +-5 %, 410-655 nm'],
        ['DHT11 datasheet', '03-04_airTemp_and_humidity_DHT11_datasheet.pdf', '+-2 deg C, +-5 % RH'], ['Soil and rain sensor pages', '05_soilMoisture_*, 06_rain_*', 'output 1.2-2.5 V; wet/dry plate'],
        ['Anemometer datasheet', '07_wind_Adafruit1733_datasheet_C2192.pdf', '0.4-2.0 V = 0-32.4 m/s'], ['Panel datasheet', 'P1_panel_JinkoSolar_JKM550M-72HL4-V_datasheet.pdf', '550 Wp, 40.90 V, 13.45 A, 21.33 %'],
        ['NASA POWER and PVGIS data', 'sunlight_datasets/ (5 files)', 'where the sunlight data comes from'], ['Model vs data', 'TRUST_sunlight_model_vs_NASA_PVGIS.png', 'daily energy within about 1-3 %'],
        ['Accuracy test', 'T11_accuracy_v2.csv (864 cases)', '99.6 % vs 91.2 % fixed 45 deg']]
table(c, 0.5, 1.65, [2.8, 5.2, 3.3], rows, rowh=0.5, size=11.5, hsize=12.5)
qp = os.path.join(IMG2, 'qr_github.png'); qrcode.make('https://github.com/thanwin19/agrovoltaic-canopy-srmc').save(qp)
c.rect(12.1, 1.65, 0.85, 0.85, fill=WHITE); c.pic(qp, 12.1, 1.65, w=0.85)
c.text(12.05, 2.55, 0.95, 0.4, 'GitHub', size=10.5, color=MUTED, align='c')
c.text(0.5, 6.7, 11.5, 0.4, 'Also: SHA-256 checksum of every proof file (MANIFEST.csv) and the Review 0 Evidence Book (Word) for the judges.', size=12.5, color=NAVY, bold=True)

# ============ 14 cost ============
s, c = frame('Cost Estimate: If the Dashboard Sensors Were Real', 'Indicative estimates in INR, not quotes; the simulation itself costs nothing')
rows = [['Item', 'Research-grade kit', 'Low-cost kit'], ['Sunlight sensor (Apogee SP-110 / reference cell)', '28,000', '1,500'], ['PAR sensor (Apogee SQ-110 / reference cell)', '28,000', '1,500'], ['Anemometer (Adafruit 1733)', '6,500', '6,500'], ['DHT11 + soil sensor + rain sensor', '700', '700'],
        ['ESP32 board + ADC (ADS1115 x 2)', '1,400', '1,400'], ['Amplifier, enclosure, cables', '3,000', '1,500'], ['Total sensing and control kit', '67,600', '13,100']]
t = table(c, 0.5, 1.7, [4.9, 1.9, 1.5], rows, rowh=0.52, size=12.5, hsize=13, aligns=['l', 'r', 'r'])
for j in range(3):
    cell = t.cell(7, j); cell.fill.solid(); cell.fill.fore_color.rgb = rgb(PALEGREEN)
    for r in cell.text_frame.paragraphs[0].runs: r.font.bold = True
card(c, 9.5, 1.7, 3.4, 2.3, 'Panels (assumed)', ['8 x 550 Wp = 4,400 Wp', 'at about INR 16 per Wp:', [('about INR 70,000', {'bold': True, 'color': NAVY, 'size': 16})]], size=13, accent=AMBER)
card(c, 9.5, 4.15, 3.4, 2.65, 'This simulation', [[('INR 0', {'bold': True, 'color': GREEN, 'size': 26})], 'MATLAB (college licence) and the web twin; no hardware.'], size=13, accent=GREEN)
c.text(0.5, 5.9, 8.8, 1.0, 'Assumptions: Apogee sensors about US$ 250-300 each plus import duty and GST; other prices typical Indian retail. Replace with quotes before purchase. The earlier Phase II sensing kit (DHT11, soil, rain, ESP) was about INR 700. A year of calibration of the Apogee sensors is not included.', size=12, color=MUTED, italic=True)

# ============ 15 feasibility SDG limits ============
s, c = frame('Feasibility, SDG Relevance and Limits')
c.pic(os.path.join(IMG2, 'poster_49.png'), 0.5, 1.3, w=6.1)
card(c, 0.5, 3.2, 6.1, 3.6, 'Feasibility', ['Sensing kit costs INR 13,100 to 67,600; all parts are standard and available in India', 'The controller needs only a small board; a distilled neural network for an ESP32 was tested in simulation', 'All results are reproducible: code and proof are on GitHub'], size=13, accent=GREEN)
card(c, 6.8, 1.3, 6.1, 1.9, 'SDGs', ['7 clean energy from farmland  |  2 crops keep their light  |  6 rain harvested for irrigation  |  13 climate action  |  8 farmer income'], size=13, accent=AMBER)
card(c, 6.8, 3.35, 6.1, 3.45, 'Limits (we state them first)', ['Simulation only: sensor readings are generated or typed', 'Sunlight checked against satellite data, not a roof sensor', 'Accuracy is against our own goal, not crop yield', 'Prices and farmer share are assumptions'], size=13, accent=RED)

# ============ 16 status and remaining ============
s, c = frame('Review 0 Status, Remaining Work and Plan', 'What is finished, what is left for tonight, and what comes next')
card(c, 0.5, 1.65, 4.05, 3.55, 'Done', ['Dashboard with 6 real-model sensors, all manual', 'Day graphs, accuracy and sensor-error tests', '29 of 29 tests pass', 'Datasheets and datasets downloaded as proof', 'Evidence Book, poster, presentation', 'Code on GitHub'], size=12.5, accent=GREEN, fill=PALEGREEN)
card(c, 4.7, 1.65, 4.05, 3.55, 'Left for tonight', ['Rehearse the 5-minute demo once', 'Open the dashboard and press every preset', 'Print the A3 poster', 'Open the Jinko PDF and the SP-110 manual to be ready', 'Charge the laptop, copy the Proof folder'], size=12.5, accent=AMBER)
card(c, 8.9, 1.65, 4.0, 3.55, 'Remaining after Review 0', ['Real sensor set and one month of logged data', 'Wind-tunnel or CFD run for the storm stow', 'Crop-light and yield measurement', 'Finish and submit the paper'], size=12.5, accent=NAVY)
steps = [('Review 0', 'now: sensors and controller'), ('Review 1', 'design and CAD'), ('Review 2', 'solar and shadow'), ('Review 3', 'digital twin'), ('Review 4', 'control and simulation'), ('Review 5', 'economics and final')]
for i, (a, b) in enumerate(steps):
    x = 0.5 + i * 2.08; sh = c.rect(x, 5.5, 2.0, 1.25, fill=GREEN if i == 0 else NAVY, shape=MSO_SHAPE.PENTAGON); c.text(x + 0.12, 5.55, 1.65, 1.15, [[(a, {'bold': True, 'size': 15, 'color': WHITE})], [(b, {'size': 11, 'color': 'D9E4F2'})]], anchor='m', line=0.95)

# ============ 17 conclusion ============
s, c = frame('Conclusion and Questions')
card(c, 0.5, 1.4, 7.6, 5.4, 'Conclusion', ['Six sensors, each modelled on a real device and adjustable by hand, choose the panel angle live in a MATLAB dashboard', 'The co-optimisation reaches 99.6 % of the best possible score; ordinary designs reach 80-91 %', 'Sunlight is checked against NASA POWER and PVGIS; every datasheet and dataset is stored as proof', 'If built for real, the sensing kit costs INR 13,100 to 67,600', 'Next: real sensors, one month of data, wind check, paper'], size=14, accent=GREEN)
card(c, 8.3, 1.4, 4.6, 5.4, 'Likely questions', ['Are the sensors real? No: models of real devices, datasheets on file', 'Where does the sunlight come from? Sun position and NASA POWER clearness index, checked against NASA and PVGIS', 'Why trust 99.6 %? Best angle found by trying every angle, with sensor errors added', 'What is next? Real sensors and one month of data'], size=12.5, accent=AMBER)
c.rect(0.5, 6.3, 12.4, 0.5, fill=NAVY); c.text(0.5, 6.3, 12.4, 0.5, 'Thank you  |  Questions and discussion', size=18, color=WHITE, bold=True, align='c', anchor='m')

out = os.path.join(HERE, 'Review0_Presentation.pptx'); p.save(out); print('saved', out, N[0], 'slides')
