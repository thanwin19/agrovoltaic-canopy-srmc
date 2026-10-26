"""Builds Review0_7slides.pptx: a stand-alone 7-slide Review 0 deck (only what exists now) from the real result files. Run: python build_review0_7slides.py"""
import os, csv
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION, XL_LABEL_POSITION
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__)); RES = os.path.join(os.path.dirname(HERE), 'results'); TMP = os.path.join(HERE, '_img'); os.makedirs(TMP, exist_ok=True)
DEEP = RGBColor(0x14, 0x34, 0x2B); LEAF = RGBColor(0x4E, 0x9A, 0x2E); AMBER = RGBColor(0xE8, 0xA3, 0x17); SKY = RGBColor(0x2D, 0x7F, 0xC1); INK = RGBColor(0x1B, 0x2A, 0x22)
MUTE = RGBColor(0x5B, 0x6B, 0x62); PAPER = RGBColor(0xF6, 0xF7, 0xF2); WHITE = RGBColor(255, 255, 255); PALE = RGBColor(0xE6, 0xEE, 0xE0); RED = RGBColor(0xB0, 0x30, 0x30); CREAM = RGBColor(0xFF, 0xF6, 0xDC)
FONT = 'Calibri'; HFONT = 'Cambria'
prs = Presentation(); prs.slide_width = Inches(13.333); prs.slide_height = Inches(7.5); BLANK = prs.slide_layouts[6]

def rd(name):
    with open(os.path.join(RES, name), newline='', encoding='utf-8-sig') as f: return list(csv.DictReader(f))
def tb(slide, x, y, w, h, paras, size=16, bold=False, color=INK, align=PP_ALIGN.LEFT, font=FONT, anchor=MSO_ANCHOR.TOP, space=4):
    s = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h)); tf = s.text_frame; tf.word_wrap = True; tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = Inches(0.05); tf.margin_top = tf.margin_bottom = Inches(0.03)
    if isinstance(paras, str): paras = [paras]
    for i, t in enumerate(paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph(); p.alignment = align; p.space_after = Pt(space)
        for text, o in (t if isinstance(t, list) else [(t, {})]):
            r = p.add_run(); r.text = text; r.font.size = Pt(o.get('size', size)); r.font.bold = o.get('bold', bold); r.font.color.rgb = o.get('color', color); r.font.name = o.get('font', font)
    return s
def bullets(slide, x, y, w, h, items, size=15, gap=6, color=INK):
    s = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h)); tf = s.text_frame; tf.word_wrap = True
    for i, t in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph(); p.space_after = Pt(gap); first = True
        for text, o in (t if isinstance(t, list) else [(t, {})]):
            r = p.add_run(); r.text = (u'•  ' if first else '') + text; first = False; r.font.size = Pt(o.get('size', size)); r.font.bold = o.get('bold', False); r.font.color.rgb = o.get('color', color); r.font.name = FONT
    return s
def box(slide, x, y, w, h, fill=WHITE, line=None, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.06, dash=False):
    s = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h)); s.fill.solid(); s.fill.fore_color.rgb = fill
    if line is None: s.line.fill.background()
    else:
        s.line.color.rgb = line; s.line.width = Pt(1.25)
        if dash: s.line.dash_style = 4
    s.shadow.inherit = False
    if shape == MSO_SHAPE.ROUNDED_RECTANGLE: s.adjustments[0] = radius
    return s
def pic(slide, path, x, y, w, h):
    iw, ih = Image.open(path).size; r = min(w / iw, h / ih); pw, ph = iw * r, ih * r
    return slide.shapes.add_picture(path, Inches(x + (w - pw) / 2), Inches(y + (h - ph) / 2), Inches(pw), Inches(ph))
def title(slide, text, sub=None, dark=False):
    tb(slide, 0.6, 0.3, 12.1, 0.75, text, size=(30 if len(text) <= 52 else 26), bold=True, color=WHITE if dark else DEEP, font=HFONT, anchor=MSO_ANCHOR.MIDDLE)
    if sub: tb(slide, 0.6, 1.02, 12.1, 0.42, sub, size=16, color=PALE if dark else MUTE)
def chip(slide, x, y, w, text, fill=LEAF, size=12, h=0.32):
    b = box(slide, x, y, w, h, fill=fill, radius=0.5); tf = b.text_frame; tf.margin_left = tf.margin_right = Inches(0.04); tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER; r = p.add_run(); r.text = text; r.font.size = Pt(size); r.font.bold = True; r.font.color.rgb = WHITE; r.font.name = FONT
def proof(slide, x, y, w, h, lines, size=12.5, head='PROOF: how it works and where it comes from'):
    box(slide, x, y, w, h, fill=CREAM, line=AMBER); tb(slide, x + 0.12, y + 0.06, w - 0.24, 0.3, head, size=12.5, bold=True, color=RGBColor(0x8A, 0x5A, 0x00))
    s = bullets(slide, x + 0.12, y + 0.38, w - 0.24, h - 0.42, lines, size=size, gap=2)
def table(slide, x, y, w, rows, colw, size=12, rowh=0.36, head=DEEP):
    t = slide.shapes.add_table(len(rows), len(rows[0]), Inches(x), Inches(y), Inches(w), Inches(rowh * len(rows))).table
    for j, cw in enumerate(colw): t.columns[j].width = Inches(cw)
    for i, row in enumerate(rows):
        t.rows[i].height = Inches(rowh)
        for j, val in enumerate(row):
            c = t.cell(i, j); c.margin_left = c.margin_right = Inches(0.06); c.margin_top = c.margin_bottom = Inches(0.02); c.vertical_anchor = MSO_ANCHOR.MIDDLE; tf = c.text_frame; tf.word_wrap = True
            r = tf.paragraphs[0].add_run(); r.text = str(val); r.font.size = Pt(size); r.font.name = FONT; c.fill.solid()
            if i == 0: c.fill.fore_color.rgb = head; r.font.bold = True; r.font.color.rgb = WHITE
            else:
                c.fill.fore_color.rgb = PALE if i % 2 == 0 else WHITE; r.font.color.rgb = INK
                if str(val) == 'REAL': r.font.color.rgb = LEAF; r.font.bold = True
                if str(val) == 'SIM': r.font.color.rgb = RGBColor(0xC0, 0x7A, 0x00); r.font.bold = True
                if j == 0: r.font.bold = True
    return t
def notes(slide, text): slide.notes_slide.notes_text_frame.text = text
def new(dark=False):
    s = prs.slides.add_slide(BLANK); f = s.background.fill; f.solid(); f.fore_color.rgb = DEEP if dark else PAPER; return s

# ---------- numbers from the real result files ----------
day = [r for r in rd('day_comparison.csv') if r['condition'] == 'Clear day']; D = {r['strategy']: r for r in day}
cl = {k: (float(v['pv_pct_of_best']), float(v['crop_pct_of_best'])) for k, v in D.items()}
srmc = D['SRMC controller (50/50)']; f45 = D['Fixed 45 deg']; trk = D['East-west sun tracking']
gainE = 100 * (float(srmc['pv_kWh_m2_day']) / float(f45['pv_kWh_m2_day']) - 1); gainC = 100 * (float(srmc['crop_light_score']) / float(f45['crop_light_score']) - 1)
trust = {(r['sky'], int(r['sensor_error_pct'])): r for r in rd('sensor_trust_study.csv') if r['mode'] == 'plain'}
mp = open(os.path.join(RES, 'mppt_study.md'), encoding='utf-8').read().split('\n')[2]       # "Cloud transient: tracking efficiency 99.83 %, fixed voltage 96.95 %, gain +2.96 %."
import re; effT, effF, gainM = re.findall(r'(\d+\.\d+) %', mp)[0:2] + [re.findall(r'([+-]\d+\.\d+) %', mp)[0]]
t1 = rd('test_results.csv'); t2 = rd('sensor_and_mppt_tests.csv'); nOK = sum(r['result'] == 'PASS' for r in t1 + t2); nAll = len(t1) + len(t2)
other = {r['condition']: r for r in rd('day_comparison.csv') if r['strategy'] == 'SRMC controller (50/50)'}

# crop the top (three graphs) of the explanation window for slide 4
im = Image.open(os.path.join(RES, 'explain', 'explain_clear_noon.png')); w, h = im.size; im.crop((0, int(h * 0.0), w, int(h * 0.53))).save(os.path.join(TMP, 'explain_top.png'))

# ================= 1 title =================
s = new(dark=True)
tb(s, 0.6, 0.55, 7.0, 0.4, 'REVIEW 0  |  PROTOTYPE + MATLAB DEMO', size=15, bold=True, color=AMBER)
tb(s, 0.6, 1.05, 6.6, 2.3, 'Smart tilt for solar panels over crops: more electricity, and the plants still get their light', size=34, bold=True, color=WHITE, font=HFONT)
tb(s, 0.6, 3.55, 6.4, 1.0, ['Live sensors on an ESP board + a MATLAB dashboard that decides the panel angle, the irrigation and the MPPT.', 'Site: TCE ground, Madurai (9.88 N).'], size=16, color=PALE)
chip(s, 0.6, 4.75, 2.1, 'REAL: DHT11, soil, rain', LEAF, 12); chip(s, 2.8, 4.75, 2.6, 'SIM: sunlight + plant light', RGBColor(0xC0, 0x7A, 0x00), 12); chip(s, 5.5, 4.75, 1.7, 'MPPT included', SKY, 12)
tb(s, 0.6, 5.35, 6.6, 0.9, 'REAL = measured by the sensors on the prototype.   SIM = simulated, set with scroll bars in the dashboard (no pyranometer / PAR sensor yet).', size=13, color=PALE)
tb(s, 0.6, 6.5, 6.6, 0.8, ['Student: ______________________', 'Guide: ______________________     Date: ___________'], size=14, color=PALE)
pic(s, os.path.join(RES, 'screens', 'dashboard_v2_clear_noon.png'), 7.35, 1.2, 5.7, 5.0); tb(s, 7.35, 6.3, 5.7, 0.5, 'The MATLAB dashboard (clear noon): canopy drawing, live plots, decision in words', size=12, color=PALE, align=PP_ALIGN.CENTER)
notes(s, 'Say in one sentence: the panels should make electricity AND let the crops below get enough light, so the tilt angle is decided every few seconds from sensor data. Be clear about REAL and SIM: DHT11, soil moisture and rain are real sensors on the prototype; sunlight (pyranometer) and plant light (PAR) are simulated and can be moved with scroll bars.')

# ================= 2 how it works =================
s = new(); title(s, 'How the system works, step by step', 'From the sensor to the decision, in five steps')
steps = [('1  Sense', 'DHT11, soil probe and rain sensor read the field', LEAF), ('2  Send', 'ESP board sends one line per second over USB', SKY), ('3  Decide', 'MATLAB picks the best panel angle (rules + search)', DEEP), ('4  Act', 'Panel angle, irrigation pump and MPPT voltage', RGBColor(0xC0, 0x7A, 0x00)), ('5  Show', 'Dashboard shows numbers, graphs and the reason in words', MUTE)]
for i, (h, d, col) in enumerate(steps):
    x = 0.6 + i * 2.45; box(s, x, 1.55, 2.3, 1.45, fill=col); tb(s, x + 0.08, 1.6, 2.15, 0.4, h, size=17, bold=True, color=WHITE); tb(s, x + 0.08, 2.0, 2.15, 1.0, d, size=13, color=WHITE)
    if i < 4: tb(s, x + 2.28, 1.95, 0.2, 0.5, '>', size=22, bold=True, color=MUTE)
rows = [['Input', 'Where it comes from', 'Status', 'Proof / how'],
        ['Air temperature, humidity', 'DHT11 on the ESP board', 'REAL', 'datasheet accuracy: 2 C and 5 % RH; checked against a thermometer on the day'],
        ['Soil moisture', 'soil probe -> analog pin', 'REAL', 'two-point calibration: dry in air = 0 %, wet in water = 100 %'],
        ['Rain', 'rain sensor module', 'REAL', 'wet plate gives rain = 1; sets the 3 degree slope for harvesting'],
        ['Sunlight (pyranometer)', 'scroll bar, or sun model', 'SIM', 'sun position from date, time and latitude; clearness index of TCE from NASA POWER'],
        ['Plant light (PAR)', 'scroll bar, or 0.45 x 4.57 x sunlight', 'SIM', 'about 45 % of sunlight is PAR; 4.57 micromol per joule (standard conversion)'],
        ['Wind', 'scroll bar', 'SIM', 'safety rule: 15 m/s or more turns the panels edge-on (90 degrees)']]
table(s, 0.6, 3.2, 12.1, rows, [2.5, 3.0, 0.9, 5.7], size=12.5, rowh=0.44)
tb(s, 0.6, 6.4, 12.1, 0.8, [[('Real sensor values on the day:  ', {'bold': True, 'color': DEEP}), ('temperature ______ C    humidity ______ %    soil ______ %    rain ______   (fill from the serial monitor / dashboard)', {})]], size=14, color=MUTE)
notes(s, 'Walk the five steps left to right. Then the table: green REAL rows are measured, orange SIM rows are simulated. The sun model uses the standard solar-position equations (Duffie and Beckman) with the monthly clearness index of TCE from NASA POWER; diffuse split by the Erbs correlation. The PAR conversion is a standard textbook value. The last line is for the live numbers read from the board on the day.')

# ================= 3 scroll bars + trust =================
s = new(); title(s, 'The two simulated sensors: scroll bars, and can we trust them?', 'Move the scroll bar and watch the angle, the electricity and the irrigation react')
pic(s, os.path.join(RES, 'screens', 'dashboard_v2_manual_cloudy.png'), 0.6, 1.5, 6.4, 3.65); tb(s, 0.6, 5.1, 6.4, 0.3, 'Manual mode: sunlight 350 W/m2, PAR 700 micromol/m2/s', size=12, color=MUTE, align=PP_ALIGN.CENTER)
proof(s, 0.6, 5.5, 6.4, 1.7, ['Sun position: standard solar equations; sky clearness for TCE: NASA POWER monthly data', 'PAR = 0.45 x 4.57 x sunlight (standard conversion); the dashboard flags it if PAR / sunlight is far from 2.06', 'Same equations were checked against the PVGIS service: +5.0 % per year'], size=12)
bullets(s, 7.3, 1.5, 5.45, 2.35, [[('Dim sky (300 W/m2): ', {'bold': True}), ('panels go steep (55.5 degrees) to give crops light; electricity 36 W/m2', {})], [('Bright sky (1000 W/m2): ', {'bold': True}), ('flatter (39.5 degrees); electricity 124 W/m2', {})], [('Real sensors later: ', {'bold': True}), ('the serial line takes two extra numbers and replaces the simulated ones', {})]], size=14, gap=5)
cd = CategoryChartData(); cd.categories = ['5 % wrong', '10 % wrong', '20 % wrong']
cd.add_series('Clear day', [round(float(trust[('Clear day', e)]['energy_loss_mean']), 1) for e in (5, 10, 20)]); cd.add_series('Partly cloudy day', [round(float(trust[('Partly cloudy day', e)]['energy_loss_mean']), 1) for e in (5, 10, 20)])
gf = s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(7.3), Inches(3.85), Inches(5.45), Inches(3.35), cd); ch = gf.chart
ch.has_title = True; ch.chart_title.text_frame.text = 'Average electricity lost if the sunlight reading is wrong (%)'; ch.chart_title.text_frame.paragraphs[0].runs[0].font.size = Pt(12); ch.chart_title.text_frame.paragraphs[0].runs[0].font.bold = True
ch.has_legend = True; ch.legend.position = XL_LEGEND_POSITION.BOTTOM; ch.legend.include_in_layout = False; ch.legend.font.size = Pt(11)
ch.plots[0].gap_width = 70; ch.plots[0].has_data_labels = True; dl = ch.plots[0].data_labels; dl.font.size = Pt(11); dl.number_format = '0.0'; dl.number_format_is_linked = False; dl.position = XL_LABEL_POSITION.OUTSIDE_END
ch.series[0].format.fill.solid(); ch.series[0].format.fill.fore_color.rgb = AMBER; ch.series[1].format.fill.solid(); ch.series[1].format.fill.fore_color.rgb = SKY
ch.category_axis.tick_labels.font.size = Pt(11); ch.value_axis.tick_labels.font.size = Pt(11); ch.value_axis.maximum_scale = 14; ch.value_axis.has_major_gridlines = True; ch.value_axis.major_gridlines.format.line.color.rgb = PALE
notes(s, 'Answer to "can we trust the simulated sensors?": they are not measurements, they are controllable inputs built on standard equations. What we CAN prove: (1) the equations match the PVGIS service within +5.0 % per year; (2) we measured what a wrong reading costs: on a clear day a 5 % error loses 2.5 % of the electricity on average, a 10 % error 5.1 % (worst single half-hour 35 %); (3) the dashboard flags inconsistent sunlight/PAR readings; (4) real sensors plug in without changing the code. Numbers: results/sensor_trust_study.csv.')

# ================= 4 how it optimises =================
s = new(); title(s, 'How the controller chooses the tilt angle', 'It tries every angle from 15 to 60 degrees and keeps the one with the best combined score')
pic(s, os.path.join(TMP, 'explain_top.png'), 0.6, 1.5, 12.1, 3.5)
cols = [('Rules first (safety and water)', ['Wind 15 m/s or more: panels edge-on (90 degrees)', 'Rain detected: 3 degree slope, rain goes to the tank', 'Night: rest at 15 degrees']),
        ('Then the search (graph 1)', ['Amber line: electricity at each angle', 'Green line: light that reaches the crops', 'Blue line: combined score = 0.5 x electricity + 0.5 x crop light; red star = the angle chosen']),
        ('Stress changes the need', ['Hot, dry air (VPD above 2.5 kPa) or dry soil: crops need less light', 'The panels can then shade more and make more electricity', 'Dry soil: pump on below 35 %, off at 55 %'])]
for i, (h, items) in enumerate(cols):
    x = 0.6 + i * 4.1; box(s, x, 5.08, 3.95, 1.5, fill=WHITE, line=PALE); tb(s, x + 0.1, 5.1, 3.75, 0.3, h, size=13.5, bold=True, color=DEEP); bullets(s, x + 0.1, 5.4, 3.75, 1.2, items, size=11.5, gap=1)
proof(s, 0.6, 6.62, 12.1, 0.8, ['Accuracy point A: the chosen angle is compared with a full search of every 0.5 degree step. Clear noon: difference 0.0 degrees. Worst case tested: 3 degrees, with the score within 0.02 % (a flat top).  Light and shadow come from the same equations checked against Blender 3-D ray tracing (mean difference 0.010).'], size=10.5, head='PROOF')
notes(s, 'Graph 1 is the heart of the system. The controller evaluates electricity (amber) and crop light (green) for each angle, joins them into one score (blue) and takes the highest point. The black circle is the best angle found by trying every 0.5 degrees; the red star is what the controller chose. The shadow and electricity values come from the physics functions that were checked against PVGIS and Blender.')

# ================= 5 results =================
s = new(); title(s, 'Result: electricity and crop light together (clear day)', 'Each bar is a percentage of the best way for that quantity; simulated day, 6 to 18 h')
names = [('Fixed 15 deg (PV-max)', 'Fixed 15 deg'), ('Fixed 45 deg', 'Fixed 45 deg'), ('East-west sun tracking', 'Sun tracking'), ('SRMC controller (50/50)', 'SRMC controller')]
cd = CategoryChartData(); cd.categories = [n[1] for n in names]; cd.add_series('Electricity (% of best)', [round(cl[n[0]][0], 1) for n in names]); cd.add_series('Crop light (% of best)', [round(cl[n[0]][1], 1) for n in names])
gf = s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(0.6), Inches(1.5), Inches(7.4), Inches(4.0), cd); ch = gf.chart
ch.has_legend = True; ch.legend.position = XL_LEGEND_POSITION.BOTTOM; ch.legend.include_in_layout = False; ch.legend.font.size = Pt(12); ch.plots[0].gap_width = 60
ch.plots[0].has_data_labels = True; dl = ch.plots[0].data_labels; dl.font.size = Pt(12); dl.number_format = '0'; dl.number_format_is_linked = False; dl.position = XL_LABEL_POSITION.OUTSIDE_END
ch.series[0].format.fill.solid(); ch.series[0].format.fill.fore_color.rgb = AMBER; ch.series[1].format.fill.solid(); ch.series[1].format.fill.fore_color.rgb = LEAF
ch.category_axis.tick_labels.font.size = Pt(12); ch.value_axis.tick_labels.font.size = Pt(11); ch.value_axis.maximum_scale = 120; ch.value_axis.has_major_gridlines = True; ch.value_axis.major_gridlines.format.line.color.rgb = PALE
box(s, 8.3, 1.5, 4.45, 4.0, fill=WHITE, line=PALE); tb(s, 8.45, 1.55, 4.2, 0.4, 'In simple words', size=17, bold=True, color=DEEP)
bullets(s, 8.45, 2.0, 4.2, 3.5, [[('Sun tracking: ', {'bold': True}), ('most electricity, but the crops get only %.0f %% of the light they need.' % cl['East-west sun tracking'][1], {})], [('Fixed 45 degrees: ', {'bold': True}), ('crops fine, electricity %.0f %% of best.' % cl['Fixed 45 deg'][0], {})], [('SRMC controller: ', {'bold': True}), ('%.0f %% of the best electricity and %.0f %% of the best crop light.' % cl['SRMC controller (50/50)'], {})], [('Against fixed 45 degrees: ', {'bold': True}), ('electricity %+.1f %%, crop light %+.1f %%.' % (gainE, gainC), {})]], size=14, gap=7)
rows = [['Other days (same controller)', 'Electricity', 'Crop light'], ['Partly cloudy day', '%.0f %% of best' % float(other['Partly cloudy day']['pv_pct_of_best']), '%.0f %% of best' % float(other['Partly cloudy day']['crop_pct_of_best'])], ['Hot, dry day (plant stress)', '%.0f %% of best' % float(other['Hot clear day (VPD stress)']['pv_pct_of_best']), '%.0f %% of best' % float(other['Hot clear day (VPD stress)']['crop_pct_of_best'])]]
table(s, 0.6, 5.65, 7.4, rows, [3.4, 2.0, 2.0], size=12.5, rowh=0.36)
proof(s, 8.3, 5.65, 4.45, 1.6, ['Simulated day 105, TCE; same functions as the dashboard', 'Sun tracking is only a reference: our panels have two positions', 'Files: results/day_comparison.csv, fig_energy_vs_crop_clear_day.png'], size=11.5)
notes(s, 'Read the chart as: there is a trade-off. Pure tracking maximises electricity but starves the crops (27 % of the light target). The controller gives up about a quarter of the maximum electricity to give the crops about 89 % of their light, and it beats a fixed 45 degree panel on both. The 50/50 weight is adjustable in the dashboard (energy share scroll bar). The equal-weight average favours the controller by construction, so the weight must be chosen by the farmer or operator.')

# ================= 6 MPPT =================
s = new(); title(s, 'MPPT: always working at the top of the power curve', 'Maximum power point tracking, Perturb and Observe')
pic(s, os.path.join(RES, 'fig_mppt_curves.png'), 0.6, 1.5, 7.3, 3.05); pic(s, os.path.join(RES, 'fig_mppt_tracking.png'), 8.1, 1.5, 4.65, 3.05)
for i, (h, d) in enumerate([('What it is', 'A solar panel gives the most power at one voltage (red star). That voltage moves with sunlight and cell temperature.'), ('What MPPT does', 'A small controller nudges the voltage up and down and keeps the point where power is highest.'), ('What we gain', 'Cloud test: MPPT keeps %s %% of the maximum energy; a fixed voltage keeps %s %% (gain %s %%).' % (effT, effF, gainM))]):
    x = 0.6 + i * 4.1; box(s, x, 4.65, 3.95, 1.4, fill=WHITE, line=PALE); tb(s, x + 0.1, 4.68, 3.75, 0.3, h, size=14, bold=True, color=DEEP); tb(s, x + 0.1, 5.02, 3.75, 1.0, d, size=13, color=INK)
proof(s, 0.6, 6.1, 12.1, 1.3, ['Model: single-diode PV model of a typical 400 W module (Isc 10.5 A, Voc 49.6 V, Vmp 40.5 V; replace with your datasheet). Tracker: Perturb and Observe, 0.5 V steps. Hotter cell: best voltage falls from 41.1 V (25 C) to 35.6 V (65 C).', 'Accuracy point C: tracking efficiency %s %%.  Tested in MATLAB (5 MPPT tests pass).  This is a model of the tracker, not yet a hardware DC-DC converter.' % effT], size=11.5, head='PROOF')
notes(s, 'MPPT is the electronics that makes sure the panel works at its maximum power point. Our main energy numbers already assume the panel works there; this slide shows how the tracker achieves it and how much it is worth compared with a fixed voltage. Be honest: this is a software model of a typical module; the hardware converter is future work.')

# ================= 7 accuracy and proof =================
s = new(); title(s, 'Accuracy points and proof', 'Every number: what it means, and where it comes from')
rows = [['', 'Accuracy point', 'Number', 'Where it comes from'],
        ['A', 'Angle chosen vs full 0.5 degree search', '0.0 degrees at clear noon (worst tested 3 degrees, score within 0.02 %)', 'search built into the dashboard (Explain window)'],
        ['B', 'Gain over a fixed 45 degree panel', 'electricity %+.1f %%, crop light %+.1f %% (clear day)' % (gainE, gainC), 'results/day_comparison.csv'],
        ['C', 'MPPT tracking efficiency', '%s %% (fixed voltage %s %%)' % (effT, effF), 'results/mppt_study.md'],
        ['D', 'Real sensors', 'DHT11: 2 C, 5 % RH (datasheet). Bench: ______ C vs ______ C', 'datasheet; thermometer check on the day'],
        ['E', 'Solar and shadow equations', '+5.0 % per year vs PVGIS; shadow difference 0.010 vs Blender', 'PVGIS service; Blender Cycles ray tracing'],
        ['F', 'Simulated-sensor error', 'wrong by 5 %%: %.1f %% less electricity; by 10 %%: %.1f %% (worst half-hour %.0f %%)' % (float(trust[('Clear day', 5)]['energy_loss_mean']), float(trust[('Clear day', 10)]['energy_loss_mean']), float(trust[('Clear day', 10)]['energy_loss_max'])), 'results/sensor_trust_study.csv'],
        ['T', 'Software tests of every rule', '%d of %d pass' % (nOK, nAll), 'results/test_results.md, sensor_and_mppt_tests.md']]
table(s, 0.6, 1.5, 12.1, rows, [0.5, 3.4, 5.0, 3.2], size=12, rowh=0.5)
box(s, 0.6, 5.65, 5.9, 1.6, fill=WHITE, line=RED); tb(s, 0.75, 5.68, 5.6, 0.3, 'What we do NOT claim', size=14, bold=True, color=RED)
bullets(s, 0.75, 6.0, 5.65, 1.2, ['Sunlight and PAR are simulated, not measured', 'No field data yet; the tilt is shown on screen only', 'MPPT and module data are for a typical 400 W module'], size=12, gap=2)
box(s, 6.8, 5.65, 5.95, 1.6, fill=WHITE, line=LEAF); tb(s, 6.95, 5.68, 5.6, 0.3, 'Next steps', size=14, bold=True, color=LEAF)
bullets(s, 6.95, 6.0, 5.65, 1.2, ['Connect a real pyranometer and PAR sensor', 'Add a motor and a hardware MPPT converter', 'Log a week of real sensor data and compare'], size=12, gap=2)
notes(s, 'This is the proof slide. Letters A to F match the labelled badges on the Explain window of the dashboard, so you can point to them live. Row D has blanks to fill with the bench numbers measured on the day. Close with the honest limits.')

out = os.path.join(HERE, 'Review0_7slides.pptx'); prs.save(out); print('saved', out, len(prs.slides), 'slides; tests', nOK, '/', nAll)
