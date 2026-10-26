"""Figures for the paper (from the project result files).  python make_paper_figs.py"""
import os, csv, json, math
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image
plt.rcParams.update({'font.family': 'serif', 'font.serif': ['Times New Roman', 'Times', 'DejaVu Serif'], 'font.size': 7.5, 'axes.linewidth': 0.6, 'mathtext.fontset': 'stix'})
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, 'figures'); os.makedirs(OUT, exist_ok=True)
SC = r'E:\final year project\srmc-twin\Review4_Control_and_Simulation\sensor_controller\results'
SHOT = r'C:\Users\ELCOT\AppData\Local\Temp\claude\E--farm-ai-cropsy-final\f56bb85c-71b9-41a8-acc9-ec01a8db9a6f\scratchpad\paperfig'
# ---- Fig 1: render crop
im = Image.open(os.path.join(SHOT, 'shot_overview.png')).convert('RGB').crop((230, 110, 1340, 940)); im.save(os.path.join(OUT, 'fig1_canopy_3d.png'), dpi=(300, 300)); print(im.size)
# ---- Fig 2: lever arm geometry and lever length
L = 0.44; a = math.radians(45); fig, (ax, bx) = plt.subplots(1, 2, figsize=(3.4, 1.95), gridspec_kw={'width_ratios': [1.05, 1]})
def tip(th): return (-L * math.sin(math.radians(th) - a), -L * math.cos(math.radians(th) - a))
for th, st, col, lab in [(3, '--', '0.55', '3\u00b0 (flat)'), (60, '-', 'C0', '60\u00b0'), (90, ':', 'C3', '90\u00b0 (stow)')]:
    t = tip(th); ax.plot([0, t[0]], [0, t[1]], st, color=col, lw=1.6); ax.plot(t[0], t[1], 'o', color=col, ms=3.5)
    ax.annotate(lab, t, textcoords='offset points', xytext={3: (0, -12), 60: (-2, -10), 90: (-4, 8)}[th], ha={3: 'center', 60: 'right', 90: 'right'}[th], fontsize=6.3, color=col)
t3, t60 = tip(3), tip(60); ax.plot(0, 0, 'ks', ms=4); ax.text(0.015, 0.03, 'tube axis', fontsize=6.5)
yb = -0.60; ax.annotate('', xy=(t60[0], yb), xytext=(t3[0], yb), arrowprops=dict(arrowstyle='<->', lw=0.8, color='C2')); ax.text((t3[0] + t60[0]) / 2, yb - 0.075, '$d$ = 408 mm at 60\u00b0', ha='center', fontsize=6.3, color='C2')
ax.set_xlim(-0.5, 0.5); ax.set_ylim(-0.74, 0.1); ax.set_aspect('equal'); ax.set_xlabel('Horizontal distance (m)'); ax.set_ylabel('Height below tube axis (m)'); ax.set_title('(a) Arm positions', fontsize=7.5, loc='left')
th = [i * 0.5 for i in range(6, 181)]
bx.plot(th, [L * math.cos(math.radians(t) - a) for t in th], 'C0', lw=1.4, label='45\u00b0 offset arm'); bx.plot(th, [L * math.cos(math.radians(t)) for t in th], 'C3--', lw=1.2, label='plain arm')
bx.axhline(0.31, color='0.5', lw=0.5, ls=':'); bx.text(4, 0.318, '0.31 m', fontsize=6.3, color='0.35'); bx.set_xlabel('Panel tilt (deg)'); bx.set_ylabel('Lever length (m)'); bx.set_xlim(0, 90); bx.set_ylim(0, 0.46); bx.legend(fontsize=6.3, frameon=False, loc='lower left'); bx.set_title('(b) Lever length', fontsize=7.5, loc='left')
fig.tight_layout(pad=0.4); fig.savefig(os.path.join(OUT, 'fig2_lever_arm.png'), dpi=300); plt.close(fig)
# ---- Fig 3: accuracy scatter
rows = list(csv.DictReader(open(os.path.join(SC, 'T11_accuracy_v2.csv'))))
fig, ax = plt.subplots(figsize=(3.3, 2.3))
for r in rows:
    k = r['strategy']; x, y = float(r['electricity % of best']), float(r['crop light value % of best']); ctl = k.startswith('SC'); ax.plot(x, y, 'o', color='C0' if ctl else '0.4', ms=4.5 if ctl else 4)
ax.annotate('Six-sensor controller (three variants)', (82.0, 97.8), textcoords='offset points', xytext=(14, 4), fontsize=6.3, arrowprops=dict(arrowstyle='-', lw=0.4))
ax.annotate('Monthly plan', (82.2, 96.3), textcoords='offset points', xytext=(14, -9), fontsize=6.3, arrowprops=dict(arrowstyle='-', lw=0.4))
for nm, x, y, o in [('Fixed 45°', 81.0, 84.6, (6, -3)), ('Sun tracking', 88.6, 64.3, (6, 3)), ('Fixed 15° (PV-max)', 99.2, 45.2, (-6, 6))]:
    ax.annotate(nm, (x, y), textcoords='offset points', xytext=o, ha='left' if o[0] > 0 else 'right', fontsize=6.3)
ax.set_xlabel('Electricity (% of best possible)'); ax.set_ylabel('Crop light value (% of best possible)'); ax.set_xlim(78, 102); ax.set_ylim(40, 105); ax.grid(lw=0.3, alpha=0.5)
fig.tight_layout(pad=0.4); fig.savefig(os.path.join(OUT, 'fig3_accuracy.png'), dpi=300); plt.close(fig)
# ---- Fig 4: weight sweep
G = json.load(open(os.path.join(SC, 'gaps_study.json')))['weight_sweep']; w = [r['w'] for r in G]; tmax = max(r['total'] for r in G)
fig, ax = plt.subplots(figsize=(3.3, 2.25)); ax.plot(w, [r['pv_pct_of_max'] for r in G], 'o-', color='C1', ms=3, lw=1.2, label='Electricity'); ax.plot(w, [r['crop_pct_of_max'] for r in G], 's-', color='C2', ms=3, lw=1.2, label='Crop income'); ax.plot(w, [100 * r['total'] / tmax for r in G], '^-', color='C0', ms=3, lw=1.2, label='Total income')
ax.axvline(0.5, color='0.5', lw=0.6, ls='--'); ax.text(0.51, 8, 'w = 0.5', fontsize=6.5, color='0.35'); ax.set_xlabel('Electricity weight $w$ in the objective (4)'); ax.set_ylabel('Value (% of the best over all weights)'); ax.set_ylim(-8, 105); ax.set_xlim(0, 1); ax.grid(lw=0.3, alpha=0.5); ax.legend(fontsize=6.5, frameon=False, loc='center left')
fig.tight_layout(pad=0.4); fig.savefig(os.path.join(OUT, 'fig4_weight_sweep.png'), dpi=300); plt.close(fig)
print('figures written to', OUT)
