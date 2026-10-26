import csv, json, os, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
here = os.path.dirname(os.path.abspath(__file__)); R = os.path.join(here, 'results')
rows = list(csv.DictReader(open(os.path.join(R, 'irrigation_daily.csv')))); d = [int(r['day']) for r in rows]
cum = lambda k: [sum(float(r[k]) for r in rows[:i + 1]) for i in range(len(rows))]
S = json.load(open(os.path.join(R, 'irrigation_study.json')))['rows']
fig, ax = plt.subplots(1, 3, figsize=(14.5, 4.4))
ax[0].plot(d, cum('timer_m3'), color='#c0392b', lw=2.4, label='timer: every 4 days, fixed depth'); ax[0].plot(d, cum('probe_m3'), color='#1f7a2e', lw=2.4, label='soil probe decides')
a2 = ax[0].twinx(); a2.bar(d, [float(r['rain_mm']) for r in rows], color='#4fa3e0', width=1.2, alpha=.6); a2.set_ylabel('rain mm/day', color='#4fa3e0'); a2.set_ylim(0, 150)
ax[0].set_xlabel('day of year'); ax[0].set_ylabel('cumulative irrigation water, m3 per hectare'); ax[0].legend(loc='upper left', fontsize=8); ax[0].grid(alpha=.3); ax[0].set_title('Water applied through the year')
n = ['timer', 'probe\n(ideal)', 'probe\n(noisy)']; v = [S[0]['applied_m3_ha'], S[1]['applied_m3_ha'], S[2]['applied_m3_ha']]
ax[1].bar(n, v, color=['#c0392b', '#1f7a2e', '#72b830']); ax[1].set_ylim(4500, 5800); ax[1].set_ylabel('m3 per hectare per year')
for i, x in enumerate(v): ax[1].text(i, x + 20, '%d' % x, ha='center'); ax[1].text(i, 4560, 'stress days %.0f\nrel. yield %.3f' % (S[i]['stress_days'], S[i]['relative_yield_from_water']), ha='center', fontsize=8, color='white')
ax[1].set_title('Water saved by the probe: %.1f %% (%d m3)' % (S[1]['water_saved_vs_timer_pct'], S[1]['water_saved_vs_timer_m3']))
f = S[3:]; lab = ['DRY\nno fb', 'DRY\nfb', 'WET\nno fb', 'WET\nfb', 'dead\nfb']; col = ['#c0392b', '#2a6fb0', '#c0392b', '#2a6fb0', '#2a6fb0']
ax[2].bar(lab, [x['relative_yield_from_water'] for x in f], color=col); ax[2].set_ylim(0, 1.15); ax[2].set_ylabel('relative yield from water (1 = no loss)'); ax[2].set_title('Probe stuck DRY, stuck WET, dead (fb = fallback)', fontsize=10)
for i, x in enumerate(f): ax[2].text(i, x['relative_yield_from_water'] + .02, '%d m3' % x['applied_m3_ha'], ha='center', fontsize=8)
plt.tight_layout(); plt.savefig(os.path.join(R, 'fig_irrigation_probe_vs_timer.png'), dpi=150); print('fig ok')
