"""Finite element check of the lever arm (plane stress, P2 triangles, scikit-fem) and of the torque tube (continuous beam).   python arm_fea.py
1. Validation: a finite-width plate with a central hole in tension against the Howland/Peterson stress concentration factor.
2. Lever arm of the final design: von Mises stress and factor of safety at the wire force of 4.1 kN (54 km/h) and at the 10.2 kN working limit of the 6 mm drive wire,
   for three arm directions (the wire is horizontal, the arm turns with the tilt), with the arm dimensions drawn in the 3D model, and for a revised arm if the first is short.
3. Torque tube: two-span continuous beam on three bearings, bending moment, reactions and deflection against the hand calculation.
Screening level: linear elastic, 2-D, root fixed, pin load as a cosine bearing pressure, no weld or clamp detail, no fatigue."""
import json, math, os
import numpy as np
from scipy.spatial import Delaunay
from matplotlib.path import Path
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.tri as mtri
from skfem import MeshTri, Basis, ElementTriP2, ElementVector, FacetBasis, asm, BilinearForm, LinearForm, condense, solve
from skfem.helpers import dot, ddot, sym_grad, eye, trace
plt.rcParams.update({'font.family': 'serif', 'font.serif': ['Times New Roman', 'DejaVu Serif'], 'font.size': 8, 'axes.linewidth': 0.6})
HERE = os.path.dirname(os.path.abspath(__file__)); E, NU = 193e9, 0.30; SY = 205e6                   # SS316 annealed: E about 193 GPa, minimum yield 205 MPa
lam, mu_ = E * NU / ((1 + NU) * (1 - 2 * NU)), E / (2 * (1 + NU)); lam_ps = 2 * lam * mu_ / (lam + 2 * mu_)    # plane stress

def make_mesh(poly, holes, h_far, h_near, band, seed=1):
    """Delaunay mesh of a polygon with circular holes: boundary points, graded rings round each hole, and a grid elsewhere; small, deterministic, no external mesher."""
    from scipy.spatial import cKDTree
    poly = np.asarray(poly, float); pp = Path(poly); pts = []
    for i in range(len(poly)):
        a, b = poly[i], poly[(i + 1) % len(poly)]; n = max(2, int(np.hypot(*(b - a)) / (0.7 * h_far)))
        pts += [a + (b - a) * k / n for k in range(n)]
    for (cx, cy, r) in holes:
        n = max(28, int(2 * math.pi * r / h_near)); pts += [np.array([cx + r * math.cos(2 * math.pi * k / n), cy + r * math.sin(2 * math.pi * k / n)]) for k in range(n)]
        rr, step = r, h_near
        while rr < r + band:
            rr += step; step *= 1.18; n = max(28, int(2 * math.pi * rr / step))
            for k in range(n):
                p = np.array([cx + rr * math.cos(2 * math.pi * k / n + 0.5 * math.pi * (step / h_near)), cy + rr * math.sin(2 * math.pi * k / n + 0.5 * math.pi * (step / h_near))])
                if pp.contains_point(p): pts.append(p)
    lo, hi = poly.min(0), poly.max(0); xs = np.arange(lo[0], hi[0] + 1e-9, h_far); ys = np.arange(lo[1], hi[1] + 1e-9, h_far)
    for x in xs:
        for y in ys:
            p = np.array([x, y])
            if pp.contains_point(p, radius=-0.5 * h_far): pts.append(p)
    P = np.array(pts); keep = np.ones(len(P), bool); tree = cKDTree(P)
    for i in range(len(P)):                                             # greedy thinning of points that sit too close together
        if not keep[i]: continue
        dh = min([np.hypot(P[i][0] - hx, P[i][1] - hy) - hr for hx, hy, hr in holes] + [1e9]); h = min(h_far, h_near + 0.35 * max(dh, 0))
        for j in tree.query_ball_point(P[i], 0.45 * h):
            if j != i and j > i: keep[j] = False
    allp = P[keep]; tri = Delaunay(allp); good = []
    for s_ in tri.simplices:
        cen = allp[s_].mean(0)
        if not pp.contains_point(cen): continue
        if any(np.hypot(cen[0] - hx, cen[1] - hy) < hr for hx, hy, hr in holes): continue
        a_, b_, c_ = allp[s_]; area = 0.5 * abs((b_[0] - a_[0]) * (c_[1] - a_[1]) - (c_[0] - a_[0]) * (b_[1] - a_[1]))
        if area > 1e-13: good.append(s_)
    good = np.array(good); used = np.unique(good); remap = -np.ones(len(allp), int); remap[used] = np.arange(len(used))
    return MeshTri(allp[used].T, remap[good].T)

def hr_min(holes): return min(h[2] for h in holes)

def solve_plane_stress(mesh, t, fixed_fn, loads):
    """fixed_fn(x) -> boolean of nodes held; loads: list of (facet_selector, traction_fn(x)->(2,..)). Returns basis, displacement."""
    basis = Basis(mesh, ElementVector(ElementTriP2()), intorder=3)
    @BilinearForm
    def K(u, v, w):
        e, f = sym_grad(u), sym_grad(v); return t * (lam_ps * trace(e) * trace(f) + 2 * mu_ * ddot(e, f))
    A = asm(K, basis); b = np.zeros(basis.N)
    for sel, tr in loads:
        fb = FacetBasis(mesh, ElementVector(ElementTriP2()), facets=mesh.facets_satisfying(sel, boundaries_only=True), intorder=3)
        @LinearForm
        def L(v, w, tr=tr): return t * dot(tr(w.x), v)
        b += asm(L, fb)
    D = basis.get_dofs(lambda x: fixed_fn(x)).all()
    u = solve(*condense(A, b, D=D))
    return basis, u

def von_mises(basis, u):
    """von Mises stress (plane stress) at each node (P2 nodal values by projection onto the vertices), and the maximum at quadrature points."""
    gr = basis.interpolate(u).grad                                           # (2,2,nel,nqp)
    exx, eyy, exy = gr[0, 0], gr[1, 1], 0.5 * (gr[0, 1] + gr[1, 0])
    sxx = lam_ps * (exx + eyy) + 2 * mu_ * exx; syy = lam_ps * (exx + eyy) + 2 * mu_ * eyy; sxy = 2 * mu_ * exy
    vm = np.sqrt(sxx ** 2 - sxx * syy + syy ** 2 + 3 * sxy ** 2)
    return vm, basis.mesh

def element_values(vm): return vm.max(axis=1)

def hole_peak(mesh, u, hole, tol_factor=0.06):
    """Largest von Mises stress on the hole boundary, evaluated on the hole facets (exact boundary values of the P2 field)."""
    hx, hy, hr = hole
    fac = mesh.facets_satisfying(lambda x: np.isclose(np.hypot(x[0] - hx, x[1] - hy), hr, atol=tol_factor * hr), boundaries_only=True)
    fb = FacetBasis(mesh, ElementVector(ElementTriP2()), facets=fac, intorder=4)
    g = fb.interpolate(u).grad; exx, eyy, exy = g[0, 0], g[1, 1], 0.5 * (g[0, 1] + g[1, 0])
    sxx = lam_ps * (exx + eyy) + 2 * mu_ * exx; syy = lam_ps * (exx + eyy) + 2 * mu_ * eyy; sxy = 2 * mu_ * exy
    return float(np.sqrt(sxx ** 2 - sxx * syy + syy ** 2 + 3 * sxy ** 2).max())

def region_peak(basis, vm, x_min):
    """Largest von Mises stress at quadrature points of elements whose centroid lies beyond x_min (keeps away from the artificial fixed root)."""
    cen = basis.mesh.p[:, basis.mesh.t].mean(axis=1)[0]; m = cen > x_min
    return float(vm[m].max()) if m.any() else 0.0

# ---------------------------------------------------------------- 1. validation: plate with a hole in tension
def plate_hole(Wd, d, Ld, h_far, h_near, sigma_g=1e6):
    t = 0.01; r = d / 2
    mesh = make_mesh([(-Ld / 2, -Wd / 2), (Ld / 2, -Wd / 2), (Ld / 2, Wd / 2), (-Ld / 2, Wd / 2)], [(0, 0, r)], h_far, h_near, 3 * r)
    P = sigma_g * Wd * t
    basis, u = solve_plane_stress(mesh, t, lambda x: np.isclose(x[0], -Ld / 2),
                                  [(lambda x: np.isclose(x[0], Ld / 2), lambda x: np.array([sigma_g * np.ones_like(x[0]), np.zeros_like(x[0])]))])
    smax = hole_peak(mesh, u, (0, 0, r))
    return smax, sigma_g * Wd / (Wd - d), mesh.t.shape[1]
val = []
for dw in (0.2, 0.4):
    Wd = 0.1; d = dw * Wd
    for hf, hn in ((0.010, 0.0020), (0.006, 0.0012), (0.004, 0.0007)):
        smax, snet, nel = plate_hole(Wd, d, 0.3, hf, hn)
        kt_fe = smax / snet; kt_ref = 3.00 - 3.14 * dw + 3.667 * dw ** 2 - 1.527 * dw ** 3; val.append(dict(d_over_W=dw, elements=nel, Ktn_FE=round(kt_fe, 3), Ktn_reference=round(kt_ref, 3), error_pct=round(100 * (kt_fe / kt_ref - 1), 1)))
        print('validation', val[-1])

# ---------------------------------------------------------------- 2. lever arm
def arm_polygon(L, w_root, w_tip, back=0.02, beyond=0.03):
    """Arm from the fixed root to the pin hole at x = L, with the plate continuing `beyond` past the pin centre (so the hole is a closed ring)."""
    xe = L + beyond; wt = w_root + (w_tip - w_root) * xe / L
    return [(0, -w_root / 2), (xe, -wt / 2), (xe, wt / 2), (0, w_root / 2)]       # the root edge x = 0 is welded to the collar: held fixed

def arm_case(L, w_root, w_tip, t, d_hole, F, phi_deg, h_far=0.010, h_near=0.0016, tag=''):
    """Arm along +x from the fixed root (x = 0 line and the tail), hole near the tip, force F horizontal in world; the arm axis is rotated phi from the vertical."""
    hole = (L, 0.0, d_hole / 2)
    mesh = make_mesh(arm_polygon(L, w_root, w_tip), [hole], h_far, h_near, 0.03)
    # world horizontal force direction expressed in the arm frame: arm axis points to (-sin phi, -cos phi) in world; world x_hat in arm frame
    ph = math.radians(phi_deg); ax = np.array([-math.sin(ph), -math.cos(ph)]); ay = np.array([-ax[1], ax[0]]); xh = np.array([1.0, 0.0]); d = np.array([xh @ ax, xh @ ay])
    r = d_hole / 2; p0 = 2 * F / (math.pi * t * r)
    def sel(x): return np.isclose(np.hypot(x[0] - hole[0], x[1] - hole[1]), r, atol=0.15 * r)
    def trac(x):
        rx, ry = x[0] - hole[0], x[1] - hole[1]; rr = np.hypot(rx, ry) + 1e-12; ux, uy = rx / rr, ry / rr; c = np.maximum(ux * d[0] + uy * d[1], 0.0)
        return np.array([p0 * c * ux, p0 * c * uy])
    basis, u = solve_plane_stress(mesh, t, lambda x: x[0] < 0.0005, [(sel, trac)])
    vm, m = von_mises(basis, u); smax = hole_peak(mesh, u, hole); shank = region_peak(basis, vm, 0.05)
    return dict(smax=smax, shank=shank, mesh=mesh, basis=basis, u=u, vm=vm, axial=float(d[0]), transverse=float(d[1]), hole=hole)

arm_a = dict(L=0.44, w_root=0.090, w_tip=0.048, t=0.014, d_hole=0.022)                      # as drawn in the 3D model
arm_b = dict(L=0.44, w_root=0.120, w_tip=0.070, t=0.016, d_hole=0.022)                      # revised: wider and thicker so that it does not yield at the 10 kN winch limit
res = {'validation': val, 'material': {'E_GPa': 193, 'yield_MPa': 205, 'note': 'SS316 annealed, minimum values'}}
cases = []
for name, geo in (('drawn in the 3D model', arm_a), ('revised 120/70 x 16 mm', arm_b)):
    for F in (4100.0, 10200.0):
        for phi in (15.0, -42.0, 45.0):                                             # tilt 60 deg, flat 3 deg, stow 90 deg (phi = tilt - 45)
            c = arm_case(geo['L'], geo['w_root'], geo['w_tip'], geo['t'], geo['d_hole'], F, phi)
            row = dict(arm=name, wire_force_kN=F / 1e3, arm_angle_phi_deg=phi, tilt_deg=phi + 45, sigma_hole_MPa=round(c['smax'] / 1e6, 1), sigma_shank_MPa=round(c['shank'] / 1e6, 1), factor_of_safety=round(SY / max(c['smax'], c['shank']), 2), elements=int(c['mesh'].t.shape[1]), axial_share=round(c['axial'], 2), transverse_share=round(c['transverse'], 2))
            cases.append((row, c)); print(row)
res['cases'] = [r for r, _ in cases]
# mesh convergence for the governing case
gov = max([c for c in cases if c[0]['arm'] == 'drawn in the 3D model' and c[0]['wire_force_kN'] == 4.1], key=lambda x: max(x[0]['sigma_hole_MPa'], x[0]['sigma_shank_MPa']))
conv = []
for hf, hn in ((0.014, 0.0030), (0.010, 0.0016), (0.007, 0.0010), (0.005, 0.0007)):
    c = arm_case(arm_a['L'], arm_a['w_root'], arm_a['w_tip'], arm_a['t'], arm_a['d_hole'], 4100.0, gov[0]['arm_angle_phi_deg'], hf, hn); conv.append(dict(h_far_mm=hf * 1e3, h_near_mm=hn * 1e3, elements=int(c['mesh'].t.shape[1]), sigma_hole_MPa=round(c['smax'] / 1e6, 1), sigma_shank_MPa=round(c['shank'] / 1e6, 1)))
res['convergence_governing_case'] = conv; print('convergence', conv)
# hand check: net-section tension at the hole + bending of the root section for the governing case
row = gov[0]; Fh = 4100.0; ph = math.radians(row['arm_angle_phi_deg']); Fax = Fh * abs(math.sin(ph)); Ftr = Fh * abs(math.cos(ph))
net = (arm_a['w_tip'] - arm_a['d_hole']) * arm_a['t']; sig_net = Fax / net
Mroot = Ftr * arm_a['L']; Sroot = arm_a['t'] * arm_a['w_root'] ** 2 / 6; sig_b = Mroot / Sroot
res['hand_check'] = dict(governing_phi_deg=row['arm_angle_phi_deg'], net_section_MPa=round(sig_net / 1e6, 1), root_bending_MPa=round(sig_b / 1e6, 1), net_section_with_Kt3_MPa=round(3 * sig_net / 1e6, 1))
# ---------------------------------------------------------------- figure: stress contours
def contour(ax, c, title, vmax=None):
    m = c['mesh']; vm = c['vm'].mean(axis=1) / 1e6; tri = mtri.Triangulation(m.p[0], m.p[1], m.t.T)
    tc = ax.tripcolor(tri, facecolors=vm, cmap='turbo', vmin=0, vmax=vmax or vm.max()); ax.set_aspect('equal'); ax.set_title(title, fontsize=7.5, loc='left')
    ax.set_xlabel('Along the arm (m)'); ax.set_ylabel('Across (m)'); return tc
sel = [c for c in cases if c[0]['arm'] == 'drawn in the 3D model' and c[0]['wire_force_kN'] == 4.1]
fig, axs = plt.subplots(2, 2, figsize=(7.2, 5.0), gridspec_kw={'hspace': 0.55, 'wspace': 0.35})
worst = max(sel, key=lambda x: max(x[0]['sigma_hole_MPa'], x[0]['sigma_shank_MPa'])); vmax = max(worst[0]['sigma_hole_MPa'], worst[0]['sigma_shank_MPa'])
tc = contour(axs[0, 0], worst[1], '(a) As drawn (90/48 x 14 mm)' + chr(10) + '%.1f kN, tilt %d°: peak %.0f MPa' % (4.1, worst[0]['tilt_deg'], max(worst[0]['sigma_hole_MPa'], worst[0]['sigma_shank_MPa'])), vmax)
revs = [c for c in cases if c[0]['arm'] == 'revised 120/70 x 16 mm' and c[0]['wire_force_kN'] == 4.1]; rw = max(revs, key=lambda x: max(x[0]['sigma_hole_MPa'], x[0]['sigma_shank_MPa']))
contour(axs[0, 1], rw[1], '(b) Revised (120/70 x 16 mm)' + chr(10) + 'same load: peak %.0f MPa' % max(rw[0]['sigma_hole_MPa'], rw[0]['sigma_shank_MPa']), vmax)
# zoom at the hole
c = worst[1]; m = c['mesh']; vm = c['vm'].mean(axis=1) / 1e6; tri = mtri.Triangulation(m.p[0], m.p[1], m.t.T); hx, hy, hr = c['hole']
axs[1, 0].tripcolor(tri, facecolors=vm, cmap='turbo', vmin=0, vmax=vmax, edgecolors='k', linewidth=0.15); axs[1, 0].set_xlim(hx - 0.04, hx + 0.012); axs[1, 0].set_ylim(-0.03, 0.03); axs[1, 0].set_aspect('equal'); axs[1, 0].set_title('(c) Mesh and stress at the pin hole (as drawn)', fontsize=7.5, loc='left'); axs[1, 0].set_xlabel('Along the arm (m)')
ph = [r for r, _ in cases if r['arm'] == 'drawn in the 3D model']; xs = np.arange(len(ph))
axs[1, 1].bar(xs, [r['factor_of_safety'] for r in ph], color=['C0' if r['wire_force_kN'] < 5 else 'C1' for r in ph]); axs[1, 1].axhline(1, color='k', lw=0.6); axs[1, 1].axhline(2, color='C3', lw=0.6, ls='--')
axs[1, 1].set_xticks(xs); axs[1, 1].set_xticklabels(['%.1f kN\n%d°' % (r['wire_force_kN'], r['tilt_deg']) for r in ph], fontsize=6.3); axs[1, 1].set_ylabel('Factor of safety against yield'); axs[1, 1].set_title('(d) Arm as drawn, all load cases (dashed: 2)', fontsize=7.5, loc='left')
fig.colorbar(tc, ax=axs[0, :], shrink=0.8, label='von Mises stress (MPa)')
fig.savefig(os.path.join(HERE, 'fig_arm_stress.png'), dpi=220, bbox_inches='tight'); plt.close(fig)

# ---------------------------------------------------------------- 3. torque tube: two-span continuous beam
Dt, tt = 0.1143, 0.004; I = math.pi / 64 * (Dt ** 4 - (Dt - 2 * tt) ** 4); Et = 210e9; Zt = 36.9e-6; MRd = 13.11e3; Lspan = 4.7; w = 8 * 10.0e3 / Lspan ** 2      # load that gives the table moment of 10.0 kNm on a 4.7 m span
def beam_fe(nspan, L, w, nel_per=40):
    n = nspan * nel_per; le = L / nel_per; N = 2 * (n + 1); K = np.zeros((N, N)); f = np.zeros(N)
    ke = Et * I / le ** 3 * np.array([[12, 6 * le, -12, 6 * le], [6 * le, 4 * le ** 2, -6 * le, 2 * le ** 2], [-12, -6 * le, 12, -6 * le], [6 * le, 2 * le ** 2, -6 * le, 4 * le ** 2]]); fe = w * le / 2 * np.array([1, le / 6, 1, -le / 6])
    for e in range(n):
        d = [2 * e, 2 * e + 1, 2 * e + 2, 2 * e + 3]; K[np.ix_(d, d)] += ke; f[d] += fe
    sup = [2 * k * nel_per for k in range(nspan + 1)]; free = [i for i in range(N) if i not in sup]
    u = np.zeros(N); u[free] = np.linalg.solve(K[np.ix_(free, free)], f[free]); R = K @ u - f
    M = []
    for e in range(n):
        d = [2 * e, 2 * e + 1, 2 * e + 2, 2 * e + 3]; fl = ke @ u[d] - fe; M.append((-fl[1], fl[3]))
    return u, R, M, le
u, Rr, M, le = beam_fe(2, Lspan, w); nel = 40; Mhog = abs(M[nel - 1][1]); defl = np.abs(u[0::2]).max()
Msag = max(abs(m[0]) for m in M[:nel]); Rmid = Rr[2 * nel]
hand = dict(M_hog_kNm=round(w * Lspan ** 2 / 8 / 1e3, 3), R_mid_kN=round(1.25 * w * Lspan / 1e3, 2), deflection_mm_L_over_200_limit=round(Lspan / 200 * 1e3, 1))
res['tube'] = dict(span_m=Lspan, line_load_kN_per_m=round(w / 1e3, 2), M_hogging_FE_kNm=round(Mhog / 1e3, 3), M_sagging_FE_kNm=round(Msag / 1e3, 3), reaction_middle_FE_kN=round(abs(Rmid) / 1e3, 2), max_deflection_FE_mm=round(defl * 1e3, 2), utilisation_bending=round(Mhog / MRd, 3), hand_calc=hand,
                   note='the hogging moment at the middle bearing equals w L^2 / 8, as in the strength table (0.76 of 13.11 kNm)')
json.dump(res, open(os.path.join(HERE, 'fea_results.json'), 'w'), indent=1, default=float)
print(json.dumps({k: res[k] for k in ('hand_check', 'tube')}, indent=1))
