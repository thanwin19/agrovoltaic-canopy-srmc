/* ---------------- Accuracy tab: year-long results (from the Node and MATLAB tests) + a live accuracy test at the current hour ---------------- */
function accBars(el, rows, key, lo, hi, color) {                // horizontal bars
  const c = cv(el, 30 + rows.length * 30), g = c.g, pad = 190, W = c.w - pad - 60; g.font = '12px sans-serif'; g.textBaseline = 'middle';
  rows.forEach((r, i) => { const y = 14 + i * 30, v = r[key], f = Math.max(0, Math.min(1, (v - lo) / (hi - lo))); g.fillStyle = TXT; g.textAlign = 'right'; g.fillText(r.strategy.replace(' (SRMC-DT)', ''), pad - 8, y + 9);
    g.fillStyle = r.strategy.startsWith('SC v2 noisy') ? '#2e9d44' : (r.strategy.startsWith('SC') ? '#72b830' : '#6c7a68'); g.fillRect(pad, y, W * f, 18); g.fillStyle = TXT; g.textAlign = 'left'; g.fillText(v.toFixed(1) + ' %', pad + W * f + 6, y + 9); });
}
function accLines(el, rows) {                                    // v1 and v2 combined score versus noise
  const c = cv(el, 210), g = c.g, L = 50, B = 30, Wd = c.w - L - 20, Ht = 210 - B - 18, lo = 97.5, hi = 100; g.font = '11px sans-serif'; g.strokeStyle = GRID; g.fillStyle = TXT;
  for (let v = 97.5; v <= 100; v += 0.5) { const y = 12 + Ht * (1 - (v - lo) / (hi - lo)); g.beginPath(); g.moveTo(L, y); g.lineTo(L + Wd, y); g.stroke(); g.textAlign = 'right'; g.fillText(v.toFixed(1), L - 5, y + 3); }
  const xs = i => L + Wd * i / (rows.length - 1);
  [['v1', '#c0392b', 'v1: one reading'], ['v2', '#2e9d44', 'v2: median of 5 + guard']].forEach(([k, col, lab], j) => { g.strokeStyle = col; g.fillStyle = col; g.lineWidth = 2.5; g.beginPath(); rows.forEach((r, i) => { const y = 12 + Ht * (1 - (r[k].J_pct - lo) / (hi - lo)); i ? g.lineTo(xs(i), y) : g.moveTo(xs(i), y); }); g.stroke(); rows.forEach((r, i) => { g.beginPath(); g.arc(xs(i), 12 + Ht * (1 - (r[k].J_pct - lo) / (hi - lo)), 4, 0, 7); g.fill(); }); g.textAlign = 'left'; g.fillText(lab, L + 8 + j * 170, 22); });
  g.fillStyle = TXT; g.textAlign = 'center'; rows.forEach((r, i) => g.fillText('noise x' + r.noise_x, xs(i), 210 - 10)); g.lineWidth = 1;
}
function tabAcc() {
  const A = window.SRMC_ACC; if (!A) return; const m = A.main, v2 = m.find(r => r.strategy.startsWith('SC v2 noisy')), pl = m.find(r => r.strategy.startsWith('Monthly')), f45 = m.find(r => r.strategy === 'Fixed 45 deg');
  $('#acc-head').innerHTML = `<div class="kpi"><b>${v2.J_pct.toFixed(1)} %</b><br><span>combined score of the best possible (noisy sensors)</span></div><div class="kpi"><b>${v2.pv_pct.toFixed(0)} %</b><br><span>of the best electricity</span></div><div class="kpi"><b>${v2.crop_pct.toFixed(0)} %</b><br><span>of the best crop light value</span></div><div class="kpi"><b>${v2.angle_rmse_deg.toFixed(1)}°</b><br><span>tilt error vs best (monthly plan ${pl.angle_rmse_deg.toFixed(1)}°, fixed 45° ${f45.angle_rmse_deg.toFixed(1)}°)</span></div>`;
  accBars($('#acc-bars'), m, 'J_pct', 70, 100); accBars($('#acc-bars2'), m, 'pv_pct', 70, 100); accBars($('#acc-bars3'), m, 'crop_pct', 40, 100); accLines($('#acc-noise'), A.noise);
  $('#acc-faults').innerHTML = '<tr><th>PAR sensor fault</th><th>v1 (one reading, no guard)</th><th>v2 (median of 5 + guard)</th></tr>' + A.faults.map(f => `<tr><td>${f.fault}</td><td>${f.v1.J_pct.toFixed(1)} %</td><td><b>${f.v2.J_pct.toFixed(1)} %</b></td></tr>`).join('');
  $('#acc-money').innerHTML = '<tr><th>Strategy (hourly angles run through the crop, water and money model)</th><th>PV kWh/m²</th><th>crop light</th><th>crop net ₹ lakh</th><th>solar net ₹ lakh</th><th>total ₹ lakh</th></tr>' + A.money.map(r => `<tr><td>${r.strategy}</td><td>${r.pv_kWh_m2}</td><td>${r.crop_light_pct} %</td><td>${r.crop_net_lakh}</td><td>${r.solar_net_lakh}</td><td><b>${r.total_lakh}</b></td></tr>`).join('');
  const M = A.matlab; $('#acc-matlab').innerHTML = `MATLAB (independent physics, ${M.cases} cases, same sensor readings): v2 <b>${M.v2.J_pct.toFixed(1)} %</b> of the best combined score, electricity ${M.v2.electricity_pct.toFixed(0)} %, crop light ${M.v2.crop_pct.toFixed(0)} %, tilt error ${M.v2.angle_rmse_deg.toFixed(1)}°; v1 ${M.v1.J_pct.toFixed(1)} %. MATLAB and the twin chose the identical angle in ${M.same_angle_js_vs_matlab_v2.identical} of ${M.same_angle_js_vs_matlab_v2.of} cases (the others differ by at most ${M.same_angle_js_vs_matlab_v2.max_diff_deg}° where the score is flat).`;
}
function gaussR() { let u = 0; while (!u) u = Math.random(); return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * Math.random()); }
function runLiveAcc() {
  const out = $('#acc-live-out'); if (!R) return; const P = R.P, n = st.day + 1, m = monthOf(st.day), hr = st.hour, sun = S.sunVec(clim.lat, n, hr), irr = senseIrr(S.irradiance(sun.sz, n, clim.kt[m]), sun);
  if (irr.ghi < 20) { out.innerHTML = 'It is night at this solar time. Move the Solar time slider (3D tab) to daytime and run again.'; return; }
  const ns = +$('#acc-noise-in').value, ver = $('#acc-ver').value, fault = $('#acc-fault-in').value, N = 40, K = ver === 'v2' ? 5 : 1;
  const mk = guard => SRMC_SC.make(S, { P, clim, zones: R.zones, w: P.energyWeight, maxStep: 90, guard }), ctl = mk(ver === 'v2'), tru = mk(true); [ctl, tru].forEach(c => c.setDay(n));
  const T = clim.tmean[m] + clim.trange[m] / 2 * Math.sin(2 * Math.PI * (hr - 9) / 24), RH = Math.max(15, Math.min(98, clim.rh[m] - 12 * Math.cos(2 * Math.PI * (hr - 15) / 24))), soil = SENS.soil, ws = clim.wind ? clim.wind[m] : 2;
  const stress = tru.stressOf(T, RH, soil).s, o = tru.search(sun, irr, T, 1, stress, ws), pm = Math.max(...o.ev.map(x => x.pv), 1e-9), cm = Math.max(...o.ev.map(x => x.crop), 1e-9), cRel = x => cm > 1e-6 ? x.crop / cm : 1, Jof = x => 0.5 * x.pv / pm + 0.5 * cRel(x), Jo = Jof(o.best);
  const inUse = 30, lsr0 = tru.evalAngle(inUse, sun, irr, T, 1, stress, ws).lsr; let sJ = 0, sPV = 0, sC = 0, sq = 0, sa = 0, mean = 0;
  for (let i = 0; i < N; i++) {
    const rd = () => { let par = SRMC_SC.UM_PER_W * lsr0 * irr.ghi * (1 + .05 * ns * gaussR()); if (fault === 'dirty') par *= .35; else if (fault === 'refl') par *= 1.9; else if (fault === 'dead') par = 0;
      return { ghi: irr.ghi * (1 + .05 * ns * gaussR()), parUm: par, T: T + 1.2 * ns * gaussR(), RH: Math.max(5, Math.min(100, RH + 3 * ns * gaussR())), soil: soil + 1.8 * ns * gaussR(), rain: false, day: n, hour: hr }; };
    const list = []; for (let k = 0; k < K; k++) list.push(rd()); const d = ctl.decide(K > 1 ? ctl.fuse(list) : list[0], { angle: inUse }), x = tru.evalAngle(d.angle, sun, irr, T, 1, stress, ws);
    sJ += Jof(x) / Jo; sPV += x.pv / pm; sC += cRel(x); sq += (d.angle - o.best.a) ** 2; sa += Math.abs(d.angle - o.best.a); mean += d.angle;
  }
  out.innerHTML = `<b>${N} decisions</b> at day ${n}, solar time ${hr.toFixed(1)} h, ${ver === 'v2' ? 'median of 5 readings + guard' : 'one reading, no guard'}, noise ×${ns}${fault !== 'none' ? ', PAR fault: ' + fault : ''}:<br>best possible angle <b>${o.best.a.toFixed(1)}°</b>, controller average <b>${(mean / N).toFixed(1)}°</b> (RMS error ${Math.sqrt(sq / N).toFixed(1)}°, mean error ${(sa / N).toFixed(1)}°)<br>combined score <b>${(100 * sJ / N).toFixed(1)} %</b> of the best, electricity <b>${(100 * sPV / N).toFixed(1)} %</b>, crop light value <b>${(100 * sC / N).toFixed(1)} %</b>`;
}
