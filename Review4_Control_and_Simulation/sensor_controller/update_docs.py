"""Update the final report, viva Q&A, expo playbook, summaries and READMEs for the final title and the six-sensor controller.  python update_docs.py"""
import os, re, copy, shutil, csv, json
from docx import Document
from docx.shared import Inches, Pt
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', '..')); RES = os.path.join(HERE, 'results')
T = 'Agrovoltaic Canopy for Protection and Sustainable Farming'
accj = json.load(open(os.path.join(RES, 'accuracy_summary.json')))['results']; A = {r['strategy']: r for r in accj}
n = A['SRMC-SC (noisy sensors)']; sch = A['Monthly schedule (SRMC-DT)']; f45 = A['Fixed 45 deg']
def backup(path):
    d = os.path.join(os.path.dirname(path), '_before_update'); os.makedirs(d, exist_ok=True); b = os.path.join(d, os.path.basename(path))
    if not os.path.exists(b): shutil.copy(path, b)
    return b
def set_par(p, txt):
    if p.runs:
        p.runs[0].text = txt
        for r in p.runs[1:]: r.text = ''
    else: p.add_run(txt)
def insert_after(par, text='', style=None):
    new = copy.deepcopy(par._p); par._p.addnext(new)
    from docx.text.paragraph import Paragraph
    np_ = Paragraph(new, par._parent)
    for r in list(np_.runs): r._r.getparent().remove(r._r)
    if style: np_.style = style
    if text: np_.add_run(text)
    return np_
# ===================== FINAL REPORT =====================
p = os.path.join(ROOT, 'Review5_Economics_and_Final', 'documents', 'final_report', 'SRMC_Final_Report.docx'); src = backup(p); d = Document(src)
P = d.paragraphs
from PIL import Image as _Img
def swap_inline(dd, idx, path):          # replace a picture of the report with a new one (aspect ratio kept)
    sh = dd.inline_shapes[idx]; rid = sh._inline.graphic.graphicData.pic.blipFill.blip.embed; part = dd.part.related_parts[rid]; part._blob = open(path, 'rb').read(); im = _Img.open(path); sh.height = int(sh.width * im.size[1] / im.size[0])
_cad = os.path.join(ROOT, 'Review1_Design_and_CAD', 'results', 'cad_drawings')
swap_inline(d, 1, os.path.join(_cad, 'SRMC_feasible_plan.png')); swap_inline(d, 2, os.path.join(_cad, 'SRMC_feasible_elevation.png'))
set_par(P[0], T + ': a six-sensor, wire-driven canopy that tilts its panels to optimise crop light and electricity, harvests rain and pays the farmer')
set_par(P[2], 'Final-year project report - computer-based study. Updated 2026-10-25 for the six-sensor controller; every number traces to a file listed in PROOF_INDEX.md.')
set_par(P[4], 'We design and simulate a stainless-steel wire-rope canopy that carries pivoting solar panels 4.5 m above crops. One motor moves a single drive wire so that all panels tilt between 15 and 60 deg, or lie nearly flat (3 deg fall to a gutter) in rain for rain harvesting. Six sensors decide the tilt: a pyranometer, a PAR sensor under the canopy, a DHT11 (temperature and humidity), a soil moisture sensor and a rain sensor. At each step the controller picks the angle with the best combined score (50 % electricity, 50 % crop light value); the PAR reading corrects the model, and hot dry air or dry soil lower the light the crop needs, so the panels give more shade (protection). Rain makes the panels a flat roof that fills a cistern. The electricity is sold to a nearby industry and the farmer receives a monthly share. The study is computational: MATLAB and Simulink models, a browser digital twin, AutoCAD drawings, a bill of materials and ray-traced renders, all driven by one design file. The PV model agrees with PVGIS within +5 %; the shadow model agrees with a 3-D ray tracer to a mean difference of 0.010. In a year-long test with noisy sensors the controller reaches @J@ % of the best possible combined score (@PV@ % of the best electricity and @CR@ % of the best crop light value), against @SCH@ % for the monthly plan and @F45@ % for a fixed 45 deg panel; MATLAB and the web twin make identical decisions. A structural screening shows that 12.5 m bays fail and a 5 m rope grid passes, with a stronger winch, 6 mm drive wire, M24 turnbuckles and larger anchors. Farmer income (about INR 2 lakh per hectare per month) depends on assumed tariff and share, and investor payback is long (about 41 years in the base case).'.replace('@J@', '%.1f' % n['J_efficiency_pct']).replace('@PV@', '%.0f' % n['pv_index_pct']).replace('@CR@', '%.0f' % n['crop_index_pct']).replace('@SCH@', '%.1f' % sch['J_efficiency_pct']).replace('@F45@', '%.1f' % f45['J_efficiency_pct']))
set_par(P[10], 'O4 Develop and test the six-sensor control algorithm, measure how close it gets to the best possible electricity and crop light, and compare it with fixed designs and the monthly plan.')
set_par(P[34], 'Controller (six sensors): rain sensor wet = flat roof 3 deg; pyranometer below 20 W/m2 = night park 15 deg; otherwise try every angle 15-60 deg (5 deg coarse, 0.5 deg fine) and pick the maximum of J = w PV/PVmax + (1-w) crop-value/cropmax (w = 0.5). The PAR reading corrects the modelled crop light (ratio limited to 0.7-1.3); DHT11 vapour-pressure deficit and soil moisture give a stress that lowers the light the crop needs. The angle changes only if the score gain is above 2 %. The hourly monthly plan (SRMC-DT) is kept as the planner and the fallback if a sensor fails. The anemometer adds wind stow: at 15 m/s (54 km/h) or more the panels go edge-on at 90 deg, resuming below 12 m/s.')
set_par(P[47], P[47].text.replace('The SRMC-DT controller', 'The hourly plan (SRMC-DT)'))
set_par(P[76], 'All results are simulation only. There is no field or prototype data, so crop yields, water balance, controller behaviour and economics are not validated. The sensors are simulated (Review 0 uses real DHT11, soil and rain readings on an ESP board).')
set_par(P[81], 'The SRMC-DT note says panels trim flatter to admit light; in this geometry steeper tilt admits more light, and the model follows the physics.')
set_par(P[83], 'A six-sensor, wire-driven canopy with sensor-based tilt and a flat rain mode was modelled consistently in MATLAB, Simulink, a live twin, CAD and ray-traced renders.')
set_par(P[86], 'The six-sensor controller reaches %.1f %% of the best combined score with noisy sensors; compared with a fixed 45 deg tilt it gives more crop light at similar electricity. A PV-only design still earns more rupees at assumed prices.' % n['J_efficiency_pct'])
set_par(P[88], 'Next: build the six-sensor pilot row and log one month of real data, replace assumptions with quotes and datasheets, obtain soil and geotechnical data, add an anemometer for wind stow, use hourly weather, price water and soil benefits, and run a formal prior-art search.')
set_par(P[112], 'Open MATLAB, cd matlab, run srmc_master() and srmc_sensitivity(); srmc_sc_crosscheck() (six-sensor controller, MATLAB vs web twin) and build_simulink_sensor_controller(); structural_check() for the structure. Node: Review4_Control_and_Simulation/sensor_controller/eval_sensor_controller.js (year-long accuracy test).')
set_par(P[114], 'python -m http.server 8765 in the srmc-twin folder, then open http://localhost:8765/Review3_Digital_Twin/results/live_twin/SRMC_Digital_Twin.html for the twin.')
# new section after Figure 14 (para index 63): six-sensor controller
anchor = P[63]; H1 = [x for x in P if x.style.name == 'Heading 1' and x.text.startswith('7 ')][0]
h = H1.insert_paragraph_before('6A Six-sensor controller and its accuracy', style='Heading 1')
def para(txt, style=None): return H1.insert_paragraph_before(txt, style=style)
para('Sensors and rule. Six sensors feed the controller every step: pyranometer (sunlight), PAR sensor under the canopy (light that reaches the crop), DHT11 (temperature and humidity, giving the vapour-pressure deficit), soil moisture and rain. The rule is given in Section 4. The same code runs in the web twin (default controller), in MATLAB (srmc_sensor_controller.m) and in a Simulink model.')
para('Test. 12 representative days x 3 sky states (clear, partly cloudy, overcast) x 2 soil states (26 % and 15 %) x 14 daylight hours = 864 cases. The sensors are the true values plus noise (pyranometer 5 %, PAR 5 %, DHT11 +-2 C and +-5 % RH, soil +-3 %). The reference (100 %) is the same combined score with perfect knowledge and a 0.5 deg search.')
tb = d.add_table(rows=1, cols=4); tb.style = 'Light Grid Accent 1'
for j, hd in enumerate(['Strategy', 'Electricity, % of best', 'Crop light value, % of best', 'Combined score, % of best']): tb.rows[0].cells[j].text = hd
for r in accj:
    c = tb.add_row().cells
    for j, v in enumerate([r['strategy'], '%.1f' % r['pv_index_pct'], '%.1f' % r['crop_index_pct'], '%.1f' % r['J_efficiency_pct']]): c[j].text = v
H1._p.addprevious(tb._tbl)
pp = para('Figure 14a. Both goals: top-right is best (left); combined score (right).'); pp.insert_paragraph_before('').add_run().add_picture(os.path.join(RES, 'fig_accuracy_both_goals.png'), width=Inches(6.2))
pp = para('Figure 14b. Tilt chosen through an October clear day (left, crop in season) and the effect of dry soil (right).'); pp.insert_paragraph_before('').add_run().add_picture(os.path.join(RES, 'fig_tilt_day_April_clear.png'), width=Inches(3.0)).__class__
pp.insert_paragraph_before('').add_run().add_picture(os.path.join(RES, 'fig_soil_stress_effect.png'), width=Inches(3.0))
pp = para('Figure 14c. Simulink six-sensor controller on a test day (cloud 11:00, rain 14:00 to 15:00, dry soil after 12:00).'); pp.insert_paragraph_before('').add_run().add_picture(os.path.join(RES, 'simulink', 'sensor_controller_day.png'), width=Inches(5.6))
pp = para('Figure 14d. Accuracy when the sensors get noisier (left) and with a faulty PAR sensor (right): v1 = one reading, v2 = median of 5 readings + fault guard.'); pp.insert_paragraph_before('').add_run().add_picture(os.path.join(RES, 'fig_noise_fault.png'), width=Inches(6.2))
pp = para('Figure 14e. Yield and rupees per hectare per year when each strategy hourly angles are run through the crop, water and economics model.'); pp.insert_paragraph_before('').add_run().add_picture(os.path.join(RES, 'fig_yield_money.png'), width=Inches(6.2))
pp = para('Figure 14f. The same accuracy test repeated in MATLAB (142 cases, same sensor readings).'); pp.insert_paragraph_before('').add_run().add_picture(os.path.join(RES, 'fig_matlab_accuracy.png'), width=Inches(6.2))
para('Robustness. The controller takes the median of 5 readings per channel and ignores a PAR sensor that reads less than half or more than 1.6 times what the model predicts. At 3 times the base noise the combined score is 98.5 % for a single reading and 99.1 % with the filter; with a dirty, reflecting or dead PAR sensor a single-reading controller falls to 97.4 to 98.7 % while the guarded one stays at 99.6 %. Tilt error against the best angle is 4.8 deg (monthly plan 9.5 deg, fixed 45 deg 16.3 deg).')
para('Yield and rupees. With the hourly angles run through the engine, the six-sensor controller gives 242 kWh/m2 and INR 55.7 lakh per hectare per year (solar plus crop), against 238 and 55.0 for the monthly plan and 233 and 52.5 for a fixed 45 deg panel. Crop net income is INR 2.2 lakh (plan 2.5, fixed 45 deg 1.6). A PV-only panel still earns the most rupees (68.0 lakh) but its crop income is negative. Prices are assumptions.')
para('MATLAB. The test repeated in MATLAB on 142 cases with the same noisy readings gives 99.5 % of the best combined score, electricity 83 %, crop light value 99 % and a tilt error of 3.4 deg; MATLAB and the twin chose the identical angle in 140 of 142 cases.')
para('Reading the results. The controller gets %.0f %% of the best electricity and %.0f %% of the best crop light value; a PV-only fixed 15 deg panel gets 99 %% of the electricity but only 45 %% of the crop light value. The combined score is the controller\'s own objective, so it measures how well the sensors reproduce the optimum, not crop yield; yield and money come from the hourly-plan runs. MATLAB and the web twin gave identical decisions in 40 of 40 random sensor states (results/crosscheck_sensor_controller_matlab_vs_js.txt).' % (n['pv_index_pct'], n['crop_index_pct']))
para('Hardware after the strength check. A 3 kN winch is at its limit near 45 km/h wind (1.4 times over at 54 km/h) and a 4 mm drive wire is too tight; the final design uses a 10 kN winch, a 6 mm SS316 drive wire, a 45 degree offset lever arm and a cup anemometer for the 90 degree storm stow, M24 turnbuckles and anchors sized for 26 kN uplift each (documents/SRMC_Component_Strength_Table.docx).')
pp = para('Figure 14g. Water link: the soil probe decides when irrigation runs (left: water through the year; middle: water saved; right: probe faults with and without the fallback).'); pp.insert_paragraph_before('').add_run().add_picture(os.path.join(RES, 'fig_irrigation_probe_vs_timer.png'), width=Inches(6.4))
para('Safety layer. Soil probe faults (no reading, out of range, a jump above 40 points in an hour, stuck for 3 daytime hours) switch the controller to the water-balance model value; a rain sensor stuck wet in dry sunny air for 30 minutes is ignored, and a dry reading with a rain forecast, RH of 90 % and a dark sky counts as rain. Panel moves are limited to one every 120 s, 12 an hour and 900 deg a day (rain, storm stow and night park are exempt) and the motor wear is counted (moves, degrees, metres of wire, drum turns). A clear day needs about 64 moves, 330 deg of travel, 2.5 m of wire and 6.5 drum turns. Eight simulation tests pass (results/safety_tests.md).')
para('Water link. With the soil probe deciding irrigation the water use is 5,372 m3 per hectare a year against 5,641 m3 for a 4-day timer (4.8 % saved) with no water-stress days instead of 20. A probe that sticks dry wastes about 46,500 m3 and one that sticks wet loses almost all the yield unless the fallback (stuck for 3 days or dead: run the timer schedule) is on; with it both stay at timer level. The simulation uses the same daily water balance as the twin and assumes the borewell supplies the demand when the cistern is empty.')
d.save(p)
# ===================== VIVA Q&A (docx + md) =====================
p = os.path.join(ROOT, 'Review5_Economics_and_Final', 'documents', 'viva_and_expo', 'SRMC_Viva_QA.docx'); src = backup(p); d = Document(src)
qa = [('How do the six sensors decide the tilt?', 'Rain wet: flat roof 3 deg. Pyranometer below 20 W/m2: night park. Otherwise the controller tries every angle from 15 to 60 deg and picks the best combined score of 50 % electricity and 50 % crop light. The PAR sensor corrects the model; DHT11 and soil moisture lower the light the crop needs when it is stressed.'),
      ('How accurate is it?', 'In a year-long test with noisy sensors the controller reaches %.1f %% of the best possible combined score, with %.0f %% of the best electricity and %.0f %% of the best crop light value. The monthly plan reaches %.1f %%, a fixed 45 deg panel %.1f %%. The score is measured against the controller\'s own objective, not against field crop yield.' % (n['J_efficiency_pct'], n['pv_index_pct'], n['crop_index_pct'], sch['J_efficiency_pct'], f45['J_efficiency_pct'])),
      ('Are the sensor readings real?', 'In the twin and the Simulink model they are simulated (sliders and climate data). Review 0 uses real DHT11, soil and rain readings on an ESP board. No pyranometer or PAR data has been measured yet.'),
      ('Why is the PAR sensor needed if there is a pyranometer?', 'The pyranometer measures total sun above the canopy. The PAR sensor measures what reaches the crop. Their ratio tells whether the model matches reality (dirt, clouds, shading error) and corrects it.'),
      ('What protects the crop?', 'Rain: flat roof. Hot dry air (VPD above 1.6 kPa rising to 2.5) or dry soil (below 20 %): the controller accepts more shade. Wind: the anemometer stows the panels at 90 deg at 15 m/s (54 km/h).'),
      ('Why does the controller keep the angle sometimes?', 'A hysteresis of 2 % of the score stops it moving for tiny gains, which protects the motor. A bigger value gives a calmer motor at a small cost in score.'),
      ('What does the soil probe change?', 'It decides when the drip irrigation runs: 5,372 m3 per hectare a year against 5,641 m3 for a timer (4.8 % saved) and no water-stress days instead of 20. A stuck or dead probe falls back to the timer schedule.'),
      ('What if the rain or soil sensor fails?', 'A soil probe that is missing, out of range, jumping or stuck is replaced by the water-balance model value; a rain sensor stuck wet in dry sunny air is ignored for 30 minutes onwards; panel moves are limited to 12 an hour and the motor wear is counted. Tested in 8 simulation tests.'),
      ('Is the motor strong enough?', 'The first parts list (3 kN winch, 4 mm drive wire) was not: its 3 kN winch is 1.4 times overloaded at 54 km/h wind and the 4 mm wire is at 0.9 of its limit. The final design uses a 10 kN winch, a 6 mm wire and a 45 degree offset lever arm, good to 54 km/h with panels held. Capacities are screening estimates.')]
for q, a in qa:
    d.add_paragraph('Q. ' + q).runs[0].bold = True; d.add_paragraph('A. ' + a)
d.save(p)
mdp = os.path.join(ROOT, 'Review5_Economics_and_Final', 'documents', 'viva_and_expo', 'SRMC_Viva_QA.md'); backup(mdp)
with open(mdp, 'a', encoding='utf-8') as f:
    f.write('\n\n## Six-sensor controller (added 2026-10-25)\n\n'); [f.write('**Q. %s**\n\nA. %s\n\n' % (q, a)) for q, a in qa]
# ===================== EXPO PLAYBOOK md + docx =====================
p = os.path.join(ROOT, 'Review5_Economics_and_Final', 'documents', 'viva_and_expo', 'SRMC_Expo_Playbook.docx'); src = backup(p); d = Document(src)
for para_ in d.paragraphs:
    if para_.text.startswith('SRMC expo playbook') or 'SRMC expo' in para_.text: set_par(para_, T + ': expo playbook')
for para_ in d.paragraphs:
    if 'Tick "Use the sensor feedback controller"' in para_.text: set_par(para_, para_.text.replace('Tick "Use the sensor feedback controller". ', 'The six-sensor controller is ON by default (controller panel under the 3D view). ').replace('The twin URL', 'The twin URL'))
d.add_heading('Update 2026-10-25: numbers to quote for the six-sensor controller', 2)
for s in ['Year-long test, noisy sensors: %.1f %% of the best possible combined score (50 %% electricity, 50 %% crop light); %.0f %% of the best electricity; %.0f %% of the best crop light value.' % (n['J_efficiency_pct'], n['pv_index_pct'], n['crop_index_pct']), 'Monthly plan %.1f %%, fixed 45 deg %.1f %%, fixed 15 deg (PV-only) %.1f %%, sun tracking %.1f %%.' % (sch['J_efficiency_pct'], f45['J_efficiency_pct'], A['Fixed 15 deg (PV-max)']['J_efficiency_pct'], A['Sun tracking (E-W)']['J_efficiency_pct']), 'MATLAB and the twin: 40 of 40 identical decisions.', 'Say once: sensor values in the twin are simulated; the pyranometer and PAR sensor have not been measured yet.', 'Where the twin is now: Review3_Digital_Twin/results/live_twin/SRMC_Digital_Twin.html (run python -m http.server 8765 in the srmc-twin folder).']:
    d.add_paragraph(s, style='List Bullet')
d.save(p)
mdp = os.path.join(ROOT, 'Review5_Economics_and_Final', 'documents', 'viva_and_expo', 'SRMC_Expo_Playbook.md'); backup(mdp)
with open(mdp, 'a', encoding='utf-8') as f:
    f.write('\n\n## Update 2026-10-25: numbers to quote for the six-sensor controller\n\n- Year-long test, noisy sensors: %.1f %% of the best possible combined score; %.0f %% of the best electricity; %.0f %% of the best crop light value.\n- Monthly plan %.1f %%, fixed 45 deg %.1f %%, PV-only 15 deg %.1f %%.\n- MATLAB and the twin: 40 of 40 identical decisions.\n- Say once: the sensor values in the twin are simulated, including the anemometer.\n' % (n['J_efficiency_pct'], n['pv_index_pct'], n['crop_index_pct'], sch['J_efficiency_pct'], f45['J_efficiency_pct'], A['Fixed 15 deg (PV-max)']['J_efficiency_pct']))
print('docs updated')
