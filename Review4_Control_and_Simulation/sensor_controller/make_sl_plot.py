import csv, os, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
here=os.path.dirname(os.path.abspath(__file__)); R=os.path.join(here,'results','simulink')
rows=list(csv.DictReader(open(os.path.join(R,'sensor_controller_log.csv'))))
h=[float(r['hour']) for r in rows]; ang=[float(r['angle_deg']) for r in rows]; ghi=[float(r['ghi_Wm2']) for r in rows]; soil=[float(r['soil_pct']) for r in rows]; wind=[float(r['wind_ms']) for r in rows]; T=[float(r['T_C']) for r in rows]
fig,ax=plt.subplots(2,1,figsize=(9.5,6.2),sharex=True,gridspec_kw={'height_ratios':[2,1.2]})
ax[0].plot(h,ang,color='#1f7a2e',lw=2.4); ax[0].set_ylabel('Panel angle (deg)'); ax[0].set_ylim(0,95); ax[0].grid(alpha=.3)
ax[0].axvspan(11,11.5,color='#bbb',alpha=.5); ax[0].text(11.05,84,'cloud',fontsize=9); ax[0].axvspan(14,15,color='#9ad0ff',alpha=.5); ax[0].text(14.05,84,'rain: flat 3 deg',fontsize=9); ax[0].axvspan(12,24,color='#ffd9b0',alpha=.25); ax[0].text(18.4,5,'soil dry (17 %): more shade',fontsize=9)
ax[0].axvspan(17,17.5,color='#f4b6a8',alpha=.6); ax[0].text(16.0,80-18,'wind 18 m/s: stow 90 deg',fontsize=9)
ax[0].set_title('Simulink: six-sensor controller on a test day (16 April, TCE ground)')
ax[1].plot(h,ghi,color='#e8a93a',label='pyranometer W/m2'); ax2=ax[1].twinx(); ax2.plot(h,T,color='#c0392b',label='DHT11 temp C'); ax2.plot(h,soil,color='#6db33f',label='soil moisture %'); ax2.plot(h,wind,color='#7a4a9e',label='anemometer m/s'); ax[1].set_ylabel('GHI W/m2'); ax2.set_ylabel('T C / soil %'); ax[1].set_xlabel('Solar hour'); ax[1].set_xlim(0,24); ax[1].grid(alpha=.3)
l1,n1=ax[1].get_legend_handles_labels(); l2,n2=ax2.get_legend_handles_labels(); ax[1].legend(l1+l2,n1+n2,fontsize=8,loc='upper left')
plt.tight_layout(); plt.savefig(os.path.join(R,'sensor_controller_day.png'),dpi=150); print('ok')
