"""Builds week_report.html (with charts) from the output of score_week.js.   python make_week_report.py [score_folder]"""
import csv, json, os, sys, io, base64
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from datetime import datetime
here = os.path.dirname(os.path.abspath(__file__)); folder = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, 'score_week_fake')
S = json.load(open(os.path.join(folder, 'week_summary.json'))); rows = list(csv.DictReader(open(os.path.join(folder, 'week_scores.csv'))))
f = lambda r, k: float(r[k]) if r[k] not in ('', None) else None
t = [datetime.fromisoformat(r['timestamp']) for r in rows]
fig, ax = plt.subplots(4, 1, figsize=(11, 10), sharex=True)
ax[0].plot(t, [f(r, 'ghi') for r in rows], color='#e8a93a', label='pyranometer W/m2'); ax[0].plot(t, [f(r, 'par') for r in rows], color='#2e9d44', lw=.9, label='PAR umol/m2/s'); ax[0].set_ylabel('sun'); ax[0].legend(loc='upper right', fontsize=8)
ax[1].plot(t, [f(r, 'tempC') for r in rows], color='#c0392b', label='DHT11 temp C'); a2 = ax[1].twinx(); a2.plot(t, [f(r, 'rh') for r in rows], color='#2a6fb0', lw=.8, label='RH %'); ax[1].set_ylabel('air'); ax[1].legend(loc='upper left', fontsize=8)
ax[2].plot(t, [f(r, 'soilPct') for r in rows], color='#6b4a2a', label='soil, available water %'); a3 = ax[2].twinx(); a3.plot(t, [f(r, 'wind') for r in rows], color='#7a4a9e', lw=.8, label='wind m/s'); a3.bar(t, [20 * float(r['rain']) for r in rows], width=0.004, color='#4fa3e0', label='rain'); ax[2].set_ylabel('soil'); ax[2].legend(loc='upper left', fontsize=8); a3.legend(loc='upper right', fontsize=8)
ax[3].plot(t, [f(r, 'angleBest') for r in rows], '.', ms=3, color='k', label='best possible'); ax[3].plot(t, [f(r, 'angleController') for r in rows], '-', color='#1f7a2e', lw=1, label='controller'); lg = [f(r, 'angleLogged') for r in rows]
if any(v is not None for v in lg): ax[3].plot(t, lg, '-', color='#2a6fb0', lw=.6, alpha=.6, label='logged (in use)')
ax[3].set_ylabel('tilt (deg)'); ax[3].legend(loc='upper right', fontsize=8); fig.autofmt_xdate(); plt.tight_layout()
b = io.BytesIO(); plt.savefig(b, format='png', dpi=110); plt.savefig(os.path.join(folder, 'week_charts.png'), dpi=130); img = base64.b64encode(b.getvalue()).decode()
sc = S['scores']; dq = S['data_quality']
tr = ''.join('<tr><td>%s</td><td>%s</td><td>%s</td><td><b>%s</b></td><td>%s</td><td>%s</td></tr>' % (k, v['electricity_pct'], v['crop_pct'], v['J_pct'], v['angle_rmse_deg'], v['kWh_per_m2_week']) for k, v in sc.items() if v)
fd = ''.join('<li><b>%s</b>: %s</li>' % (d, '; '.join(x)) for d, x in S['flagged_days'].items()) or '<li>none</li>'
c = sc['controller']
html = '''<!doctype html><html lang="en"><head><meta charset="utf-8"><title>SRMC week report</title><style>body{font:15px/1.5 Calibri,Segoe UI,sans-serif;background:#f4f8ef;color:#1d221d;margin:0}header{background:#1f4d2b;color:#fff;padding:16px 22px}main{max-width:1050px;margin:auto;padding:14px}table{border-collapse:collapse;width:100%%;background:#fff}th,td{padding:6px 10px;border-bottom:1px solid #ccc;text-align:left}th{background:#72b830}img{width:100%%;background:#fff;border-radius:6px}.k{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:10px}.k div{background:#fff;border-left:6px solid #72b830;padding:10px;border-radius:6px}.k b{font-size:26px;display:block}</style></head><body>
<header><h2 style="margin:0">Week report: %s</h2><div>%d readings, %d days, one every %d s. Soil calibration dry %d / wet %d.</div></header><main>
<div class="k"><div><b>%s %%</b>combined score of the best (controller)</div><div><b>%s %%</b>of the best electricity</div><div><b>%s %%</b>of the best crop light</div><div><b>%s&deg;</b>tilt error vs best</div><div><b>%s</b>data complete, DHT11 failures %s %%</div></div>
<h3>Scores (100 %% = best angle for each reading)</h3><table><tr><th>Strategy</th><th>Electricity %%</th><th>Crop light %%</th><th>Combined %%</th><th>Tilt error deg</th><th>Week kWh/m2 panel</th></tr>%s</table>
<h3>Sensors and tilt through the week</h3><img src="data:image/png;base64,%s">
<h3>Flagged days (check these first)</h3><ul>%s</ul>
<p>Data quality: %s</p><p><small>Scores use the logged sensor values as truth, so a faulty sensor lowers the confidence in them. Fake data is for rehearsal only. Real data replaces it by running srmc_logger.py with your board.</small></p></main></body></html>''' % (
    S['file'], S['rows'], S['days'], S['interval_s'], S['soil_calibration']['dry_raw'], S['soil_calibration']['wet_raw'], c['J_pct'], c['electricity_pct'], c['crop_pct'], c['angle_rmse_deg'], str(dq['complete_pct']) + ' %', dq['dht11_failure_pct'], tr, img, fd, ', '.join('%s %s' % (k.replace('_', ' '), v) for k, v in dq.items()))
open(os.path.join(folder, 'week_report.html'), 'w', encoding='utf-8').write(html); print('wrote', os.path.join(folder, 'week_report.html'))
