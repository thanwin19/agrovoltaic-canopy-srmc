// Fake-sensor (false data injection) test of the storm stow:  node attack_test.js   -> results/T26_attack_test.csv, attack_test.json
// A hacker or a failed amplifier makes the anemometer read low during a storm, so the panels are not stowed.  The defence needs one more measurement that the attacker does not control:
// the TENSION OF THE DRIVE WIRE (a load cell on the winch).  The wind torque on the tubes pulls on the wire, so the tension tells the wind speed independently.
// Simulated here (no hardware): wire force F = 4.1 kN (v/15)^2 (l60 / l(tilt)) + 0.4 kN calm load, 5 % noise; anemometer noise 3 %.  Monitor: wind estimated from the tension is
// more than `margin` m/s above the anemometer for `hold` consecutive minutes -> the anemometer is declared faulty and the larger value is used.
const fs = require('fs'), path = require('path');
function rng(seed) { let a = seed >>> 0; return () => { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
const gauss = r => { let u = 0; while (!u) u = r(); const v = r(); return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v); };
const L = 0.44, ALPHA = Math.PI / 4, lever = th => L * Math.cos(th * Math.PI / 180 - ALPHA), l60 = lever(60), F15 = 4.1, F_CALM = 0.4, WIRE_LIMIT = 10.2, WINCH = 10.0;
const arm = th => th <= 60 ? 1 : 1 - 0.85 * (th - 60) / 30;                                         // wind torque arm relative to the held case: edge-on panels (90 deg) carry little torque (strength table); 0.15 is an assumption
const force = (v, th) => F_CALM + (F15 - F_CALM) * (v / 15) ** 2 * (l60 / lever(th)) * arm(th);              // kN, panels at tilt th, wind v
const windFromForce = (F, th) => 15 * Math.sqrt(Math.max(0, (F - F_CALM)) / ((F15 - F_CALM) * (l60 / lever(th)) * arm(th)));
// ---- one storm day: 06:00 to 18:00, one-minute steps; storm of peak `peak` m/s from minute 240 to 420 (ramp up 40 min, hold, ramp down 40 min)
function trace(seed, peak) {
  const r = rng(seed), v = []; let g = 0;
  for (let m = 0; m < 720; m++) { g = 0.9 * g + 0.4 * gauss(r); let base = 3 + 1.2 * g; let s = 0; if (m >= 240 && m < 420) s = Math.min(1, (m - 240) / 40, (420 - m) / 40); v.push(Math.max(0, base + s * (peak - base))); }
  return v;
}
function attackOf(kind, trueV, m, seed) {                                                               // what the anemometer reports
  const r = rng(seed * 7 + m); const noise = 1 + 0.03 * gauss(r);
  if (kind === 'none') return trueV * noise;
  if (kind === 'stealth_zero') return m >= 200 ? 0.5 + 0.2 * Math.abs(gauss(r)) : trueV * noise;       // reads about zero from minute 200
  if (kind === 'ramp_down') return m >= 200 ? Math.max(0, trueV * noise - 0.05 * (m - 200)) : trueV * noise;      // drifts down 3 m/s every hour
  if (kind === 'replay_calm') return 2.5 + 0.8 * Math.abs(gauss(r));                                    // replays a calm recording all day
  if (kind === 'spoof_high') return m >= 100 && m < 220 ? 22 : trueV * noise;                          // false storm in calm air: needless stow
  return trueV;
}
function run(kind, seed, peak, monitor, margin, hold) {
  const v = trace(seed, peak), r = rng(seed + 99); let th = 45, stowed = false, flagged = false, cnt = 0, flagMin = null, overload = 0, stormMin = 0, stormUnprot = 0, needlessStow = 0, energyLost = 0, maxF = 0;
  for (let m = 0; m < 720; m++) {
    const rep = attackOf(kind, v[m], m, seed), F = force(v[m], stowed ? 90 : th) * (1 + 0.05 * gauss(r)), vEst = windFromForce(F, stowed ? 90 : th);
    let used = rep;
    if (monitor) { if (vEst > rep + margin) cnt++; else cnt = 0; if (cnt >= hold && !flagged) { flagged = true; flagMin = m; } if (flagged) used = 99; }       // once the anemometer is declared faulty the panels stay stowed until the operator resets (the tension cannot tell the wind speed once the panels are edge-on)
    if (used >= 15) stowed = true; else if (stowed && used < 12) stowed = false;      // stow at 15 m/s, resume below 12 m/s
    const tilt = stowed ? 90 : th, Ftrue = force(v[m], tilt); if (Ftrue > maxF) maxF = Ftrue; if (Ftrue > WINCH) overload++;
    if (v[m] >= 15) { stormMin++; if (!stowed) stormUnprot++; } else if (stowed) needlessStow++;
    if (stowed && v[m] < 15) energyLost++;
  }
  return { overload_min: overload, storm_min: stormMin, storm_unprotected_min: stormUnprot, needless_stow_min: needlessStow, max_force_kN: maxF, detected_after_min: flagMin == null ? null : flagMin };
}
const KINDS = ['none', 'stealth_zero', 'ramp_down', 'replay_calm', 'spoof_high'], PEAKS = [18, 24, 32], N = 30, rows = [], summary = {};
for (const kind of KINDS) for (const monitor of [false, true]) {
  const res = []; for (let s = 1; s <= N; s++) for (const pk of PEAKS) res.push(run(kind, s, pk, monitor, 4, 3));
  const mean = k => res.reduce((a, x) => a + x[k], 0) / res.length, det = res.filter(x => x.detected_after_min != null);
  const row = { attack: kind, monitor: monitor ? 'on' : 'off', storm_minutes_unprotected: +mean('storm_unprotected_min').toFixed(1), storm_minutes: +mean('storm_min').toFixed(1), minutes_wire_force_above_winch_limit: +mean('overload_min').toFixed(1), peak_wire_force_kN: +(res.reduce((a, x) => a + x.max_force_kN, 0) / res.length).toFixed(2), needless_stow_minutes: +mean('needless_stow_min').toFixed(1), runs_flagged_pct: +(100 * det.length / res.length).toFixed(0), mean_detection_minute: det.length ? +(det.reduce((a, x) => a + x.detected_after_min, 0) / det.length).toFixed(0) : null };
  rows.push(row); summary[kind + '|' + monitor] = row;
}
// false alarms: benign storms with a healthy anemometer, monitor on, and the margin / hold trade-off
const fa = []; for (const margin of [2, 3, 4, 6]) for (const hold of [2, 3, 5]) { let flagged = 0, det = 0, n = 0, delay = 0; for (let s = 1; s <= N; s++) for (const pk of PEAKS) { n++; if (run('none', s, pk, true, margin, hold).detected_after_min != null) flagged++; const rr = run('stealth_zero', s, pk, true, margin, hold); if (rr.detected_after_min != null) { det++; delay += rr.detected_after_min - 240; } }
  fa.push({ margin_m_s: margin, hold_min: hold, false_alarm_pct: +(100 * flagged / n).toFixed(1), detection_pct: +(100 * det / n).toFixed(1), mean_delay_after_storm_start_min: det ? +(delay / det).toFixed(0) : null }); }
const od = path.join(__dirname, 'results'); fs.mkdirSync(od, { recursive: true });
const head = ['attack', 'monitor', 'storm_minutes', 'storm_minutes_unprotected', 'minutes_wire_force_above_winch_limit', 'peak_wire_force_kN', 'needless_stow_minutes', 'runs_flagged_pct', 'mean_detection_minute'];
fs.writeFileSync(path.join(od, 'T26_attack_test.csv'), head.join(',') + '\n' + rows.map(r => head.map(h => r[h]).join(',')).join('\n') + '\n\nmargin,hold,false alarm %,detection %,delay min\n' + fa.map(r => [r.margin_m_s, r.hold_min, r.false_alarm_pct, r.detection_pct, r.mean_delay_after_storm_start_min].join(',')).join('\n'));
fs.writeFileSync(path.join(od, 'attack_test.json'), JSON.stringify({ rows, tradeoff: fa, assumptions: 'simulated wire tension from the strength-table wire force (4.1 kN at 15 m/s, 60 deg), calm load 0.4 kN, 5 % load cell noise, 3 % anemometer noise; storms of 18, 24 and 32 m/s; 30 seeds each', winch_limit_kN: WINCH }, null, 1));
console.log(rows.map(r => [r.attack, r.monitor, r.storm_minutes_unprotected + '/' + r.storm_minutes, r.minutes_wire_force_above_winch_limit, r.peak_wire_force_kN, r.needless_stow_minutes, r.runs_flagged_pct, r.mean_detection_minute].join('\t')).join('\n')); console.log(fa.map(r => JSON.stringify(r)).join('\n'));
