"""Figures and the compatibility summary for the v2 accuracy study.  python make_figs_v2.py"""
import json, csv, os, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
here = os.path.dirname(os.path.abspath(__file__)); R = os.path.join(here, 'results')
d = json.load(open(os.path.join(R, 'accuracy_v2.json'))); M = d['main']
name_map = {'SC v2 noisy (median of 5 + guard)': 'SRMC-SC (noisy sensors)', 'SC v2 ideal sensors': 'SRMC-SC (ideal sensors)', 'SC v1 noisy (1 reading)': 'SC v1 (one reading, no guard)'}
col = {'SC v2 noisy (median of 5 + guard)': '#1f7a2e', 'SC v2 ideal sensors': '#72b830', 'SC v1 noisy (1 reading)': '#a0c080', 'Monthly schedule (SRMC-DT)': '#2a6fb0', 'Fixed 45 deg': '#e8a93a', 'Fixed 15 deg (PV-max)': '#c0392b', 'Sun tracking (E-W)': '#777'}
# compatibility summary used by the deck / report scripts
res = [{'strategy': name_map.get(r['strategy'], r['strategy']), 'pv_index_pct': r['pv_pct'], 'crop_index_pct': r['crop_pct'], 'J_efficiency_pct': r['J_pct'], 'angle_rmse_deg': r['angle_rmse_deg']} for r in M]
json.dump({'weights': d['weights'], 'noise': 'pyranometer 5 %, PAR 5 %, DHT11 +-2 C +-5 % RH, soil +-3 %', 'states': 864, 'results': res}, open(os.path.join(R, 'accuracy_summary.json'), 'w'), indent=1)
open(os.path.join(R, 'accuracy_table.csv'), 'w').write('strategy,PV index % of best,crop index % of best,objective J efficiency %,angle RMSE deg\n' + '\n'.join('%s,%s,%s,%s,%s' % (r['strategy'], r['pv_index_pct'], r['crop_index_pct'], r['J_efficiency_pct'], r['angle_rmse_deg']) for r in res))
# 1. both goals
fig, ax = plt.subplots(1, 2, figsize=(12, 4.8))
for r in M: ax[0].scatter(r['pv_pct'], r['crop_pct'], s=150, color=col[r['strategy']], edgecolor='k', label=name_map.get(r['strategy'], r['strategy']))
ax[0].set_xlabel('Electricity: % of best possible'); ax[0].set_ylabel('Crop light value: % of best possible'); ax[0].set_xlim(78, 101); ax[0].set_ylim(40, 101); ax[0].grid(alpha=.3); ax[0].set_title('Both goals: top-right is best'); ax[0].legend(fontsize=7.5, loc='lower left')
ax[1].barh([name_map.get(r['strategy'], r['strategy']).replace(' (', '\n(') for r in M][::-1], [r['J_pct'] for r in M][::-1], color=[col[r['strategy']] for r in M][::-1]); ax[1].set_xlim(70, 101)
for i, r in enumerate(M[::-1]): ax[1].text(r['J_pct'] + .2, i, '%.1f  (tilt error %.1f deg)' % (r['J_pct'], r['angle_rmse_deg']), va='center', fontsize=8.5)
ax[1].set_xlabel('Combined score, % of the perfect-knowledge optimum'); ax[1].set_title('Combined score (50 % electricity + 50 % crop light)'); plt.tight_layout(); plt.savefig(os.path.join(R, 'fig_accuracy_both_goals.png'), dpi=150); plt.close()
# 2. noise sweep + faults
fig, ax = plt.subplots(1, 2, figsize=(12, 4.4)); nz = d['noise']
ax[0].plot([r['noise_x'] for r in nz], [r['v1']['J_pct'] for r in nz], 'o-', color='#c0392b', lw=2.4, label='v1: one reading'); ax[0].plot([r['noise_x'] for r in nz], [r['v2']['J_pct'] for r in nz], 'o-', color='#1f7a2e', lw=2.4, label='v2: median of 5 readings + guard')
ax[0].set_xlabel('Sensor noise (x the DHT11/PAR/pyranometer base noise)'); ax[0].set_ylabel('Combined score, % of best'); ax[0].set_ylim(97.5, 100); ax[0].grid(alpha=.3); ax[0].legend(); ax[0].set_title('Accuracy as the sensors get noisier')
fl = d['faults']; x = range(len(fl)); ax[1].bar([i - .2 for i in x], [f['v1']['J_pct'] for f in fl], .4, color='#c0392b', label='v1: no guard'); ax[1].bar([i + .2 for i in x], [f['v2']['J_pct'] for f in fl], .4, color='#1f7a2e', label='v2: guard')
ax[1].set_xticks(list(x)); ax[1].set_xticklabels([f['fault'].replace(' (', '\n(') for f in fl]); ax[1].set_ylim(95, 100); ax[1].set_ylabel('Combined score, % of best'); ax[1].legend(); ax[1].grid(alpha=.3, axis='y'); ax[1].set_title('Faulty PAR sensor')
for i, f in enumerate(fl): ax[1].text(i - .2, f['v1']['J_pct'] + .05, '%.1f' % f['v1']['J_pct'], ha='center', fontsize=8); ax[1].text(i + .2, f['v2']['J_pct'] + .05, '%.1f' % f['v2']['J_pct'], ha='center', fontsize=8)
plt.tight_layout(); plt.savefig(os.path.join(R, 'fig_noise_fault.png'), dpi=150); plt.close()
# 3. yield and money
mo = [r for r in d['money'] if r['strategy'] not in ('SC v2 stress relax 0 (full crop light)', 'SC v2 stress relax 0.15', 'SC v2 ideal sensors')]
fig, ax = plt.subplots(1, 3, figsize=(13, 4.2)); labs = [name_map.get(r['strategy'], r['strategy']).replace(' (', '\n(').replace('Oracle\n(perfect knowledge)', 'Perfect\nknowledge') for r in mo]
for a, key, ttl in zip(ax, ['pv_kWh_m2', 'crop_net_lakh', 'total_lakh'], ['PV energy, kWh/m2 per year', 'Crop net income, INR lakh/ha/yr', 'Solar + crop total, INR lakh/ha/yr']):
    a.barh(labs[::-1], [r[key] for r in mo][::-1], color=['#6c7a68' if not r['strategy'].startswith(('SC', 'Oracle')) else ('#1f7a2e' if 'v2 noisy' in r['strategy'] else '#2a6fb0') for r in mo][::-1]); a.set_title(ttl, fontsize=10); a.grid(alpha=.3, axis='x'); a.tick_params(axis='y', labelsize=7.5)
    for i, r in enumerate(mo[::-1]): a.text(r[key], i, ' %.2f' % r[key] if key != 'pv_kWh_m2' else ' %.0f' % r[key], va='center', fontsize=8)
plt.tight_layout(); plt.savefig(os.path.join(R, 'fig_yield_money.png'), dpi=150); plt.close()
# 4. tilt through a crop-season day (October, clear) and the soil effect
rows = list(csv.DictReader(open(os.path.join(R, 'angles_by_hour_v2.csv'))))
sel = [r for r in rows if r['month'] == 'Oct' and r['sky'] == 'clear' and r['soil'].startswith('normal')]; h = [int(r['hour']) + .5 for r in sel]
fig, ax = plt.subplots(figsize=(8, 4.5)); ax.plot(h, [float(r['oracle_deg']) for r in sel], 'k-', lw=2.5, label='perfect-knowledge optimum'); ax.plot(h, [float(r['sensor_v2_deg']) for r in sel], 'o-', color='#1f7a2e', label='six-sensor controller (noisy sensors)'); ax.plot(h, [float(r['schedule_deg']) for r in sel], 's--', color='#2a6fb0', label='monthly plan')
ax.set_xlabel('Solar hour'); ax.set_ylabel('Panel tilt (deg)'); ax.set_title('October clear day (crop in season): tilt chosen through the day'); ax.grid(alpha=.3); ax.legend(); plt.tight_layout(); plt.savefig(os.path.join(R, 'fig_tilt_day_April_clear.png'), dpi=150); plt.close()
fig, ax = plt.subplots(figsize=(8, 4.5))
for soil, c, lab in [('normal', '#1f7a2e', 'soil 26 %'), ('dry', '#c0392b', 'soil 15 % (dry): more shade')]:
    rr = [r for r in rows if r['month'] == 'Oct' and r['sky'] == 'clear' and r['soil'].startswith(soil)]; ax.plot([int(r['hour']) + .5 for r in rr], [float(r['sensor_v2_deg']) for r in rr], 'o-', color=c, label=lab)
ax.set_xlabel('Solar hour'); ax.set_ylabel('Tilt chosen from the sensors (deg)'); ax.set_title('Effect of soil moisture (plant stress) on the tilt'); ax.grid(alpha=.3); ax.legend(); plt.tight_layout(); plt.savefig(os.path.join(R, 'fig_soil_stress_effect.png'), dpi=150); plt.close()
print('figs v2 ok')
