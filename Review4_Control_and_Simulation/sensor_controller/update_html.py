"""Make the one-page HTML summaries self-contained (images embedded) and update them for the final title and the six-sensor controller.  python update_html.py"""
import os, re, io, base64, json, glob, shutil
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', '..')); RES = os.path.join(HERE, 'results')
T = 'Agrovoltaic Canopy for Protection and Sustainable Farming'
accj = json.load(open(os.path.join(RES, 'accuracy_summary.json')))['results']; A = {r['strategy']: r for r in accj}; n = A['SRMC-SC (noisy sensors)']
# index of images / files in the review folders (+ the new figures)
idx = {}
for f in glob.glob(os.path.join(ROOT, 'Review*', '**', '*'), recursive=True):
    if os.path.isfile(f) and '_before_update' not in f and '_old' not in f: idx.setdefault(os.path.basename(f), f)
for f in glob.glob(os.path.join(RES, '*.png')) + glob.glob(os.path.join(RES, 'simulink', '*.png')): idx[os.path.basename(f)] = f
def data_uri(path, maxw=900):
    ext = os.path.splitext(path)[1].lower()
    if ext == '.gif': return 'data:image/gif;base64,' + base64.b64encode(open(path, 'rb').read()).decode()
    im = Image.open(path).convert('RGB'); im.thumbnail((maxw, maxw * 2)); b = io.BytesIO(); im.save(b, 'JPEG', quality=82); return 'data:image/jpeg;base64,' + base64.b64encode(b.getvalue()).decode()
def selfcontain(html):
    def img(m):
        src = m.group(1)
        if src.startswith('data:'): return m.group(0)
        f = idx.get(os.path.basename(src))
        return 'src="%s"' % data_uri(f) if f else m.group(0)
    return re.sub(r'src="([^"]+)"', img, html)
def relink(html, here_dir):
    def lk(m):
        h = m.group(1)
        if h.startswith(('http', '#', 'data:', 'mailto')): return m.group(0)
        f = idx.get(os.path.basename(h))
        return 'href="%s"' % os.path.relpath(f, here_dir).replace('\\', '/') if f else m.group(0)
    return re.sub(r'href="([^"]+)"', lk, html)
def backup(path):
    d = os.path.join(os.path.dirname(path), '_before_update'); os.makedirs(d, exist_ok=True); b = os.path.join(d, os.path.basename(path))
    if not os.path.exists(b): shutil.copy(path, b)
    return b
def uri(name, w=900): return data_uri(idx[name], w)
table = '<table><tr><th>Strategy</th><th>Electricity, % of best</th><th>Crop light value, % of best</th><th>Combined score, % of best</th></tr>' + ''.join('<tr><td>%s</td><td>%.1f</td><td>%.1f</td><td><b>%.1f</b></td></tr>' % (r['strategy'], r['pv_index_pct'], r['crop_index_pct'], r['J_efficiency_pct']) for r in accj) + '</table>'
ctl_block = ('<h2>The six-sensor controller and how well it works</h2><div class="say">Safety and water: a faulty soil probe, rain sensor or PAR sensor is detected and replaced by a fallback; the panels may move at most 12 times an hour; the soil probe decides when irrigation runs and saves 4.8 %% of the water against a timer with no water-stress days (a timer has 20).</div><div class="say">Six sensors decide the tilt: <b>pyranometer</b> (sun), <b>PAR sensor</b> under the panels (light the crop gets), <b>DHT11</b> (air temperature and humidity), <b>soil moisture</b> and <b>rain sensor</b>. Rain: flat roof to the gutter. Night: park. Otherwise it tries every angle and picks the best mix of <b>50 %% electricity and 50 %% crop light</b>. The PAR sensor corrects the model; hot dry air or dry soil mean the crop needs less light, so the panels give more shade.</div>'
             '<p>Year-long test with noisy sensors (864 cases): <b>%.1f %%</b> of the best possible combined score, with <b>%.0f %%</b> of the best electricity and <b>%.0f %%</b> of the best crop light value. MATLAB and the web twin make identical decisions in 40 of 40 random cases.</p>' % (n['J_efficiency_pct'], n['pv_index_pct'], n['crop_index_pct']) + table +
             '<div class="p"><img src="%s"><small>Top-right is best. A PV-only panel (fixed 15 deg) gets 99 %% of the electricity but only 45 %% of the crop light value. The score is measured against the controller\'s own objective, not against field crop yield.</small></div>' % uri('fig_accuracy_both_goals.png', 1100) +
             '<div class="p"><img src="%s"><small>Simulink test day: cloud at 11:00, rain 14:00 to 15:00 (flat 3 deg), soil dries after 12:00 (more shade).</small></div>' % uri('sensor_controller_day.png', 900))
# ================= judge summary =================
p = os.path.join(ROOT, 'Review5_Economics_and_Final', 'documents', 'one_page_summaries', 'SRMC_Judge_Summary.html'); html = open(backup(p), encoding='utf-8').read()
html = html.replace('<title>SRMC Judge Summary</title>', '<title>%s: Judge Summary</title>' % T)
html = html.replace('<h1>SRMC: farming, rain harvest and solar power on one piece of land</h1>', '<h1>%s</h1>' % T)
html = html.replace('A computer simulation study (no field trial yet).', 'Six sensors tilt the panels to optimise crop light and electricity; rain is harvested. A computer simulation study (no field trial yet).')
html = html.replace('<p><b>Rule:</b> keep just enough light for the crop and give the rest to the panels. Hot, dry air or dry soil means a little more shade. Rain means panels go flat (3 degrees) and the water runs to the tank. One motor and one wire tilt all the panels together. <small>In our demo the sensor values are simulated with sliders.</small></p>',
                    '<p><b>Rule:</b> try every angle from 15 to 60 degrees and pick the best mix of electricity and crop light (50 : 50). The light sensor under the panels corrects the model. Hot, dry air or dry soil means the crop needs less light, so the panels give a little more shade. Rain means panels go flat (3 degrees) and the water runs to the tank. One motor and one wire tilt all the panels together. <small>In our demo the sensor values are simulated with sliders.</small></p>')
html = html.replace('In strong wind the controller turns panels vertical (needs a wind sensor, which we do not have yet).', 'In a storm the anemometer stows the panels edge-on at 90 degrees (15 m/s = 54 km/h). Moving the panels in wind needs the 10 kN winch and 6 mm drive wire of the final design.')
html = html.replace('<h2>4. Proof it is correct', ctl_block + '<h2>4. Proof it is correct')
html = selfcontain(html); open(p, 'w', encoding='utf-8').write(html)
# ================= results sheet =================
p = os.path.join(ROOT, 'Review5_Economics_and_Final', 'documents', 'one_page_summaries', 'SRMC_Results_Sheet.html'); html = open(backup(p), encoding='utf-8').read()
html = html.replace('<title>SRMC Results Sheet</title>', '<title>%s: Results Sheet</title>' % T)
html = html.replace('<h1>SRMC: wire-driven agrivoltaic canopy, results sheet</h1>', '<h1>%s: results sheet</h1>' % T)
html = html.replace('<h2>Headline numbers</h2>', ctl_block.replace('<h2>', '<h2 id="ctl">', 1) + '<h2>Headline numbers</h2>')
html = relink(html, os.path.dirname(p)); html = selfcontain(html); open(p, 'w', encoding='utf-8').write(html)
# ================= accuracy scorecard =================
p = os.path.join(ROOT, 'Review3_Digital_Twin', 'documents', 'SRMC_Accuracy_Scorecard.html'); html = open(backup(p), encoding='utf-8').read()
html = html.replace('<title>SRMC Accuracy Scorecard</title>', '<title>%s: Accuracy Scorecard</title>' % T)
html = html.replace('How accurate is the SRMC model?', 'How accurate is the model and the six-sensor controller?')
row = ('<tr><td>Six-sensor controller (tilt decisions)</td><td><span class="tag t-ok">Tested</span></td><td>Year-long test, 864 cases, noisy sensors: %.1f %% of the best combined score (%.0f %% of the best electricity, %.0f %% of the best crop light value). MATLAB and web twin: 40 of 40 identical decisions. Simulated sensors, no hardware test.</td></tr>' % (n['J_efficiency_pct'], n['pv_index_pct'], n['crop_index_pct']))
html = html.replace('<tr><td>Controller (tilt angles)</td>', row + '<tr><td>Controller (tilt angles), earlier note</td>', 1)
html = html.replace('<tr><td>Six sensors (pyranometer, PAR, DHT11, soil, rain, wind)</td><td><span class="tag t-no">Simulated</span></td><td>Slider values in the twin. Not yet measured on real hardware.</td></tr>', '<tr><td>Six sensors (pyranometer, PAR, DHT11, soil, rain, wind)</td><td><span class="tag t-no">Simulated</span></td><td>Slider values in the twin and Simulink. Review 0 reads real DHT11, soil and rain on an ESP board. Pyranometer and PAR are not yet measured.</td></tr>')
html = relink(html, os.path.dirname(p)); html = selfcontain(html); open(p, 'w', encoding='utf-8').write(html)
print('html updated', os.path.getsize(os.path.join(ROOT, 'Review5_Economics_and_Final', 'documents', 'one_page_summaries', 'SRMC_Judge_Summary.html')) // 1024, 'KB')
