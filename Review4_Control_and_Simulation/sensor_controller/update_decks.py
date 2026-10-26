"""Retitle the review decks and add the six-sensor-controller slides.   python update_decks.py
Title: Agrovoltaic Canopy for Protection and Sustainable Farming.  Safe to re-run (slides already added are skipped by title)."""
import os, re, shutil, csv, json
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', '..')); RES = os.path.join(HERE, 'results')
T = 'Agrovoltaic Canopy for Protection and Sustainable Farming'
GREEN = RGBColor(0x1f, 0x4d, 0x2b); INK = RGBColor(0x22, 0x26, 0x22); GREY = RGBColor(0x66, 0x6b, 0x66); WHITE = RGBColor(255, 255, 255); LIME = RGBColor(0x72, 0xb8, 0x30)
acc = {r['strategy']: r for r in csv.DictReader(open(os.path.join(RES, 'accuracy_table.csv'), encoding='utf-8'))} if False else None
accj = json.load(open(os.path.join(RES, 'accuracy_summary.json')))['results']
# ---------- figures into Review4 results ----------
fd = os.path.join(ROOT, 'Review4_Control_and_Simulation', 'results', 'figures'); os.makedirs(fd, exist_ok=True)
for f in ['fig_accuracy_both_goals.png', 'fig_tilt_day_April_clear.png', 'fig_soil_stress_effect.png', 'fig_noise_fault.png', 'fig_yield_money.png', 'fig_matlab_accuracy.png', 'fig_matlab_angles.png', 'fig_irrigation_probe_vs_timer.png']: shutil.copy(os.path.join(RES, f), os.path.join(fd, f))
td = os.path.join(ROOT, 'Review4_Control_and_Simulation', 'results', 'tables'); shutil.copy(os.path.join(RES, 'accuracy_table.csv'), os.path.join(td, 'T9_sensor_controller_accuracy.csv')); shutil.copy(os.path.join(RES, 'angles_by_hour_v2.csv'), os.path.join(td, 'T10_sensor_controller_angles_by_hour.csv'))
for _a, _b in [('T11_accuracy_v2.csv', 'T11_accuracy_v2.csv'), ('T12_noise_sweep.csv', 'T12_noise_sweep.csv'), ('T13_fault_test.csv', 'T13_fault_test.csv'), ('T14_yield_and_money.csv', 'T14_yield_and_money.csv'), ('accuracy_matlab.csv', 'T15_accuracy_matlab.csv'), ('T16_irrigation_probe_vs_timer.csv', 'T16_irrigation_probe_vs_timer.csv')]: shutil.copy(os.path.join(RES, _a), os.path.join(td, _b))
sd = os.path.join(ROOT, 'Review4_Control_and_Simulation', 'results', 'simulink'); os.makedirs(sd, exist_ok=True)
for f in os.listdir(os.path.join(RES, 'simulink')): shutil.copy(os.path.join(RES, 'simulink', f), os.path.join(sd, f))
shutil.copy(os.path.join(RES, 'crosscheck_sc_matlab_vs_js.txt'), os.path.join(ROOT, 'Review4_Control_and_Simulation', 'results', 'crosscheck_sensor_controller_matlab_vs_js.txt'))
# ---------- helpers ----------
def replace_in_frame(tf, pairs):
    n = 0
    for para in tf.paragraphs:
        tx = ''.join(r.text for r in para.runs)
        new = tx
        for a, b in pairs: new = new.replace(a, b)
        if new != tx and para.runs:
            para.runs[0].text = new
            for r in para.runs[1:]: r.text = ''
            n += 1
    return n
def retitle(prs, pairs):
    n = 0
    for s in prs.slides:
        for sh in s.shapes:
            if sh.has_text_frame: n += replace_in_frame(sh.text_frame, pairs)
            if getattr(sh, 'has_table', False) and sh.has_table:
                for r in sh.table.rows:
                    for c in r.cells: n += replace_in_frame(c.text_frame, pairs)
    return n
def titles(prs): return [next((sh.text_frame.text for sh in s.shapes if sh.has_text_frame and sh.text_frame.text.strip()), '') for s in prs.slides]
def has_slide(prs, title): return any(title in t for t in titles(prs))
def text(s, x, y, w, h, items, size=19, color=INK, bold=False, bullet=True, space=6):
    tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h)); tf = tb.text_frame; tf.word_wrap = True
    for i, it in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph(); r = p.add_run(); r.text = ('• ' if bullet else '') + it; r.font.size = Pt(size); r.font.bold = bold; r.font.color.rgb = color; r.font.name = 'Calibri'; p.space_after = Pt(space)
    return tb
def pic(s, path, x, y, w, h):
    im = Image.open(path); iw, ih = im.size; sc = min(w / iw, h / ih); pw, ph = iw * sc, ih * sc
    s.shapes.add_picture(path, Inches(x + (w - pw) / 2), Inches(y), Inches(pw), Inches(ph)); return pw, ph
def add_slide(prs, title, footer, after, body=None, pics=None, table=None, notes='', size=19):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    bar = s.shapes.add_shape(1, 0, 0, prs.slide_width, Inches(.95)); bar.fill.solid(); bar.fill.fore_color.rgb = GREEN; bar.line.fill.background()
    text(s, .45, .12, 12.4, .75, [title], 28, WHITE, True, False)
    text(s, .45, 7.08, 12.4, .3, [footer], 10, GREY, False, False)
    if body: text(s, .5, 1.15, pics and 5.9 or 12.3, 5.8, body, size)
    if table:
        head, rows = table; shp = s.shapes.add_table(len(rows) + 1, len(head), Inches(.5), Inches(1.2), Inches(12.3), Inches(.45 * (len(rows) + 1))); tb = shp.table
        for j, h in enumerate(head):
            c = tb.cell(0, j); c.text = h; c.fill.solid(); c.fill.fore_color.rgb = LIME
            for r in c.text_frame.paragraphs[0].runs: r.font.size = Pt(14); r.font.bold = True; r.font.color.rgb = INK
        for i, row in enumerate(rows, 1):
            for j, v in enumerate(row):
                c = tb.cell(i, j); c.text = str(v)
                for r in c.text_frame.paragraphs[0].runs: r.font.size = Pt(13)
    if pics:
        for (path, x, y, w, h) in pics: pic(s, path, x, y, w, h)
    if notes: s.notes_slide.notes_text_frame.text = notes
    lst = prs.slides._sldIdLst; el = lst[-1]; lst.remove(el); lst.insert(after, el)      # move to position 'after'
    return s
def renumber(prs, tag):
    for i, s in enumerate(prs.slides, 1):
        for sh in s.shapes:
            if sh.has_text_frame and sh.text_frame.text.startswith(tag) and '|' in sh.text_frame.text:
                for para in sh.text_frame.paragraphs:
                    tx = ''.join(r.text for r in para.runs)
                    new = re.sub(r'\|\s*\d+\s*$', '| %d' % i, tx)
                    if new != tx: para.runs[0].text = new; [setattr(r, 'text', '') for r in para.runs[1:]]
BASE = [('SRMC wire-driven agrivoltaic canopy, TCE Madurai', T + ', TCE Madurai'), ('SRMC: wire-driven agrivoltaic canopy', T), ('Project: SRMC - Soil Regeneration Microclimatic Chamber (SRMC-DT controller)', 'Project: ' + T + ' (six-sensor controller)')]
def open_(rel): return Presentation(os.path.join(ROOT, rel))
def save(prs, rel): prs.save(os.path.join(ROOT, rel))
acc_rows = [[r['strategy'], '%.1f' % r['pv_index_pct'], '%.1f' % r['crop_index_pct'], '%.1f' % r['J_efficiency_pct']] for r in accj]
# ================= Review4 (R6 control) =================
rel = 'Review4_Control_and_Simulation/ppt/Review4_Control_and_Simulation.pptx'; prs = open_(rel); retitle(prs, BASE)
retitle(prs, [('SRMC-DT: sensor-driven tilt control that co-optimises energy and crops', 'Six-sensor controller: pyranometer, PAR, DHT11, soil moisture, rain sensor and anemometer tilt the panels to co-optimise electricity and crop light'),
              ('Hourly decisions at 0.5 deg resolution; flat mode in rain; wind stow', 'A decision at every step, 0.5 deg resolution; flat roof (3 deg) in rain; night park; extra shade in heat or dry soil'),
              ('Priority: wind stow (> 15 m/s -> 90 deg) > rain (>= 1 mm/h -> 3 deg) > night park (15 deg) > scheduled tilt angle.', 'Priority: anemometer wind stow (15 m/s: 90 deg) > rain sensor (3 deg flat roof) > night park (15 deg) > six-sensor optimiser.'),
              ('The controller also protects the structure: stow in wind, flat sealed roof in rain.', 'The controller protects the crop and the structure: flat sealed roof in rain, more shade in heat or dry soil. The anemometer stows the panels edge-on at 90 deg in a storm (15 m/s, resume below 12 m/s).')])
FOOT = 'R6 Control  |  ' + T + ', TCE Madurai  |  0'
if not has_slide(prs, 'Six-sensor controller: what each sensor does'):
    add_slide(prs, 'Six-sensor controller: what each sensor does', FOOT, 2, body=[
        'Pyranometer: how much sun there is. Below 20 W/m2 = night, park at 15 deg.', 'PAR sensor under the panels: how much light the crop really gets. It corrects the model (PAR divided by pyranometer).',
        'DHT11: air temperature and humidity give VPD. Hot, dry air = plant stress = accept more shade.', 'Soil moisture: below 20 % = dry. More shade, drip irrigation ON.', 'Rain sensor: wet = flat roof at 3 deg, water to the gutter and cistern.',
        'Anemometer: wind at or above 15 m/s (54 km/h) = storm: panels edge-on at 90 deg; resume below 12 m/s.',
        'Decision: try every angle 15 to 60 deg in 0.5 deg steps and pick the best combined score J = 50 % electricity + 50 % crop light value. Keep the angle unless the gain is above 2 % (protects the motor).'], size=18,
        notes='Say it in one sentence: keep just enough light for the crop and give the rest to the panels. The weight 50/50 is a setting; the twin has a slider. The PAR correction means: if the PAR sensor reads less light than the model predicts (dirt, cloud pattern), the optimiser scales the crop light by that ratio (limited to 0.7 to 1.3).')
    add_slide(prs, 'How accurate is the control? Year-long test', FOOT, 3, table=(['Strategy', 'Electricity, % of best', 'Crop light value, % of best', 'Combined score, % of best'], acc_rows),
              pics=[(os.path.join(RES, 'fig_accuracy_both_goals.png'), 1.2, 4.6, 10.9, 2.4)],
              notes='Test (calm to moderate wind; wind stow is checked in Simulink and in the MATLAB cross-check): 12 representative days x 3 sky states x 2 soil states x 14 daylight hours = 864 cases. Sensors = truth plus noise (pyranometer 5 %, PAR 5 %, DHT11 +-2 C and +-5 % RH, soil +-3 %). 100 % = perfect-knowledge optimum of the same combined score. The score is the controller own objective, so it is not an independent measure of crop yield; the yield and money results come from the hourly-plan runs in T1. Fixed 15 deg gives the most electricity but only 33 % of the crop light value.')
    add_slide(prs, 'Tilt through the day, and the effect of dry soil', FOOT, 4, pics=[(os.path.join(RES, 'fig_tilt_day_April_clear.png'), .4, 1.2, 6.2, 4.6), (os.path.join(RES, 'fig_soil_stress_effect.png'), 6.7, 1.2, 6.2, 4.6)],
              body=None, notes='Left: October clear day (crop in season), tilt chosen by the six-sensor controller with noisy sensors follows the perfect-knowledge optimum; the monthly plan is up to 15 degrees away from the best angle (tilt error 9.5 deg against 4.8 deg). Right: the same day with dry soil (15 %): the controller accepts more shade because dry soil lowers the light the crop needs.')
    add_slide(prs, 'Simulink: six-sensor controller on a test day', FOOT, 5, pics=[(os.path.join(sd, 'srmc_sensor_controller_diagram.png'), .4, 1.2, 12.5, 1.9), (os.path.join(sd, 'sensor_controller_day.png'), 3.0, 3.2, 7.3, 3.8)],
              notes='Block diagram: sensors (From Workspace) to the controller block (same rule as the twin) with a unit delay feeding the previous angle back, 0.5 deg encoder quantiser. Test day 16 April: cloud 11:00 to 11:30, rain 14:00 to 15:00 (flat 3 deg), soil dries to 17 % after 12:00.')
    add_slide(prs, 'MATLAB and the web twin make the same decisions', FOOT, 6, body=[
        '40 random sensor states (sun, cloud, DHT11, soil, rain, wind, previous angle) run through MATLAB (srmc_sensor_controller.m) and through the JavaScript twin.', 'Result: same mode in 40 of 40 cases, identical angle in 40 of 40 (0.0 deg difference).',
        'Hysteresis (2 % of the score) stops the panels hunting; the median of 5 readings and a PAR fault guard keep the decisions accurate with noisy or faulty sensors (see the Accuracy slides).', 'Files: matlab/srmc_sc_crosscheck.m, results/crosscheck_sensor_controller_matlab_vs_js.txt.'], size=20)
    add_slide(prs, 'Robust to noisy and faulty sensors', FOOT, 4, pics=[(os.path.join(RES, 'fig_noise_fault.png'), .6, 1.3, 12.1, 4.6)], body=None, notes='v1 takes one reading per decision. v2 takes the median of 5 readings per channel and ignores a PAR sensor that reads less than half or more than 1.6 times what the model predicts. At 3 times the base noise the combined score is 98.5 percent for v1 and 99.1 percent for v2. With a dirty, reflecting or dead PAR sensor, v1 drops to 97.4 to 98.7 percent and v2 stays at 99.6 percent.')
    add_slide(prs, 'Yield and rupees (engine model, per hectare per year)', FOOT, 5, pics=[(os.path.join(RES, 'fig_yield_money.png'), .4, 1.2, 12.5, 4.3)], body=None, notes='Each strategy hourly angles (clear-sky, normal soil) run through the engine crop, water and economics model. The six-sensor controller gives 242 kWh/m2 and INR 55.7 lakh in total, against 238 and 55.0 for the monthly plan and 233 and 52.5 for a fixed 45 degree panel. Crop income is INR 2.2 lakh against 2.5 (plan) and 1.6 (fixed 45). A PV-only panel still earns most rupees (68.0 lakh) but destroys the crop income. Prices are assumptions.')
    add_slide(prs, 'Accuracy measured in MATLAB', FOOT, 6, body=['142 test cases (4 months x 3 skies x 2 soils x daylight hours) with the same noisy sensor readings as the web twin.', 'MATLAB repeats the decisions with its own controller and scores every angle with its own physics against the best possible angle.', 'Result: combined score 99.5 % of the best, electricity 83 %, crop light value 99 %, tilt error 3.4 deg. MATLAB and the twin chose the identical angle in 140 of 142 cases (the other two differ by up to 6 deg where the score is flat).'], pics=[(os.path.join(RES, 'fig_matlab_accuracy.png'), 6.3, 1.3, 6.7, 3.0)], size=17, notes='Files: matlab/srmc_sc_accuracy.m, results/accuracy_matlab.csv and .json, figures fig_matlab_accuracy.png, fig_matlab_angles.png.')
    add_slide(prs, 'Controller safety: fallbacks, move limits, wear count', FOOT, 7, body=[
        'Soil probe fault (no reading, out of range, jump above 40 points, stuck for 3 daytime hours): the controller switches to the water-balance model value.', 'Rain sensor fault: wet for 30 minutes in dry sunny air = ignored (panels keep tracking); dry in real rain with a forecast, RH 90 % and a dark sky = flat roof anyway.',
        'Move limits: at least 120 s between moves, at most 12 moves an hour, at most 900 deg of travel a day. Rain flat roof, storm stow and night park are never blocked.', 'Wear count: moves, degrees of travel, metres of drive wire, drum turns, reversals. A clear day: about 64 moves, 330 deg, 2.5 m of wire, 6.5 drum turns.',
        'Two hours of 1-minute cloud flicker: 92 moves with no protection, 14 with the 2 % hysteresis, 24 with limits but no hysteresis. 8 of 8 tests pass.'], size=17, notes='Files: results/safety_tests.md, safety_flicker.csv, code in sensor_controller.js (makeSafe). Tested in simulation only.')
    add_slide(prs, 'Water link: the soil probe decides when irrigation runs', FOOT, 8, pics=[(os.path.join(RES, 'fig_irrigation_probe_vs_timer.png'), .3, 3.2, 12.7, 3.8)], body=None, notes='Probe-triggered irrigation uses 5,372 m3 per hectare a year against 5,641 m3 for a timer (every 4 days, fixed depth): 4.8 % saved, 0 water-stress days instead of 20. A probe stuck dry without a fallback wastes about 46,500 m3; stuck wet without a fallback kills the yield (0.155); with the fallback (stuck 3 days or dead: run the timer) both stay at timer level. Same daily water balance as the twin; simulated.')
    add_slide(prs, 'Water link results (per hectare per year)', FOOT, 9, table=(['Strategy', 'Water m3', 'Stress days', 'Relative yield', 'Saved vs timer'], [[r['name'], r['applied_m3_ha'], r['stress_days'], r['relative_yield_from_water'], '%s %%' % r['water_saved_vs_timer_pct']] for r in __import__('json').load(open(os.path.join(RES, 'irrigation_study.json')))['rows']]))
renumber(prs, 'R6 Control'); save(prs, rel)
# ================= Review3 (R5 twin) =================
rel = 'Review3_Digital_Twin/ppt/Review3_Digital_Twin.pptx'; prs = open_(rel); retitle(prs, BASE); FOOT = 'R5 Digital twin  |  ' + T + ', TCE Madurai  |  0'
if not has_slide(prs, 'The twin runs the six-sensor controller'):
    add_slide(prs, 'The twin runs the six-sensor controller', FOOT, 2, body=[
        'Open the twin: the six-sensor controller is ON by default. The panels follow the rule: rain = flat roof, night = park, otherwise the best mix of electricity and crop light.', 'Sensor card on the 3D tab: pyranometer, PAR under the canopy, DHT11 temperature and humidity (VPD), soil moisture, rain sensor, anemometer.',
        'Controller panel: sliders for cloud cover, DHT11 temperature and humidity, soil moisture; the rain button is the rain sensor. A decision trace explains each tilt.', 'Year-long test: 99.6 % of the best combined score with noisy sensors (82 % of the best electricity, 98 % of the best crop light value, tilt error 4.8 deg).', 'The sensor values here are simulated; Review 0 shows the real ESP board feeding DHT11, soil and rain readings to MATLAB.'], size=18,
        pics=[(os.path.join(ROOT, 'Review4_Control_and_Simulation', 'results', 'figures', 'fig_accuracy_both_goals.png'), 6.6, 1.3, 6.4, 2.6)], notes='Live demo order: 3D tab, play day, then drag cloud cover up, then temperature 40 C and humidity 25 %, then soil 15 %, then press Rain mode.')
renumber(prs, 'R5 Digital twin'); save(prs, rel)
# ================= Review1 (R3 design) =================
rel = 'Review1_Design_and_CAD/ppt/Review1_Design_and_CAD.pptx'; prs = open_(rel)
retitle(prs, BASE + [('SS316 4 mm 7x7', 'SS316 6 mm 7x19'), ('4 mm 7x7', '6 mm 7x19'), ('Turnbuckle M16 SS316', 'Turnbuckle M24 SS316 (>= 72 kN)'), ('Ground anchor block', 'Ground anchor (screw/rock, or 1.6 m3 buried concrete)')])
retitle(prs, [('Rain: panels settle at 3 deg and seal; wind: 90 deg stow.', 'Rain: panels settle at 3 deg and seal; heat or dry soil: more shade. Anemometer: wind stow at 15 m/s, using a 45 deg offset lever arm.')])
def replace_pic(slide, shape, path):          # swap a picture for a new image, keeping the box (aspect ratio preserved)
    l, t, w, h = shape.left, shape.top, shape.width, shape.height; shape._element.getparent().remove(shape._element)
    im = Image.open(path); iw, ih = im.size; sc = min(w / iw, h / ih); pw, ph = int(iw * sc), int(ih * sc)
    slide.shapes.add_picture(path, l + (w - pw) // 2, t, pw, ph)
R1 = os.path.join(ROOT, 'Review1_Design_and_CAD', 'results'); cadp = lambda n: os.path.join(R1, 'cad_drawings', 'SRMC_feasible_%s.png' % n); mechp = lambda n: os.path.join(R1, 'mechanism', n)
def pics_of(slide): return sorted([sh for sh in slide.shapes if sh.shape_type == 13], key=lambda x: (x.left, x.top))
sl = list(prs.slides)
if not has_slide(prs, 'Hardware changes after the strength check'):
    for idx, paths in [(5, [cadp('plan')]), (6, [cadp('elevation')]), (7, [cadp('section'), cadp('wire_drive')]), (8, [mechp('mechanism_closeup.gif')]), (10, [mechp('mechanism_tilt.gif')])]:
        for shp, pth in zip(pics_of(sl[idx]), paths): replace_pic(sl[idx], shp, pth)
retitle(prs, [('Lever arm SS316 150-250 mm', 'Lever arm SS316 0.44 m, 45 deg offset'), ('Sensors: pyranometer x1 reference + 4 zone, rain gauge, T/RH, soil moisture x4, panel IR', 'Sensors: pyranometer, PAR, DHT11, soil, rain, cup anemometer (wind)'), ('Gearmotor winch, IP66, >= 3 kN, encoder 0.5 deg', 'Gearmotor winch, IP66, >= 10 kN, encoder 0.5 deg')])
FOOT = 'R3 Design  |  ' + T + ', TCE Madurai  |  0'
if not has_slide(prs, 'Hardware changes after the strength check'):
    add_slide(prs, 'Hardware changes after the strength check', FOOT, 12, table=(['Part', 'First parts list', 'Final design', 'Why'], [
        ['Drive wire', 'SS316 4 mm', 'SS316 6 mm 7x19', 'wire load 4.1 kN at 54 km/h wind; 4 mm allows 4.6 kN (0.9, too tight)'], ['Motor winch', '3 kN', '10 kN, about 0.25 kW', '3 kN is at its limit near 45 km/h wind and 1.4x over at 54 km/h'],
        ['Turnbuckle (stay)', 'M16 SS316', 'M24 SS316, >= 72 kN', 'stay pull 36 kN'], ['Ground anchor', 'block 1.0 x 0.8 x 0.35 m (6.6 kN)', 'screw/rock anchor or 1.6 m3 concrete', 'each stay lifts about 26 kN'],
        ['Lever arm', 'plain arm: no lever at 90 deg', '45 deg offset arm', 'needed for the 90 deg wind stow'], ['Wind sensor', 'none', 'cup anemometer on a mast', 'storm stow at 15 m/s'],
        ['Carrier rope 16 mm', 'ok (0.37)', 'unchanged', 'uses 37 % of allowed load'], ['Pivot tube 114.3 x 4', 'ok (0.76)', 'unchanged', 'tube length 4.7 m between supports'], ['Column RHS 200 x 200 x 6', 'ok (0.05)', 'unchanged', 'very strong']]),
        notes='All loads at 140 km/h basic wind speed (IS 875-3), panels held, screening level. The motor numbers use a flat-plate coefficient of 1.0 and a 5 cm centre-of-mass offset. Weights, costs and installation steps are in documents/SRMC_8Panel_Guide_and_Cost.docx.')
    add_slide(prs, '8-panel set (4.4 kWp): weights and cost', FOOT, 13, body=[
        '8 x 550 Wp monocrystalline modules (27.5 kg each, 220 kg) in 2 rows of 4 on a 5 m x 5 m bay; 4 columns, 2 tubes, 2 carrier ropes, 4 stays, one winch.', 'SS316 rope weights from supplier listings: 16 mm = 0.975 kg/m, 12 mm = 0.549, 10 mm = 0.381, 8 mm = 0.244; rule 0.00381 x d x d kg/m.',
        'Above-ground weight about 1.6 t; concrete about 20 t with buried anchors (less with screw anchors).', 'Indicative cost INR 6 to 10 lakh (mid about 7 lakh, about INR 1.6 lakh per kWp). Price rates are assumptions; replace them with quotes.', 'Files: documents/SRMC_8Panel_Guide_and_Cost.docx, SRMC_Component_Strength_Table.docx, 8panel_BOM.csv.'], size=18)
renumber(prs, 'R3 Design'); save(prs, rel)
# ================= Review5 (R7 final) =================
rel = 'Review5_Economics_and_Final/ppt/Review5_Economics_and_Final.pptx'; prs = open_(rel); retitle(prs, BASE); FOOT = 'R7 Economics and final  |  ' + T + ', TCE Madurai  |  0'
if not has_slide(prs, 'Both goals together: what the sensors achieve'):
    add_slide(prs, 'Both goals together: what the sensors achieve', FOOT, 7, body=[
        'Six sensors decide every tilt. Year-long test with noisy sensors: 99.6 % of the best combined score, tilt error 4.8 deg.', 'Electricity 82 % of the best possible, crop light value 98 % of the best possible. A PV-only panel gets 99 % of the electricity but only 45 % of the crop light value.',
        'Against the monthly plan (98.8 %) and a fixed 45 deg panel (91.2 %) the sensor controller is closer to the optimum.', 'Money results stay assumption-based (tariff INR 3/kWh, farmer share 30 %). Our electricity costs about INR 6 to 7 per kWh with interest, near the Tamil Nadu industrial grid charge (INR 7.50), above big solar farms (INR 2 to 2.6).'], size=18,
        pics=[(os.path.join(ROOT, 'Review4_Control_and_Simulation', 'results', 'figures', 'fig_accuracy_both_goals.png'), 6.6, 1.3, 6.4, 2.6)], notes='The combined score is the controller own objective. Independent checks (PVGIS, Blender, MATLAB) validate the solar and shadow parts, not the crop or money parts.')
renumber(prs, 'R7 Economics and final'); save(prs, rel)
# ================= Review0 + Review2 + poster: retitle only =================
for rel in ['Review0_Prototype_Demo/ppt/Review0_Prototype_Demo.pptx', 'Review0_Prototype_Demo/ppt/Review0_7slides.pptx', 'Review2_Solar_and_Shadow/ppt/Review2_Solar_and_Shadow.pptx']:
    prs = open_(rel); retitle(prs, BASE); save(prs, rel)
print('decks updated')
