"""Review 0 poster, A3 portrait (297 x 420 mm), built with python-pptx -> Review0_Poster_A3.pptx.   python build_review0_poster.py"""
import os, qrcode
from review0_ppt_common import *
W, H = 297, 420
p = new_pres(10692079, 15119604); s = blank(p); c = Canvas(s, 'mm')
c.rect(0, 0, W, H, fill='F4F7FB')                                              # page

# ---------------- header ----------------
c.gradient(0, 0, W, 66, DEEP, NAVY, angle=0)
sun = c.rect(215, -40, 130, 130, fill=SUN, shape=MSO_SHAPE.OVAL, alpha=0.18); c.rect(238, -17, 84, 84, fill=AMBER, shape=MSO_SHAPE.OVAL, alpha=0.20)
for k in range(5):                                                              # tilted solar-panel strips (the idea in one picture)
    sh = c.rect(236 + k * 10, 6 + (k % 2) * 0.5, 9, 2.4, fill='8FB4E8', alpha=0.6); sh.rotation = -30 + k * 15
c.rect(0, 66, W, 3.5, fill=AMBER)
c.rect(11, 11, 40, 40, fill=WHITE, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.08); c.pic(os.path.join(IMG2, 'poster_02.png'), 13, 13.5, w=36)
c.text(58, 8, 170, 8, 'THIAGARAJAR COLLEGE OF ENGINEERING, MADURAI  625 015   |   Department of EEE', size=13, color=SUN, bold=True)
c.text(58, 17, 225, 26, 'AGROVOLTAIC CANOPY FOR PROTECTION AND SUSTAINABLE FARMING', size=27, color=WHITE, bold=True, line=0.92)
c.text(58, 40, 225, 9, 'Six sensors in, best panel angle out: the crop and the solar panels both win', size=17, color=SUN, italic=True)
c.text(58, 51.5, 172, 8, 'Thanwin S S  |  Chandru P M  |  Kuberaeshwaran S  |  Mukilan A      Guide: Dr. M. Meenakshi Devi', size=12, color='D9E4F2')
b = c.rect(233, 50, 54, 12, fill=AMBER, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.3); c.text(233, 50, 54, 12, [[('REVIEW 0', {'size': 14})], [('Project III  |  2026-27', {'size': 10.5})]], size=12.5, color=DEEP, bold=True, align='c', anchor='m')

# ---------------- stat strip ----------------
stats = [('99.6 %', 'accuracy of the co-optimisation against the best possible angle (fixed 45 deg: 91.2 %)', GREEN), ('6', 'sensors, each simulated from a real datasheet and adjustable by hand', AMBER),
         ('4.4 kWp', '8 x JinkoSolar Tiger Pro JKM550M-72HL4-V panels, 550 Wp each', NAVY), ('29 / 29', 'software tests pass; sunlight checked against NASA POWER and PVGIS', TEAL)]
cw = (W - 24 - 3 * 5) / 4
for i, (big, lab, col) in enumerate(stats):
    x = 12 + i * (cw + 5); c.rect(x, 73, cw, 29, fill=WHITE, line=LINE, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.08); c.rect(x, 73, 3.2, 29, fill=col)
    c.text(x + 6, 74.5, cw - 8, 14, big, size=34, color=col, bold=True, anchor='m'); c.text(x + 6, 88, cw - 8, 14, lab, size=10.5, color=MUTED, line=0.95)

def bar(x, y, w, num, title, col=GREEN):
    c.rect(x, y, w, 9.5, fill=col, shape=MSO_SHAPE.RECTANGLE)
    c.rect(x + 2, y + 1.5, 6.5, 6.5, fill=AMBER, shape=MSO_SHAPE.OVAL); c.text(x + 2, y + 1.5, 6.5, 6.5, str(num), size=12, color=DEEP, bold=True, align='c', anchor='m')
    c.text(x + 10.5, y, w - 12, 9.5, title, size=15, color=WHITE, bold=True, anchor='m')
def card(x, y, w, h): c.rect(x, y, w, h, fill=WHITE, line=LINE)

# ---------------- row 1: dashboard + logic ----------------
y1 = 106; h1 = 122
bar(12, y1, 160, 1, 'LIVE MATLAB DASHBOARD: change any sensor, the panels react'); card(12, y1 + 9.5, 160, h1 - 9.5)
pc, pw, ph = c.pic(os.path.join(RES, 'dashboard_tab_angle_output.png'), 14.5, y1 + 12, w=155, border=LINE)
for n, (fx, fy) in enumerate([(0.272, 0.30), (0.56, 0.33), (0.50, 0.70), (0.64, 0.085)], 1):
    cx = 14.5 + fx * pw; cy = y1 + 12 + fy * ph; c.rect(cx - 4.5, cy - 4.5, 9, 9, fill=AMBER, line=WHITE, lw=1.5, shape=MSO_SHAPE.OVAL); c.text(cx - 4.5, cy - 4.5, 9, 9, str(n), size=14, color=DEEP, bold=True, align='c', anchor='m')
ly = y1 + 12 + ph + 2
c.text(15, ly, 154, 26, [[('1 ', {'bold': True, 'color': AMBER}), ('Seven readings from six real devices: slider or typed number, tagged MANUAL or AUTO.   ', {}), ('2 ', {'bold': True, 'color': AMBER}), ('Live canopy: the blue panels tilt.', {})],
                          [('3 ', {'bold': True, 'color': AMBER}), ('The decision, in plain words.   ', {}), ('4 ', {'bold': True, 'color': AMBER}), ('Day graphs: sensors, angle, electricity, crop light, accuracy. Each graph has a one-line explanation.', {})]], size=11.5, color=INK, spacing=2)

bar(177, y1, 108, 2, 'HOW IT DECIDES'); card(177, y1 + 9.5, 108, 54)
pc, fw, fh = c.pic(os.path.join(IMG2, 'poster_23.png'), 179, y1 + 12, h=49)
c.text(179 + fw + 3, y1 + 12, 108 - fw - 8, 50, [[('Safety first', {'bold': True, 'color': RED})], 'Wind 15 m/s or more: stow at 90 deg', 'Rain: 3 deg, fill the tank', 'Night: park at 15 deg', [('Otherwise', {'bold': True, 'color': GREEN})], 'Best of 15-60 deg for 1/2 electricity + 1/2 crop light; more shade if hot and dry'], size=10.5, spacing=1, line=0.93)
bar(177, y1 + 66, 108, 3, 'THE SYSTEM', col=NAVY); card(177, y1 + 75.5, 108, h1 - 75.5)
pc, aw, ah = c.pic(os.path.join(IMG2, 'poster_19.png'), 177 + (108 - (h1 - 79.5) * 1.6696) / 2, y1 + 77.5, h=h1 - 79.5)

# ---------------- row 2: sensors + accuracy ----------------
y2 = 232; h2 = 88
bar(12, y2, 133, 4, 'SIX SENSORS = SIX REAL DEVICES'); card(12, y2 + 9.5, 133, h2 - 9.5)
sens = [('Apogee SP-110', 'pyranometer: sunlight', '0-2000 W/m2, +-5 %', AMBER), ('Apogee SQ-110', 'PAR: light plants use', '0-4000 umol/m2/s, +-5 %', GREEN), ('DHT11', 'air temperature and humidity', '0-50 C +-2 C | 20-90 % +-5 %', RED),
        ('DFRobot SEN0193', 'soil moisture (capacitive)', '1.2-2.5 V analog', TEAL), ('YL-83 / FC-37', 'rain plate + LM393', 'wet / dry, digital', NAVY), ('Adafruit 1733', 'cup anemometer: wind', '0-32.4 m/s, +-1 m/s', 'B5651D')]
for i, (nm, what, spec, col) in enumerate(sens):
    cx = 14 + (i % 2) * 65.5; cy = y2 + 12 + (i // 2) * 21
    c.rect(cx, cy, 64, 19.5, fill=LIGHT, line=LINE, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.12); c.rect(cx, cy, 2.8, 19.5, fill=col)
    c.text(cx + 5, cy + 1, 58, 18.5, [[(nm, {'bold': True, 'size': 13, 'color': NAVY})], [(what, {'size': 10.5, 'color': INK})], [(spec, {'size': 10, 'color': MUTED})]], line=0.95)
c.rect(14, y2 + 76, 129, 10.5, fill=PALEGREEN, line=GREEN, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.2)
c.text(16, y2 + 76, 125, 10.5, [[('Panels: ', {'bold': True, 'color': GREEN}), ('8 x JinkoSolar Tiger Pro JKM550M-72HL4-V, 550 Wp, 40.90 V, 13.45 A, 21.33 %, 2274 x 1134 mm (datasheet on file)', {})]], size=10.5, anchor='m', line=0.95)

bar(150, y2, 135, 5, 'ACCURACY: WHAT WE OBTAINED'); card(150, y2 + 9.5, 135, h2 - 9.5)
pc, aw2, ah2 = c.pic(os.path.join(IMG2, 'poster_accuracy.png'), 151.5, y2 + 11, w=132)
c.text(152, y2 + 11 + ah2 + 1, 131, h2 - ah2 - 12, [[('Our six-sensor controller: 99.6 %', {'bold': True, 'color': GREEN}), (' of the best possible score, 4.8 deg from the best angle. Fixed 45 deg: 91.2 % (16.3 deg). Sun tracking: 84.0 %. Fixed 15 deg: 80.0 %. ', {}), ('864 noisy cases, simulation.', {'italic': True, 'color': MUTED})]], size=11, line=0.95)

# ---------------- row 3: trust, proof, cost ----------------
y3 = 324; h3 = 62
bar(12, y3, 98, 6, 'CAN YOU TRUST THE SUNLIGHT?'); card(12, y3 + 9.5, 98, h3 - 9.5)
pc, tw, th = c.pic(os.path.join(IMG2, 'poster_trust.png'), 13.5 + 7, y3 + 11, h=36)
c.text(14, y3 + 11 + 36.5, 94, 14, [[('Dashboard Clear day 6502 Wh/m2', {'bold': True, 'color': GREEN}), (' vs NASA POWER 6539 and PVGIS 6337. Plant-light share 0.444 vs 0.45. A check against satellite data, not a roof sensor.', {})]], size=10.5, line=0.95)

bar(114, y3, 83, 7, 'PROOF YOU CAN OPEN', col=NAVY); card(114, y3 + 9.5, 83, h3 - 9.5)
proof = ['7 sensor and panel datasheets, downloaded', 'NASA POWER + PVGIS sunlight data', 'Model vs data figure and numbers', 'Accuracy test file (864 cases)', 'SHA-256 checksum of every proof file', 'Evidence Book (Word) for the judges', 'Code and results on GitHub']
c.text(116, y3 + 11, 79, h3 - 12, [[('✓  ', {'bold': True, 'color': GREEN}), (t, {})] for t in proof], size=11.5, spacing=2.2, line=0.95)

bar(201, y3, 84, 8, 'IF IT WERE REAL: COST (INR)', col=AMBER); card(201, y3 + 9.5, 84, h3 - 9.5)
rows = [('Research-grade sensing kit', '67,600'), ('Low-cost sensing kit', '13,100'), ('8 panels, 4.4 kWp (assumed)', '70,000'), ('This simulation', '0')]
for i, (a, bb) in enumerate(rows):
    yy = y3 + 12 + i * 9.2; c.rect(203, yy, 80, 8, fill=LIGHT if i % 2 == 0 else WHITE); c.text(205, yy, 55, 8, a, size=11, anchor='m', color=INK); c.text(255, yy, 27, 8, bb, size=12, bold=True, anchor='m', align='r', color=GREEN if i == 3 else NAVY)
c.text(203, y3 + 12 + 4 * 9.2 + 0.5, 80, 9, 'Estimates, not quotes. Sensors: 2 Apogee ~INR 56,000, anemometer 6,500, DHT11 + soil + rain 700, ESP32, ADC, wiring.', size=9.5, color=MUTED, italic=True, line=0.92)

# ---------------- footer ----------------
y4 = 390
c.rect(12, y4, 273, 26, fill=DEEP, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.1)
c.text(16, y4 + 1.5, 142, 23, [[('NEXT  ', {'bold': True, 'color': SUN, 'size': 12.5}), ('Real sensors and one month of logged data  |  wind-tunnel or CFD run to settle the storm stow  |  crop-light and yield measurement  |  paper submission', {'color': WHITE, 'size': 11})],
                                [('HONEST LIMITS  ', {'bold': True, 'color': SUN, 'size': 12.5}), ('Simulation only. Sensor readings are generated or typed, not measured. Accuracy is against the controller\'s own goal, not crop yield. Prices are estimates.', {'color': 'D9E4F2', 'size': 11})]], spacing=3, line=0.95)
pc, sw, sh_ = c.pic(os.path.join(IMG2, 'poster_49.png'), 160, y4 + 5, w=72)
qp = os.path.join(HERE, '_img2', 'qr_github.png'); qrcode.make('https://github.com/thanwin19/agrovoltaic-canopy-srmc').save(qp)
c.rect(257, y4 + 2, 24, 22, fill=WHITE, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.08); c.pic(qp, 259, y4 + 3, w=20); c.text(236, y4 + 4, 20, 18, 'Scan for code and proof', size=9.5, color=SUN, bold=True, align='r', anchor='m', line=0.9)
out = os.path.join(HERE, 'Review0_Poster_A3.pptx'); p.save(out); print('saved', out)
