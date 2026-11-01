"""Ground light map under the tilting canopy, three-dimensional ray cast, plan view.   python shade3d.py
Rows run north-south (as in the engine), pitch 2.5 m east-west, ten rows 25 m long, pivot height 5.58 m, panel width 2.497 m, tilt about the north-south axis (normal toward the
east for tilt > 0, the convention of srmc_engine.js).  For every ground point the beam is traced to the sun in 3-D (so shadows shift along the rows when the sun is north or south,
and the array ends and the field edge are modelled) and the sky is sampled with 96 cosine-weighted directions for the diffuse light.
Light value = ground irradiance / open-field global horizontal irradiance (clear sky of the month).  Checked against the 2-D engine (Review2 shadow_heatmap/shade_data.json) in the middle of the array.
Writes ../results/ground_heatmap/ (data for the viewer, figures, validation).  Screening level: panels are opaque flat plates, ground is flat, no reflections."""
import json, math, os
import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
plt.rcParams.update({'font.family': 'serif', 'font.serif': ['Times New Roman', 'DejaVu Serif'], 'font.size': 8})
HERE = os.path.dirname(os.path.abspath(__file__)); RES = os.path.join(HERE, '..', 'results', 'ground_heatmap'); os.makedirs(RES, exist_ok=True)
D2R = math.pi / 180
clim = json.load(open(os.path.join(HERE, '..', '..', 'Review1_Design_and_CAD', 'results', 'design', 'climates.json')))[0]
LAT, KT = clim['lat'], clim['kt']
PITCH, CHORD, H, NROW, ROWLEN = 2.5, 2.497, 5.581232716624871, 10, 25.0
CUM = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334, 365]
def month_of(n): return max(i for i in range(12) if n > CUM[i])
def declination(n): return 23.45 * math.sin(D2R * 360 / 365 * (284 + n))
def sun_vec(lat, n, hour):
    d = declination(n) * D2R; ph = lat * D2R; w = 15 * (hour - 12) * D2R
    return (-math.cos(d) * math.sin(w), math.sin(d) * math.cos(ph) - math.cos(d) * math.cos(w) * math.sin(ph), math.sin(ph) * math.sin(d) + math.cos(ph) * math.cos(d) * math.cos(w))   # east, north, up
def erbs(kt):
    if kt <= 0.22: return 1 - 0.09 * kt
    if kt <= 0.8: return 0.9511 - 0.1604 * kt + 4.388 * kt ** 2 - 16.638 * kt ** 3 + 12.336 * kt ** 4
    return 0.165
def irradiance(sz, n, kt):
    g0 = 1361 * (1 + 0.033 * math.cos(2 * math.pi * n / 365)); ghi = kt * g0 * sz; dhi = erbs(kt) * ghi; dni = min((ghi - dhi) / max(sz, 0.1), 1000); return ghi, dni, dhi
# panel rows: pivot x_i = (i + 0.5) * pitch  (east), y from 0 to ROWLEN (north), z = H
PIV = np.array([(i + 0.5) * PITCH for i in range(NROW)])
# sky directions: cosine-weighted hemisphere, fixed set
def sky_dirs(n=96):
    k = np.arange(n) + 0.5; r = np.sqrt(k / n); th = np.pi * (3 - np.sqrt(5)) * np.arange(n)       # Vogel spiral on the disc, projected up: cosine weighted
    return np.stack([r * np.cos(th), r * np.sin(th), np.sqrt(np.maximum(0, 1 - r ** 2))], 1)
SKY = sky_dirs()
def blocked(P, d, tilt):
    """P: (N,3) points, d: (M,3) directions -> (N,M) True where the ray from P along d (going up) hits any panel."""
    t = tilt * D2R; nrm = np.array([math.sin(t), 0.0, math.cos(t)]); u = np.array([math.cos(t), 0.0, -math.sin(t)])      # panel normal and chord direction (in the x-z plane)
    hit = np.zeros((P.shape[0], d.shape[0]), bool); dn = d @ nrm                                                          # (M,)
    for xp in PIV:
        piv = np.array([xp, 0.0, H]); num = (piv - P) @ nrm                                                              # (N,)
        with np.errstate(divide='ignore', invalid='ignore'): lam = num[:, None] / dn[None, :]
        ok = (lam > 0) & (np.abs(dn)[None, :] > 1e-9)
        Q = P[:, None, :] + lam[:, :, None] * d[None, :, :]                                                              # (N,M,3)
        along = (Q[:, :, 0] - xp) * u[0] + (Q[:, :, 2] - H) * u[2]
        hit |= ok & (np.abs(along) <= CHORD / 2) & (Q[:, :, 1] >= 0) & (Q[:, :, 1] <= ROWLEN)
    return hit
def light_map(n, hour, tilt, gx, gy, kt):
    sx, sy, sz = sun_vec(LAT, n, hour)
    if sz < 0.05: return None
    ghi, dni, dhi = irradiance(sz, n, kt)
    P = np.stack([gx.ravel(), gy.ravel(), np.zeros(gx.size)], 1)
    lit = ~blocked(P, np.array([[sx, sy, sz]]), tilt)[:, 0]
    svf = 1.0 - blocked(P, SKY, tilt).mean(1)
    return ((dni * sz * lit + dhi * svf) / ghi).reshape(gx.shape), (sx, sy, sz), (ghi, dni, dhi)
# ------------------------------------------------------------------ validation against the 2-D engine, middle of the array
sd = json.load(open(os.path.join(HERE, '..', 'results', 'shadow_heatmap', 'shade_data.json')))
xs_val = (np.arange(40) + 0.5) / 40 * PITCH                                          # across one pitch, as in the engine (row 4 -> pitch from x = 10 to 12.5)
gx_v = 10.0 + xs_val[:, None]; gy_v = np.full((40, 1), 12.5); gxv = np.repeat(gx_v, 1, axis=1)
vals = []
for dname in sd['days']:
    n = {'21 Mar': 80, '21 Jun': 172, '23 Sep': 266, '21 Dec': 355}[dname]
    for h in ['8', '10', '12', '14', '16']:
        if h not in sd['data'][dname]: continue
        for ti, tilt in enumerate(sd['tilts']):
            if tilt not in (15, 30, 45, 60): continue
            eng = np.array(sd['data'][dname][h][ti]['l']); r = light_map(n, float(h), tilt, gxv, gy_v, KT[month_of(n)])
            if r is None: continue
            mine = r[0][:, 0]; vals.append(dict(day=dname, hour=float(h), tilt=tilt, engine_mean=float(eng.mean()), mine_mean=float(mine.mean()), mean_abs_diff=float(min(np.abs(eng - np.roll(mine, k)).mean() for k in range(40)))))
val = dict(cases=len(vals), mean_abs_diff_of_light_fraction=round(float(np.mean([v['mean_abs_diff'] for v in vals])), 3), mean_of_means_engine=round(float(np.mean([v['engine_mean'] for v in vals])), 3), mean_of_means_3d=round(float(np.mean([v['mine_mean'] for v in vals])), 3),
           worst=max(vals, key=lambda v: v['mean_abs_diff']), note='profile difference is the smallest over circular shifts across the pitch, because the two models place the row at different positions inside the pitch')
print('validation vs 2-D engine:', val)
# ------------------------------------------------------------------ maps
X0, X1, Y0, Y1, RES_M = -5.0, 30.0, -5.0, 30.0, 0.5
xs = np.arange(X0 + RES_M / 2, X1, RES_M); ys = np.arange(Y0 + RES_M / 2, Y1, RES_M); gx, gy = np.meshgrid(xs, ys)           # gx east, gy north; image rows go north at the top
DAYS = [(80, '21 Mar'), (172, '21 Jun'), (266, '23 Sep'), (355, '21 Dec')]; HOURS = [h / 2 for h in range(12, 37)]; TILTS = [3, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 90]
inside = (gx >= 0) & (gx <= NROW * PITCH) & (gy >= 0) & (gy <= ROWLEN)
import sys, zlib
frames = {}; stats = {}
if '--figs' in sys.argv and os.path.exists(os.path.join(RES, 'maps.bin.z')):                       # redraw the figures from the saved maps (no ray tracing)
    meta = json.load(open(os.path.join(RES, 'meta.json'))); raw = zlib.decompress(open(os.path.join(RES, 'maps.bin.z'), 'rb').read()); sz_ = meta['ny'] * meta['nx']
    for i, k in enumerate(meta['keys']): frames[k] = np.frombuffer(raw[i * sz_:(i + 1) * sz_], np.uint8).reshape(meta['ny'], meta['nx'])
    stats = meta['stats']
else:
    for n, name in DAYS:
        kt = KT[month_of(n)]
        for h in HOURS:
            sx, sy, sz = sun_vec(LAT, n, h)
            if sz < 0.05: continue
            for t in TILTS:
                m, _, (ghi, dni, dhi) = light_map(n, h, t, gx, gy, kt)
                frames['%s|%g|%d' % (name, h, t)] = np.clip(np.round(m * 255 / 1.0), 0, 255).astype(np.uint8)
                v = m[inside]; stats['%s|%g|%d' % (name, h, t)] = dict(mean=round(float(v.mean()), 3), red=round(float((v < 0.15).mean()), 3), green=round(float((v >= 0.45).mean()), 3), ghi=round(ghi))
        print(name, 'done')

import base64
if '--figs' not in sys.argv:
    order = sorted(frames.keys())
    blob = b''.join(frames[k].tobytes() for k in order)
    json.dump(dict(keys=order, ny=len(ys), nx=len(xs), res=RES_M, x0=X0, y0=Y0, rowlen=ROWLEN, pitch=PITCH, nrow=NROW, stats=stats), open(os.path.join(RES, 'meta.json'), 'w'))
    open(os.path.join(RES, 'maps.bin.z'), 'wb').write(zlib.compress(blob, 9))
    json.dump(dict(validation=val), open(os.path.join(RES, 'validation.json'), 'w'), indent=1)
    print('frames', len(order), 'bytes', len(blob))

# ------------------------------------------------------------------ figure: the wow figure (time series at fixed and controller tilt)
cmap = LinearSegmentedColormap.from_list('shade', [(0, '#b2182b'), (0.15, '#d6604d'), (0.3, '#fddb7a'), (0.45, '#fee08b'), (0.62, '#a6d96a'), (1.0, '#1a9850')])
ctrl = sd['ctrl']['21 Mar']
fig, axs = plt.subplots(2, 4, figsize=(7.4, 4.1), gridspec_kw={'wspace': 0.08, 'hspace': 0.28})
for r, (tilt_of, lab) in enumerate((((lambda h: 45), 'Fixed 45°'), ((lambda h: float(ctrl.get('%g' % h, ctrl.get(str(h), 30)))), 'Controller'))):
    for c, h in enumerate((8.0, 10.0, 12.0, 16.0)):
        tilt = tilt_of(h); tilt_r = min(TILTS, key=lambda a: abs(a - tilt)) if lab == 'Controller' else 45
        key = '21 Mar|%g|%d' % (h, tilt_r); ax = axs[r, c]
        ax.imshow(frames[key].astype(float) / 255, origin='lower', extent=[X0, X1, Y0, Y1], cmap=cmap, vmin=0, vmax=1)
        ax.add_patch(plt.Rectangle((0, 0), NROW * PITCH, ROWLEN, fill=False, ec='k', lw=0.6, ls='--')); ax.set_xticks([]); ax.set_yticks([])
        ax.set_title('%s, %d:%02d, %d°\nmean %.0f %%' % (lab, int(h), int(round((h % 1) * 60)), tilt_r, 100 * stats[key]['mean']), fontsize=7)
fig.subplots_adjust(right=0.9); cax = fig.add_axes([0.92, 0.15, 0.015, 0.7]); sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(0, 1)); fig.colorbar(sm, cax=cax).set_label('Light on the ground (fraction of open-field sunlight)', fontsize=7)
fig.savefig(os.path.join(RES, 'fig_ground_map_21Mar.png'), dpi=220, bbox_inches='tight'); plt.close(fig)
# tilt comparison at noon
fig, axs = plt.subplots(1, 4, figsize=(7.4, 2.2), gridspec_kw={'wspace': 0.06})
for c, t in enumerate((15, 30, 45, 60)):
    key = '21 Mar|12|%d' % t; ax = axs[c]; ax.imshow(frames[key].astype(float) / 255, origin='lower', extent=[X0, X1, Y0, Y1], cmap=cmap, vmin=0, vmax=1); ax.add_patch(plt.Rectangle((0, 0), NROW * PITCH, ROWLEN, fill=False, ec='k', lw=0.6, ls='--')); ax.set_xticks([]); ax.set_yticks([])
    ax.set_title('Tilt %d°, noon\nmean %.0f %%, shaded below 15 %%: %.0f %%' % (t, 100 * stats[key]['mean'], 100 * stats[key]['red']), fontsize=7)
fig.savefig(os.path.join(RES, 'fig_ground_map_tilts.png'), dpi=220, bbox_inches='tight'); plt.close(fig)
