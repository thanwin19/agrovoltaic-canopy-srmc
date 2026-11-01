/* ---------------- Added tabs: ground light map, structure and trade-off, design explorer, edge AI and sensor-attack test ---------------- */
const WOW = window.SRMC_WOW || {};
const GMCOL = [[0, [178, 24, 43]], [0.15, [214, 96, 77]], [0.3, [253, 219, 122]], [0.45, [254, 224, 139]], [0.62, [166, 217, 106]], [1, [26, 152, 80]]];
function gmColor(v) { v = Math.max(0, Math.min(1, v)); for (let i = 1; i < GMCOL.length; i++) if (v <= GMCOL[i][0]) { const a = GMCOL[i - 1], b = GMCOL[i], f = (v - a[0]) / (b[0] - a[0]); return [0, 1, 2].map(k => Math.round(a[1][k] + (b[1][k] - a[1][k]) * f)); } return GMCOL[GMCOL.length - 1][1]; }
const GM = { buf: null, idx: null, loading: false, day: '21 Mar', hour: 12, tiltA: 'ctrl', tiltB: 45 };
async function gmLoad() {
  if (GM.buf || GM.loading || !window.SRMC_GM_B64) return; GM.loading = true;
  try {
    const bin = Uint8Array.from(atob(window.SRMC_GM_B64), c => c.charCodeAt(0)), ds = new DecompressionStream('deflate');
    GM.buf = new Uint8Array(await new Response(new Blob([bin]).stream().pipeThrough(ds)).arrayBuffer()); GM.idx = {}; WOW.gm.keys.forEach((k, i) => GM.idx[k] = i);
  } catch (e) { const el = $('#gm-stats'); if (el) el.textContent = 'Could not unpack the map data in this browser: ' + e.message; }
  GM.loading = false; tabGmap();
}
function gmTilt(sel) { return sel === 'ctrl' ? (WOW.gm.ctrl[GM.day] && WOW.gm.ctrl[GM.day][String(GM.hour)] != null ? WOW.gm.ctrl[GM.day][String(GM.hour)] : null) : +sel; }
function gmDraw(canvas, tiltSel, title) {
  const M = WOW.gm, tl = gmTilt(tiltSel); const c = canvas, g = c.getContext('2d'); c.width = 420; c.height = 440; g.fillStyle = '#10150f'; g.fillRect(0, 0, c.width, c.height);
  if (tl == null) { g.fillStyle = TXT; g.font = '13px sans-serif'; g.fillText('sun below the horizon at this hour', 20, 40); return null; }
  const tilts = M.tilts, tUse = tilts.reduce((b, a) => Math.abs(a - tl) < Math.abs(b - tl) ? a : b), key = GM.day + '|' + GM.hour + '|' + tUse, i = GM.idx[key];
  if (i == null) { g.fillStyle = TXT; g.font = '13px sans-serif'; g.fillText('no data for this hour (sun too low)', 20, 40); return null; }
  const n = M.ny * M.nx, off = i * n, px = 6, W = M.nx * px; const img = g.createImageData(W, M.ny * px);
  for (let y = 0; y < M.ny; y++) for (let x = 0; x < M.nx; x++) { const col = gmColor(GM.buf[off + y * M.nx + x] / 255); for (let dy = 0; dy < px; dy++) for (let dx = 0; dx < px; dx++) { const o = (((M.ny - 1 - y) * px + dy) * W + x * px + dx) * 4; img.data[o] = col[0]; img.data[o + 1] = col[1]; img.data[o + 2] = col[2]; img.data[o + 3] = 255; } }
  g.putImageData(img, 0, 30); g.strokeStyle = 'rgba(0,0,0,.75)'; g.setLineDash([5, 4]); g.strokeRect((0 - M.x0) / M.res * px, 30 + (M.ny - (25 - M.y0) / M.res) * px, 25 / M.res * px, 25 / M.res * px); g.setLineDash([]);
  g.fillStyle = '#e8efe0'; g.font = 'bold 13px sans-serif'; g.fillText(title + ': tilt ' + tUse + '°', 8, 18); const s = M.stats[key];
  g.font = '11px sans-serif'; g.fillStyle = '#10150f'; g.fillText('N', 14, 52); g.fillText('E →', W - 30, 30 + M.ny * px - 6);
  return { tUse, s };
}
function tabGmap() {
  const M = WOW.gm; if (!M) return; if (!GM.buf) { gmLoad(); $('#gm-stats').textContent = 'Unpacking the map data...'; return; }
  const d = $('#gm-day'), h = $('#gm-hour'), a = $('#gm-tiltA'), b = $('#gm-tiltB');
  if (!d.options.length) { M.days.forEach(x => d.add(new Option(x, x))); [['ctrl', 'controller (best angle)']].concat(M.tilts.map(t => [String(t), t + '°'])).forEach(([v, t]) => { a.add(new Option(t, v)); b.add(new Option(t, v)); }); a.value = 'ctrl'; b.value = '45'; }
  d.value = GM.day; h.value = GM.hour; $('#v-gm-hour').textContent = Math.floor(GM.hour) + ':' + (GM.hour % 1 ? '30' : '00');
  d.onchange = () => { GM.day = d.value; tabGmap(); }; h.oninput = () => { GM.hour = +h.value; tabGmap(); }; a.onchange = () => { GM.tiltA = a.value; tabGmap(); }; b.onchange = () => { GM.tiltB = b.value; tabGmap(); };
  $$('.gm-hr').forEach(btn => btn.onclick = () => { GM.hour = +btn.dataset.h; tabGmap(); }); a.value = GM.tiltA; b.value = String(GM.tiltB);
  const ra = gmDraw($('#gm-cvA'), GM.tiltA, 'Controller'), rb = gmDraw($('#gm-cvB'), GM.tiltB, 'Comparison');
  const fmtS = r => r ? `mean light on the ground <b>${(100 * r.s.mean).toFixed(0)} %</b> of open field · heavy shade (below 15 %) on <b>${(100 * r.s.red).toFixed(0)} %</b> of the land · well lit (above 45 %) on <b>${(100 * r.s.green).toFixed(0)} %</b>` : 'no map';
  $('#gm-stats').innerHTML = `<div><b>Left:</b> ${fmtS(ra)}</div><div><b>Right:</b> ${fmtS(rb)}</div>`;
}
/* ---- structure and trade-off ---- */
const STR = { UTIL60: { carrier: .37, stay: .32, tube: .76, pad: .69, wire54: .41 }, L: .44, A: Math.PI / 4 };
function strCn(th, model) { if (model === 'B') return 1.3; const a = Math.max(th, .1) * Math.PI / 180; return Math.min(2 * Math.PI * a, 1.2); }
function strParts(th, model) { const r = strCn(th, model), t = th * Math.PI / 180; return [r, r * Math.cos(t), r * Math.sin(t)]; }
function strLever(th) { return STR.L * Math.cos(th * Math.PI / 180 - STR.A); }
function strUtil(th, model) { const [R, V, H] = strParts(th, model), [R0, V0, H0] = strParts(60, model), U = STR.UTIL60; return { 'carrier rope': U.carrier * Math.abs(V) / Math.abs(V0), 'column pad (uplift)': U.pad * Math.abs(V) / Math.abs(V0), 'stay ropes': U.stay * H / H0, 'torque tube': U.tube * R / R0, 'drive wire at 54 km/h': U.wire54 * (R / R0) * (strLever(60) / strLever(th)) }; }
function tabStruct() {
  const W = WOW.str; if (!W) return; const sl = $('#st-angle'), md = $('#st-model'); const th = +sl.value, model = md.value; $('#v-st-angle').textContent = th + '°';
  sl.oninput = md.onchange = tabStruct; const u = strUtil(th, model), keys = Object.keys(u), mx = Math.max(...keys.map(k => u[k]));
  $('#st-util').innerHTML = '<tr><th>Part</th><th>Utilisation at 140 km/h wind, panels held at ' + th + '°</th><th></th></tr>' + keys.map(k => `<tr><td>${k}</td><td>${u[k].toFixed(2)}</td><td><span class="hb" style="width:160px"><i style="width:${Math.min(100, 100 * u[k] / 1.5)}%;background:${u[k] > 1 ? '#ff8a5c' : u[k] > .8 ? '#f0c24a' : '#6fe07c'}"></i></span></td></tr>`).join('') + `<tr><td><b>governing</b></td><td><b>${mx.toFixed(2)}</b> ${mx > 1 ? '<span style="color:#ff8a5c">above capacity: this stow angle fails</span>' : '<span style="color:#6fe07c">within capacity</span>'}</td><td></td></tr>`;
  const f = W.fea; $('#st-fea').innerHTML = '<tr><th>Arm</th><th>Wire force</th><th>Tilt</th><th>Peak stress at the pin hole</th><th>Peak stress along the arm</th><th>Factor of safety</th></tr>' + f.cases.map(c => `<tr><td>${c.arm}</td><td>${c.wire_force_kN} kN</td><td>${c.tilt_deg}°</td><td>${c.sigma_hole_MPa} MPa</td><td>${c.sigma_shank_MPa} MPa</td><td><b style="color:${c.factor_of_safety < 1 ? '#ff8a5c' : c.factor_of_safety < 2 ? '#f0c24a' : '#6fe07c'}">${c.factor_of_safety}</b></td></tr>`).join('');
  $('#st-pareto').innerHTML = '<tr><th>Design</th><th>Electricity kWh/m²</th><th>Crop net, lakh</th><th>Demand index</th><th>On the front</th></tr>' + W.pareto.map(d => `<tr><td>${d.name}</td><td>${d.pv}</td><td>${d.crop}</td><td style="color:${d.load > 1 ? '#ff8a5c' : 'inherit'}">${d.load.toFixed(2)}</td><td>${d.front ? 'yes' : ''}</td></tr>`).join('');
}
/* ---- design explorer ---- */
const DEX = { x: 'solar', y: 'crop', sel: -1 };
function tabDex() {
  const W = WOW.dex; if (!W) return; const xs = $('#dx-x'), ys = $('#dx-y'); xs.value = DEX.x; ys.value = DEX.y; xs.onchange = ys.onchange = () => { DEX.x = xs.value; DEX.y = ys.value; tabDex(); };
  const lab = { solar: 'Solar net income (INR lakh / ha / yr)', crop: 'Crop net income (INR lakh / ha / yr)', steel_t: 'Structural steel (t / ha)', rainfed: 'Irrigation met from rain (%)' }, all = W.front, ref = W.reference, pts = all.concat([ref]);
  const c = cv($('#dx-cv'), 360), g = c.g, L = 60, B = 36, Wd = c.w - L - 16, Ht = 360 - B - 14, vx = pts.map(p => p[DEX.x]), vy = pts.map(p => p[DEX.y]), x0 = Math.min(...vx), x1 = Math.max(...vx), y0 = Math.min(...vy), y1 = Math.max(...vy), px = v => L + Wd * (v - x0) / ((x1 - x0) || 1), py = v => 12 + Ht * (1 - (v - y0) / ((y1 - y0) || 1));
  g.font = '11px sans-serif'; g.fillStyle = TXT; g.strokeStyle = GRID; for (let i = 0; i <= 4; i++) { const yy = 12 + Ht * i / 4; g.beginPath(); g.moveTo(L, yy); g.lineTo(L + Wd, yy); g.stroke(); g.textAlign = 'right'; g.fillText((y1 - (y1 - y0) * i / 4).toFixed(1), L - 5, yy + 4); const xx = L + Wd * i / 4; g.textAlign = 'center'; g.fillText((x0 + (x1 - x0) * i / 4).toFixed(1), xx, 12 + Ht + 14); }
  g.textAlign = 'center'; g.fillText(lab[DEX.x], L + Wd / 2, 360 - 4); g.save(); g.translate(14, 12 + Ht / 2); g.rotate(-Math.PI / 2); g.fillText(lab[DEX.y], 0, 0); g.restore();
  all.forEach((p, i) => { g.fillStyle = i === DEX.sel ? '#ffd24a' : 'rgba(79,209,255,.85)'; g.beginPath(); g.arc(px(p[DEX.x]), py(p[DEX.y]), i === DEX.sel ? 7 : 4.5, 0, 7); g.fill(); });
  g.strokeStyle = '#ff6b4a'; g.lineWidth = 2; g.beginPath(); g.arc(px(ref[DEX.x]), py(ref[DEX.y]), 8, 0, 7); g.stroke(); g.fillStyle = '#ff6b4a'; g.textAlign = 'left'; g.fillText('final design', px(ref[DEX.x]) + 11, py(ref[DEX.y]) + 4); g.lineWidth = 1;
  c.g.canvas.onclick = ev => { const r = ev.target.getBoundingClientRect(), mx = ev.clientX - r.left, my = ev.clientY - r.top; let best = -1, bd = 1e9; all.forEach((p, i) => { const d = Math.hypot(px(p[DEX.x]) - mx, py(p[DEX.y]) - my); if (d < bd) { bd = d; best = i; } }); if (bd < 16) { DEX.sel = best; tabDex(); } };
  const fm = d => `<td>${d.gcr}</td><td>${d.clearance} m</td><td>${d.tilt_max}°</td><td>${d.w}</td><td>${d.solar}</td><td>${d.crop}</td><td>${d.steel_t}</td><td>${d.rainfed}</td>`;
  $('#dx-table').innerHTML = '<tr><th></th><th>Ground coverage</th><th>Clearance</th><th>Upper tilt stop</th><th>Electricity weight</th><th>Solar net</th><th>Crop net</th><th>Steel t/ha</th><th>Rain-fed %</th></tr>' + `<tr style="color:#ff9a7a"><td><b>final design</b></td>${fm(Object.assign({}, ref, { tilt_max: ref.tilt_max }))}</tr>` + all.map((d, i) => `<tr data-i="${i}" style="${i === DEX.sel ? 'background:rgba(255,210,74,.15)' : ''};cursor:pointer"><td>${i + 1}</td>${fm(d)}</tr>`).join('');
  $('#dx-note').innerHTML = `Of the ${W.evaluated} designs the search evaluated, <b>${W.dominating}</b> beat the final design on all four goals at once, so it sits on the trade-off surface. The explorer shows the alternatives: designs with more crop income (up to ${Math.max(...all.map(d => d.crop)).toFixed(1)} lakh) give up solar income, and designs with more solar income (up to ${Math.max(...all.map(d => d.solar)).toFixed(0)} lakh) leave almost no crop. The search ran 40 designs for 30 generations; the front is an approximation, not a proof of optimality.`;
  $$('#dx-table tr[data-i]').forEach(tr => tr.onclick = () => { DEX.sel = +tr.dataset.i; tabDex(); });
}
/* ---- edge AI: the distilled network, and the sensor-attack test ---- */
function wowNN(sun, irr, T, RH, soil, parUm, prev, n) {                    // the same computation as the C code for the ESP32 (srmc_nn.h)
  const M = WOW.nn.model, g0 = 1361 * (1 + .033 * Math.cos(2 * Math.PI * n / 365)), kt = irr.ghi / (g0 * sun.sz), lsr = parUm / 2.05 / Math.max(irr.ghi, 1);
  const f = [sun.sz, sun.sx, kt, T, RH, soil, lsr, prev, Math.sin(2 * Math.PI * n / 365), Math.cos(2 * Math.PI * n / 365)]; let h = f.map((v, i) => (v - M.mu[i]) / M.sd[i]);
  M.layers.forEach((Ly, li) => { const o = Ly.b.map((b, j) => { let s = b; for (let i = 0; i < h.length; i++) s += Ly.w[j][i] * h[i]; return s; }); h = li < 2 ? o.map(Math.tanh) : o; });
  return Math.max(15, Math.min(60, Math.round((h[0] * 22.5 + 37.5) * 2) / 2));
}
const WF = { F15: 4.1, CALM: .4 }; const wfArm = th => th <= 60 ? 1 : 1 - .85 * (th - 60) / 30;
function wfForce(v, th) { return WF.CALM + (WF.F15 - WF.CALM) * (v / 15) ** 2 * (strLever(60) / strLever(th)) * wfArm(th); }
function wfWind(F, th) { return 15 * Math.sqrt(Math.max(0, F - WF.CALM) / ((WF.F15 - WF.CALM) * (strLever(60) / strLever(th)) * wfArm(th))); }
const WLATCH = { on: false };
function wowWind(fault, trueV, th) {                                         // anemometer reading under an injected attack, and the wire-tension monitor
  let read = trueV; if (fault === 'windZero') read = .5; else if (fault === 'windReplay') read = 2.5; else if (fault === 'windRamp') read = Math.max(0, trueV - 6);
  const F = wfForce(trueV, th), vEst = wfWind(F, th), mon = !($('#wow-mon') && !$('#wow-mon').checked);
  if (fault === 'none' || fault === 'rainWet' || fault === 'rainDead' || fault === 'soilStuck' || fault === 'soilDead' || fault === 'soilGlitch') WLATCH.on = false;
  if (mon && vEst > read + 4) WLATCH.on = true;
  return { read, F, vEst, flagged: mon && WLATCH.on, used: mon && WLATCH.on ? Math.max(15, vEst) : read, monitor: mon };
}
function tabEdge() {
  const W = WOW.nn, A = WOW.atk; if (!W) return; const r = W.results;
  const nm = ['oracle (best possible)', 'optimiser, single noisy readings', 'neural network (float32)', 'neural network (int8 weights)', 'monthly plan', 'fixed 45 deg', 'previous angle held'];
  $('#ed-nn').innerHTML = '<tr><th>Strategy (5 000 test hours)</th><th>Accuracy A, %</th><th>Electricity, %</th><th>Crop light, %</th><th>Tilt error (rms), deg</th></tr>' + nm.filter(k => r[k]).map(k => `<tr><td>${k}</td><td><b>${r[k].A.toFixed(1)}</b></td><td>${r[k].elec.toFixed(1)}</td><td>${r[k].crop.toFixed(1)}</td><td>${r[k].rmse.toFixed(1)}</td></tr>`).join('');
  const cl = W.closed; $('#ed-closed').innerHTML = cl ? '<tr><th>Closed loop, 864 cases, reference site</th><th>Accuracy A, %</th><th>Electricity, %</th><th>Crop light, %</th><th>Tilt error, deg</th></tr>' + Object.entries(cl).map(([k, v]) => `<tr><td>${k}</td><td><b>${v.J.toFixed(1)}</b></td><td>${v.elec.toFixed(1)}</td><td>${v.crop.toFixed(1)}</td><td>${v.rmse.toFixed(1)}</td></tr>`).join('') : '';
  $('#ed-size').textContent = `${r.params} weights: ${r.bytes_float32} bytes as float32, about ${r.bytes_int8} bytes as int8 (an ESP32 has 4 MB of flash).`;
  $('#ed-use').onchange = $('#wow-mon').onchange = () => { try { scene3d.refresh(true); } catch (e) { } };
  $('#ed-run').onclick = () => { if (!R || !SENS.last) { $('#ed-live').textContent = 'Open the 3D twin tab once so the controller has a state.'; return; } const n = st.day + 1, m = monthOf(st.day), sun = S.sunVec(clim.lat, n, st.hour), irr = senseIrr(S.irradiance(sun.sz, n, clim.kt[m]), sun); if (irr.ghi < 20) { $('#ed-live').textContent = 'Night: no decision needed.'; return; }
    const a = wowNN(sun, irr, SENS.temp, SENS.rh, SENS.soil, SENS.last.par, SENS.cmd, n); $('#ed-live').innerHTML = `At the twin's current hour: distilled network <b>${a.toFixed(1)}°</b>, full optimiser target <b>${SENS.last.target != null ? SENS.last.target.toFixed(1) : 'n/a'}°</b>, angle now in use ${SENS.cmd.toFixed(1)}°.`; };
  if (A) { $('#ed-atk').innerHTML = '<tr><th>Attack on the anemometer</th><th>Tension monitor</th><th>Storm minutes without stow</th><th>Minutes wire force above the winch limit</th><th>Peak wire force kN</th><th>Detected after (min of the day)</th></tr>' + A.rows.map(x => `<tr><td>${x.attack.replace('_', ' ')}</td><td>${x.monitor}</td><td>${x.storm_minutes_unprotected} of ${x.storm_minutes}</td><td>${x.minutes_wire_force_above_winch_limit}</td><td>${x.peak_wire_force_kN}</td><td>${x.mean_detection_minute == null ? '' : x.mean_detection_minute}</td></tr>`).join(''); }
}
