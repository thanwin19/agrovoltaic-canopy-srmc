"""Accuracy figure for Review 0: what the co-optimising controller obtains against ordinary designs. Data: Proof/05_Controller_and_Accuracy/T11_accuracy_v2.csv (864 noisy cases) + the dashboard day result.   python make_accuracy_figure.py"""
import csv, os
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
rows = list(csv.DictReader(open(os.path.join(root, 'Proof', '05_Controller_and_Accuracy', 'T11_accuracy_v2.csv'), encoding='utf8')))
by = {r['strategy']: r for r in rows}; k = list(rows[0].keys())
EL, CR, CO, RM = k[1], k[2], k[3], k[4]
names = [('Fixed 15 deg\n(max electricity)', 'Fixed 15 deg (PV-max)'), ('Sun tracking\n(ordinary tracker)', 'Sun tracking (E-W)'), ('Fixed 45 deg\n(ordinary roof)', 'Fixed 45 deg'), ('Monthly plan\n(no sensors)', 'Monthly schedule (SRMC-DT)'), ('OUR controller\n(6 sensors, noisy)', 'SC v2 noisy (median of 5 + guard)')]
g = lambda col: [float(by[n[1]][col]) for n in names]
col = ['#9aa3ad', '#9aa3ad', '#9aa3ad', '#e0a030', '#1a8f4a']
fig, ax = plt.subplots(1, 3, figsize=(19, 7.4), facecolor='white')
v = g(CO); b = ax[0].bar([n[0] for n in names], v, color=col)
for r, x in zip(b, v): ax[0].text(r.get_x() + r.get_width() / 2, x + 0.8, f'{x:.1f} %', ha='center', fontweight='bold', fontsize=11)
ax[0].axhline(100, ls='--', c='k', lw=1); ax[0].text(-0.4, 102.2, '100 % = the best possible angle every hour', fontsize=9); ax[0].set_ylim(60, 108); ax[0].set_ylabel('combined score, % of the best possible'); ax[0].set_title('A  Accuracy of the co-optimisation', fontweight='bold')
x = range(len(names)); w = 0.38
e, c = g(EL), g(CR)
ax[1].bar([i - w / 2 for i in x], e, w, color='#f0a020', label='electricity'); ax[1].bar([i + w / 2 for i in x], c, w, color='#2a9a50', label='crop light value')
for i in x: ax[1].text(i - w / 2, e[i] + 1, f'{e[i]:.0f}', ha='center', fontsize=9); ax[1].text(i + w / 2, c[i] + 1, f'{c[i]:.0f}', ha='center', fontsize=9)
ax[1].set_xticks(list(x)); ax[1].set_xticklabels([n[0] for n in names], fontsize=8); ax[1].set_ylim(0, 118); ax[1].set_ylabel('% of the best possible'); ax[1].legend(loc='upper left', ncol=2, fontsize=9); ax[1].set_title('B  Ordinary designs give up one goal', fontweight='bold')
ax[1].annotate('only 45 % of the\ncrop light', (0 + w / 2, c[0]), (-0.45, 66), arrowprops=dict(arrowstyle='->'), fontsize=9, color='#a02020'); ax[1].annotate('only 64 % of the\ncrop light', (1 + w / 2, c[1]), (0.75, 40), arrowprops=dict(arrowstyle='->'), fontsize=9, color='#a02020')
v = g(RM); b = ax[2].bar([n[0] for n in names], v, color=col)
for r, x2 in zip(b, v): ax[2].text(r.get_x() + r.get_width() / 2, x2 + 0.6, f'{x2:.1f}', ha='center', fontweight='bold', fontsize=11)
ax[2].set_ylabel('angle error vs the best angle (deg, lower is better)'); ax[2].set_title('C  How far the angle is from the best', fontweight='bold')
for a in ax: a.tick_params(axis='x', labelsize=8); a.spines[['top', 'right']].set_visible(False)
fig.suptitle('What we obtained: the six-sensor co-optimising controller against ordinary designs (864 noisy test cases, TCE Madurai)', fontsize=14, fontweight='bold')
fig.text(0.5, 0.012, 'Review 0 dashboard, one clear day (day 105, 13 hours, datasheet-sized sensor errors): our controller 99.4 %, fixed 45 deg 87.0 %, plain sun tracking 87.5 %.' + chr(10) + 'SIMULATION: measured against the controller own goal (half electricity, half crop light), not against real crop yield.', ha='center', fontsize=9, color='#444')
plt.tight_layout(rect=[0, 0.07, 1, 0.94])
for out in (os.path.join(root, 'Review0_Prototype_Demo', 'results', 'ACCURACY_obtained_vs_ordinary.png'), os.path.join(root, 'Proof', '10_Review0_Sensors_and_Panels', 'ACCURACY_obtained_vs_ordinary.png')):
    plt.savefig(out, dpi=150)
print('saved')
