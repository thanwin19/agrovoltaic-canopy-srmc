"""Mechanism animations for the FINAL design (45 deg offset lever arm, 6 mm drive wire, 10 kN winch, anemometer storm stow).
Writes ../results/mechanism/mechanism_closeup.gif and mechanism_tilt.gif (old versions are kept in results/mechanism/_old).   python make_mech_gifs.py"""
import os, math, shutil, io
import numpy as np
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, Rectangle
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, '..', 'results', 'mechanism'); OLD = os.path.join(OUT, '_old'); os.makedirs(OLD, exist_ok=True)
for f in ['mechanism_closeup.gif', 'mechanism_tilt.gif']:
    if os.path.exists(os.path.join(OUT, f)) and not os.path.exists(os.path.join(OLD, f)): shutil.copy(os.path.join(OUT, f), os.path.join(OLD, f))
OFF = math.radians(45); LREAL = 0.44; A_REAL = 2.497 / 2
SEQ = [(3, 'RAIN MODE: flat roof, 3 deg fall to the gutter', 3.0), (15, 'TILT 15 deg', 3.0), (30, 'TILT 30 deg', 3.5), (45, 'TILT 45 deg', 4.0), (60, 'TILT 60 deg (maximum working tilt)', 5.0), (90, 'STORM STOW 90 deg: anemometer reads 18 m/s (limit 15 m/s)', 18.0), (45, 'wind below 12 m/s: back to normal tilt', 4.0), (3, 'RAIN MODE: flat roof, 3 deg fall to the gutter', 3.0)]
def schedule(n_move=13, n_hold=7):
    th = []; info = []
    for i, (a, name, wind) in enumerate(SEQ):
        if i == 0:
            for k in range(n_hold): th.append(a); info.append((name, wind, i))
            continue
        prev = SEQ[i - 1][0]
        for k in range(n_move): th.append(prev + (a - prev) * (0.5 - 0.5 * math.cos(math.pi * (k + 1) / n_move))); info.append((name, wind, i))
        for k in range(n_hold): th.append(a); info.append((name, wind, i))
    return th, info
def tip_of(theta_deg, L, cx=0.0, cz=0.0):
    a = math.radians(theta_deg) - OFF; return cx - L * math.sin(a), cz - L * math.cos(a)
def fig_to_img(fig):
    b = io.BytesIO(); fig.savefig(b, format='png', dpi=80, facecolor=fig.get_facecolor()); b.seek(0); return Image.open(b).convert('P', palette=Image.ADAPTIVE)
def closeup(theta, name, wind, t):
    fig, ax = plt.subplots(figsize=(9, 5.4)); fig.patch.set_facecolor('#1b2733'); ax.set_facecolor('#1b2733'); ax.set_xlim(-3.6, 3.6); ax.set_ylim(-2.35, 2.0); ax.set_aspect('equal'); ax.axis('off')
    L = 1.0; a = 1.3; th = math.radians(theta)
    ax.plot([-3.4, 3.4], [1.1, 1.1], ls=':', color='#8f99a3', lw=1.5); ax.text(-3.4, 1.17, 'carrier rope above (carries the weight)', color='#98a4ae', fontsize=8)
    rest = tip_of(0, L); tip = tip_of(theta, L)
    ax.plot([-3.4, 3.4], [tip[1]] * 2, color='#ff5a4a', lw=3.2, solid_capstyle='butt')
    ph = (t * 0.9) % 0.4; spd = 1
    for xx in np.arange(-3.4 + ph, 3.4, 0.4): ax.add_patch(Circle((xx, tip[1]), 0.03, color='#ffe3dd'))
    ax.add_patch(Circle(rest, 0.07, fill=False, ec='white', ls='--', lw=1.2)); ax.text(rest[0] + 0.15, rest[1] - 0.12, 'rest position of the tip (panel flat)', color='#cfd8e0', fontsize=8)
    ax.add_patch(Circle((0, 0), L, fill=False, ec=(1, 1, 1, .25), ls=':', lw=1))
    ax.plot([-a * math.cos(th), a * math.cos(th)], [a * math.sin(th), -a * math.sin(th)], color='#2349a6', lw=9, solid_capstyle='butt'); ax.plot([-a * math.cos(th), a * math.cos(th)], [a * math.sin(th), -a * math.sin(th)], color='#9fbcf5', lw=1.2)
    ax.plot([0, tip[0]], [0, tip[1]], color='#f0b030', lw=5); ax.add_patch(Circle((0, 0), 0.11, fc='#c9d0d6', ec='#222', lw=1.5)); ax.add_patch(Circle(tip, 0.075, fc='#ff5a4a', ec='white', lw=1.5))
    ax.text(0.16, 0.14, 'PIVOT TUBE', color='#e6edf3', fontsize=9, fontweight='bold'); ax.text(a * math.cos(th) * 0.55, -a * math.sin(th) * 0.55 + 0.12, 'PANEL', color='#9fbcf5', fontsize=9, fontweight='bold')
    ax.text(-3.55, 1.62, 'LEVER ARM (rigid with the tube, fixed 45 deg offset, drawn 2.3x real)', color='#ffd36a', fontsize=9, fontweight='bold'); ax.text(-3.4, tip[1] - 0.2, 'DRIVE WIRE clamped to the arm tip', color='#ff9a8c', fontsize=9, fontweight='bold')
    d_m = LREAL * (math.sin(th - OFF) + math.sin(OFF)); lever = LREAL * math.cos(th - OFF)
    if abs(tip[0] - rest[0]) > 0.03:
        zb = -1.75; ax.plot([rest[0]] * 2, [rest[1] - .08, zb - .08], color='#7CFFB2', lw=1); ax.plot([tip[0]] * 2, [tip[1] - .08, zb - .08], color='#7CFFB2', lw=1)
        ax.add_patch(FancyArrowPatch((rest[0], zb), (tip[0], zb), arrowstyle='-|>', mutation_scale=14, color='#7CFFB2', lw=3)); ax.text((rest[0] + tip[0]) / 2, zb - .3, 'wire slid d = %d mm' % round(d_m * 1000), color='#7CFFB2', fontsize=10, ha='center', fontweight='bold')
    # readout and anemometer
    stow = theta > 60.5
    force = None if stow or theta < 6 else 2 * (0.6 * 15 ** 2 * (2.278 * 4.54) * 0.57 + 86) / lever / 1000
    ax.add_patch(Rectangle((1.55, 0.5), 2.0, 1.4, fc='#252a30', ec='#555')); ax.text(1.65, 1.68, 'angle  %.1f deg' % theta, color='white', fontsize=9, fontweight='bold'); ax.text(1.65, 1.42, 'lever  %d mm' % round(lever * 1000), color='#ffd36a', fontsize=9, fontweight='bold')
    ax.text(1.65, 1.16, 'wire pull in 54 km/h wind:', color='#c9d0d6', fontsize=7.5); ax.text(1.65, .9, ('%.1f kN (10 kN winch)' % force) if force else ('edge-on: very small' if stow else 'flat: none'), color='#7CFFB2', fontsize=9, fontweight='bold'); ax.text(1.65, .62, 'lever never below 311 mm', color='#8fa3b3', fontsize=7.5)
    ax.plot([-3.2, -3.2], [0.0, 0.85], color='#cfd8e0', lw=2); ax.add_patch(Circle((-3.2, 0.95), 0.1, fc='none', ec='#cfd8e0', lw=2)); ang = t * (6 if wind > 15 else 2.2) * 2 * math.pi / 3
    for q in range(3): ax.plot([-3.2, -3.2 + 0.32 * math.cos(ang + q * 2.094)], [0.95, 0.95 + 0.32 * math.sin(ang + q * 2.094)], color='#7bc4ff', lw=2.5)
    ax.text(-3.45, -0.15, 'anemometer  %.0f m/s' % wind, color='#ff8a78' if wind > 15 else '#7bc4ff', fontsize=9, fontweight='bold')
    if theta < 6:
        for i in range(25): rx = -3.3 + (i * 0.29) % 6.6; rz = 1.9 - ((i * 0.37 + t * 2.6) % 1.2); ax.plot([rx, rx - .03], [rz, rz - .12], color=(.6, .8, 1, .7), lw=1)
    ax.text(0, -2.25, name, color='white', fontsize=11, ha='center', fontweight='bold')
    ax.text(-3.55, 1.88, 'Agrovoltaic Canopy for Protection and Sustainable Farming: one panel, final mechanism', color='#8fd0a0', fontsize=8.5, ha='left')
    img = fig_to_img(fig); plt.close(fig); return img
def rowview(theta, name, wind, t):
    fig, ax = plt.subplots(figsize=(10, 4.8)); fig.patch.set_facecolor('#16222e'); ax.set_facecolor('#16222e'); ax.set_xlim(-8.2, 8.2); ax.set_ylim(-1.9, 4.7); ax.set_aspect('equal'); ax.axis('off')
    ax.add_patch(Rectangle((-8.2, -1.0), 16.4, 0.8, fc='#4f9d2f')); ax.text(-8.0, -0.75, 'crops below (not to scale)', color='#e8eef0', fontsize=8)
    H = 3.2; L = 0.8; a = 1.3; th = math.radians(theta); xs = [-4.5, -1.5, 1.5, 4.5]
    for cx in (-7.5, 0, 7.5): ax.add_patch(Rectangle((cx - .08, -0.2), .16, H + 0.85, fc='#8d969e'))
    for x0, x1 in ((-7.5, 0), (0, 7.5)):
        u = np.linspace(0, 1, 40); ax.plot(x0 + (x1 - x0) * u, H + .65 - 4 * 0.0833 * (x1 - x0) * 0.12 * u * (1 - u) * 12, color='#c9d0d6', lw=2.2)
    tips = []
    for cx in xs:
        ax.plot([cx, cx], [H + .62 - 0.3, H + .05], color='#c9d0d6', lw=1.2)
        ax.plot([cx - a * math.cos(th), cx + a * math.cos(th)], [H + a * math.sin(th), H - a * math.sin(th)], color='#1f3d8a', lw=8, solid_capstyle='butt')
        t_ = tip_of(theta, L, cx, H); tips.append(t_); ax.plot([cx, t_[0]], [H, t_[1]], color='#f0b030', lw=3.2); ax.add_patch(Circle((cx, H), .1, fc='#c9d0d6', ec='#222')); ax.add_patch(Circle(t_, .07, fc='#ff5a4a'))
        r_ = tip_of(0, L, cx, H); ax.add_patch(Circle(r_, .07, fill=False, ec='white', ls='--', lw=1))
    xE, xW, zp, retZ = 7.0, -7.0, H - 1.5, H - 2.0
    path = [(xE, zp)] + tips[::-1] + [(xW, zp)]; ax.plot(*zip(*path), color='#ff5a4a', lw=2.6); ax.plot([xW, xW, xE], [zp, retZ, retZ], color='#b84a3c', lw=2, ls=(0, (5, 4)))
    ax.plot([xE, xE], [zp, retZ], color='#b84a3c', lw=2); ax.add_patch(Circle((xE + .55, (zp + retZ) / 2), .45, fc='#c9d0d6', ec='#333', lw=2)); ax.text(xE - .2, retZ - .45, 'MOTOR + DRUM (10 kN)', color='#8ff0b0', fontsize=8, ha='right', fontweight='bold')
    for q in range(6): aa = -math.radians(theta) * 3 + q * math.pi / 3; ax.plot([xE + .55, xE + .55 + .4 * math.cos(aa)], [(zp + retZ) / 2, (zp + retZ) / 2 + .4 * math.sin(aa)], color='#b02020' if q == 0 else '#555', lw=2 if q == 0 else 1)
    ax.plot([-7.9, -7.9], [-0.2, H + 0.9], color='#cfd8e0', lw=2); ang = t * (6 if wind > 15 else 2.2) * 2 * math.pi / 3; cz = H + 1.05
    for q in range(3): ax.plot([-7.9, -7.9 + .4 * math.cos(ang + q * 2.094)], [cz, cz + .4 * math.sin(ang + q * 2.094)], color='#7bc4ff', lw=2.5)
    ax.text(-7.6, H + 1.55, 'ANEMOMETER %.0f m/s' % wind, color='#ff8a78' if wind > 15 else '#7bc4ff', fontsize=9, fontweight='bold')
    if wind > 15:
        for k in range(5): ax.add_patch(FancyArrowPatch((-7.4, 1.0 + k * .42), (-6.1 + 0.15 * math.sin(t * 8 + k), 1.0 + k * .42), arrowstyle='-|>', mutation_scale=10, color='#ff8a78', lw=1.5))
    ax.text(0, 4.5, 'Agrovoltaic Canopy for Protection and Sustainable Farming: one motor, one wire, all panels (side view, 4 of 10 panels)', color='#8fd0a0', fontsize=8.5, ha='center')
    ax.text(0, -0.8 + 0.0, '', color='white'); ax.text(0, 0.15 - 1.0, '', color='white')
    ax.text(0, -1.55, name + '    (panel angle %.0f deg)' % theta, color='white', fontsize=10.5, ha='center', fontweight='bold')
    img = fig_to_img(fig); plt.close(fig); return img
def make(fn, draw, dur):
    th, info = schedule(); frames = [draw(t, info[i][0], info[i][1], i * dur / 1000.0) for i, t in enumerate(th)]
    frames[0].save(os.path.join(OUT, fn), save_all=True, append_images=frames[1:], duration=dur, loop=0, optimize=False); print(fn, len(frames), 'frames', round(os.path.getsize(os.path.join(OUT, fn)) / 1e6, 2), 'MB')
make('mechanism_closeup.gif', closeup, 90); make('mechanism_tilt.gif', rowview, 90)
