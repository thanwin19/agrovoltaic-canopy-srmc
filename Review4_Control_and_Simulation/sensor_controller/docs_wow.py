"""Appends the November 2026 update notes to the review READMEs and the proof manifest (safe to re-run).   python docs_wow.py"""
import os, csv, hashlib
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')); os.chdir(ROOT)
s = open('WOW_ADDITIONS.md', encoding='utf8').read().replace(' (but 17 % less electricity at that hour)', ''); open('WOW_ADDITIONS.md', 'w', encoding='utf8').write(s)
def app(path, text):
    t = open(path, encoding='utf8').read()
    if 'Update 2026-11-01' in t: return
    open(path, 'w', encoding='utf8').write(t.rstrip() + '\n\n' + text + '\n')
app('README.md', "## Update 2026-11-01: additions to the one digital twin\n\nFour new tabs in the single twin (ground light map, structure and trade-off, design explorer, edge AI and sensor-attack test) plus a finite element check of the lever arm and a revised arm. See `WOW_ADDITIONS.md` for what each does, the numbers, and the limits. The second copy of the twin was moved to `_archive/`.")
app('Review1_Design_and_CAD/README.md', "## Update 2026-11-01: finite element check of the lever arm\n\n`fea/arm_fea.py` (scikit-fem). The arm as first drawn is safe at the 4.1 kN design load (factor of safety 2.3) but yields at the 10.2 kN limit of the drive wire (0.9); the arm is now 120/70 x 16 mm (4.7 and 1.9) and the 3D mechanism viewer shows it. See `../WOW_ADDITIONS.md`.")
app('Review2_Solar_and_Shadow/README.md', "## Update 2026-11-01: ground light map\n\n`code_reference/shade3d.py`, results in `results/ground_heatmap/`: 3-D ray cast, any day, hour and tilt, red / yellow / green. Checked against the 2-D engine (mean difference 0.046). Shown in the twin's Ground map tab. See `../WOW_ADDITIONS.md`.")
app('Review3_Digital_Twin/README.md', "## Update 2026-11-01: four new tabs in the one twin\n\nGround map, Structure, Design explorer, Edge AI (with the anemometer attack test). Built by `Review4_Control_and_Simulation/sensor_controller/patch_wow.py`. See `../WOW_ADDITIONS.md`.")
app('Review4_Control_and_Simulation/README.md', "## Update 2026-11-01: trade-off, design explorer, edge AI, attack test\n\n`sensor_controller/pareto3/` (energy, crop, structural demand and the storm stow angle), `design_explorer/` (NSGA-III), `esp32_model/` (small network, C code, closed-loop score 97.3 %, below the monthly plan 98.8 %), `attack_test.js` (spoofed anemometer and a wire-tension monitor). See `../WOW_ADDITIONS.md`.")
A = 'Proof/09_Additions_Ground_Map_Pareto_FEA_EdgeAI'
open(A + '/README.md', 'w', encoding='utf8').write("# Additions of November 2026: evidence\n\nCopies of the figures, tables, results and code behind the new tabs of the twin (ground map, 3-objective trade-off, finite element check, design explorer, small network for the ESP32, sensor-attack test). The twin itself is `Proof/07_Live_Twin_and_Screenshots/SRMC_Digital_Twin.html` (screens 11 to 14). What each result means, and its limits: `../../WOW_ADDITIONS.md`. Everything is simulation.\n")
mp = 'Proof/MANIFEST.csv'; rows = list(csv.reader(open(mp, encoding='utf8'))); head = rows[0]; have = {r[0] for r in rows[1:]}
files = []
for dp, dn, fn in os.walk(A):
    for f in fn: files.append(os.path.join(dp, f).replace(chr(92), '/'))
files += ['Proof/07_Live_Twin_and_Screenshots/screens/' + f for f in os.listdir('Proof/07_Live_Twin_and_Screenshots/screens') if f[:3] in ('11_', '12_', '13_', '14_', '00_', '00b')] + ['Proof/07_Live_Twin_and_Screenshots/SRMC_Digital_Twin.html']
new = []
for p in files:
    rel = p[len('Proof/'):]; sha = hashlib.sha256(open(p, 'rb').read()).hexdigest()
    new.append(rel)
    rows = [r for r in rows if r and r[0] != rel]
    rows.append([rel, str(os.path.getsize(p)), sha, "added 2026-11-01"])
with open(mp, 'w', encoding='utf8', newline='') as f: csv.writer(f).writerows([head] + rows[1:] if rows[0] != head else rows)
print('manifest columns', head, 'rows now', len(rows), 'added/updated', len(new))
