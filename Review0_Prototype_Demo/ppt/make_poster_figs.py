"""Large-print figures for the Review 0 poster (same data as the Evidence Book figures).   python make_poster_figs.py"""
import csv, json, os
import numpy as np
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', '..')); P10 = os.path.join(ROOT, 'Proof', '10_Review0_Sensors_and_Panels')
plt.rcParams.update({'font.size': 15, 'axes.spines.top': False, 'axes.spines.right': False})
rows = list(csv.DictReader(open(os.path.join(ROOT, 'Proof', '05_Controller_and_Accuracy', 'T11_accuracy_v2.csv'), encoding='utf8'))); by = {r['strategy']: r for r in rows}; k = list(rows[0].keys())
names = [('Fixed\n15 deg', 'Fixed 15 deg (PV-max)'), ('Sun\ntracking', 'Sun tracking (E-W)'), ('Fixed\n45 deg', 'Fixed 45 deg'), ('Monthly\nplan', 'Monthly schedule (SRMC-DT)'), ('OUR\ncontroller', 'SC v2 noisy (median of 5 + guard)')]
g = lambda col: [float(by[n[1]][col]) for n in names]; col = ['#9aa3ad', '#9aa3ad', '#9aa3ad', '#e0a030', '#1a8f4a']
fig, ax = plt.subplots(1, 2, figsize=(14, 5.6), facecolor='white')
v = g(k[3]); b = ax[0].bar([n[0] for n in names], v, color=col, width=0.72)
for r, x in zip(b, v): ax[0].text(r.get_x() + r.get_width() / 2, x + 0.7, f'{x:.1f}%', ha='center', fontweight='bold', fontsize=16)
ax[0].axhline(100, ls='--', c='k', lw=1.2); ax[0].set_ylim(60, 106); ax[0].set_ylabel('% of the best possible score'); ax[0].set_title('How close to the best angle', fontweight='bold', fontsize=17)
e, c = g(k[1]), g(k[2]); x = np.arange(5); w = 0.38
ax[1].bar(x - w / 2, e, w, color='#f0a020', label='electricity'); ax[1].bar(x + w / 2, c, w, color='#2a9a50', label='crop light')
for i in range(5): ax[1].text(i - w / 2, e[i] + 1, f'{e[i]:.0f}', ha='center', fontsize=12); ax[1].text(i + w / 2, c[i] + 1, f'{c[i]:.0f}', ha='center', fontsize=12)
ax[1].set_xticks(x); ax[1].set_xticklabels([n[0] for n in names]); ax[1].set_ylim(0, 120); ax[1].legend(loc='upper left', ncol=2, frameon=False); ax[1].set_title('Ordinary designs give up one goal', fontweight='bold', fontsize=17)
plt.tight_layout(); plt.savefig(os.path.join(HERE, '_img2', 'poster_accuracy.png'), dpi=170)
# sunlight trust, large print
K = 1e6 / 3600.0; n = json.load(open(os.path.join(P10, 'sunlight_datasets', 'NASA_POWER_hourly_2023-04-15_LST_TCE.json')))['properties']['parameter']; H = np.arange(24)
gg = lambda kk: np.array([n[kk]['20230415%02d' % h] for h in H]) * K; A, C = gg('ALLSKY_SFC_SW_DWN'), gg('CLRSKY_SFC_SW_DWN')
M = np.genfromtxt(os.path.join(P10, 'sunlight_datasets', 'DASHBOARD_model_ghi_day105.csv'), delimiter=',', names=True)
fig, a = plt.subplots(figsize=(9, 5.4), facecolor='white')
a.plot(M['solar_hour'], M['ghi_clear_kt062'], '-', c='#1a4fa0', lw=4, label='our dashboard model, Clear sky'); a.plot(H + 0.5, A, 's-', c='#c03030', lw=2, ms=6, label='NASA POWER, actual day'); a.plot(H + 0.5, C, 'o--', c='#e08a00', lw=1.6, ms=5, label='NASA POWER, perfect clear sky')
a.set_xlim(5, 19); a.set_xlabel('solar hour'); a.set_ylabel('sunlight (W/m2)'); a.legend(frameon=False, fontsize=13, loc='upper right'); a.grid(alpha=.3); a.set_title('15 April, TCE: model against real data', fontweight='bold', fontsize=17)
plt.tight_layout(); plt.savefig(os.path.join(HERE, '_img2', 'poster_trust.png'), dpi=170); print('ok')
