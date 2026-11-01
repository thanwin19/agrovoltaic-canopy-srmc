"""Three-objective trade-off: electricity, crop value and structural demand against tilt (and storm stow angle).   python pareto3.py
Structural demand at the 140 km/h design wind is scaled from the strength table of the final design (panels held at 60 deg:
carrier rope 0.37, stay 0.32, torque tube 0.76, column pad 0.69, drive wire 0.41 at 54 km/h).  A load model gives how the normal wind force R and its
vertical and horizontal parts change with the angle of the panel:   R = q A Cn,  V = R cos(theta),  H = R sin(theta).
 model B (code-like, conservative): |Cn| = 1.3 at every angle (IS 875 monopitch-roof style net coefficient);
 model A (flat plate): Cn = min(2 pi alpha, 1.2), alpha in radians, plateau after about 11 deg (thin-plate lift slope and stall).
Screening level only: neither model replaces a wind-tunnel or CFD study."""
import json, math, os
import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams.update({'font.family': 'serif', 'font.serif': ['Times New Roman', 'DejaVu Serif'], 'font.size': 8, 'axes.linewidth': 0.6})
HERE = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(os.path.join(HERE, 'pareto3_fixed_tilt.json')))['rows']
UTIL60 = {'carrier': 0.37, 'stay': 0.32, 'tube': 0.76, 'pad': 0.69, 'wire54': 0.41}   # strength table, final design, panels held at 60 deg
L, ALPHA = 0.44, math.radians(45)

def Cn(th, model):
    if model == 'B': return 1.3
    a = math.radians(max(th, 0.1)); return min(2 * math.pi * a, 1.2)

def parts(th, model):
    r = Cn(th, model); t = math.radians(th); return r, r * math.cos(t), r * math.sin(t)       # R, V (vertical), H (horizontal) per unit q A

def lever(th): return L * math.cos(math.radians(th) - ALPHA)

def util(th, model):
    R, V, H = parts(th, model); R0, V0, H0 = parts(60, model)
    u = {'carrier': UTIL60['carrier'] * abs(V) / abs(V0), 'pad': UTIL60['pad'] * abs(V) / abs(V0), 'stay': UTIL60['stay'] * H / H0, 'tube': UTIL60['tube'] * R / R0}
    u['wire54'] = UTIL60['wire54'] * (R / R0) * (lever(60) / lever(th))                     # drive wire and winch at the 54 km/h stow speed
    return u

def index(th, model, with_wire=False):
    u = util(th, model); keys = ['carrier', 'pad', 'stay', 'tube'] + (['wire54'] if with_wire else []); k = max(keys, key=lambda x: u[x]); return u[k], k

# ---------------------------------------------------------------- stow angle sweep
sweep = {m: [(th,) + index(th, m, True) for th in range(3, 91, 1)] for m in 'AB'}
res = {'stow_sweep': {}}
for m in 'AB':
    best = min(sweep[m], key=lambda x: x[1])
    res['stow_sweep'][m] = {'best_angle': best[0], 'best_index': round(best[1], 3), 'governing': best[2], 'at_90': round(index(90, m, True)[0], 3), 'at_3': round(index(3, m, True)[0], 3), 'at_60': round(index(60, m, True)[0], 3), 'at_45': round(index(45, m, True)[0], 3)}
# ---------------------------------------------------------------- candidate designs
fixed = [dict(name='Fixed %d deg' % r['tilt'], kind='fixed', tilt=r['tilt'], pv=r['pv_kWh_m2'], crop=r['crop_net_lakh'], light=r['mean_light_pct']) for r in D if r['tilt'] >= 15]
CTRL = dict(pv=241.6, crop=2.22, light=32.4)                                                # six-sensor controller, T14_yield_and_money.csv (noisy sensors)
designs = {}
for m in 'AB':
    ds = []
    for f in fixed:
        d = dict(f); d['load'], d['gov'] = index(f['tilt'], m); ds.append(d)
    for s in (3, 15, 30, 45, 60, 90):
        d = dict(name='Controller with stow %d deg' % s, kind='controller', tilt=s, pv=CTRL['pv'], crop=CTRL['crop'], light=CTRL['light']); d['load'], d['gov'] = index(s, m, True); ds.append(d)
    for d in ds:                                                                             # Pareto: maximise energy, maximise crop value, minimise structural demand
        d['dominated'] = any((o['pv'] >= d['pv'] and o['crop'] >= d['crop'] and o['load'] <= d['load']) and (o['pv'] > d['pv'] or o['crop'] > d['crop'] or o['load'] < d['load']) for o in ds if o is not d)
    front = [d for d in ds if not d['dominated']]
    pv = np.array([d['pv'] for d in front]); cr = np.array([d['crop'] for d in front]); ld = np.array([d['load'] for d in front])
    nz = lambda x: (x - x.min()) / max(x.max() - x.min(), 1e-9)
    dist = np.sqrt((1 - nz(pv)) ** 2 + (1 - nz(cr)) ** 2 + nz(ld) ** 2); knee = front[int(np.argmin(dist))]
    designs[m] = {'all': ds, 'front': front, 'knee': knee}
    res[m] = {'n_designs': len(ds), 'n_front': len(front), 'front': [(d['name'], d['pv'], d['crop'], round(d['load'], 3)) for d in sorted(front, key=lambda x: x['load'])], 'knee': knee['name']}
json.dump(res, open(os.path.join(HERE, 'pareto3_results.json'), 'w'), indent=1)
# ---------------------------------------------------------------- tables
with open(os.path.join(HERE, 'T23_pareto3_designs.csv'), 'w') as f:
    f.write('load model,design,energy kWh/m2/yr,crop net INR lakh/ha/yr,structural demand index at 140 km/h,governing part,on Pareto front\n')
    for m in 'AB':
        for d in designs[m]['all']: f.write('%s,%s,%.1f,%.2f,%.2f,%s,%s\n' % (m, d['name'], d['pv'], d['crop'], d['load'], d['gov'], 'yes' if not d['dominated'] else 'no'))
with open(os.path.join(HERE, 'T24_stow_angle_sweep.csv'), 'w') as f:
    f.write('stow angle deg,model A index,model A governing,model B index,model B governing\n')
    for (th, ia, ka), (_, ib, kb) in zip(sweep['A'], sweep['B']): f.write('%d,%.3f,%s,%.3f,%s\n' % (th, ia, ka, ib, kb))
# ---------------------------------------------------------------- figures
th = np.arange(3, 91)
fig, axs = plt.subplots(1, 3, figsize=(7.2, 2.6))
for m, c, lab in (('A', 'C0', 'A: flat plate'), ('B', 'C3', 'B: code-like')):
    axs[0].plot(th, [index(t, m, True)[0] for t in th], c, lw=1.4, label=lab)
axs[0].axhline(1, color='k', lw=0.6, ls='--'); axs[0].text(4, 1.03, 'capacity', fontsize=6.5)
axs[0].set_xlabel('Tilt held in the 140 km/h storm (deg)'); axs[0].set_ylabel('Structural demand index (1 = capacity)'); axs[0].set_title('(a) Demand against storm angle', fontsize=8, loc='left'); axs[0].legend(fontsize=6.3, frameon=False, loc='upper center'); axs[0].set_ylim(0, 1.8)
for k, ls, lab in (('carrier', ':', 'carrier rope, pad'), ('stay', '-', 'stays'), ('tube', '--', 'torque tube'), ('wire54', '-.', 'drive wire (54 km/h)')):
    axs[1].plot(th, [util(t, 'B')[k] for t in th], ls, lw=1.2, label=lab)
axs[1].axhline(1, color='k', lw=0.6, ls='--'); axs[1].set_xlabel('Tilt held (deg), load model B'); axs[1].set_ylabel('Utilization of each part'); axs[1].set_title('(b) Which part governs', fontsize=8, loc='left'); axs[1].legend(fontsize=6, frameon=False, loc='upper center'); axs[1].set_ylim(0, 2.4)
ax = axs[2]
for d in designs['B']['all']:
    c = 'C0' if d['kind'] == 'controller' else '0.45'; ax.scatter(d['pv'], d['load'], c=c, marker='o' if not d['dominated'] else 'x', s=22 if not d['dominated'] else 16, zorder=3)
kn = designs['B']['knee']; ax.scatter([kn['pv']], [kn['load']], s=110, facecolors='none', edgecolors='C3', lw=1.2, zorder=4)
ax.set_xlabel('Electricity (kWh/m$^2$ of panel per year)'); ax.set_ylabel('Structural demand index'); ax.set_title('(c) Energy against demand, model B', fontsize=8, loc='left'); ax.grid(lw=0.3, alpha=0.5)
fig.tight_layout(pad=0.5); fig.savefig(os.path.join(HERE, 'fig_pareto3_load.png'), dpi=220); plt.close(fig)
fig = plt.figure(figsize=(4.6, 3.6)); ax = fig.add_subplot(111, projection='3d')
for d in designs['B']['all']:
    c = 'C0' if d['kind'] == 'controller' else '0.4'; ax.scatter(d['pv'], d['crop'], d['load'], c=c, marker='o' if not d['dominated'] else 'x', s=24 if not d['dominated'] else 14)
ax.scatter([kn['pv']], [kn['crop']], [kn['load']], s=140, facecolors='none', edgecolors='C3', lw=1.4)
ax.set_xlabel('Electricity (kWh/m$^2$/yr)', fontsize=7); ax.set_ylabel('Crop net (lakh/ha/yr)', fontsize=7); ax.set_zlabel('Structural demand', fontsize=7); ax.tick_params(labelsize=6); ax.view_init(24, -58)
fig.tight_layout(); fig.savefig(os.path.join(HERE, 'fig_pareto3_3d.png'), dpi=220); plt.close(fig)
print(json.dumps({m: res[m] for m in 'AB'}, indent=1)); print(json.dumps(res['stow_sweep'], indent=1))
