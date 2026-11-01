"""Adds one slide per review deck for the November 2026 additions (backups once in _archive/backups_of_files_before_the_final_update/deck_wow).   python add_wow_slides.py"""
import os, re, copy, shutil
from pptx import Presentation
from pptx.util import Emu, Pt
from pptx.dml.color import RGBColor
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')); BK = os.path.join(ROOT, '_archive', 'backups_of_files_before_the_final_update', 'deck_wow'); os.makedirs(BK, exist_ok=True)
P = os.path.join(ROOT, 'Proof', '09_Additions_Ground_Map_Pareto_FEA_EdgeAI'); SC = os.path.join(ROOT, 'Proof', '07_Live_Twin_and_Screenshots', 'screens')
JOBS = [
 ('Review1_Design_and_CAD/ppt/Review1_Design_and_CAD.pptx', 'Lever arm: finite element check', [os.path.join(P, 'fea', 'fig_arm_stress.png')],
  ['Plane-stress finite elements (P2, scikit-fem), SS316 yield 205 MPa, root fixed, wire force on the pin hole.',
   'Method checked: plate with a hole gives the textbook stress concentration within 2 %; mesh converged; peak along the arm 91 MPa against 92 MPa by hand.',
   'The arm as first drawn (90/48 x 14 mm): factor of safety 2.3 at the 4.1 kN design load, 0.9 at the 10.2 kN limit of the drive wire.',
   'Revised arm 120/70 x 16 mm: 4.7 and 1.9. The 3D mechanism viewer shows it.',
   'Screening level: 2-D, linear, no weld or fatigue detail.']),
 ('Review2_Solar_and_Shadow/ppt/Review2_Solar_and_Shadow.pptx', 'Ground light map: where the crop is shaded', [os.path.join(P, 'ground_map', 'fig_ground_map_21Mar.png')],
  ['3-D ray cast of the 25 m x 25 m array: red = heavy shade, yellow = partial, green = well lit. Any day, hour and tilt in the twin (Ground map tab).',
   'Top row: fixed 45 deg. Bottom row: the angle chosen by the controller at 8:00, 10:00, 12:00 and 16:00 on 21 March.',
   'Check against the 2-D engine in the middle of the array: mean difference of the light fraction 0.05. The 3-D map is higher on average (0.32 against 0.28) because shadow leaves through the row ends.',
   'Clear sky, opaque panels, flat ground.']),
 ('Review3_Digital_Twin/ppt/Review3_Digital_Twin.pptx', 'The one twin now has four more tabs', [os.path.join(SC, '12_structure_and_tradeoff.png')],
  ['Ground map, Structure, Design explorer and Edge AI (with the anemometer attack test) were added to the same twin file.',
   'Rebuildable: patch_wow.py runs after the other three patch scripts.',
   'The second copy of the twin was archived: there is one twin.',
   'Details and limits: WOW_ADDITIONS.md.']),
 ('Review4_Control_and_Simulation/ppt/Review4_Control_and_Simulation.pptx', 'Trade-off, edge AI and sensor-attack test', [os.path.join(P, 'pareto3', 'fig_pareto3_load.png')],
  ['Three goals (electricity, crop income, structural demand at 140 km/h): a conservative wind-load model needs the 90 deg stow (a flat stow gives 1.38 of capacity); a flat-plate model would allow a flat stow. A wind-tunnel or CFD run is needed to settle it.',
   'Design explorer (NSGA-III, 1,187 designs): none beats the final design on all four goals together.',
   'Small network for the ESP32: 98.2 % of the best on single hours, 97.3 % when steering a whole year, below the monthly plan (98.8 %) and the full controller (99.5 %). C code verified on 400 vectors.',
   'Spoofed anemometer: 40 minutes above the winch limit without a wire-tension monitor, none with it. Simulation only.']),
]
def clone_slide(prs, src):
    new = prs.slides.add_slide(src.slide_layout)
    for sh in list(new.shapes): sh._element.getparent().remove(sh._element)
    for sh in src.shapes: new.shapes._spTree.insert_element_before(copy.deepcopy(sh._element), 'p:extLst')
    return new
for rel, title, pics, bullets in JOBS:
    path = os.path.join(ROOT, *rel.split('/')); b = os.path.join(BK, os.path.basename(path))
    if not os.path.exists(b): shutil.copy(path, b)
    prs = Presentation(b)                                                      # always from the saved original: re-runnable
    src = None
    for s in prs.slides:
        ts = [sh.text_frame.text for sh in s.shapes if sh.has_text_frame]
        if any(t.startswith('Limits') for t in ts) or any(t.startswith('Conclusions') for t in ts): src = s
    src = src or prs.slides[len(prs.slides) - 2]
    new = clone_slide(prs, src); W, H = prs.slide_width, prs.slide_height
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
        for r in p.runs:
            r.font.size = Pt(13); r.font.bold = False; r.font.color.rgb = RGBColor(0x22, 0x2B, 0x22)
    for p in tf.paragraphs[len(bullets):]:
        for r in p.runs: r.text = ''
    body.left = int(W * 0.03); body.width = int(W * 0.40); body.top = int(H * 0.2); body.height = int(H * 0.68)
    from PIL import Image
    im = Image.open(pics[0]); ar = im.size[1] / im.size[0]; pw = int(W * 0.53); ph = int(pw * ar)
    if ph > H * 0.72: ph = int(H * 0.72); pw = int(ph / ar)
    new.shapes.add_picture(pics[0], int(W * 0.45), int(H * 0.2), pw, ph)
    n = len(prs.slides._sldIdLst)
    for sh in foot:
        for p in sh.text_frame.paragraphs:
            t = ''.join(r.text for r in p.runs); nt = re.sub(r'\|\s*\d+$', '| %d' % n, t)
            if p.runs: p.runs[0].text = nt; [setattr(r, 'text', '') for r in p.runs[1:]]
    lst = prs.slides._sldIdLst; el = list(lst)[-1]; lst.remove(el); lst.insert(n - 2 if n > 2 else n - 1, el)
    for i, sl in enumerate(prs.slides, 1):                                      # renumber the footers
        for sh in sl.shapes:
            if sh.has_text_frame:
                for p in sh.text_frame.paragraphs:
                    t = ''.join(r.text for r in p.runs)
                    if re.search(r'\|\s*\d+$', t) and p.runs: p.runs[0].text = re.sub(r'\|\s*\d+$', '| %d' % i, t); [setattr(r, 'text', '') for r in p.runs[1:]]
    prs.save(path); print('added slide to', os.path.basename(path), 'now', n, 'slides')
