import json, csv, os, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
here=os.path.dirname(os.path.abspath(__file__)); R=os.path.join(here,'results')
d=json.load(open(os.path.join(R,'accuracy_summary.json')))['results']
col={'SRMC-SC (noisy sensors)':'#1f7a2e','SRMC-SC (ideal sensors)':'#72b830','Monthly schedule (SRMC-DT)':'#2a6fb0','Fixed 45 deg':'#e8a93a','Fixed 15 deg (PV-max)':'#c0392b','Sun tracking (E-W)':'#777'}
fig,ax=plt.subplots(1,2,figsize=(12,4.8))
for r in d:
    ax[0].scatter(r['pv_index_pct'],r['crop_index_pct'],s=140,color=col[r['strategy']],label=r['strategy'],edgecolor='k')
ax[0].set_xlabel('Electricity: % of best possible'); ax[0].set_ylabel('Crop light value: % of best possible'); ax[0].set_xlim(70,102); ax[0].set_ylim(20,102); ax[0].grid(alpha=.3); ax[0].set_title('Both goals: top-right is best'); ax[0].legend(fontsize=7.5,loc='lower left')
names=[r['strategy'].replace(' (','\n(') for r in d]; ax[1].barh(names[::-1],[r['J_efficiency_pct'] for r in d][::-1],color=[col[r['strategy']] for r in d][::-1]); ax[1].set_xlim(60,102); ax[1].set_xlabel('Combined score J, % of the perfect-knowledge optimum')
for i,r in enumerate(d[::-1]): ax[1].text(r['J_efficiency_pct']+.3,i,'%.1f'%r['J_efficiency_pct'],va='center',fontsize=9)
ax[1].set_title('Combined score (50 % electricity + 50 % crop)'); plt.tight_layout(); plt.savefig(os.path.join(R,'fig_accuracy_both_goals.png'),dpi=150)
rows=[r for r in csv.DictReader(open(os.path.join(R,'angles_by_hour.csv'))) if r['month']=='Apr' and r['sky']=='clear' and r['soil'].startswith('normal')]
fig,ax=plt.subplots(figsize=(8,4.5)); h=[int(r['hour'])+.5 for r in rows]
ax.plot(h,[float(r['oracle_deg']) for r in rows],'k-',lw=2.5,label='perfect-knowledge optimum'); ax.plot(h,[float(r['sensor_noisy_deg']) for r in rows],'o-',color='#1f7a2e',label='5-sensor controller (noisy sensors)'); ax.plot(h,[float(r['schedule_deg']) for r in rows],'s--',color='#2a6fb0',label='monthly schedule')
ax.set_xlabel('Solar hour'); ax.set_ylabel('Panel tilt (deg)'); ax.set_title('April clear day: tilt chosen through the day'); ax.grid(alpha=.3); ax.legend(); plt.tight_layout(); plt.savefig(os.path.join(R,'fig_tilt_day_April_clear.png'),dpi=150)
rows=[r for r in csv.DictReader(open(os.path.join(R,'angles_by_hour.csv'))) if r['month']=='Apr' and r['sky']=='clear']
fig,ax=plt.subplots(figsize=(8,4.5))
for soil,c in [('normal',"#1f7a2e"),('dry','#c0392b')]:
    rr=[r for r in rows if r['soil'].startswith(soil)]; ax.plot([int(r['hour'])+.5 for r in rr],[float(r['sensor_noisy_deg']) for r in rr],'o-',color=c,label='soil %s'%('26 %' if soil=='normal' else '15 % (dry): more shade'))
ax.set_xlabel('Solar hour'); ax.set_ylabel('Tilt chosen by sensors (deg)'); ax.set_title('Effect of soil moisture (DHT11/soil stress) on the tilt'); ax.grid(alpha=.3); ax.legend(); plt.tight_layout(); plt.savefig(os.path.join(R,'fig_soil_stress_effect.png'),dpi=150)
print('figs ok')
