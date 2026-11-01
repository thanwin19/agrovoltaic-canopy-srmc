"""Adds one slide per review deck for the Review 0 sensor work (real device names, datasheet proof, NASA POWER / PVGIS check, real-weather replay, cost if real).
Works from a saved copy of each deck in _archive/backups_of_files_before_the_final_update/deck_sensor, so it can be re-run.  Run add_wow_slides.py first if you rebuild the decks from the originals.   python add_sensor_slides.py"""
import os, re, copy, shutil
from pptx import Presentation
from pptx.util import Pt
from pptx.dml.color import RGBColor
from PIL import Image
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')); BK = os.path.join(ROOT, '_archive', 'backups_of_files_before_the_final_update', 'deck_sensor'); os.makedirs(BK, exist_ok=True)
I2 = os.path.join(ROOT, 'Review0_Prototype_Demo', 'ppt', '_img2'); R0 = os.path.join(ROOT, 'Review0_Prototype_Demo', 'results'); P10 = os.path.join(ROOT, 'Proof', '10_Review0_Sensors_and_Panels')
JOBS = [
 ('Review1_Design_and_CAD/ppt/Review1_Design_and_CAD.pptx', 'Panel and sensor hardware: datasheet check', os.path.join(R0, 'dashboard_tab_sensors_panels.png'),
  ['Panel: JinkoSolar Tiger Pro JKM550M-72HL4-V, 550 Wp; 8 panels = 4.4 kWp.',
   'Official datasheet: 2274 x 1134 x 35 mm, 28.9 kg. The drawings and strength check used 2278 mm and 27.5 kg from listings: about +11 kg on the set (about 0.5 % of its weight); update in the next drawing revision.',
   'Sensor mounting: pyranometer in open sun, PAR under the panels, DHT11 in a shaded vent box, soil probe in the root zone, rain sensor at the panel edge, anemometer on a 3 m mast.',
   'Real devices simulated: Apogee SP-110 and SQ-110, DHT11, DFRobot SEN0193, YL-83 / FC-37, Adafruit 1733. Datasheets downloaded as proof.']),
 ('Review2_Solar_and_Shadow/ppt/Review2_Solar_and_Shadow.pptx', 'Sunlight model against NASA POWER and PVGIS, month by month', os.path.join(P10, 'TRUST_monthly_sunlight_model_vs_NASA_PVGIS.png'),
  ['Against NASA POWER hourly 2023: year average +2.0 %, monthly -6.9 % to +9.9 %, hourly shape RMSE 40-91 W/m2.',
   'Against PVGIS-ERA5 of the single year 2020: +7.9 % on average, +16 to +26 % in June to September and December. One reanalysis year differs from the long-term climate (multi-year PVGIS: +5.0 %).',
   'The model is a good typical year, not a prediction of one year. PAR share: NASA 0.444, model 0.45.',
   'Satellite and reanalysis data, not a pyranometer on the TCE roof: a check, not a field validation.']),
 ('Review3_Digital_Twin/ppt/Review3_Digital_Twin.pptx', 'Review 0 sensors and proof inside the twin', os.path.join(I2, 'twin_proof_tab.png'),
  ['The sensor panel names the real devices and shows each signal (SP-110: 837 W/m2 = 167 mV; Adafruit 1733: 20 m/s = 1.39 V).',
   'Switch for datasheet-sized sensor errors; recorder with CSV download.',
   'Replay of 15 real NASA POWER days of 2023 (the 15th of each month, the rainiest, windiest and sunniest day).',
   'New tab Sensors and proof: datasheet links, Jinko panel with a live I-V curve, sunlight check, accuracy, cost.',
   'The sensors are software models; readings are not measured.']),
 ('Review4_Control_and_Simulation/ppt/Review4_Control_and_Simulation.pptx', 'Sensor models and accuracy with real-device errors', os.path.join(I2, 'poster_accuracy.png'),
  ['The controller sees sunlight and PAR +-5 % (SP-110, SQ-110), DHT11 +-2 C and +-5 % RH, soil +-3 %.',
   '864 noisy cases: our controller 99.6 % of the best score; fixed 45 deg 91.2 %; sun tracking 84.0 %; fixed 15 deg 80.0 %.',
   'Review 0 dashboard, one clear April day: 99.4 % against 87.0 % (fixed 45 deg) and 87.5 % (tracking).',
   'Real hourly wind at TCE in 2023 never passed 10.9 m/s (10 m, no gusts): the 15 m/s storm stow stays a safety margin.',
   'Measured against the controller own goal, in simulation.']),
 ('Review5_Economics_and_Final/ppt/Review5_Economics_and_Final.pptx', 'Cost of the sensing kit if it were built', os.path.join(I2, 'cost_kits.png'),
  ['Research-grade kit about INR 67,600 (two Apogee sensors about 56,000, anemometer 6,500, the rest about 5,100).',
   'Low-cost kit about INR 13,100 (reference cells instead of the Apogee sensors).',
   '8 panels (4.4 kWp) about INR 70,000 at an assumed INR 16 per Wp.',
   'Indicative estimates, not quotes: replace with supplier quotes. The simulation itself costs nothing.']),
]
def clone_slide(prs, src):
    new = prs.slides.add_slide(src.slide_layout)
    for sh in list(new.shapes): sh._element.getparent().remove(sh._element)
    for sh in src.shapes: new.shapes._spTree.insert_element_before(copy.deepcopy(sh._element), 'p:extLst')
    return new
for rel, title, pic, bullets in JOBS:
    path = os.path.join(ROOT, *rel.split('/')); b = os.path.join(BK, os.path.basename(path))
    if not os.path.exists(b): shutil.copy(path, b)
    prs = Presentation(b); src = None
    for s in prs.slides:
        ts = [sh.text_frame.text for sh in s.shapes if sh.has_text_frame]
        if any(t.startswith('Limits') for t in ts) or any(t.startswith('Conclusions') for t in ts): src = s
    src = src or prs.slides[len(prs.slides) - 2]
    new = clone_slide(prs, src); W, H = prs.slide_width, prs.slide_height
    for sh in list(new.shapes):
        if sh.shape_type == 13 and sh.height > H * 0.15: sh._element.getparent().remove(sh._element)      # drop the pictures of the template slide, keep any small logo
    texts = [sh for sh in new.shapes if sh.has_text_frame]; ttl = next(sh for sh in texts if sh.text_frame.text.strip() and sh.top < H * 0.15 and len(sh.text_frame.text) < 90 and sh.height < H * 0.2 and sh.width > W * 0.3 and not re.search(r'\|\s*\d+$', sh.text_frame.text))
    foot = [sh for sh in texts if re.search(r'\|\s*\d+$', sh.text_frame.text)]; body = max([sh for sh in texts if sh is not ttl and sh not in foot], key=lambda s: s.width * s.height)
    for p in ttl.text_frame.paragraphs:
        if p.runs: p.runs[0].text = title; [setattr(r, 'text', '') for r in p.runs[1:]]
    tf = body.text_frame; ps = tf.paragraphs
    for i, t in enumerate(bullets):
        if i < len(ps): p = ps[i]
        else: pe = copy.deepcopy(ps[0]._p); tf._txBody.append(pe); p = tf.paragraphs[-1]
        for r in p.runs[1:]: r.text = ''
        if p.runs: p.runs[0].text = '• ' + t
        for r in p.runs: r.font.size = Pt(12.5); r.font.bold = False; r.font.color.rgb = RGBColor(0x22, 0x2B, 0x22)
    for p in tf.paragraphs[len(bullets):]:
        for r in p.runs: r.text = ''
    body.left = int(W * 0.03); body.width = int(W * 0.42); body.top = int(H * 0.2); body.height = int(H * 0.70)
    im = Image.open(pic); ar = im.size[1] / im.size[0]; pw = int(W * 0.52); ph = int(pw * ar)
    if ph > H * 0.70: ph = int(H * 0.70); pw = int(ph / ar)
    new.shapes.add_picture(pic, int(W * 0.46), int(H * 0.2), pw, ph)
    n = len(prs.slides._sldIdLst)
    lst = prs.slides._sldIdLst; el = list(lst)[-1]; lst.remove(el); lst.insert(n - 2 if n > 2 else n - 1, el)
    for i, sl in enumerate(prs.slides, 1):
        for sh in sl.shapes:
            if sh.has_text_frame:
                for p in sh.text_frame.paragraphs:
                    t = ''.join(r.text for r in p.runs)
                    if re.search(r'\|\s*\d+$', t) and p.runs: p.runs[0].text = re.sub(r'\|\s*\d+$', '| %d' % i, t); [setattr(r, 'text', '') for r in p.runs[1:]]
    prs.save(path); print('added slide to', os.path.basename(path), 'now', n, 'slides')
