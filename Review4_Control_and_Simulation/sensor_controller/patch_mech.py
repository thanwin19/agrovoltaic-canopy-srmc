"""Second patch of the final twin (run AFTER patch_twin.py): the Mechanism tab shows the final design: lever arm fixed at a 45 deg offset (keeps a lever at the 90 deg storm stow),
6 mm drive wire, anemometer storm stow.   python patch_mech.py"""
import os
here = os.path.dirname(os.path.abspath(__file__)); root = os.path.abspath(os.path.join(here, '..', '..'))
tw = os.path.join(root, 'Review3_Digital_Twin', 'results', 'live_twin', 'SRMC_Digital_Twin.html')
s = open(tw, encoding='utf8').read()
assert 'MECH_OFFSET_PATCHED' not in s, 'already patched; run patch_twin.py first to start from the saved original'
def rep(old, new, cnt=1):
    global s
    assert old in s, 'MISSING: ' + old[:80]
    s = s.replace(old, new, cnt)
D = '°'
# ---- row view (STEP B)
rep("const tips = xs.map(xc => [xc - L * Math.sin(tr), H - L * Math.cos(tr)])", "const OFF = 45 * D2R /*MECH_OFFSET_PATCHED*/, tips = xs.map(xc => [xc - L * Math.sin(tr - OFF), H - L * Math.cos(tr - OFF)])")
rep("const rx = xc, rz = H - L;", "const rx = xc + L * Math.sin(OFF), rz = H - L * Math.cos(OFF);")
rep("Lreal * 1000 * (Math.sin(tr) - Math.sin(3 * D2R))", "Lreal * 1000 * (Math.sin(tr - 45 * D2R) - Math.sin(3 * D2R - 45 * D2R))")
# ---- close-up (STEP A)
rep("const tip = [-L * Math.sin(tr), -L * Math.cos(tr)], pit = 2.5;", "const OFF = 45 * D2R, tip = [-L * Math.sin(tr - OFF), -L * Math.cos(tr - OFF)], rest = [L * Math.sin(OFF), -L * Math.cos(OFF)], pit = 2.5;")
rep("Ln(0, 0, 0, -L, 'rgba(255,255,255,.6)', 1.6, [5, 4]);", "Ln(0, 0, rest[0], rest[1], 'rgba(255,255,255,.6)', 1.6, [5, 4]);")
rep("g.arc(X(0), Z(-L), 7, 0, 7); g.stroke(); g.setLineDash([]); T('rest position of the tip (panel flat)', X(0) + 12, Z(-L) + 4,", "g.arc(X(rest[0]), Z(rest[1]), 7, 0, 7); g.stroke(); g.setLineDash([]); T('rest position of the tip (panel flat)', X(rest[0]) + 12, Z(rest[1]) + 4,")
rep("g.arc(X(0), Z(0), .55 * s, Math.PI / 2, Math.PI / 2 + tr, false)", "g.arc(X(0), Z(0), .55 * s, Math.PI / 2 - OFF, Math.PI / 2 - OFF + tr, false)")
rep("const dd = Math.abs(tip[0]); if (dd > .03) { const zb = -L - .38; Ln(0, -L - .12, 0, zb - .1, '#7CFFB2', 1.3); Ln(tip[0], wz - .12, tip[0], zb - .1, '#7CFFB2', 1.3); Ln(0, zb, tip[0], zb, '#7CFFB2', 3);",
    "const dd = Math.abs(tip[0] - rest[0]); if (dd > .03) { const zb = -L - .38; Ln(rest[0], rest[1] - .12, rest[0], zb - .1, '#7CFFB2', 1.3); Ln(tip[0], wz - .12, tip[0], zb - .1, '#7CFFB2', 1.3); Ln(rest[0], zb, tip[0], zb, '#7CFFB2', 3);")
rep("(Lreal * Math.sin(tr) * 1000).toFixed(0) + ' mm   (d = arm x sin θ, real arm 0.44 m)', X(tip[0] / 2) - 20,", "(Lreal * (Math.sin(tr - OFF) + Math.sin(OFF)) * 1000).toFixed(0) + ' mm   (d = arm x [sin 45" + D + " + sin(θ - 45" + D + ")], arm 0.44 m)', X((tip[0] + rest[0]) / 2) - 20,")
rep("'RAIN MODE: the arm hangs straight down, the panels are flat and sealed.'", "'RAIN MODE: panels flat and sealed; the 45" + D + " offset arm points down and to the east.'")
rep("'LEVER ARM (rigid with the tube, drawn 2.3x real)'", "'LEVER ARM (rigid with the tube, fixed 45" + D + " offset, drawn 2.3x real)'")
# ---- explanation text
rep("(stainless steel 4 mm)", "(stainless steel 6 mm)")
rep("When its tip moves sideways by d, the tube turns by an angle with sin(angle) = d / arm length (about 0.44 m).", "When its tip moves sideways by d, the tube turns: d = arm length x [sin 45" + D + " + sin(angle - 45" + D + ")] (arm about 0.44 m). The arm is fixed at a 45" + D + " offset, so the wire always keeps a lever of at least 0.31 m, even at the 90" + D + " storm stow (a plain arm has no lever at 90" + D + ").")
rep("<li><b>Controller</b> (or rain sensor) sends a target angle to the motor drive.</li>", "<li><b>Controller</b> (six sensors: the rain sensor gives the flat roof, the anemometer trips the 90" + D + " storm stow at 15 m/s) sends a target angle to the motor drive (10 kN winch, about 0.25 kW).</li>")
rep("(about 80 mm across for the 4 mm wire)", "(about 80 mm across for the 6 mm wire)")
rep("<li><b>Lever arms:</b> fix one arm (150-250 mm SS316 flat bar) to each tube end, all identical and pointing the same way.</li>", "<li><b>Lever arms:</b> fix one arm (0.44 m SS316 flat bar) to each tube end, all identical and set at the 45" + D + " offset (panel flat: the arm points down and 45" + D + " to the east).</li>")
rep("run the 4 mm SS316 wire through them", "run the 6 mm SS316 wire through them")
rep("mount the winch (IP66, at least 3 kN pull)", "mount the winch (IP66, 10 kN pull, about 0.25 kW worm gear)")
rep("<li><b>Commission:</b>", "<li><b>Anemometer:</b> fit a cup anemometer on a 3 m mast above the canopy; it trips the 90" + D + " storm stow at 15 m/s (54 km/h) and releases below 12 m/s.</li>\n       <li><b>Commission:</b>")
rep("(the link is d = arm x sin θ, not a straight line)", "(the link is d = arm x [sin 45" + D + " + sin(θ - 45" + D + ")], not a straight line)")
rep("test the rain trigger, wind stow (90 deg) and the brake.", "test the rain trigger, the anemometer stow (90 deg) and the brake.")
rep("<td>about 358 mm (arm 0.44 m)</td>", "<td>about 408 mm to 60 deg, 606 mm to the 90 deg stow (arm 0.44 m, 45 deg offset)</td>")
rep("<td>about 0.95 turn</td>", "<td>about 1.08 turns (1.61 turns to 90 deg)</td>")
rep("<td>Motor pull, wire working load</td><td>at least 3 kN, wire at most 2.6 kN</td><td>wire spec</td>", "<td>Motor pull, wire working load</td><td>10 kN winch; wire load 0.4 kN calm, 4.1 kN in 54 km/h wind (6 mm wire limit 10 kN)</td><td>strength check</td>")
open(tw, 'w', encoding='utf8').write(s); print('mechanism tab patched')
