/* SRMC Digital Twin — UI layer. Uses window.SRMC (engine) and window.SRMC_DATA (libraries). */
(function () {
'use strict';
const S = window.SRMC, DATA = window.SRMC_DATA, D2R = Math.PI / 180;
const $ = (q, el) => (el || document).querySelector(q), $$ = (q, el) => [...(el || document).querySelectorAll(q)];
const fmt = (v, d = 0) => Number.isFinite(v) ? v.toLocaleString('en-IN', { maximumFractionDigits: d, minimumFractionDigits: d }) : '—';
const inr = v => '₹' + (Math.abs(v) >= 1e7 ? fmt(v / 1e7, 2) + ' Cr' : Math.abs(v) >= 1e5 ? fmt(v / 1e5, 2) + ' L' : fmt(v));
const GROUP_COLOR = { 'Shade-tolerant spice': 0x9a7b1a, 'Leafy / herb': 0x4f9d2f, 'Plantation': 0x2f6b2a, 'Vegetable': 0x6aa84f, 'Cereal': 0xb8b04a, 'Millet': 0xa9a14a, 'Oilseed / pulse': 0x7bb33a, 'Cash crop': 0x3f8a3a };
const ZCOL = ['#72B830', '#2AC4C4', '#F0B030', '#C084FC'];

const st = { climId: 'tce_madurai', soilId: 'red_sandy_loam', p: {}, zoneSel: [null, null, null, null], zoneSow: [null, null, null, null],
  day: 105, hour: 9.5, tab: 'twin', rain: false, playing: false, siteId: 'trotters', labels: true, overlay: false, grid: true, auto: true };
let R = null, clim, soil;

/* ---------------- compute ---------------- */
function compute() {
  clim = DATA.climates.find(c => c.id === st.climId); soil = DATA.soils.find(s => s.id === st.soilId);
  const zoneCrops = st.zoneSel.map((id, i) => id ? { id, sowMonth: st.zoneSow[i] } : (st.zoneSow[i] != null ? { id: null, sowMonth: st.zoneSow[i] } : null));
  R = S.run({ clim, soil, crops: DATA.crops, params: st.p, zoneCrops });
  R._sweep = null; R._tank = null;
  updateKPIs(); designChecks(); updateZoneCards(); renderTab(); scene3d.refresh();
}
let tmr; const compSoon = () => { clearTimeout(tmr); tmr = setTimeout(compute, 60); };

/* ---------------- KPI / sidebar ---------------- */
function updateKPIs() {
  const e = R.eco, w = R.wb, self = w.demand ? 100 * w.supplied / w.demand : 100;
  $('#kpis').innerHTML = [
    ['Solar output', fmt(e.kwh / 1000, 0) + ' MWh/yr', fmt(e.specificYield, 0) + ' kWh/kWp · ' + fmt(e.kwp, 0) + ' kWp/ha'],
    ['Rain harvested', fmt(w.harvested, 0) + ' m³/yr', 'of ' + fmt(w.rainTotal, 0) + ' mm rain · cistern ' + fmt(R.P.tankM3) + ' m³'],
    ['Irrigation from rain', fmt(self, 0) + ' %', fmt(w.unmet, 0) + ' m³ borewell top-up'],
    ['Mean crop light', fmt(R.annual.meanLight * 100, 0) + ' %', 'of open-field sunlight'],
    ['Crop net / yr', inr(e.cropNet), 'per hectare'],
    ['Farmer income / month', inr(e.farmerMonthlyAvg), 'industry pays ₹' + R.P.tariff + '/kWh · farmer gets ' + fmt(R.P.farmerShare * 100, 0) + '% + crops']
  ].map(k => `<div class="kpi"><div class="kl">${k[0]}</div><div class="kv">${k[1]}</div><div class="ks">${k[2]}</div></div>`).join('');
}
function designChecks() {
  const P = R.P, N = Math.max(2, Math.round(25 / P.pitch)), W = N * P.pitch, maxT = P.tiltMode === 'fixed' ? Math.abs(P.tilt) : P.tiltMode === 'smart' ? Math.max(...P.stops) : P.tiltMax;
  const edge = P.height - P.panelW / 2 * Math.sin(maxT * D2R), need = 4 + P.panelW / 2 * Math.sin(maxT * D2R), gap = P.pitch - P.panelW;
  const rows = [
    [edge >= 4, `Lowest panel edge at ${maxT}° = <b>${fmt(edge, 2)} m</b> (spec ≥ 4.0 m for the harvester)` + (edge >= 4 ? '' : ` — raise pivot height to ≥ <b>${fmt(need, 1)} m</b> or lower the tilt stop`)],
    [gap <= 0.004, gap <= 0.004 ? `Flat-mode seals: gap <b>${fmt(gap * 1000, 0)} mm</b> ≤ 3 mm — sealed catchment (${fmt(Math.min(1, P.panelW / P.pitch) * 100, 0)}% of land)` : `Flat mode does <b>not</b> seal (gap ${fmt(gap, 2)} m): catchment is only the panel footprint (${fmt(Math.min(1, P.panelW / P.pitch) * 100, 0)}%) — the rest of the rain falls on the crops`],
    [W <= 30 && N <= 20, `Wire run ${fmt(W, 1)} m with ${N} panels — single motor OK (≤ 30 m, ≤ 20 panels)`],
    [P.bayLen - 0.22 >= 6, `Machinery lane between columns ${fmt(P.bayLen - 0.22, 1)} m (spec ≥ 6 m; harvester ≈ 3 m wide)`]
  ];
  $('#checks').innerHTML = '<b>Design checks vs your specification</b>' + rows.map(r => `<div class="${r[0] ? 'ok' : 'bad'}">${r[0] ? '✔' : '✖'} ${r[1]}</div>`).join('');
}
function applyDesign(id, quiet) {
  const D = DATA.design.presets[id]; if (!D) return; st.designId = id;
  const w = +(D.panelPitch - D.panelGap).toFixed(4), H = +(D.clearanceLowestEdge + w / 2 * Math.sin(D.maxTiltDeg * D2R)).toFixed(2), n = Math.round((D.stopsDeg[1] - D.stopsDeg[0]) / 5) + 1;
  Object.assign(st.p, { bayLen: D.bayLen, pitch: D.panelPitch, panelW: w, height: H, tankM3: D.cistern.m3, rainSlope: D.rainSlopeDeg, stops: Array.from({ length: n }, (_, i) => D.stopsDeg[0] + 5 * i), tilt: Math.min(45, D.stopsDeg[1]), sagRatio: D.sagRatio, tubeD: D.tube ? D.tube.D : 60.3 });
  const set = (id2, v, lab) => { const el = $('#' + id2); if (el) { el.value = v; const l = $('#v-' + id2); if (l) l.textContent = lab; } };
  set('p-pitch', D.panelPitch, D.panelPitch + ' m'); set('p-width', w, w + ' m'); set('p-height', H, H + ' m'); set('p-tank', D.cistern.m3, D.cistern.m3 + ' m³');
  $('#design-info').textContent = D.label + ' · pivot height derived: ' + D.clearanceLowestEdge + ' m lowest-edge clearance + ' + (w / 2).toFixed(2) + ' m × sin ' + D.maxTiltDeg + '° = ' + H + ' m';
  if (!quiet) compute();
}
function buildControls() {
  const sel = (id, arr, val, lab) => `<select id="${id}">${arr.map(a => `<option value="${a.id}" ${a.id === val ? 'selected' : ''}>${lab(a)}</option>`).join('')}</select>`;
  $('#s-design').innerHTML = Object.entries(DATA.design.presets).map(([k, v]) => `<option value="${k}" ${k === DATA.design.active ? 'selected' : ''}>${v.label}</option>`).join('');
  $('#s-design').onchange = e => applyDesign(e.target.value);
  $('#c-clim').innerHTML = sel('s-clim', DATA.climates, st.climId, c => c.name);
  $('#c-soil').innerHTML = sel('s-soil', DATA.soils, st.soilId, s => s.name);
  $('#s-clim').onchange = e => { st.climId = e.target.value; const c = DATA.climates.find(x => x.id === st.climId);
    if (c.suggest_soil && $('#auto-soil').checked) { st.soilId = c.suggest_soil; $('#s-soil').value = st.soilId; } info(); compute(); };
  $('#s-soil').onchange = e => { st.soilId = e.target.value; info(); compute(); };
  $('#auto-soil').onchange = () => {};
  const sl = (id, key, fmtf) => { const el = $('#' + id); el.oninput = () => { st.p[key] = el.tagName === 'SELECT' ? el.value : +el.value; $('#v-' + id).textContent = fmtf ? fmtf(el.value) : el.value; compSoon(); }; };
  sl('p-height', 'height', v => v + ' m'); sl('p-pitch', 'pitch', v => v + ' m'); sl('p-width', 'panelW', v => v + ' m');
  sl('p-tilt', 'tilt', v => v + '°'); sl('p-tank', 'tankM3', v => v + ' m³'); sl('p-thr', 'harvestThreshold', v => v + ' mm');
  sl('p-year', 'year', v => 'year ' + v); sl('p-tiltMax', 'tiltMax', v => v + '°');
  const rowsFor = v => { $('#row-tilt').style.display = v === 'fixed' ? '' : 'none'; $('#row-tmax').style.display = v === 'track' ? '' : 'none'; $('#row-w').style.display = v === 'smart' ? '' : 'none'; };
  $('#p-res').onchange = e => { st.p.angleStep = +e.target.value; compute(); };
  $('#p-mode').onchange = e => { st.p.tiltMode = e.target.value; rowsFor(e.target.value); compute(); }; rowsFor('smart');
  sl('p-w', 'energyWeight', v => Math.round(v * 100) + '% energy / ' + Math.round((1 - v) * 100) + '% crop');
  $('#p-layout').onchange = e => { const v = e.target.value; if (v === 'spec') { st.p.pitch = 3.125; st.p.panelW = 3.122; } else if (v === 'bal') { st.p.pitch = 6.25; st.p.panelW = 3.1; } else { st.p.pitch = 12.5; st.p.panelW = 3.1; }
    $('#p-pitch').value = st.p.pitch; $('#v-p-pitch').textContent = st.p.pitch + ' m'; $('#p-width').value = st.p.panelW; $('#v-p-width').textContent = st.p.panelW + ' m'; compute(); };
  $('#s-site').onchange = e => { st.siteId = e.target.value; scene3d.rebuild(); scene3d.view('canopy'); };
  $$('[data-view]').forEach(b => b.onclick = () => scene3d.view(b.dataset.view));
  $('#c-labels').onchange = e => { st.labels = e.target.checked; scene3d.refresh(true); };
  $('#c-overlay').onchange = e => { st.overlay = e.target.checked; scene3d.refresh(true); };
  $('#c-grid').onchange = e => { st.grid = e.target.checked; scene3d.refresh(true); };
  $('#c-auto').onchange = e => { st.auto = e.target.checked; scene3d.refresh(true); };
  $('#t-day').oninput = e => { st.day = +e.target.value; scene3d.refresh(true); hud(); if (st.tab === 'light') renderTab(); };
  $('#t-hour').oninput = e => { st.hour = +e.target.value; scene3d.refresh(true); hud(); if (st.tab === 'light') renderTab(); };
  $('#b-rain').onclick = () => { st.rain = !st.rain; $('#b-rain').classList.toggle('on', st.rain); scene3d.refresh(true); };
  $('#b-play').onclick = () => { st.playing = !st.playing; $('#b-play').textContent = st.playing ? '⏸ Pause day' : '▶ Play day'; };
  $$('.tab').forEach(t => t.onclick = () => { st.tab = t.dataset.t; $$('.tab').forEach(x => x.classList.toggle('on', x === t)); renderTab(); });
  info();
}
function info() { const s = DATA.soils.find(x => x.id === st.soilId), c = DATA.climates.find(x => x.id === st.climId);
  $('#soil-info').textContent = s.note + ' · drainage ' + s.drain + '/5 · pH ' + s.ph.join('–') + ' · OC ' + s.oc0 + '%';
  $('#clim-info').textContent = `${c.lat.toFixed(2)}°N ${c.lon.toFixed(2)}°E · ${fmt(c.rain.reduce((a, b) => a + b, 0))} mm/yr · ${fmt(c.tmean.reduce((a, b) => a + b, 0) / 12, 1)} °C mean`; }
function updateZoneCards() {
  const mn = S.MNAME;
  $('#zones').innerHTML = R.wb.zones.map((z, i) => {
    const rk = R.ranking[i];
    const opts = ['<option value="">Auto: best fit</option>'].concat(rk.map(r => `<option value="${r.id}" ${st.zoneSel[i] === r.id ? 'selected' : ''}>${r.name} · ${fmt(r.net / 1000, 0)}k ₹/ha</option>`));
    const sow = ['<option value="">Default sowing</option>'].concat(mn.map((m, k) => `<option value="${k}" ${st.zoneSow[i] === k ? 'selected' : ''}>Sow ${m}</option>`));
    return `<div class="zcard" style="border-left-color:${ZCOL[i]}"><div class="zh"><b>Zone ${i + 1}</b><span>${fmt(R.annual.meanStrip[i] * 100, 0)}% light</span></div>
      <select data-z="${i}" class="zs">${opts}</select><select data-z="${i}" class="zw">${sow}</select>
      <div class="zm">${z.name}: <b>${fmt(z.yield, 1)} t/ha</b> · water ${fmt(z.waterRatio * 100, 0)}%</div></div>`;
  }).join('');
  $$('.zs').forEach(el => el.onchange = () => { st.zoneSel[+el.dataset.z] = el.value || null; compute(); });
  $$('.zw').forEach(el => el.onchange = () => { st.zoneSow[+el.dataset.z] = el.value === '' ? null : +el.value; compute(); });
}

/* ---------------- tabs ---------------- */
function renderTab() {
  $$('.pane').forEach(p => p.style.display = p.id === 'pane-' + st.tab ? '' : 'none');
  if (st.tab === 'twin') { scene3d.resize(); hud(); }
  else if (st.tab === 'light') tabLight(); else if (st.tab === 'tilt') tabTilt(); else if (st.tab === 'water') tabWater();
  else if (st.tab === 'mech') tabMech(); else if (st.tab === 'crops') tabCrops(); else if (st.tab === 'eco') tabEco(); else if (st.tab === 'method') tabMethod();
}

/* ---------------- tiny chart library ---------------- */
function cv(el, h) { const dpr = Math.min(2, window.devicePixelRatio || 1), w = el.clientWidth || 600; el.width = w * dpr; el.height = h * dpr; el.style.height = h + 'px';
  const g = el.getContext('2d'); g.setTransform(dpr, 0, 0, dpr, 0, 0); g.clearRect(0, 0, w, h); return { g, w, h }; }
const TXT = '#c9d1c0', GRID = 'rgba(255,255,255,.08)';
function nice(a, b) { if (a === b) { b = a + 1; } const sp = (b - a), mag = Math.pow(10, Math.floor(Math.log10(sp))), n = sp / mag; const st = n > 5 ? 2 : n > 2 ? 1 : n > 1 ? .5 : .2; const step = st * mag; return { lo: Math.floor(a / step) * step, hi: Math.ceil(b / step) * step, step }; }
function chart(el, o) {                          // o: {h, xs, series:[{y, color, type, axis, label, dash}], xl, yl, y2l, xt, ymin, ymax, y2min, y2max, marks:[{x,label,color}]}
  const { g, w, h } = cv(el, o.h || 260), L = 52, Rr = o.y2 ? 52 : 14, T = 14, B = 38, pw = w - L - Rr, ph = h - T - B;
  const ax = n => { const ys = o.series.filter(s => (s.axis || 1) === n).flatMap(s => s.stackedTop || s.y); if (!ys.length) return null;
    let lo = n === 1 ? o.ymin : o.y2min, hi = n === 1 ? o.ymax : o.y2max; if (lo == null) lo = Math.min(0, ...ys); if (hi == null) hi = Math.max(...ys); return nice(lo, hi); };
  const A1 = ax(1), A2 = ax(2), xs = o.xs, bars = o.series.some(s => s.type === 'bar');
  const xmin = bars ? -0.5 : xs[0], xmax = bars ? xs.length - 0.5 : xs[xs.length - 1];
  const X = (v, i) => L + ((bars ? i : v) - xmin) / (xmax - xmin) * pw, Yf = (A, v) => T + ph - (v - A.lo) / (A.hi - A.lo) * ph;
  g.font = '11px system-ui'; g.fillStyle = TXT; g.strokeStyle = GRID; g.lineWidth = 1; g.textAlign = 'right'; g.textBaseline = 'middle';
  for (let v = A1.lo; v <= A1.hi + 1e-9; v += A1.step) { const y = Yf(A1, v); g.beginPath(); g.moveTo(L, y); g.lineTo(L + pw, y); g.stroke(); g.fillText(+v.toFixed(2), L - 6, y); }
  if (A2) { g.textAlign = 'left'; for (let v = A2.lo; v <= A2.hi + 1e-9; v += A2.step) g.fillText(+v.toFixed(2), L + pw + 6, Yf(A2, v)); }
  g.textAlign = 'center'; g.textBaseline = 'top';
  (o.xt || xs.map((v, i) => [bars ? i : v, String(v)])).forEach(([v, lab]) => { const x = X(v, v); g.fillText(lab, x, T + ph + 6); });
  g.fillText(o.xl || '', L + pw / 2, h - 14);
  g.save(); g.translate(12, T + ph / 2); g.rotate(-Math.PI / 2); g.fillText(o.yl || '', 0, 0); if (A2) { g.restore(); g.save(); g.translate(w - 12, T + ph / 2); g.rotate(Math.PI / 2); g.fillText(o.y2l || '', 0, 0); } g.restore();
  const nb = o.series.filter(s => s.type === 'bar').length; let bi = 0;
  o.series.forEach(s => { const A = (s.axis || 1) === 2 ? A2 : A1; g.strokeStyle = s.color; g.fillStyle = s.color; g.lineWidth = 2;
    if (s.type === 'bar') { const bw = pw / xs.length * 0.8 / nb; xs.forEach((v, i) => { const x = X(v, i) - bw * nb / 2 + bi * bw, y0 = Yf(A, s.base ? s.base[i] : 0), y1 = Yf(A, (s.base ? s.base[i] : 0) + s.y[i]); g.fillRect(x, Math.min(y0, y1), bw - 1, Math.abs(y0 - y1)); }); if (!s.stack) bi++; }
    else { g.beginPath(); xs.forEach((v, i) => { const x = X(v, i), y = Yf(A, s.y[i]); i ? g.lineTo(x, y) : g.moveTo(x, y); }); if (s.dash) g.setLineDash([5, 4]); g.stroke(); g.setLineDash([]);
      if (s.type === 'area') { g.lineTo(X(xs[xs.length - 1], xs.length - 1), Yf(A, 0)); g.lineTo(X(xs[0], 0), Yf(A, 0)); g.globalAlpha = .25; g.fill(); g.globalAlpha = 1; }
      if (s.dots) xs.forEach((v, i) => { g.beginPath(); g.arc(X(v, i), Yf(A, s.y[i]), 3.5, 0, 7); g.fill(); }); } });
  (o.marks || []).forEach(m => { const x = L + (m.x - xmin) / (xmax - xmin) * pw; g.strokeStyle = m.color || '#fff'; g.setLineDash([4, 3]); g.beginPath(); g.moveTo(x, T); g.lineTo(x, T + ph); g.stroke(); g.setLineDash([]);
    g.fillStyle = m.color || '#fff'; g.textAlign = 'center'; g.textBaseline = 'bottom'; g.fillText(m.label, x, T + ph - 4); });
  const lg = o.series.filter(s => s.label); let lx = L + 8; g.textAlign = 'left'; g.textBaseline = 'middle';
  lg.forEach(s => { g.fillStyle = s.color; g.fillRect(lx, T + 6, 10, 10); g.fillStyle = TXT; g.fillText(s.label, lx + 14, T + 11); lx += 24 + g.measureText(s.label).width; });
}
function heat(el, rows, cols, M, o) {            // M[r][c] value; o:{lo,hi,fmt,h,color(v)->css, rowLab, colLab}
  const rh = o.rh || 26, lw = o.lw || 120, h = rows.length * rh + 30, { g, w } = cv(el, h), cw = (w - lw) / cols.length;
  g.font = '11px system-ui'; g.textBaseline = 'middle'; g.textAlign = 'center';
  cols.forEach((c, j) => { g.fillStyle = TXT; g.fillText(c, lw + cw * (j + .5), 12); });
  rows.forEach((r, i) => { g.textAlign = 'right'; g.fillStyle = TXT; g.fillText(r, lw - 6, 30 + rh * (i + .5) - 4);
    cols.forEach((c, j) => { const v = M[i][j]; g.fillStyle = o.color(v); g.fillRect(lw + cw * j + 1, 24 + rh * i + 1, cw - 2, rh - 2);
      g.fillStyle = '#0b0f0a'; g.textAlign = 'center'; g.fillText(o.fmt(v), lw + cw * (j + .5), 24 + rh * (i + .5)); }); });
}
const ramp = (t, a = [34, 49, 44], b = [114, 184, 48], c = [240, 200, 60]) => { t = Math.max(0, Math.min(1, t)); const m = t < .5 ? [a, b, t * 2] : [b, c, (t - .5) * 2]; return `rgb(${[0, 1, 2].map(k => Math.round(m[0][k] + (m[1][k] - m[0][k]) * m[2])).join(',')})`; };
const monthOf = d => { let m = 11; while (S.CUM[m] > d) m--; return m; };

/* ---------------- Tab: sun & light ---------------- */
function tabLight() {
  const lat = clim.lat, cols = ['#4B9EE8', '#2AC4C4', '#72B830', '#F0B030', '#FF8080'];
  const dates = [[355, 'Dec 21'], [80, 'Mar 21'], [172, 'Jun 21'], [264, 'Sep 21']]; const sp = $('#sunpath'); const { g, w, h } = cv(sp, 300);
  const L = 44, T = 14, pw = w - L - 14, ph = h - T - 40;
  g.font = '11px system-ui'; g.strokeStyle = GRID; g.fillStyle = TXT; g.textAlign = 'right'; g.textBaseline = 'middle';
  for (let e = 0; e <= 90; e += 15) { const y = T + ph - e / 90 * ph; g.beginPath(); g.moveTo(L, y); g.lineTo(L + pw, y); g.stroke(); g.fillText(e + '°', L - 6, y); }
  g.textAlign = 'center'; g.textBaseline = 'top'; ['N', 'E', 'S', 'W', 'N'].forEach((t, i) => { const x = L + i / 4 * pw; g.beginPath(); g.moveTo(x, T); g.lineTo(x, T + ph); g.stroke(); g.fillText(t, x, T + ph + 6); });
  g.fillText('Azimuth', L + pw / 2 + 60, h - 16);
  dates.forEach(([n, lab], k) => { g.strokeStyle = cols[k]; g.lineWidth = 2; g.beginPath(); let first = true;
    let pa = null; for (let hr = 4; hr <= 20; hr += .1) { const s = S.sunVec(lat, n, hr); if (s.sz <= 0) { first = true; continue; } const az = (Math.atan2(s.sx, s.sy) / D2R + 360) % 360, x = L + az / 360 * pw, y = T + ph - Math.asin(s.sz) / D2R / 90 * ph;
      if (pa !== null && Math.abs(az - pa) > 180) first = true;      // sun crosses north: break the line at the azimuth wrap
      first ? g.moveTo(x, y) : g.lineTo(x, y); first = false; pa = az; } g.stroke(); g.fillStyle = cols[k]; g.fillRect(L + 6 + k * 62, h - 14, 9, 9); g.fillStyle = TXT; g.textAlign = 'left'; g.textBaseline = 'middle'; g.fillText(lab, L + 18 + k * 62, h - 9); });
  const cs = S.sunVec(lat, st.day + 1, st.hour); if (cs.sz > 0) { const az = (Math.atan2(cs.sx, cs.sy) / D2R + 360) % 360; g.fillStyle = '#fff'; g.beginPath(); g.arc(L + az / 360 * pw, T + ph - Math.asin(cs.sz) / D2R / 90 * ph, 6, 0, 7); g.fill(); }
  heat($('#zonelight'), ['Zone 1', 'Zone 2', 'Zone 3', 'Zone 4'], S.MNAME, R.zoneMonthly.map(r => r.map(v => v * 100)), { fmt: v => v.toFixed(0), color: v => { const f = R.zoneMonthly.flat().map(x => x * 100), lo = Math.min(...f), hi = Math.max(...f); return ramp(hi - lo < 1 ? .5 : (v - lo) / (hi - lo)); }, lw: 60 });
  // hourly profile across the pitch for the selected day/hour
  const n = st.day + 1, m = monthOf(st.day), P = R.P, sun = S.sunVec(lat, n, st.hour), t = S.tiltFor(sun, Object.assign({}, P, st.rain ? { tiltMode: 'rain' } : {}), m, st.hour);
  const irr = S.irradiance(sun.sz, n, clim.kt[m]), segs = S.segments(P, t), xs = [], ys = [];
  for (let i = 0; i < 80; i++) { const x = (i + .5) / 80 * P.pitch; xs.push(+x.toFixed(2)); let lit = !S.rayBlocked(x, 0, sun.sx, sun.sz, segs, null);
    let vis = 0, tot = 0; for (let a = -90 + 3.75; a < 90; a += 7.5) { const wgt = Math.cos(a * D2R); tot += wgt; if (!S.rayBlocked(x, 0, Math.sin(a * D2R), Math.cos(a * D2R), segs, null)) vis += wgt; }
    const og = irr.ghi || 1; ys.push(sun.sz > 0.02 ? 100 * ((lit ? irr.dni * sun.sz : 0) + irr.dhi * vis / tot) / og : 0); }
  chart($('#profile'), { xs, series: [{ y: ys, color: '#72B830', type: 'area' }], xl: 'Position across one row pitch (m) — panel centred at ' + (P.pitch / 2).toFixed(2) + ' m', yl: 'Light (% open field)', ymin: 0, ymax: 100, h: 230,
    xt: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12].filter(v => v <= P.pitch).map(v => [v, String(v)]) });
  $('#light-note').innerHTML = `Selected: <b>day ${n}</b>, <b>${st.hour.toFixed(1)} h</b> solar time · sun elevation <b>${fmt(Math.asin(Math.max(0, sun.sz)) / D2R, 1)}°</b> · panel tilt <b>${fmt(t, 0)}°</b> · GHI ${fmt(irr.ghi)} W/m² (monthly-mean sky, kt ${clim.kt[m].toFixed(2)})`;
}

/* ---------------- Tab: tilt trade-off ---------------- */
function tabTilt() {
  if (!R._sweep) { const tl = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90]; R._sweep = tl.map(t => { const a = S.annualLight(R.P, clim, t); return { t, pv: a.pvKWhPerM2, light: a.meanLight * 100 }; });
    const tr = S.annualLight(Object.assign({}, R.P, { tiltMode: 'track' }), clim); R._track = { pv: tr.pvKWhPerM2, light: tr.meanLight * 100 }; }
  const sw = R._sweep, pvMax = Math.max(...sw.map(s => s.pv)), lgMax = Math.max(...sw.map(s => s.light));
  chart($('#tiltchart'), { xs: sw.map(s => s.t), series: [{ y: sw.map(s => s.pv), color: '#F0B030', label: 'PV energy (kWh/m²·yr)', dots: true }, { y: sw.map(s => s.light), color: '#72B830', label: 'Mean crop light (%)', axis: 2, dots: true }],
    xl: 'Fixed panel tilt (°)', yl: 'kWh / m² panel / yr', y2l: '% of open-field light', y2: true, ymin: 0, y2min: 0, y2max: 100, h: 300 });
  const sc = sw.map(s => s.pv / pvMax + s.light / Math.max(lgMax, 1)), best = sw[sc.indexOf(Math.max(...sc))];
  $('#tilt-note').innerHTML = `Balanced fixed tilt (max of normalised PV + light): <b>${best.t}°</b>. Sun-tracking at this layout gives <b>${fmt(R._track.pv, 0)} kWh/m²·yr</b> and <b>${fmt(R._track.light, 0)}%</b> crop light.
   Steeper panels let more light through but lose energy — the best design depends on which crops you grow.`;
  $('#tilt-table').innerHTML = '<tr><th>Tilt</th><th>kWh/m²·yr</th><th>kWh/kWp</th><th>Crop light</th></tr>' + sw.map(s => `<tr><td>${s.t}°</td><td>${fmt(s.pv, 0)}</td><td>${fmt(s.pv / R.P.eff, 0)}</td><td>${fmt(s.light, 0)}%</td></tr>`).join('') +
    `<tr class="hl"><td>Track</td><td>${fmt(R._track.pv, 0)}</td><td>${fmt(R._track.pv / R.P.eff, 0)}</td><td>${fmt(R._track.light, 0)}%</td></tr>`;
  if (R.ctrl) {
    heat($('#ctrl-heat'), S.MNAME, R.P.windows.map(w => w[0] + '–' + w[1]), R.P.schedule, { fmt: v => fmt(v, 1), color: v => ramp((v - 15) / 45), lw: 50, rh: 20 });
    $('#ctrl-note').innerHTML = `One wire-drive decision every hour (14 per day). Each window picks the tilt stop that maximises <b>${Math.round(R.P.energyWeight * 100)}% × PV energy + ${Math.round((1 - R.P.energyWeight) * 100)}% × crop-light value</b> (both normalised to the best option in that window). Steeper stops (dark green→yellow) let more light through; in months when no crop is growing the controller goes to the energy-best stop. Flat (0°) is used only in rain.`;
  }
  if (!R._cmp) { const cases = [['SRMC-DT controller', {}], ['Fixed 45° stop', { tiltMode: 'fixed', tilt: 45 }], ['PV-max fixed 15°', { tiltMode: 'fixed', tilt: 15 }], ['Crop-max controller (w = 0)', { tiltMode: 'smart', energyWeight: 0 }]];
    R._cmp = cases.map(([n, p]) => { const q = S.run({ clim, soil, crops: DATA.crops, params: Object.assign({}, st.p, p) }); return { n, q }; }); }
  $('#ctrl-table').innerHTML = '<tr><th>Design</th><th>PV kWh/m²·yr</th><th>Crop light</th><th>Solar ₹L/ha</th><th>Crop net ₹L/ha</th><th>Total ₹L/ha</th><th>Rain-fed irrigation</th></tr>' +
    R._cmp.map((c, i) => { const e = c.q.eco, w = c.q.wb; return `<tr class="${i === 0 ? 'hl' : ''}"><td>${c.n}</td><td>${fmt(c.q.annual.pvKWhPerM2, 0)}</td><td>${fmt(c.q.annual.meanLight * 100, 0)}%</td><td>${fmt((e.solarRev - e.om) / 1e5, 1)}</td><td>${fmt(e.cropNet / 1e5, 1)}</td><td>${fmt((e.solarRev - e.om + e.cropNet) / 1e5, 1)}</td><td>${fmt(w.demand ? 100 * w.supplied / w.demand : 100, 0)}%</td></tr>`; }).join('');
}

/* ---------------- Tab: water ---------------- */
function tabWater() {
  const w = R.wb, mr = [], mh = [], mi = [], md = [];
  for (let m = 0; m < 12; m++) { let a = 0, b = 0, c = 0; for (let d = S.CUM[m]; d < S.CUM[m] + S.DIM[m]; d++) { a += w.rain[d]; b += w.harvSeries[d]; c += w.irrSeries[d]; } mr.push(a); mh.push(b); mi.push(c); }
  chart($('#w-month'), { xs: S.MNAME, series: [{ y: mr, color: '#4B9EE8', type: 'bar', label: 'Rain (mm)' }, { y: mh.map(v => v / (w.catchArea / 1000)), color: '#2AC4C4', type: 'bar', label: 'Harvest (mm of catchment)' }],
    xl: 'Month', yl: 'mm', h: 240 });
  const days = [...Array(365).keys()];
  chart($('#w-tank'), { xs: days, series: [{ y: w.tankSeries, color: '#2AC4C4', type: 'area', label: 'Cistern level (m³)' }, { y: w.irrSeries.map(v => v * 4), color: '#F0B030', label: 'Irrigation draw ×4 (m³/day)' }],
    xl: 'Day of year', yl: 'm³', h: 250, ymin: 0, xt: S.CUM.map((c, i) => [c, S.MNAME[i]]), marks: [{ x: st.day, label: 'now', color: '#fff' }] });
  if (!R._tank) R._tank = S.sizeCistern(R.P, clim, soil, R.zones);
  const c = R._tank.curve;
  chart($('#w-size'), { xs: c.map(x => x.size), series: [{ y: c.map(x => x.unmetPct), color: '#FF8080', dots: true, label: 'Irrigation demand not met (%)' }, { y: c.map(x => x.harvested), color: '#2AC4C4', dots: true, axis: 2, label: 'Water harvested (m³)' }],
    xl: 'Cistern size (m³)', yl: '% unmet', y2l: 'm³ harvested', y2: true, ymin: 0, ymax: 100, y2min: 0, h: 250, marks: [{ x: R.P.tankM3, label: 'current', color: '#fff' }].filter(m => m.x <= c[c.length - 1].size) });
  const sz = R._tank.size;
  $('#w-note').innerHTML = `Catchment <b>${fmt(w.catchArea, 0)} m²/ha</b> (${fmt(w.cover * 100, 0)}% cover) · harvest <b>${fmt(w.harvested, 0)} m³</b> · overflow lost <b>${fmt(w.overflow, 0)} m³</b> · irrigation demand <b>${fmt(w.demand, 0)} m³</b> · borewell/other top-up <b>${fmt(w.unmet, 0)} m³</b>.
    Smallest tank for ≥95% of irrigation from rain: <b>${sz == null ? 'more than 3000 m³ (rain alone is not enough — add a supplementary source)' : sz + ' m³'}</b>.`;
}

/* ---------------- Tab: crops & soil ---------------- */
function tabCrops() {
  const w = R.wb;
  $('#crop-table').innerHTML = '<tr><th>Zone</th><th>Crop</th><th>Light</th><th>Season T</th><th>Light f.</th><th>Temp f.</th><th>Soil f.</th><th>Water</th><th>Yield t/ha</th><th>Net ₹/ha·yr</th></tr>' +
    w.zones.map((z, i) => `<tr><td style="color:${ZCOL[i]}">Z${i + 1}</td><td>${z.name}</td><td>${fmt(z.light * 100, 0)}%</td><td>${fmt(z.tmean, 1)}°C</td><td>${fmt(z.lf, 2)}</td><td>${fmt(z.tf, 2)}</td><td>${fmt(z.sf, 2)}</td><td>${fmt(z.waterRatio * 100, 0)}%</td><td>${fmt(z.yield, 1)}</td><td>${fmt(z.net / (z.area / 10000))}</td></tr>`).join('');
  // universal crop × soil matrix at the light of the chosen zone
  const zi = +($('#mx-zone').value || 0), Lz = R.annual.meanStrip[zi];
  const rows = DATA.crops.map(c => c.name), M = DATA.crops.map(c => { const si = S.seasonInfo(c, clim, c.sow - 1), Lc = R.zoneMonthly[zi].reduce((a, v, m) => a + v * si.monthWeights[m], 0) / c.days;
    return DATA.soils.map(s => S.potentialYield(c, s, Lc, si.tmean, R.P.year).yield * 1000 * c.price - c.cost); });
  const mx = Math.max(...M.flat()), cur = DATA.soils.findIndex(s => s.id === st.soilId);
  heat($('#matrix'), rows, DATA.soils.map(s => s.name.split(' ')[0].replace('(', '')), M.map(r => r.map(v => v / 1000)), { fmt: v => v < 0 ? '–' : fmt(v, 0), color: v => v < 0 ? '#3a2a2a' : ramp(v / (mx / 1000)), lw: 150, rh: 22 });
  $('#mx-note').innerHTML = `Net profit (₹ thousand / ha / season) if each crop is grown in each soil at <b>Zone ${zi + 1} light (${fmt(Lz * 100, 0)}%)</b> at <b>${clim.name.split(' (')[0]}</b>, before water-stress effects. Current soil: <b>${DATA.soils[cur].name}</b>. “–” = loss.`;
  const yrs = [...Array(11).keys()].map(y => y), oc = yrs.map(y => S.ocAt(soil, y));
  chart($('#oc-chart'), { xs: yrs, series: [{ y: oc, color: '#72B830', dots: true }], xl: 'Years of regeneration (cover crops, compost, mulch)', yl: 'Organic carbon (%)', ymin: 0, h: 200, marks: [{ x: R.P.year, label: 'now', color: '#fff' }] });
}

/* ---------------- Tab: economics ---------------- */
function tabEco() {
  const e = R.eco, w = R.wb, mo = e.monthly;
  chart($('#eco-bars'), { xs: S.MNAME, series: [{ y: mo.farmerSolar.map(v => v / 1e3), color: '#F0B030', type: 'bar', stack: true, label: 'Solar share from industry (monthly)' }, { y: mo.crop.map(v => v / 1e3), base: mo.farmerSolar.map(v => v / 1e3), color: '#72B830', type: 'bar', label: 'Crop net (at harvest)' }],
    xl: 'Month', yl: '₹ thousand / ha', h: 260 });
  $('#eco-table').innerHTML = `<tr><th>Who earns what (per hectare / year)</th><th>Value</th></tr>
   <tr class="hl"><td>Farmer: solar share (${fmt(R.P.farmerShare * 100, 0)}% of industry payment)</td><td>${inr(e.solarRev * R.P.farmerShare)}</td></tr><tr class="hl"><td>Farmer: crop net income</td><td>${inr(e.cropNet)}</td></tr>
   <tr class="hl"><td>Farmer total · per month</td><td>${inr(e.farmerAnnual)} · ${inr(e.farmerMonthlyAvg)}</td></tr>
   <tr><td>Industry pays for ${fmt(e.kwh / 1000, 0)} MWh at ₹${R.P.tariff}/kWh</td><td>${inr(e.solarRev)}</td></tr><tr><td>Investor / operator keeps after O&amp;M</td><td>${inr(e.industryNet)}</td></tr>
   <tr><td>Capex incl. cistern</td><td>${inr(e.capex)}</td></tr><tr><td>Investor payback</td><td>${e.industryNet > 0 ? fmt(e.capex / e.industryNet, 1) + ' years' : 'n/a'}</td></tr>
   <tr><td>CO₂ avoided (0.71 kg/kWh grid factor, assumption)</td><td>${fmt(e.co2t, 0)} t / yr</td></tr><tr><td>Rain harvested for irrigation</td><td>${fmt(w.harvested, 0)} m³ (₹ value not counted)</td></tr>`;
  const tar = [2.5, 3, 3.5, 4, 5], cap = [40000, 50000, 60000, 70000, 80000];
  const base = R.P, grid = cap.map(c => tar.map(t => { const E = S.economics(Object.assign({}, base, { capexPerKWp: c, tariff: t }), clim, R.annual, w, base.tankM3); return E.payback || 99; }));
  heat($('#eco-sens'), cap.map(c => '₹' + c / 1000 + 'k /kWp'), tar.map(t => '₹' + t + '/kWh'), grid, { fmt: v => v >= 99 ? '—' : v.toFixed(1), color: v => ramp(1 - Math.min(1, (v - 5) / 20)), lw: 90, rh: 26 });
}

function tabMethod() { /* static */ }

/* ---------------- Sensor feedback controller: pyranometer + PAR + DHT11 + soil moisture + rain sensor -> tilt ---------------- */
const SENS = { on: false, cloud: 0, temp: 31, rh: 55, soil: 26, cmd: 27, timer: 0, manualTH: false, last: null };
function senseIrr(irr, sun) {                                  // clouds: less beam, more diffuse
  const c = SENS.cloud, ghi = irr.ghi * (1 - .72 * c), dni = irr.dni * Math.pow(1 - c, 1.6), dhi = Math.max(0, ghi - dni * Math.max(sun.sz, .05));
  return { ghi, dni, dhi };
}
function senseDecide(apply) {
  if (!R || !SENS.on) return; const P = R.P, n = st.day + 1, m = monthOf(st.day), hr = st.hour, sun = S.sunVec(clim.lat, n, hr);
  const irr = senseIrr(S.irradiance(sun.sz, n, clim.kt[m]), sun);
  const mt = clim.tmean[m] + clim.trange[m] / 2 * Math.sin(2 * Math.PI * (hr - 9) / 24), mr = Math.max(15, Math.min(98, clim.rh[m] - 12 * Math.cos(2 * Math.PI * (hr - 15) / 24)));
  if (!SENS.manualTH) { SENS.temp = +mt.toFixed(1); SENS.rh = Math.round(mr); const a = $('#sens-temp'), b = $('#sens-rh'); if (a) { a.value = SENS.temp; $('#v-sens-temp').textContent = SENS.temp + ' °C'; } if (b) { b.value = SENS.rh; $('#v-sens-rh').textContent = SENS.rh + ' %'; } }
  const T = SENS.temp, RH = SENS.rh, es = 0.6108 * Math.exp(17.27 * T / (T + 237.3)), vpd = es * (1 - RH / 100);
  const lopt = R.zones.reduce((a, z) => a + z.crop.lopt, 0) / R.zones.length, lmin = R.zones.reduce((a, z) => a + z.crop.lmin, 0) / R.zones.length;
  let sf = 1; const why = []; if (vpd > 2.5) { sf *= .85; why.push('VPD ' + vpd.toFixed(1) + ' kPa > 2.5: more shade'); } if (T > 38) { sf *= .9; why.push('air ' + T.toFixed(0) + ' C > 38: more shade'); } if (SENS.soil < 20) { sf *= .9; why.push('soil dry (' + SENS.soil + ' %): more shade'); }
  const target = Math.max(lmin, Math.min(1, lopt * sf)), rain = st.rain, night = irr.ghi < 20;
  const Q = Object.assign({}, P, { tiltMode: 'fixed', tilt: SENS.cmd }); let lsr = 0, parUm = 0, pv = 0, pvBest = 0;
  if (!night) { const g = S.groundLightHour(Q, sun, irr, SENS.cmd), mean = g.reduce((a, b) => a + b, 0) / g.length; lsr = mean / Math.max(irr.ghi, 1); parUm = 2.05 * mean;
    const w = clim.wind ? clim.wind[m] : 2; pv = S.panelPower(Q, sun, irr, SENS.cmd, T, w).p; pvBest = S.panelPower(Object.assign({}, P, { tiltMode: 'fixed', tilt: 15 }), sun, irr, 15, T, w).p; }
  let action;
  if (rain) action = 'RAIN SENSOR WET: flat roof, ' + P.rainSlope + '° fall to the gutter (harvest)';
  else if (night) action = 'Pyranometer < 20 W/m2: night, park at 15°';
  else { const err = target - lsr; if (Math.abs(err) < .03) action = 'PAR/GHI = ' + (lsr * 100).toFixed(0) + ' % is on target (' + (target * 100).toFixed(0) + ' %): hold angle';
    else { const step = Math.max(-6, Math.min(6, err * 90)); if (apply) SENS.cmd = Math.max(15, Math.min(60, Math.round((SENS.cmd + step) * 2) / 2)); action = err > 0 ? 'crops get too little light (' + (lsr * 100).toFixed(0) + ' % < ' + (target * 100).toFixed(0) + ' %): tilt UP to ' + SENS.cmd.toFixed(1) + '°' : 'crops get more light than needed (' + (lsr * 100).toFixed(0) + ' % > ' + (target * 100).toFixed(0) + ' %): tilt DOWN toward the panels\' best angle, now ' + SENS.cmd.toFixed(1) + '°'; } }
  const dry = SENS.soil < 20, wet = SENS.soil > 35;
  SENS.last = { lsr, target, vpd, T, RH, par: parUm, ghi: irr.ghi, rain, night, action, pvRel: pvBest > 0 ? pv / pvBest : 0 };
  const el = $('#sens-trace'); if (el) el.innerHTML =
    `<div><b>1 Pyranometer (GHI):</b> ${irr.ghi.toFixed(0)} W/m² ${night ? '(night)' : ''}</div>
     <div><b>2 PAR sensor under the canopy:</b> ${parUm.toFixed(0)} µmol/m²/s → share of full sun (PAR/GHI) = <b>${(lsr * 100).toFixed(0)} %</b> · crop target <b>${(target * 100).toFixed(0)} %</b></div>
     <div><b>3 DHT11:</b> ${T.toFixed(1)} °C, ${RH} % RH → VPD ${vpd.toFixed(1)} kPa ${why.length ? '<span style="color:#ffb3a8">(' + why.join('; ') + ')</span>' : '(no stress)'}</div>
     <div><b>4 Soil moisture:</b> ${SENS.soil} % → ${dry ? '<span style="color:#ffb3a8">dry: drip irrigation ON</span>' : wet ? 'waterlogging risk: irrigation OFF' : 'optimal, irrigation standby'}</div>
     <div><b>5 Rain sensor:</b> ${rain ? '<span style="color:#9ad0ff">WET</span> → flat mode' : 'dry'}</div>
     <div style="margin-top:6px;color:#ffe08a"><b>Decision:</b> ${action}</div>
     <div style="color:#b8e6a0">Panel angle <b>${SENS.cmd.toFixed(1)}°</b> · solar output now ≈ <b>${(SENS.last.pvRel * 100).toFixed(0)} %</b> of the best-angle output while keeping the crop at its light target</div>`;
}

/* ---------------- Tab: mechanism (how the motor tilts the panels) ---------------- */
const MECH = { cur: 3, target: 3, auto: true, step: 0, hold: 0, running: false, last: 0, seq: [3, 15, 30, 45, 60, 90, 45, 3], names: ['RAIN MODE (flat roof, 3° fall)', 'TILT 15°', 'TILT 30°', 'TILT 45°', 'TILT 60° (max)', 'WIND STOW 90°', 'TILT 45°', 'RAIN MODE (flat roof, 3° fall)'], t: 0 };
function tabMech() {
  const el = $('#mechcv'); if (!el) return; MECH.t = 0;
  if (!MECH.bound) {
    MECH.bound = true;
    $$('[data-mech]').forEach(b => b.onclick = () => { MECH.auto = false; $('#mech-auto').checked = false; MECH.target = +b.dataset.mech; });
    $('#mech-slider').oninput = e => { MECH.auto = false; $('#mech-auto').checked = false; MECH.target = +e.target.value; MECH.cur = +e.target.value; };
    $('#mech-auto').onchange = e => { MECH.auto = e.target.checked; MECH.step = 0; MECH.hold = 0; };
  }
  if (!MECH.running) { MECH.running = true; MECH.last = performance.now(); requestAnimationFrame(mechLoop); }
}
function mechLoop(now) {
  if (st.tab !== 'mech' || !R) { MECH.running = false; return; }
  const dt = Math.min(.08, (now - MECH.last) / 1000); MECH.last = now; MECH.t += dt;
  if (MECH.auto) { if (Math.abs(MECH.cur - MECH.seq[MECH.step]) < .05) { MECH.hold += dt; if (MECH.hold > 1.8) { MECH.hold = 0; MECH.step = (MECH.step + 1) % MECH.seq.length; } } MECH.target = MECH.seq[MECH.step]; }
  const e = MECH.target - MECH.cur, mv = 22 * dt; MECH.cur += Math.abs(e) < mv ? e : Math.sign(e) * mv;     // motor + rate limit
  $('#mech-slider').value = MECH.cur; $('#mech-v').textContent = MECH.cur.toFixed(1) + '°'; drawMech($('#mechcv'), MECH.cur, MECH.target); drawClose($('#mechcv2'), MECH.cur, MECH.target); drawPulley($('#mechcv3')); requestAnimationFrame(mechLoop);
}
function drawMech(cvEl, th, target) {
  const P = R.P, PITCH = P.pitch, PW = P.panelW, H = P.height, bay = P.bayLen, SAG = P.sagRatio || 0.0833, Lreal = 0.44, L = 0.85, tr = th * D2R;
  const VX = 8.3, W0 = cvEl.clientWidth || 700, s = W0 / (2 * VX), zp = H - 1.15, retZ = zp - .55, zmin = retZ - .95, zmax = H + 1.55;
  const { g, w, h } = cv(cvEl, Math.round((zmax - zmin) * s + 70)), x0 = w / 2, X = x => x0 + x * s, Z = z => h - 30 - (z - zmin) * s;
  const sky = g.createLinearGradient(0, 0, 0, h); sky.addColorStop(0, '#16222e'); sky.addColorStop(1, '#2b3f52'); g.fillStyle = sky; g.fillRect(0, 0, w, h);
  g.fillStyle = '#4f9d2f'; g.fillRect(0, h - 22, w, 22); g.fillStyle = '#e8eef0'; g.font = '11px system-ui'; g.textAlign = 'left'; g.fillText('crops and soil below (not to scale)', 8, h - 7);
  const nPan = 4, xs = Array.from({ length: nPan }, (_, k) => (k - (nPan - 1) / 2) * PITCH), topY = H - .1;
  const cols = []; for (let j = 0; j < 12; j++) { const xx = (j + .5) * bay; if (xx <= VX - .6) { cols.push(xx); cols.push(-xx); } } cols.sort((a, b) => a - b);
  const rain = th < 6, line = (a, b, c, d, col, lw, dash) => { g.strokeStyle = col; g.lineWidth = lw; g.setLineDash(dash || []); g.beginPath(); g.moveTo(X(a), Z(b)); g.lineTo(X(c), Z(d)); g.stroke(); g.setLineDash([]); };
  const txt = (t, x, y, col, size, al) => { g.fillStyle = col || '#e8eef0'; g.font = '600 ' + (size || 12) + 'px system-ui'; g.textAlign = al || 'left'; g.fillText(t, x, y); };
  if (rain) { g.strokeStyle = 'rgba(150,200,255,.6)'; g.lineWidth = 1.3; for (let i = 0; i < 60; i++) { const rx = ((i * 97) % 1000) / 1000 * w, ry = (((i * 53) % 400) + MECH.t * 330) % (h * .5); g.beginPath(); g.moveTo(rx, 4 + ry); g.lineTo(rx - 3, 4 + ry + 14); g.stroke(); } }
  else { g.strokeStyle = 'rgba(255,224,120,.22)'; g.lineWidth = 7; for (let i = -4; i <= 4; i++) { g.beginPath(); g.moveTo(X(i * 2.4 - 3), 0); g.lineTo(X(i * 2.4 + 1.5), h - 22); g.stroke(); } }
  // columns, carrier rope, hangers
  cols.forEach(cx => { g.fillStyle = '#8d969e'; g.fillRect(X(cx) - .1 * s, Z(H + .75), .2 * s, h - Z(H + .75) - 22); });
  for (let i = 0; i < cols.length - 1; i++) { const a = cols[i], b = cols[i + 1], sp = b - a, sag = SAG * sp; g.strokeStyle = '#c9d0d6'; g.lineWidth = 2.5; g.beginPath(); for (let u = 0; u <= 20; u++) { const xx = a + sp * u / 20, zz = topY - 4 * sag * (u / 20) * (1 - u / 20); u ? g.lineTo(X(xx), Z(zz)) : g.moveTo(X(xx), Z(zz)); } g.stroke(); }
  const carrierZ = xx => { for (let i = 0; i < cols.length - 1; i++) if (xx >= cols[i] && xx <= cols[i + 1]) { const sp = cols[i + 1] - cols[i], u = (xx - cols[i]) / sp; return topY - 4 * SAG * sp * u * (1 - u); } return topY; };
  xs.forEach(xc => line(xc, carrierZ(xc), xc, H - .05, '#c9d0d6', 1.6));
  // gutter on the east edge
  const lastx = xs[nPan - 1] + PW / 2 * Math.cos(3 * D2R), gx = lastx; g.fillStyle = '#7a838c'; g.fillRect(X(gx), Z(H - .2), .5 * s, .07 * s); g.fillRect(X(gx + .45), Z(H + .02), .05 * s, .3 * s);
  if (rain) { g.fillStyle = 'rgba(60,160,230,.95)'; g.fillRect(X(gx + .03), Z(H - .13), .4 * s, .08 * s); }
  // drive wire path
  const tips = xs.map(xc => [xc - L * Math.sin(tr), H - L * Math.cos(tr)]), xE = xs[nPan - 1] + PITCH / 2 + .75, xW = xs[0] - PITCH / 2 - .75;
  const path = [[xE, zp]].concat(tips.slice().reverse()).concat([[xW, zp]]);
  line(xW, zp, xW, retZ, '#b84a3c', 2.4); line(xW, retZ, xE, retZ, '#b84a3c', 2.4, [7, 5]);
  g.strokeStyle = '#ff5a4a'; g.lineWidth = 3.2; g.beginPath(); path.forEach((p, i) => i ? g.lineTo(X(p[0]), Z(p[1])) : g.moveTo(X(p[0]), Z(p[1]))); g.stroke();
  // panels, pivots, lever arms
  xs.forEach((xc, k) => {
    const dx = PW / 2 * Math.cos(tr), dz = PW / 2 * Math.sin(tr); g.strokeStyle = '#1f3d8a'; g.lineWidth = .14 * s; g.lineCap = 'butt'; g.beginPath(); g.moveTo(X(xc - dx), Z(H + dz)); g.lineTo(X(xc + dx), Z(H - dz)); g.stroke();
    g.strokeStyle = '#8fb0ee'; g.lineWidth = 1.2; for (let c = 1; c < 8; c++) { const u = c / 8 - .5, px = X(xc + 2 * dx * u), pz = Z(H - 2 * dz * u); g.beginPath(); g.moveTo(px, pz - .07 * s); g.lineTo(px, pz + .07 * s); g.stroke(); }
    g.fillStyle = '#05080c'; [-1, 1].forEach(sg => { g.beginPath(); g.arc(X(xc + sg * dx), Z(H - sg * dz), .055 * s, 0, 7); g.fill(); });
    g.fillStyle = '#c9d0d6'; g.beginPath(); g.arc(X(xc), Z(H), .14 * s, 0, 7); g.fill(); g.strokeStyle = '#222'; g.lineWidth = 1; g.stroke();
    line(xc, H, tips[k][0], tips[k][1], '#f0b030', 4); g.fillStyle = '#ff5a4a'; g.beginPath(); g.arc(X(tips[k][0]), Z(tips[k][1]), .1 * s, 0, 7); g.fill();
  });
  // rest positions of the tips and the identical shift d of every tip
  xs.forEach((xc, k) => { const rx = xc, rz = H - L; g.strokeStyle = 'rgba(255,255,255,.8)'; g.lineWidth = 1.3; g.setLineDash([3, 3]); g.beginPath(); g.arc(X(rx), Z(rz), .1 * s, 0, 7); g.stroke(); g.setLineDash([]);
    if (Math.abs(tips[k][0] - rx) > .08) { g.strokeStyle = '#7CFFB2'; g.lineWidth = 2.2; g.beginPath(); g.moveTo(X(rx), Z(rz) + .22 * s); g.lineTo(X(tips[k][0]), Z(rz) + .22 * s); g.stroke(); const dir = Math.sign(tips[k][0] - rx); g.beginPath(); g.moveTo(X(tips[k][0]), Z(rz) + .22 * s); g.lineTo(X(tips[k][0]) - dir * 7, Z(rz) + .22 * s - 4); g.lineTo(X(tips[k][0]) - dir * 7, Z(rz) + .22 * s + 4); g.closePath(); g.fillStyle = '#7CFFB2'; g.fill(); } });
  { const ph = (MECH.t * 60) % 26; g.fillStyle = '#ffd0c8'; for (let i = 0; i < path.length - 1; i++) { const a = path[i], b = path[i + 1], len = Math.hypot((b[0] - a[0]) * s, (b[1] - a[1]) * s); for (let q = ph; q < len; q += 26) { const u = q / len, px = X(a[0] + (b[0] - a[0]) * u), pz = Z(a[1] + (b[1] - a[1]) * u); g.beginPath(); g.arc(px, pz, 2.2, 0, 7); g.fill(); } } }
  // pulleys, motor, drum (pull-pull loop: forward strand + return strand wound on the same drum)
  [[xE, zp], [xW, zp]].forEach(([a, b]) => { g.fillStyle = '#c9d0d6'; g.beginPath(); g.arc(X(a), Z(b), .17 * s, 0, 7); g.fill(); g.strokeStyle = '#222'; g.stroke(); });
  const dwx = xE + 1.15, dwz = (zp + retZ) / 2, dr = .45, d_mm = Lreal * 1000 * (Math.sin(tr) - Math.sin(3 * D2R)), phi = d_mm / 1000 / 0.06;
  g.fillStyle = '#252a30'; g.fillRect(X(dwx - .75), Z(dwz + .95), 2.2 * s, 1.9 * s); g.fillStyle = '#c9d0d6'; g.beginPath(); g.arc(X(dwx), Z(dwz), dr * s, 0, 7); g.fill(); g.strokeStyle = '#333'; g.lineWidth = 2; g.stroke();
  for (let q = 0; q < 6; q++) { const a = -phi * 3.3 + q * Math.PI / 3; g.strokeStyle = q === 0 ? '#b02020' : 'rgba(40,40,40,.55)'; g.lineWidth = q === 0 ? 3 : 1.5; g.beginPath(); g.moveTo(X(dwx), Z(dwz)); g.lineTo(X(dwx + dr * .92 * Math.cos(a)), Z(dwz + dr * .92 * Math.sin(a))); g.stroke(); }
  line(xE, zp, dwx - dr * .75, dwz + dr * .7, '#ff5a4a', 3.2); line(xE, retZ, dwx - dr * .75, dwz - dr * .7, '#b84a3c', 2.4, [7, 5]);
  g.fillStyle = '#35e07a'; g.beginPath(); g.arc(X(dwx + .9), Z(dwz + .65), .07 * s, 0, 7); g.fill();
  // labels
  const lab = (t, tx, ty, ax, az, col, al) => { g.font = '600 12.5px system-ui'; const tw = g.measureText(t).width; tx = Math.max(tw / 2 + 4, Math.min(w - tw / 2 - 4, tx)); g.strokeStyle = 'rgba(255,255,255,.55)'; g.lineWidth = 1; g.beginPath(); g.moveTo(tx, ty + 4); g.lineTo(X(ax), Z(az)); g.stroke(); txt(t, tx, ty, col, 12.5, al || 'center'); };
  lab('1 MOTOR + DRUM + ENCODER', X(dwx + .2), 20, dwx + .1, dwz + .95, '#8ff0b0');
  lab('2 DRIVE WIRE slides', X(xE - 2.2), h - 38, xE - 2.2, zp - .02, '#ff9a8c');
  lab('3 LEVER ARM on the pivot tube', X(tips[1][0]) - 30, h - 54, tips[1][0] + .1, (H + tips[1][1]) / 2, '#ffd36a');
  lab('4 PANEL + PIVOT TUBE turns', X(xs[0]) - 10, 20, xs[0] - .2, H + dz0(PW, tr), '#9ec1ff');
  lab('5 CARRIER ROPE (holds the weight)', X(cols.length > 3 ? cols[1] : -2.5) - 30, 44, cols[Math.min(1, cols.length - 1)] - .6, carrierZ(cols[Math.min(1, cols.length - 1)] - .6), '#e0e6ea');
  lab('6 GUTTER to cistern', X(gx + .45) + 10, Z(H) - 26, gx + .25, H - .2, '#8fd0ff');
  lab('return strand (pull-pull loop)', X(0), Z(retZ) + 22, 0, retZ, '#e1928a');
  // readouts
  const edge = H - PW / 2 * Math.sin(Math.abs(tr)), gap = PITCH - PW * Math.cos(tr), turns = phi / (2 * Math.PI);
  $('#mech-read').innerHTML = `<table><tr><td>Panel angle</td><td><b>${th.toFixed(1)}°</b> → target ${target.toFixed(0)}°</td><td>Encoder count</td><td><b>${Math.round(th / .5)}</b> (0.5° each)</td></tr>
   <tr><td>Wire paid out vs rain position</td><td><b>${d_mm.toFixed(0)} mm</b></td><td>Drum turns</td><td><b>${turns.toFixed(2)}</b> (Ø120 mm drum)</td></tr>
   <tr><td>Gap between panels</td><td><b>${(gap * 1000).toFixed(0)} mm</b> ${th < 6 ? '(sealed: rain flows to the gutter)' : '(open: light and air pass)'}</td><td>Lowest panel edge</td><td><b>${edge.toFixed(2)} m</b></td></tr></table>`;
  const phase = Math.abs(target - th) > .3 ? (target > th ? 'Motor turns the drum one way: the wire slides, every lever arm swings and the panels TILT UP.' : 'Motor turns the drum the other way: the wire slides back and the panels go FLATTER.') : 'Motor stopped: the brake holds the wire and the encoder confirms the angle.';
  $('#mech-phase').textContent = (MECH.auto ? 'Auto demo: ' + MECH.names[MECH.step] + '. ' : '') + phase;
}

function drawClose(cvEl, th, target) {
  if (!cvEl) return; const P = R.P, PW = P.panelW, tr = th * D2R, L = 1.0, Lreal = .44, a = PW / 2, W0 = cvEl.clientWidth || 700, s = Math.min(W0 / 8.0, 105), h0 = Math.round(s * 4.7);
  const { g, w, h } = cv(cvEl, h0), x0 = w * .46, y0 = h * .40, X = x => x0 + x * s, Z = z => y0 - z * s;
  const bg = g.createLinearGradient(0, 0, 0, h); bg.addColorStop(0, '#1b2733'); bg.addColorStop(1, '#2a3947'); g.fillStyle = bg; g.fillRect(0, 0, w, h);
  const T = (t, x, y, col, size, al) => { g.fillStyle = col; g.font = '600 ' + size + 'px system-ui'; g.textAlign = al || 'left'; g.fillText(t, x, y); };
  const Ln = (x1, z1, x2, z2, col, lw, dash) => { g.strokeStyle = col; g.lineWidth = lw; g.setLineDash(dash || []); g.beginPath(); g.moveTo(X(x1), Z(z1)); g.lineTo(X(x2), Z(z2)); g.stroke(); g.setLineDash([]); };
  const tip = [-L * Math.sin(tr), -L * Math.cos(tr)], pit = 2.5;
  [-1, 1].forEach(sg => { const cx = sg * pit; g.globalAlpha = .45; const dx = a * Math.cos(tr), dz = a * Math.sin(tr); Ln(cx - dx, dz, cx + dx, -dz, '#4f6fb8', .12 * s); Ln(cx, 0, cx + tip[0], tip[1], '#f0b030', 3); g.fillStyle = '#ff5a4a'; g.beginPath(); g.arc(X(cx + tip[0]), Z(tip[1]), 6, 0, 7); g.fill(); g.fillStyle = '#c9d0d6'; g.beginPath(); g.arc(X(cx), Z(0), 8, 0, 7); g.fill(); g.globalAlpha = 1; });
  Ln(-4, 1.35, 4, 1.35, '#8f99a3', 2, [2, 5]); T('carrier rope above (carries the weight)', X(-3.9), Z(1.35) - 6, '#98a4ae', 11);
  const wz = tip[1]; Ln(-4, wz, 4, wz, '#ff5a4a', 3.4); const spd = (Math.abs(target - th) > .3 ? Math.sign(-(target - th)) : 0);
  const ph = (MECH.t * 70) % 30; g.fillStyle = '#ffe3dd'; for (let xx = -4 * s; xx < 4 * s; xx += 30) { let px = xx + ph * spd; px = ((px + 4 * s) % (8 * s) + 8 * s) % (8 * s) - 4 * s; g.beginPath(); g.arc(x0 + px, Z(wz), 2.4, 0, 7); g.fill(); }
  Ln(0, 0, 0, -L, 'rgba(255,255,255,.6)', 1.6, [5, 4]); g.strokeStyle = 'rgba(255,255,255,.35)'; g.lineWidth = 1.2; g.setLineDash([2, 4]); g.beginPath(); g.arc(X(0), Z(0), L * s, Math.PI / 2, Math.PI / 2 + Math.PI, false); g.stroke(); g.setLineDash([]);
  g.strokeStyle = 'rgba(255,255,255,.9)'; g.lineWidth = 1.4; g.setLineDash([3, 3]); g.beginPath(); g.arc(X(0), Z(-L), 7, 0, 7); g.stroke(); g.setLineDash([]); T('rest position of the tip (panel flat)', X(0) + 12, Z(-L) + 4, '#cfd8e0', 11);
  const dx = a * Math.cos(tr), dz = a * Math.sin(tr); Ln(-dx, dz, dx, -dz, '#2349a6', .16 * s); Ln(-dx, dz, dx, -dz, '#9fbcf5', 1.2); g.fillStyle = '#05080c'; [-1, 1].forEach(sg => { g.beginPath(); g.arc(X(sg * dx), Z(-sg * dz), 4, 0, 7); g.fill(); });
  Ln(0, 0, tip[0], tip[1], '#f0b030', 6); g.fillStyle = '#c9d0d6'; g.beginPath(); g.arc(X(0), Z(0), 13, 0, 7); g.fill(); g.strokeStyle = '#222'; g.lineWidth = 2; g.stroke(); g.fillStyle = '#ff5a4a'; g.beginPath(); g.arc(X(tip[0]), Z(tip[1]), 9, 0, 7); g.fill(); g.strokeStyle = '#fff'; g.lineWidth = 2; g.stroke();
  g.strokeStyle = '#ffd36a'; g.lineWidth = 2.5; g.beginPath(); g.arc(X(0), Z(0), .55 * s, Math.PI / 2, Math.PI / 2 + tr, false); g.stroke(); T('θ', X(-.42 * Math.sin(tr / 2)) - 4, Z(-.62 * Math.cos(tr / 2)) + 12, '#ffd36a', 16, 'center');
  g.strokeStyle = '#8fb6ff'; g.beginPath(); g.arc(X(0), Z(0), .85 * s, 0, tr, false); g.stroke(); T('θ', X(.98), Z(-.18 * tr) + (tr > .1 ? 18 : -2), '#8fb6ff', 16);
  const dd = Math.abs(tip[0]); if (dd > .03) { const zb = -L - .38; Ln(0, -L - .12, 0, zb - .1, '#7CFFB2', 1.3); Ln(tip[0], wz - .12, tip[0], zb - .1, '#7CFFB2', 1.3); Ln(0, zb, tip[0], zb, '#7CFFB2', 3); g.fillStyle = '#7CFFB2'; g.beginPath(); g.moveTo(X(tip[0]), Z(zb)); g.lineTo(X(tip[0]) + 9, Z(zb) - 5); g.lineTo(X(tip[0]) + 9, Z(zb) + 5); g.fill(); T('wire slid d = ' + (Lreal * Math.sin(tr) * 1000).toFixed(0) + ' mm   (d = arm x sin θ, real arm 0.44 m)', X(tip[0] / 2) - 20, Z(zb) + 22, '#7CFFB2', 13, 'left'); }
  T('PIVOT TUBE (panel turns about this point)', X(0) + 18, Z(0) - 20, '#e6edf3', 13); Ln(0, 0, .45, .22, 'rgba(255,255,255,.6)', 1);
  T('LEVER ARM (rigid with the tube, drawn 2.3x real)', 8, Z(-.35) - 6, '#ffd36a', 13); Ln(-1.2, -.35, tip[0] / 2, tip[1] / 2, 'rgba(255,211,106,.7)', 1);
  T('DRIVE WIRE clamped to the arm tip', 8, Z(wz) + 24, '#ff9a8c', 13);
  T('PANEL', X(a * Math.cos(tr)) + 6, Z(-a * Math.sin(tr)) - 8, '#9fbcf5', 13);
  const mx = w - 64, my = 74; g.fillStyle = '#252a30'; g.fillRect(mx - 52, my - 50, 104, 100); g.fillStyle = '#c9d0d6'; g.beginPath(); g.arc(mx, my, 34, 0, 7); g.fill(); const ang = -Math.sin(tr) * 3.1;
  for (let q = 0; q < 6; q++) { const aa = ang + q * Math.PI / 3; g.strokeStyle = q === 0 ? '#b02020' : '#555'; g.lineWidth = q === 0 ? 3 : 1.5; g.beginPath(); g.moveTo(mx, my); g.lineTo(mx + 31 * Math.cos(aa), my + 31 * Math.sin(aa)); g.stroke(); }
  T('MOTOR DRUM', mx, my + 66, '#8ff0b0', 12, 'center'); const mv = Math.abs(target - th) > .3 ? (target > th ? 'pays wire out' : 'winds wire in') : 'stopped, brake on'; T(mv, mx, my - 58, '#8ff0b0', 12, 'center');
  const txt = th < 6 ? 'RAIN MODE: the arm hangs straight down, the panels are flat and sealed.' : 'The wire has slid sideways by d. Every arm tip is clamped to it, so every arm swings by the same angle θ and every panel tilts by θ.';
  const cut = txt.length > 64 ? txt.lastIndexOf(' ', 64) : -1; if (cut > 0) { T(txt.slice(0, cut), 12, h - 30, '#ffffff', 13); T(txt.slice(cut + 1), 12, h - 12, '#ffffff', 13); } else T(txt, 12, h - 12, '#ffffff', 13);
}

function drawPulley(cvEl) {
  if (!cvEl) return; const W0 = cvEl.clientWidth || 700, stack = W0 < 820, PH = 300, h0 = stack ? PH * 2 : PH + 10, { g, w, h } = cv(cvEl, h0), t = MECH.t;
  const bg = g.createLinearGradient(0, 0, 0, h); bg.addColorStop(0, '#1b2733'); bg.addColorStop(1, '#27384a'); g.fillStyle = bg; g.fillRect(0, 0, w, h);
  const T = (s, x, y, col, size, al) => { g.fillStyle = col; g.font = '600 ' + size + 'px system-ui'; g.textAlign = al || 'left'; g.fillText(s, x, y); };
  const u = 70 * Math.sin(t * 0.9), dirText = Math.cos(t * 0.9) > 0 ? 'wire sliding this way' : 'wire sliding the other way', pw = stack ? w : w / 2, R = 40, Lx = Math.min(150, pw * .34);
  const mu = 0.3, fr = Math.exp(mu * Math.PI);
  const side = (ox, oy, withPulley) => {
    const cx = ox + pw * .42, cy = oy + 118, yT = cy - R, yB = cy + R, plen = Lx + Math.PI * R + Lx, spacing = 24;
    g.fillStyle = withPulley ? '#33525f' : '#4b3a3a'; g.fillRect(cx - R - 34, cy - 30, 14, 100); g.fillStyle = '#8d969e'; g.fillRect(cx - 7, cy + R + 2, 14, 46);
    const pos = s => { if (s < Lx) return [cx + Lx - s, yT]; s -= Lx; if (s < Math.PI * R) { const a = -Math.PI / 2 - s / R; return [cx + R * Math.cos(a), cy + R * Math.sin(a)]; } s -= Math.PI * R; return [cx + s, yB]; };
    g.strokeStyle = '#ff5a4a'; g.lineWidth = 3.4; g.beginPath(); g.moveTo(cx + Lx, yT); g.lineTo(cx, yT); g.arc(cx, cy, R, -Math.PI / 2, Math.PI / 2, true); g.lineTo(cx + Lx, yB); g.stroke();
    g.fillStyle = '#ffe3dd'; for (let k = 0; k < plen / spacing + 2; k++) { const s = ((k * spacing + u) % plen + plen) % plen, p = pos(s); g.beginPath(); g.arc(p[0], p[1], 2.4, 0, 7); g.fill(); }
    if (withPulley) {
      g.fillStyle = '#c9d0d6'; g.beginPath(); g.arc(cx, cy, R - 4, 0, 7); g.fill(); g.strokeStyle = '#6a737c'; g.lineWidth = 3; g.beginPath(); g.arc(cx, cy, R - 4, 0, 7); g.stroke();
      g.strokeStyle = '#8a939c'; g.lineWidth = 1.2; g.beginPath(); g.arc(cx, cy, R - 12, 0, 7); g.stroke(); const ang = u / R; for (let q = 0; q < 6; q++) { const a = ang + q * Math.PI / 3; g.strokeStyle = q === 0 ? '#b02020' : '#59636c'; g.lineWidth = q === 0 ? 3 : 1.6; g.beginPath(); g.moveTo(cx, cy); g.lineTo(cx + (R - 6) * Math.cos(a), cy + (R - 6) * Math.sin(a)); g.stroke(); }
      g.fillStyle = '#2f3a44'; g.beginPath(); g.arc(cx, cy, 7, 0, 7); g.fill(); T('bearing + axle', cx + R + 8, cy + R + 22, '#9fb0bf', 12);
      T('WITH a GUIDE PULLEY (grooved wheel that turns with the wire)', ox + 12, oy + 24, '#8ff0b0', 14);
      T('T', cx + Lx * .5, yT - 8, '#ffd36a', 15); T('T', cx + Lx * .5, yB + 20, '#ffd36a', 15);
      T('about the same pull T on both strands: only ~2 % friction loss', ox + 12, oy + PH - 40, '#8ff0b0', 14); T('gentle bend, long wire life; the bracket takes the turning force', ox + 12, oy + PH - 18, '#cfe6d6', 12);
    } else {
      g.fillStyle = '#6b6f73'; g.beginPath(); g.arc(cx, cy, R - 4, 0, 7); g.fill(); g.strokeStyle = '#46494c'; g.lineWidth = 3; g.beginPath(); g.arc(cx, cy, R - 4, 0, 7); g.stroke();
      for (let k = 0; k < 7; k++) { const a = Math.PI / 2 + (k + 1) / 8 * Math.PI; if (Math.sin(t * 17 + k * 2.1) > .2) { g.strokeStyle = '#ffb347'; g.lineWidth = 1.6; g.beginPath(); g.moveTo(cx + R * Math.cos(a), cy + R * Math.sin(a)); g.lineTo(cx + (R + 9) * Math.cos(a), cy + (R + 9) * Math.sin(a)); g.stroke(); } }
      T('WITHOUT: a fixed post (the wire drags around it)', ox + 12, oy + 24, '#ff9a8c', 14); T('rubbing, wear, heat', cx - R - 8, cy + 4, '#ffb347', 12, 'right');
      T('T', cx + Lx * .5, yT - 8, '#ffd36a', 15); T(fr.toFixed(1) + ' T', cx + Lx * .5, yB + 20, '#ff9a8c', 15);
      T('friction multiplies the pull: e^(0.3 x 3.14) = ' + fr.toFixed(1) + ' times', ox + 12, oy + PH - 40, '#ff9a8c', 14); T('motor pulls ' + fr.toFixed(1) + ' x harder; wire frays; the angle drifts', ox + 12, oy + PH - 18, '#e8c0b8', 12);
    }
    T(dirText, ox + 12, oy + 48, '#cfd8e0', 12);
  };
  side(0, 0, false); side(stack ? 0 : pw, stack ? PH : 0, true); g.strokeStyle = 'rgba(255,255,255,.2)'; g.lineWidth = 1; g.beginPath(); if (stack) { g.moveTo(8, PH); g.lineTo(w - 8, PH); } else { g.moveTo(pw, 8); g.lineTo(pw, h - 8); } g.stroke();
}

function dz0(PW, tr) { return PW / 2 * Math.sin(tr) + .2; }

/* ---------------- 3D scene ---------------- */
const scene3d = (function () {
  const LZ = 25, COLH = 0.22;
  let scene, cam, ren, ctl, sky, sunL, hemi, rainPts, ready = false, lastTilt = 0, curTilt = 0, fly = null;
  const field = new THREE.Group(), ctx = new THREE.Group(), overlay = new THREE.Group(), labelGrp = new THREE.Group(), env = new THREE.Group();
  let motorLed = null, gutterWater = null, flowPath = [], flowDots = [], gridObjs = [], pvFrac = 0, lastTarget = 0, panels = [], levers = [], driveSegs = [], driveEnds = null, cistW = null, harvester = null, site = null, fieldMeta = {};
  const V = (x, y, z) => new THREE.Vector3(x, y, z);
  const mats = {};
  const M = (key, make) => mats[key] || (mats[key] = make());
  const std = (color, o) => new THREE.MeshStandardMaterial(Object.assign({ color, roughness: .85, metalness: 0 }, o || {}));
  const steel = () => M('steel', () => std(0xc9d0d6, { metalness: .85, roughness: .28 }));
  const galv = () => M('galv', () => std(0x8d969e, { metalness: .7, roughness: .45 }));
  function box(x0, x1, y0, y1, z0, z1, mat, shadow) {
    const m = new THREE.Mesh(new THREE.BoxGeometry(x1 - x0, y1 - y0, z1 - z0), mat);
    m.position.set((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2); m.castShadow = shadow !== false; m.receiveShadow = true; return m;
  }
  const UP = V(0, 1, 0), _d = V(0, 0, 0);
  function placeSeg(m, a, b) {
    _d.subVectors(b, a); const len = _d.length() || 1e-6;
    m.position.addVectors(a, b).multiplyScalar(.5); m.scale.set(1, len, 1); m.quaternion.setFromUnitVectors(UP, _d.normalize());
  }
  function seg(a, b, r, mat) { const m = new THREE.Mesh(new THREE.CylinderGeometry(r, r, 1, 8), mat); m.castShadow = true; placeSeg(m, a, b); return m; }
  function catenary(a, b, sag, r, mat) {                   // cable with parabolic sag between two points
    const pts = [];
    for (let i = 0; i <= 20; i++) { const u = i / 20; pts.push(V(a.x + (b.x - a.x) * u, a.y + (b.y - a.y) * u - 4 * sag * u * (1 - u), a.z + (b.z - a.z) * u)); }
    const m = new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts), 24, r, 6, false), mat); m.castShadow = true; return m;
  }
  function panelTexture() {
    const c = document.createElement('canvas'); c.width = 256; c.height = 512; const g = c.getContext('2d');
    g.fillStyle = '#aab3bd'; g.fillRect(0, 0, 256, 512); g.fillStyle = '#0d1b3d'; g.fillRect(8, 8, 240, 496);
    const cw = 240 / 6, ch = 496 / 12;
    for (let i = 0; i < 6; i++) for (let j = 0; j < 12; j++) {
      const gr = g.createLinearGradient(0, 8 + j * ch, 0, 8 + (j + 1) * ch); gr.addColorStop(0, '#1b3a82'); gr.addColorStop(1, '#13296a');
      g.fillStyle = gr; g.fillRect(8 + i * cw + 1.5, 8 + j * ch + 1.5, cw - 3, ch - 3); g.strokeStyle = 'rgba(190,205,235,.55)'; g.lineWidth = 1;
      for (let b = 1; b < 4; b++) { g.beginPath(); g.moveTo(8 + i * cw + b * cw / 4, 8 + j * ch + 2); g.lineTo(8 + i * cw + b * cw / 4, 8 + (j + 1) * ch - 2); g.stroke(); }
    }
    const t = new THREE.CanvasTexture(c); t.wrapS = t.wrapT = THREE.RepeatWrapping; t.anisotropy = 8; return t;
  }

  function noiseTex(gray, amp, rep, size) {          // procedural grain texture (multiplied by the material colour)
    size = size || 256; const c = document.createElement('canvas'); c.width = c.height = size; const g = c.getContext('2d'), img = g.createImageData(size, size);
    for (let i = 0; i < size * size; i++) { const v = Math.max(0, Math.min(255, gray + (Math.random() - .5) * amp)); img.data[i * 4] = img.data[i * 4 + 1] = img.data[i * 4 + 2] = v; img.data[i * 4 + 3] = 255; }
    g.putImageData(img, 0, 0);
    for (let i = 0; i < 260; i++) { g.fillStyle = 'rgba(' + (Math.random() < .5 ? '255,255,255' : '0,0,0') + ',' + (Math.random() * .07).toFixed(3) + ')'; g.beginPath(); g.arc(Math.random() * size, Math.random() * size, 4 + Math.random() * 22, 0, 7); g.fill(); }
    const t = new THREE.CanvasTexture(c); t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(rep, rep); t.anisotropy = 8; t.encoding = THREE.sRGBEncoding; return t;
  }
  function facadeTex() {                                // one storey of a college facade: wall, window with frame and sill
    const c = document.createElement('canvas'); c.width = 256; c.height = 220; const g = c.getContext('2d');
    g.fillStyle = '#e9dfc6'; g.fillRect(0, 0, 256, 220); for (let i = 0; i < 500; i++) { g.fillStyle = 'rgba(0,0,0,' + (Math.random() * .035).toFixed(3) + ')'; g.fillRect(Math.random() * 256, Math.random() * 220, 3, 3); }
    g.fillStyle = '#c9bd9f'; g.fillRect(0, 205, 256, 15); g.fillRect(0, 0, 256, 6);
    [[26, 52], [150, 52]].forEach(([x, y]) => { g.fillStyle = '#7d756a'; g.fillRect(x - 6, y - 6, 92, 112); const gr = g.createLinearGradient(x, y, x + 80, y + 100); gr.addColorStop(0, '#6f93b3'); gr.addColorStop(1, '#2f4a63'); g.fillStyle = gr; g.fillRect(x, y, 80, 100);
      g.strokeStyle = '#d8d2c4'; g.lineWidth = 4; g.strokeRect(x, y, 80, 100); g.beginPath(); g.moveTo(x + 40, y); g.lineTo(x + 40, y + 100); g.moveTo(x, y + 50); g.lineTo(x + 80, y + 50); g.stroke(); g.fillStyle = '#b9b2a2'; g.fillRect(x - 8, y + 102, 96, 8); });
    const t = new THREE.CanvasTexture(c); t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(1 / 8, 1 / 3.4); t.anisotropy = 8; t.encoding = THREE.sRGBEncoding; return t;
  }
  function init() {
    const el = $('#three'); scene = new THREE.Scene();
    ren = new THREE.WebGLRenderer({ antialias: true }); ren.shadowMap.enabled = true; ren.shadowMap.type = THREE.PCFSoftShadowMap;
    ren.toneMapping = THREE.ACESFilmicToneMapping; ren.toneMappingExposure = .4; ren.outputEncoding = THREE.sRGBEncoding; el.appendChild(ren.domElement);
    cam = new THREE.PerspectiveCamera(45, 1, .3, 6000); cam.position.set(-30, 16, 38);
    ctl = new THREE.OrbitControls(cam, ren.domElement); ctl.target.set(0, 2.5, 0); ctl.maxPolarAngle = Math.PI * .497; ctl.maxDistance = 1800; ctl.update();
    sky = new THREE.Sky(); sky.scale.setScalar(5000); scene.add(sky);
    const u = sky.material.uniforms; u.turbidity.value = 5; u.rayleigh.value = 1.6; u.mieCoefficient.value = .004; u.mieDirectionalG.value = .85;
    hemi = new THREE.HemisphereLight(0xbfd8ff, 0x6a7a4a, .4); scene.add(hemi);
    sunL = new THREE.DirectionalLight(0xfff0d8, 2.2); sunL.castShadow = true; sunL.shadow.mapSize.set(4096, 4096);
    const sc = sunL.shadow.camera; sc.left = -34; sc.right = 34; sc.top = 34; sc.bottom = -34; sc.near = 1; sc.far = 260; sunL.shadow.bias = -.0003; sunL.shadow.normalBias = .03;
    scene.add(sunL); scene.add(sunL.target); scene.fog = new THREE.FogExp2(0xcfdceb, .00045);
    scene.add(field); scene.add(ctx); scene.add(overlay); scene.add(labelGrp); scene.add(env);
    const N = 1500, pos = new Float32Array(N * 3);
    for (let i = 0; i < N; i++) { pos[i * 3] = (Math.random() - .5) * 60; pos[i * 3 + 1] = Math.random() * 26; pos[i * 3 + 2] = (Math.random() - .5) * 60; }
    const gg = new THREE.BufferGeometry(); gg.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    rainPts = new THREE.Points(gg, new THREE.PointsMaterial({ color: 0xa9d4ff, size: .09, transparent: true, opacity: .8 })); rainPts.visible = false; rainPts.frustumCulled = false; scene.add(rainPts);
    site = DATA.site; buildCampus(); placeSite(); window.SRMC_SCENE = { scene, cam, ren, ctx, field, sunL, hemi }; ready = true; resize(); animate();
  }

  /* ----- campus context from OpenStreetMap (real TCE building footprints) ----- */
  function buildCampus() {
    while (ctx.children.length) ctx.remove(ctx.children[0]);
    const ground = new THREE.Mesh(new THREE.PlaneGeometry(9000, 9000), std(0x4c6a2c, { roughness: 1, map: noiseTex(150, 70, 900, 256) })); ground.rotation.x = -Math.PI / 2; ground.position.y = -.08; ground.receiveShadow = true; ctx.add(ground);
    const AC = { grass: 0x58783a, recreation_ground: 0x5f8040, pitch: 0x2f7a35, track: 0xb5523b, sports_centre: 0x9aa58a, wood: 0x3e6b2f };
    site.areas.forEach(a => {
      const sh = new THREE.Shape(a.p.map(p => new THREE.Vector2(p[0], p[1]))); const m = new THREE.Mesh(new THREE.ShapeGeometry(sh), std(AC[a.k] || 0x7fa34f, { roughness: 1 }));
      m.rotation.x = -Math.PI / 2; m.position.y = (a.k === 'pitch' || a.k === 'track') ? .03 : -.02; m.receiveShadow = true; ctx.add(m);
    });
    const Pp = [], I = []; let vi = 0;                      // roads: one merged ribbon mesh
    site.roads.forEach(r => {
      const q = r.p, n = q.length; if (n < 2) return; const hw = r.w / 2;
      for (let i = 0; i < n; i++) {
        const a = q[Math.max(0, i - 1)], b = q[Math.min(n - 1, i + 1)]; let dx = b[0] - a[0], dy = b[1] - a[1]; const l = Math.hypot(dx, dy) || 1; dx /= l; dy /= l;
        Pp.push(q[i][0] - dy * hw, .02, -(q[i][1] + dx * hw), q[i][0] + dy * hw, .02, -(q[i][1] - dx * hw));
      }
      for (let i = 0; i < n - 1; i++) { const a = vi + i * 2; I.push(a, a + 1, a + 2, a + 1, a + 3, a + 2); } vi += n * 2;
    });
    const rg = new THREE.BufferGeometry(); rg.setAttribute('position', new THREE.Float32BufferAttribute(Pp, 3)); rg.setIndex(I); rg.computeVertexNormals();
    const rm = new THREE.Mesh(rg, std(0x2d3034, { roughness: .95, side: THREE.DoubleSide })); rm.receiveShadow = true; ctx.add(rm);
    const fac = facadeTex(), wall = std(0xf6ead0, { map: fac, roughness: .9 }), wall2 = std(0xe6e0d4, { map: fac, roughness: .95 }), roof = std(0x7d7a74, { roughness: 1 });
    const tints = [0xf4ead0, 0xf1e0c0, 0xe9eef0, 0xf3d9d0, 0xe8e2c8, 0xdfe7d8], tankMat = std(0x2a2f33, { roughness: .6 }), headMat = std(0xcfc8b8), cacheM = {};
    const wallFor = tint => cacheM[tint] || (cacheM[tint] = std(tint, { map: fac, roughness: .9 }));
    site.buildings.forEach((b, i) => {
      const nm = (b.n || '').toLowerCase(); let tint, h = b.h;
      if (/hostel|guest/.test(nm)) tint = 0xeed9a2; else if (/auditorium|hall/.test(nm)) { tint = 0xe2e2de; h = Math.max(h, 9.5); }
      else if (/temple|jeeva/.test(nm)) tint = 0xe0b070; else if (/canteen/.test(nm)) tint = 0xf0e4c4; else if (b.n) tint = 0xf3ead2; else { tint = tints[i % tints.length]; if (b.a < 120) h = Math.min(h, 3.9); }
      const sh = new THREE.Shape(b.p.map(p => new THREE.Vector2(p[0], p[1]))); const g = new THREE.ExtrudeGeometry(sh, { depth: h, bevelEnabled: false });
      const m = new THREE.Mesh(g, [roof, wallFor(tint)]); m.rotation.x = -Math.PI / 2; m.receiveShadow = true; ctx.add(m);
      if (b.a > 250) {                                  // roof furniture: stair head-room and overhead water tanks
        const cx = b.p.reduce((q, p) => q + p[0], 0) / b.p.length, cy = b.p.reduce((q, p) => q + p[1], 0) / b.p.length;
        const sh1 = new THREE.Mesh(new THREE.BoxGeometry(3.2, 2.6, 3.2), headMat); sh1.position.set(cx, h + 1.3, -cy); ctx.add(sh1);
        const tk = new THREE.Mesh(new THREE.CylinderGeometry(.95, .95, 1.5, 12), tankMat); tk.position.set(cx + 3.4, h + .75, -cy + 1.2); ctx.add(tk);
        if (b.a > 700) { const tk2 = tk.clone(); tk2.position.x += 2.4; ctx.add(tk2); }
      }
    });
    const trees = []; let seed = 7; const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
    const inside = (p, poly) => { let c = false; for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) { if ((poly[i][1] > p[1]) !== (poly[j][1] > p[1]) && p[0] < (poly[j][0] - poly[i][0]) * (p[1] - poly[i][1]) / (poly[j][1] - poly[i][1]) + poly[i][0]) c = !c; } return c; };
    site.areas.filter(a => a.k === 'wood' || a.k === 'grass' || a.k === 'recreation_ground').forEach(a => {
      const xs = a.p.map(p => p[0]), ys = a.p.map(p => p[1]), x0 = Math.min(...xs), x1 = Math.max(...xs), y0 = Math.min(...ys), y1 = Math.max(...ys);
      const want = Math.min(260, Math.round(a.a / (a.k === 'wood' ? 120 : 900))); let tries = 0, got = 0;
      while (got < want && trees.length < 1800 && tries++ < want * 25) { const p = [x0 + rnd() * (x1 - x0), y0 + rnd() * (y1 - y0)]; if (!inside(p, a.p)) continue; trees.push([p[0], p[1], 5 + rnd() * 5]); got++; }
    });
    const tcan = new THREE.InstancedMesh(new THREE.IcosahedronGeometry(1, 1), std(0xffffff, { roughness: 1 }), trees.length), ttr = new THREE.InstancedMesh(new THREE.CylinderGeometry(.18, .26, 1, 6), std(0x5a3d22), trees.length);
    const mm = new THREE.Matrix4(), q = new THREE.Quaternion(), c = new THREE.Color();
    trees.forEach((t, i) => {
      const h = t[2]; mm.compose(V(t[0], h * .62, -t[1]), q, V(h * .38, h * .34, h * .38)); tcan.setMatrixAt(i, mm); c.setHSL(.27 + rnd() * .06, .5, .22 + rnd() * .1); tcan.setColorAt(i, c);
      mm.compose(V(t[0], h * .25, -t[1]), q, V(1, h * .5, 1)); ttr.setMatrixAt(i, mm);
    });
    ctx.add(tcan, ttr);
    while (labelGrp.children.length) labelGrp.remove(labelGrp.children[0]);
    site.buildings.filter(b => b.n && b.a > 180).forEach(b => {
      const cx = b.p.reduce((a, p) => a + p[0], 0) / b.p.length, cy = b.p.reduce((a, p) => a + p[1], 0) / b.p.length;
      const cv2 = document.createElement('canvas'); cv2.width = 512; cv2.height = 96; const g = cv2.getContext('2d'); g.font = '600 38px system-ui';
      const txt = b.n.replace('Department of ', 'Dept. of '), w = Math.min(500, g.measureText(txt).width + 30);
      g.fillStyle = 'rgba(10,16,10,.72)'; g.fillRect((512 - w) / 2, 14, w, 64); g.fillStyle = '#fff'; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText(txt, 256, 47);
      const sp = new THREE.Sprite(new THREE.SpriteMaterial({ map: new THREE.CanvasTexture(cv2), transparent: true, depthWrite: false, fog: false }));
      sp.scale.set(40, 7.5, 1); sp.userData = { x: cx, y: cy, h: b.h }; labelGrp.add(sp);
    });
  }

  /* ----- landscape for each climate preset (representative, not a surveyed site; TCE uses the real campus) ----- */
  const hash = (x, y) => { const q = Math.sin(x * 127.1 + y * 311.7) * 43758.5453; return q - Math.floor(q); };
  const vnoise = (x, y) => { const xi = Math.floor(x), yi = Math.floor(y), xf = x - xi, yf = y - yi, u = xf * xf * (3 - 2 * xf), v = yf * yf * (3 - 2 * yf);
    return hash(xi, yi) * (1 - u) * (1 - v) + hash(xi + 1, yi) * u * (1 - v) + hash(xi, yi + 1) * (1 - u) * v + hash(xi + 1, yi + 1) * u * v; };
  const fbm = (x, y) => { let a = .5, f = 1, t = 0; for (let i = 0; i < 5; i++) { t += a * vnoise(x * f, y * f); f *= 2; a *= .5; } return t; };
  const smooth = (a, b, x) => { const t = Math.max(0, Math.min(1, (x - a) / (b - a))); return t * t * (3 - 2 * t); };
  const ENVS = {
    coastal_chennai: { name: 'Coastal plain with sea (Chennai-type)', c: [0xcdbb8c, 0xb4c47c], amp: 5, f: .002, flat: 200, sea: 430, trees: [['palm', 240, 60, 700], ['round', 70, 60, 500]], huts: 16, turb: 6, fog: .0005, fogc: 0xd6e4ef },
    hill_ooty: { name: 'Hill-station terraces (Nilgiris-type)', c: [0x4c8a34, 0x2f5e26, 0x857d6b], amp: 300, f: .0011, flat: 150, terr: 1, trees: [['cone', 520, 80, 1400]], turb: 3, fog: .0011, fogc: 0xc9d6df },
    humid_kerala: { name: 'Humid tropical coconut country (Kerala-type)', c: [0x2f7d2a, 0x44913a], amp: 60, f: .0015, flat: 220, trees: [['palm', 520, 50, 900]], fields: [[0x78b84e, 14, 1], [0x4f9a3a, 8, 0]], turb: 9, fog: .0009, fogc: 0xcfe0d8 },
    arid_rajasthan: { name: 'Arid desert dunes (Rajasthan-type)', c: [0xdcb673, 0xc99c56], amp: 16, f: .0035, flat: 120, dunes: 1, trees: [['umbrella', 55, 90, 900]], turb: 13, fog: .0006, fogc: 0xe9d9b4 },
    plains_punjab: { name: 'Northern plains, wheat country (Punjab-type)', c: [0x93a757, 0xa9ab55], amp: 0, f: .001, flat: 3000, trees: [['poplar', 240, 70, 900], ['round', 60, 70, 700]], fields: [[0xcdb84e, 24, 0], [0x7fae3e, 16, 0]], sheds: 9, turb: 5, fog: .0006, fogc: 0xdbe6ee },
    deccan_vidarbha: { name: 'Deccan plateau, black cotton soil (Vidarbha-type)', c: [0x55412f, 0x65503b], amp: 70, f: .0009, flat: 260, trees: [['round', 70, 70, 800], ['umbrella', 55, 70, 800]], fields: [[0xe9e4d6, 18, 0], [0x8a7b4a, 10, 0]], turb: 6, fog: .0007, fogc: 0xd9dfe4 }
  };
  let envCfg = { turb: 5, fog: .00045, fogc: 0xcfdceb, name: 'TCE campus (OpenStreetMap)' }, envId = null;
  function stripeTex(col, water) {
    const c = document.createElement('canvas'); c.width = 128; c.height = 128; const g = c.getContext('2d'), base = new THREE.Color(col);
    g.fillStyle = '#' + base.getHexString(); g.fillRect(0, 0, 128, 128);
    for (let i = 0; i < 16; i++) { g.fillStyle = 'rgba(0,0,0,' + (water ? .05 : (i % 2 ? .1 : .0)) + ')'; g.fillRect(0, i * 8, 128, 4); }
    if (water) { g.fillStyle = 'rgba(120,170,210,.35)'; g.fillRect(0, 0, 128, 128); }
    const t = new THREE.CanvasTexture(c); t.wrapS = t.wrapT = THREE.RepeatWrapping; t.encoding = THREE.sRGBEncoding; return t;
  }
  function treeSet(kind, pts) {
    const mm = new THREE.Matrix4(), q = new THREE.Quaternion(), col = new THREE.Color(), n = pts.length; if (!n) return;
    const specs = {
      palm: { tg: new THREE.CylinderGeometry(.18, .3, 1, 6), cg: new THREE.SphereGeometry(1, 8, 6), tc: 0x7a6544, cc: [.27, .55, .26], cs: [3.4, .7, 3.4], th: [9, 14], cy: 1.02 },
      round: { tg: new THREE.CylinderGeometry(.2, .3, 1, 6), cg: new THREE.IcosahedronGeometry(1, 1), tc: 0x5a3d22, cc: [.28, .5, .24], cs: [.4, .36, .4], th: [5, 10], cy: .72, rel: 1 },
      cone: { tg: new THREE.CylinderGeometry(.2, .35, 1, 6), cg: new THREE.ConeGeometry(1, 2, 8), tc: 0x5a3d22, cc: [.33, .5, .18], cs: [.22, .5, .22], th: [10, 18], cy: .8, rel: 1 },
      poplar: { tg: new THREE.CylinderGeometry(.15, .25, 1, 6), cg: new THREE.SphereGeometry(1, 8, 6), tc: 0x6a5a40, cc: [.25, .45, .3], cs: [.12, .5, .12], th: [14, 20], cy: .6, rel: 1 },
      umbrella: { tg: new THREE.CylinderGeometry(.15, .25, 1, 6), cg: new THREE.SphereGeometry(1, 8, 6), tc: 0x6b5438, cc: [.2, .35, .3], cs: [.9, .22, .9], th: [4.5, 8], cy: .8, rel: 0 }
    }[kind];
    const T = new THREE.InstancedMesh(specs.tg, std(specs.tc, { roughness: 1 }), n), C = new THREE.InstancedMesh(specs.cg, std(0xffffff, { roughness: 1 }), n);
    pts.forEach((p, i) => {
      const h = specs.th[0] + hash(p[0], p[1]) * (specs.th[1] - specs.th[0]);
      mm.compose(V(p[0], p[2] + h * .5, p[1]), q, V(1, h, 1)); T.setMatrixAt(i, mm);
      const sc = kind === 'palm' ? V(specs.cs[0], specs.cs[1], specs.cs[2]) : specs.rel ? V(h * specs.cs[0], h * specs.cs[1], h * specs.cs[2]) : V(h * specs.cs[0] * 1.6, h * specs.cs[1] * 1.6, h * specs.cs[2] * 1.6);
      mm.compose(V(p[0], p[2] + h * (kind === 'palm' ? 1.02 : specs.cy), p[1]), q, sc); C.setMatrixAt(i, mm);
      col.setHSL(specs.cc[0] + (hash(p[1], p[0]) - .5) * .05, specs.cc[1], specs.cc[2] + (hash(p[0] + 3, p[1]) - .5) * .1); C.setColorAt(i, col);
    });
    C.castShadow = false; T.castShadow = false; env.add(T, C);
  }
  function setEnv(id) {
    envId = id; while (env.children.length) { const c = env.children.pop(); c.traverse(o => { if (o.geometry) o.geometry.dispose(); }); }
    const E = ENVS[id], isTce = !E; ctx.visible = isTce; labelGrp.visible = isTce && st.labels;
    if (isTce) { envCfg = { turb: 5, fog: .00045, fogc: 0xcfdceb, name: 'TCE campus (real OpenStreetMap footprints)' }; return; }
    envCfg = { turb: E.turb, fog: E.fog, fogc: E.fogc, name: E.name };
    const SZ = 4000, SEG = 170, geo = new THREE.PlaneGeometry(SZ, SZ, SEG, SEG); geo.rotateX(-Math.PI / 2);
    const pos = geo.attributes.position, cols = new Float32Array(pos.count * 3), c0 = new THREE.Color(E.c[0]), c1 = new THREE.Color(E.c[1]), c2 = new THREE.Color(E.c[2] || E.c[1]), tmp = new THREE.Color();
    const hAt = (x, z) => {
      const rr = Math.hypot(x, z); let h = 0;
      if (E.amp) h = E.amp * Math.pow(fbm(x * E.f, z * E.f), 2.2) * 1.9 * smooth(E.flat, E.flat + 420, rr);
      if (E.dunes) h += 7 * Math.sin((x * .6 + z * .3) * .02 + fbm(x * .004, z * .004) * 6) * smooth(E.flat, E.flat + 160, rr) + 4 * fbm(x * .01, z * .01) * smooth(E.flat, E.flat + 160, rr);
      if (E.sea) h -= smooth(E.sea - 70, E.sea + 90, x) * 7;
      return h - .1;
    };
    for (let i = 0; i < pos.count; i++) {
      const x = pos.getX(i), z = pos.getZ(i), h = hAt(x, z); pos.setY(i, h); const n = fbm(x * .01, z * .01);
      tmp.copy(c0).lerp(c1, n);
      if (E.terr) { const band = Math.floor(h / 7) % 2 ? .86 : 1; tmp.multiplyScalar(band); if (h > E.amp * .55) tmp.lerp(c2, smooth(E.amp * .55, E.amp * .95, h)); }
      else if (E.amp && h > E.amp * .5) tmp.lerp(c2, .5);
      if (E.sea && x > E.sea - 120) tmp.lerp(new THREE.Color(0xe3d5a8), smooth(E.sea - 120, E.sea - 40, x));
      cols[i * 3] = tmp.r; cols[i * 3 + 1] = tmp.g; cols[i * 3 + 2] = tmp.b;
    }
    geo.setAttribute('color', new THREE.BufferAttribute(cols, 3)); geo.computeVertexNormals();
    const terrain = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 1, map: noiseTex(150, 60, 700, 256) })); terrain.receiveShadow = true; env.add(terrain);
    if (E.sea) { const sea = new THREE.Mesh(new THREE.PlaneGeometry(SZ, SZ), new THREE.MeshStandardMaterial({ color: 0x2d86b0, roughness: .15, metalness: .3, transparent: true, opacity: .92 })); sea.rotation.x = -Math.PI / 2; sea.position.set(E.sea + SZ / 2 - 20, -2.4, 0); env.add(sea); }
    let seed = 91; const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
    (E.fields || []).forEach(([col, nf, water]) => { for (let i = 0; i < nf; i++) {
      const ang = rnd() * 6.283, rad = 60 + rnd() * 420, x = Math.cos(ang) * rad, z = Math.sin(ang) * rad; if (Math.abs(hAt(x, z) + .1) > .5) continue;
      const w = 40 + rnd() * 90, d = 40 + rnd() * 90, tx = stripeTex(col, water); tx.repeat.set(w / 12, d / 12); if (rnd() < .5) tx.rotation = Math.PI / 2;
      const m = new THREE.Mesh(new THREE.PlaneGeometry(w, d), new THREE.MeshStandardMaterial({ map: tx, roughness: .9 })); m.rotation.x = -Math.PI / 2; m.position.set(x, -.04, z); m.receiveShadow = true; env.add(m); } });
    const huts = (E.huts || 0) + (E.sheds || 0); for (let i = 0; i < huts; i++) {
      const ang = rnd() * 6.283, rad = 70 + rnd() * 380, x = Math.cos(ang) * rad, z = Math.sin(ang) * rad; if (E.sea && x > E.sea - 150) continue;
      const w = 5 + rnd() * 8, d = 5 + rnd() * 6, h = 3 + rnd() * 2, hut = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), std([0xf2efe6, 0xe8d6b0, 0xb9d3dc, 0xe7c0a8][i % 4]));
      hut.position.set(x, h / 2 - .1, z); hut.rotation.y = rnd() * 3; env.add(hut);
      const roofm = new THREE.Mesh(new THREE.BoxGeometry(w + .4, .3, d + .4), std(E.sheds ? 0x8a8f94 : 0xa6532f)); roofm.position.set(x, h - .1, z); roofm.rotation.y = hut.rotation.y; env.add(roofm); }
    E.trees.forEach(([kind, n, r0, r1]) => { const pts = []; let tries = 0;
      while (pts.length < n && tries++ < n * 20) { const ang = rnd() * 6.283, rad = r0 + rnd() * (r1 - r0), x = Math.cos(ang) * rad, z = Math.sin(ang) * rad;
        if (Math.hypot(x, z) < 50 || (E.sea && x > E.sea - 100)) continue; if (fbm(x * .012, z * .012) < (kind === 'palm' || kind === 'cone' ? .38 : .5)) continue; pts.push([x, z, hAt(x, z)]); }
      treeSet(kind, pts); });
  }

  function placeSite() {                                    // put the selected canopy site at the scene origin
    const s = site.sites.find(x => x.id === st.siteId) || site.sites[0]; st.siteId = s.id; fieldMeta.site = s;
    ctx.position.set(-s.c[0], 0, s.c[1]); labelGrp.position.copy(ctx.position);
    labelGrp.children.forEach(sp => sp.position.set(sp.userData.x, sp.userData.h + 9, -sp.userData.y)); labelGrp.visible = st.labels;
  }

  /* ----- the canopy: columns, wire-rope carriers, wire-driven panels, crops, cistern ----- */
  function clearGroup(g) { while (g.children.length) { const c = g.children.pop(); c.traverse(o => { if (o.geometry) o.geometry.dispose(); }); } }
  function build() {
    clearGroup(field); clearGroup(overlay); panels = []; levers = []; driveSegs = [];
    const P = R.P, H = P.height, N = Math.max(2, Math.round(25 / P.pitch)), W = N * P.pitch, half = W / 2, gap = P.pitch / 4, bay = P.bayLen;
    const colX = []; for (let x = -half; x <= half + 1e-6; x += bay) colX.push(+x.toFixed(3)); const nl = Math.max(2, Math.round(LZ / bay)), colZ = Array.from({ length: nl + 1 }, (_, i) => -LZ / 2 + i * LZ / nl), SAG = P.sagRatio || 0.0256, TUBE_R = (P.tubeD || 60.3) / 2000;
    const sdef = soil.color || '#6b4a2b', soilMat = std(new THREE.Color(sdef), { roughness: 1, map: M('soiltex', () => noiseTex(190, 90, 5, 256)) });
    const cw = 6, cx = half + 4.5, ex = half + 9;           // soil block with side cut-away + cistern pit
    field.add(box(-half, half, -1.8, -.02, -LZ / 2, LZ / 2, soilMat));
    [[-LZ / 2, -cw / 2, half, ex], [cw / 2, LZ / 2, half, ex], [-cw / 2, cw / 2, half, cx - cw / 2], [-cw / 2, cw / 2, cx + cw / 2, ex]].forEach(([z0, z1, x0, x1]) => field.add(box(x0, x1, -3.7, -.02, z0, z1, soilMat)));
    field.add(box(cx - cw / 2, cx + cw / 2, -3.7, -3.4, -cw / 2, cw / 2, std(0x9aa0a6)));
    const wm = new THREE.Mesh(new THREE.BoxGeometry(cw - .1, 1, cw - .1), std(0x2a9dd8, { transparent: true, opacity: .82, roughness: .1 })); wm.userData = { depth: 3.1 }; field.add(wm); cistW = wm; wm.position.set(cx, -3.4, 0);
    field.add(box(cx - cw / 2, cx + cw / 2, -.05, .02, -cw / 2, cw / 2, std(0x4aa3d8, { transparent: true, opacity: .25 }), false));
    const cell = new THREE.Matrix4(), q0 = new THREE.Quaternion(), col = new THREE.Color(); let rs = 11;       // crops: instanced plants per zone strip
    const rnd = () => (rs = (rs * 16807) % 2147483647) / 2147483647, plantG = new THREE.IcosahedronGeometry(.5, 1);
    for (let z = 0; z < 4; z++) {
      const cz = R.wb.zones[z], crop = DATA.crops.find(q => q.id === cz.crop), rows = Math.max(1, Math.round(gap / .7)), sp = crop.h > 1.4 ? .7 : .38, nz = Math.floor((LZ - .6) / sp);
      const im = new THREE.InstancedMesh(plantG, std(0xffffff, { roughness: 1 }), N * rows * nz); let k = 0;
      const base = new THREE.Color(GROUP_COLOR[crop.group] || 0x5a9a3a), hh = crop.h * (.75 + .5 * Math.min(1, cz.yield / Math.max(crop.ym, .1)));
      for (let i = 0; i < N; i++) for (let r = 0; r < rows; r++) for (let j = 0; j < nz; j++) {
        const x = -half + i * P.pitch + z * gap + gap * (r + .5) / rows + (rnd() - .5) * .06, zz = -LZ / 2 + .3 + j * sp + (rnd() - .5) * .08, s = .85 + rnd() * .3;
        cell.compose(V(x, hh * s * .45, zz), q0, V(Math.min(gap / rows * .85, crop.h > 1.4 ? .6 : .45) * s, hh * s, Math.min(sp * .95, .5) * s)); im.setMatrixAt(k, cell);
        col.copy(base).offsetHSL((rnd() - .5) * .03, 0, (rnd() - .5) * .08); im.setColorAt(k, col); k++;
      }
      im.castShadow = true; im.receiveShadow = true; field.add(im);
      for (let i = 0; i < N; i++) overlay.add(box(-half + i * P.pitch + z * gap, -half + i * P.pitch + (z + 1) * gap, -.03, .0, -LZ / 2, LZ / 2, std(new THREE.Color(ZCOL[z]), { transparent: true, opacity: .55 }), false));
    }
    overlay.visible = st.overlay;
    const colMat = galv(), wireMat = steel(), topY = H - .1;     // columns, wire-rope carriers, stays
    colX.forEach(x => colZ.forEach(z => {
      field.add(box(x - COLH / 2, x + COLH / 2, -.4, H + .75, z - COLH / 2, z + COLH / 2, colMat));
      field.add(box(x - .45, x + .45, -.5, -.2, z - .45, z + .45, std(0x9b9b96))); field.add(box(x - .18, x + .18, H + .75, H + .8, z - .18, z + .18, colMat));
    }));
    colZ.forEach(z => { for (let i = 0; i < colX.length - 1; i++) field.add(catenary(V(colX[i], topY, z), V(colX[i + 1], topY, z), SAG * (colX[i + 1] - colX[i]), .022, wireMat)); });
    colX.forEach(x => { for (let j = 0; j < colZ.length - 1; j++) field.add(catenary(V(x, H + .7, colZ[j]), V(x, H + .7, colZ[j + 1]), SAG * (colZ[j + 1] - colZ[j]), .02, wireMat)); });
    [-1, 1].forEach(sx => colZ.forEach(z => { const a = V(sx * half, H + .7, z), b = V(sx * (half + 6.5), -.35, z); field.add(seg(a, b, .016, wireMat)); field.add(box(b.x - .5, b.x + .5, -.45, -.1, b.z - .4, b.z + .4, std(0x9b9b96))); }));
    [-1, 1].forEach(sz => colX.forEach(x => { field.add(seg(V(x, H + .7, sz * LZ / 2), V(x, -.35, sz * (LZ / 2 + 6.5)), .016, wireMat)); }));
    const base = std(0x1a2a52, { roughness: .4, metalness: .5 }), frame = std(0xaab3bd, { metalness: .6, roughness: .4 }), epdm = std(0x0a0a0a, { roughness: .9 }), ptex = M('ptex', panelTexture);
    for (let k = 0; k < N; k++) {                           // individual pivot tube + panel + EPDM seals + lever arm
      const xc = -half + k * P.pitch + P.pitch / 2, g = new THREE.Group(), tex = ptex.clone(); tex.needsUpdate = true; tex.repeat.set(P.panelW / 1.1, LZ / 2.3);
      const pmat = new THREE.MeshStandardMaterial({ map: tex, roughness: .22, metalness: .35 });
      const body = new THREE.Mesh(new THREE.BoxGeometry(P.panelW, .05, LZ), [base, base, pmat, base, base, base]); body.position.y = .09; body.castShadow = true; body.receiveShadow = true; g.add(body);
      const tube = new THREE.Mesh(new THREE.CylinderGeometry(TUBE_R, TUBE_R, LZ, 12), galv()); tube.rotation.x = Math.PI / 2; tube.castShadow = true; g.add(tube);
      [-1, 1].forEach(s => {
        g.add(box(s * P.panelW / 2 - .02, s * P.panelW / 2 + .02, .06, .14, -LZ / 2, LZ / 2, frame));
        const se = new THREE.Mesh(new THREE.CylinderGeometry(.016, .016, LZ, 6), epdm); se.rotation.x = Math.PI / 2; se.position.set(s * (P.panelW / 2 + .012), .1, 0); g.add(se);
      });
      g.add(box(-.025, .025, -.46, 0, LZ / 2 - .55, LZ / 2 - .5, steel())); levers.push(V(0, -.44, LZ / 2 - .525));
      g.position.set(xc, H, 0); field.add(g); panels.push(g);
      colZ.forEach(z => { const u = (((xc + half) % bay) / bay), y = topY - 4 * (SAG * bay) * u * (1 - u); field.add(seg(V(xc, y, z), V(xc, H - .05, z), .012, wireMat)); });
    }
    const zW = LZ / 2 - .525;                               // drive wire: motor winch (east) -> lever-arm tips -> tensioner anchor (west)
    field.add(box(half + .45, half + 1.2, H - .2, H + .4, zW - .25, zW + .25, std(0x252a30, { metalness: .5 })));
    const drum = new THREE.Mesh(new THREE.CylinderGeometry(.14, .14, .3, 16), steel()); drum.rotation.x = Math.PI / 2; drum.position.set(half + .3, H - .05, zW); field.add(drum);
    const led = new THREE.Mesh(new THREE.SphereGeometry(.05, 8, 8), new THREE.MeshBasicMaterial({ color: 0x35e07a })); led.position.set(half + .85, H + .25, zW + .26); field.add(led); motorLed = led;
    // rain gutter along the low (east) edge of the sloped canopy, with end-cap and downpipe
    const gm = std(0x7a838c, { metalness: .6, roughness: .4 }); field.add(box(half - .02, half + .4, H - .5, H - .46, -LZ / 2, 10.8, gm)); field.add(box(half + .38, half + .4, H - .5, H - .2, -LZ / 2, 10.8, gm)); field.add(box(half - .02, half, H - .5, H - .22, -LZ / 2, 10.8, gm));
    field.add(box(half - .02, half + .4, H - .5, H - .2, -LZ / 2, -LZ / 2 + .02, gm)); field.add(box(half - .02, half + .4, H - .5, H - .2, 10.78, 10.8, gm));
    const gw = new THREE.Mesh(new THREE.BoxGeometry(.34, .06, 10.8 + LZ / 2), std(0x2a9dd8, { transparent: true, opacity: 0, roughness: .1 })); gw.position.set(half + .2, H - .44, (-LZ / 2 + 10.8) / 2); gutterWater = gw; field.add(gw);
    // drip irrigation: pump, header and one lateral per crop strip, fed from the cistern
    const blue = std(0x2b7fd4, { roughness: .5 }); field.add(box(cx - .5, cx + .5, -.05, 1.0, -cw / 2 - 1.8, -cw / 2 - .8, std(0x2f6fa8, { metalness: .3 })));
    field.add(seg(V(cx, -.5, -cw / 2 + .3), V(cx, .45, -cw / 2 - .8), .06, blue)); field.add(seg(V(cx, .12, -cw / 2 - 1.3), V(cx, .12, -LZ / 2 - .6), .05, blue)); field.add(seg(V(cx, .12, -LZ / 2 - .6), V(-half, .12, -LZ / 2 - .6), .05, blue));
    for (let i = 0; i < N; i++) for (let z = 0; z < 4; z++) { const lx = -half + i * P.pitch + z * gap + gap / 2; field.add(seg(V(lx, .09, -LZ / 2 - .6), V(lx, .07, -LZ / 2 + .1), .014, blue)); field.add(seg(V(lx, .07, -LZ / 2 + .1), V(lx, .07, LZ / 2 - .2), .012, blue)); }
    // electrical: DC cabling -> inverter + transformer -> overhead line -> nearby industry (energy buyer)
    const inv = new THREE.Group(); const ix = -half - 4.2, iz = 9; inv.add(box(ix - .6, ix + .6, 0, 1.8, iz - .4, iz + .4, std(0xe9ecef, { metalness: .3 })), box(ix + 1.2, ix + 2.8, 0, 2.0, iz - .8, iz + .8, std(0x3a4a57, { metalness: .4 })));
    for (let k = 0; k < 6; k++) inv.add(box(ix + 2.8, ix + 3.05, .2 + k * .3, .4 + k * .3, iz - .7, iz + .7, std(0x2a3640))); field.add(inv);
    field.add(seg(V(-half, H - .4, LZ / 2), V(-half, .15, LZ / 2), .03, std(0xc0392b))); field.add(seg(V(-half, .12, LZ / 2), V(ix, .12, iz), .03, std(0xc0392b)));
    const ind = V(-30, 0, 170), poles = []; const p0 = V(ix + 3.2, 0, iz), nPoles = 6; for (let k = 0; k <= nPoles; k++) { const u = k / nPoles; poles.push(V(p0.x + (ind.x - p0.x) * u, 0, p0.z + (ind.z - p0.z) * u)); }
    const lineMat = std(0x222222, { metalness: .5 }), poleObjs = []; poles.forEach(p => { const a1 = seg(V(p.x, 0, p.z), V(p.x, 9.5, p.z), .14, std(0x8a8f94)), a2 = box(p.x - 1.2, p.x + 1.2, 9.3, 9.45, p.z - .08, p.z + .08, std(0x6a6f74)); field.add(a1, a2); poleObjs.push(a1, a2); });
    for (let k = 0; k < poles.length - 1; k++) [-1, 0, 1].forEach(o => { const w = catenary(V(poles[k].x + o * 1, 9.4, poles[k].z), V(poles[k + 1].x + o * 1, 9.4, poles[k + 1].z), 1.0, .025, lineMat); field.add(w); poleObjs.push(w); });
    flowPath = [V(ix + 3.2, 1.0, iz)].concat(poles.map(p => V(p.x, 9.4, p.z))); flowPath.push(V(ind.x, 6, ind.z));
    const fac = new THREE.Group(); [[0, 0, 40, 9, 22], [46, 0, 26, 11, 22], [-3, 30, 36, 8, 16]].forEach(([dx, dz, w, h, d], i) => { fac.add(box(dx - w / 2, dx + w / 2, 0, h, dz - d / 2, dz + d / 2, std([0xc9ced2, 0xb7c0c7, 0xd3d0c8][i], { roughness: .8 })));
      fac.add(box(dx - w / 2 - .3, dx + w / 2 + .3, h, h + .5, dz - d / 2 - .3, dz + d / 2 + .3, std(0x59616a))); for (let k = 0; k < 5; k++) fac.add(box(dx - w / 2 + 3 + k * (w - 6) / 4, dx - w / 2 + 3 + k * (w - 6) / 4 + 1.2, h, h + 1.6, dz - d / 2, dz + d / 2, std(0x8a949c))); });
    const ch = new THREE.Mesh(new THREE.CylinderGeometry(.9, 1.4, 26, 14), std(0x9b6a55)); ch.position.set(60, 13, 12); fac.add(ch); const tkk = new THREE.Mesh(new THREE.CylinderGeometry(3.5, 3.5, 9, 18), std(0xdfe3e6, { metalness: .4 })); tkk.position.set(-26, 4.5, 6); fac.add(tkk);
    fac.add(box(-14, -9, 0, 4, -12, -5, std(0x3a4a57))); fac.position.copy(ind); field.add(fac);
    const lbl = document.createElement('canvas'); lbl.width = 512; lbl.height = 96; const lg = lbl.getContext('2d'); lg.fillStyle = 'rgba(10,16,10,.8)'; lg.fillRect(20, 14, 472, 64); lg.fillStyle = '#ffd36a'; lg.font = '600 34px system-ui'; lg.textAlign = 'center'; lg.textBaseline = 'middle'; lg.fillText('Nearby industry · buys the power', 256, 47);
    const lsp = new THREE.Sprite(new THREE.SpriteMaterial({ map: new THREE.CanvasTexture(lbl), transparent: true, depthWrite: false, fog: false })); lsp.scale.set(46, 8.6, 1); lsp.position.set(ind.x, 34, ind.z); field.add(lsp);
    flowDots = []; const dotG = new THREE.SphereGeometry(.15, 8, 8), dotM = new THREE.MeshBasicMaterial({ color: 0xffd23c }); for (let k = 0; k < 36; k++) { const d = new THREE.Mesh(dotG, dotM); d.userData.u = k / 36; field.add(d); flowDots.push(d); }
    gridObjs = [inv, fac, lsp, ...flowDots, ...poleObjs];
    [half, -half].forEach(x => { const pu = new THREE.Mesh(new THREE.CylinderGeometry(.08, .08, .05, 16), steel()); pu.rotation.x = Math.PI / 2; pu.position.set(x, H - .33, zW); field.add(pu); });
    driveEnds = [V(half, H - .33, zW), V(-half, H - .33, zW)];
    for (let i = 0; i < N + 1; i++) { const s = seg(V(0, 0, 0), V(0, 1, 0), .011, wireMat); field.add(s); driveSegs.push(s); }
    const mx = -half - 2.2, mz = -LZ / 2 + 2; field.add(seg(V(mx, 0, mz), V(mx, 3.2, mz), .04, galv()));   // sensor mast, downpipe, underground pipe
    field.add(box(mx - .12, mx + .12, 3.2, 3.3, mz - .12, mz + .12, std(0xf0f0f0))); field.add(box(mx + .25, mx + .55, 2.6, 2.75, mz - .1, mz + .1, std(0x222222)));
    const rg2 = new THREE.Mesh(new THREE.CylinderGeometry(.1, .1, .3, 12), std(0xe8e8e8)); rg2.position.set(mx, 1.0, mz); field.add(rg2);
    field.add(seg(V(half + .2, H - .5, 0), V(half + .2, -.6, 0), .06, std(0x555b61)));
    const pipe = new THREE.Mesh(new THREE.CylinderGeometry(.07, .07, cx - cw / 2 - half, 10), std(0x555b61)); pipe.rotation.z = Math.PI / 2; pipe.position.set((cx - cw / 2 + half) / 2, -.6, 0); field.add(pipe);
    harvester = new THREE.Group(); const hb = (x0, x1, y0, y1, z0, z1, c) => harvester.add(box(x0, x1, y0, y1, z0, z1, std(c)));    // scale references
    hb(-1.4, 1.4, .7, 3.0, -3.8, 3.8, 0x6aa31a); hb(-1.0, 1.0, 3.0, 4.0, 1.6, 3.8, 0xe8e8e8); hb(-.9, .9, 3.2, 3.9, 3.7, 3.82, 0x9ac7e8); hb(-3.0, 3.0, .3, 1.2, 3.8, 5.0, 0xc83030);
    [[-1.5, 2], [1.5, 2], [-1.4, -2.4], [1.4, -2.4]].forEach(([x, z]) => hb(x - .3, x + .3, 0, 1.7, z - .85, z + .85, 0x1b1b1b)); harvester.position.set(-half + bay / 2, 0, 4); field.add(harvester);
    const person = new THREE.Group(); person.add(box(-.2, .2, 0, 1.0, -.1, .1, std(0x2a4d8f)), box(-.18, .18, 1.0, 1.7, -.1, .1, std(0xd8a070))); person.position.set(half - 2, 0, 8); field.add(person);
    fieldMeta.N = N; fieldMeta.half = half; fieldMeta.H = H; fieldMeta.bay = bay;
  }
  function refresh(light) {
    if (!ready || !R) return; if (envId !== clim.id) setEnv(clim.id); if (!light) build();
    const n = st.day + 1, sun = S.sunVec(clim.lat, n, st.hour), P = R.P, up = sun.sz > .02;
    const dir = V(sun.sx, Math.max(sun.sz, 0), -sun.sy).normalize();
    sunL.position.copy(dir.clone().multiplyScalar(120)); sunL.intensity = up ? (st.rain ? .7 : 2.2) * Math.min(1, sun.sz * 6) : 0;
    const su = sky.material.uniforms; su.sunPosition.value.copy(dir.clone().setY(Math.max(dir.y, -.05))); su.turbidity.value = st.rain ? 18 : envCfg.turb; su.rayleigh.value = up ? 1.6 : .15;
    hemi.intensity = up ? (st.rain ? .3 : .4) : .06; scene.fog.color.set(up ? (st.rain ? 0x8a97a5 : envCfg.fogc) : 0x0a0f18); scene.fog.density = st.rain ? .0016 : envCfg.fog;
    const autoFlat = st.auto && R.wb.rain[st.day] >= P.harvestThreshold, flat = st.rain || autoFlat; fieldMeta.flat = flat;
    const mode = flat ? 'rain' : P.tiltMode; lastTilt = S.tiltFor(sun, Object.assign({}, P, { tiltMode: mode }), monthOf(st.day), st.hour); if (!light) curTilt = lastTilt;
    if (SENS.on) { lastTilt = flat ? P.rainSlope : (sun.sz < .02 ? 15 : SENS.cmd); if (!light) curTilt = lastTilt; senseDecide(false); }
    if (cistW) { const f = Math.max(.03, Math.min(1, R.wb.tankSeries[st.day] / Math.max(P.tankM3, 1))), d = cistW.userData.depth; cistW.scale.y = f * d; cistW.position.y = -3.4 + f * d / 2; }
    rainPts.visible = flat; overlay.visible = st.overlay; labelGrp.visible = st.labels && !ENVS[envId]; gridObjs.forEach(o => o.visible = st.grid); if (gutterWater) gutterWater.material.opacity = flat ? .85 : 0;
    let irrNow = S.irradiance(sun.sz, n, clim.kt[monthOf(st.day)]); if (SENS.on) irrNow = senseIrr(irrNow, sun); pvFrac = Math.max(0, Math.min(1, irrNow.ghi / 900)) * (flat ? .35 : 1); sensors(sun, irrNow, lastTilt, flat); hud();
  }
  function hud() {
    if (!R) return; const n = st.day + 1, sun = S.sunVec(clim.lat, n, st.hour), t = lastTilt, P = R.P;
    const el = Math.asin(Math.max(-1, Math.min(1, sun.sz))) / D2R, az = (Math.atan2(sun.sx, sun.sy) / D2R + 360) % 360, dt = new Date(2025, 0, n);
    const edge = P.height - P.panelW / 2 * Math.sin(Math.abs(t) * D2R);
    $('#hud').innerHTML = `<b>${dt.toLocaleDateString('en-GB', { day: 'numeric', month: 'short' })}</b> · ${Math.floor(st.hour)}:${String(Math.round((st.hour % 1) * 60)).padStart(2, '0')} solar time<br>Sun elevation ${fmt(el, 0)}° · azimuth ${fmt(az, 0)}°<br>Panel angle <b>${fmt(Math.abs(t), 1)}°</b> ${fieldMeta.flat ? '— RAIN MODE: ' + P.rainSlope + '° fall to gutter' : (P.tiltMode === 'smart' ? '— TILT MODE · sensor-driven stop, hour ' + (S.winIndex(P, st.hour) + 1) + '/' + P.windows.length : '— TILT MODE')}<br>Lowest panel edge <b>${fmt(edge, 2)} m</b><br>Cistern ${fmt(R.wb.tankSeries[st.day], 0)} / ${fmt(P.tankM3)} m³<br><span style="color:#9a9;font-size:11px">${envId && ENVS[envId] ? 'Landscape: ' + envCfg.name + ' (illustrative)' : 'Visual: ' + (fieldMeta.site ? fieldMeta.site.name : '')} · sun &amp; weather: ${clim.name.split(' (')[0]}</span>`;
    $('#t-day-v').textContent = dt.toLocaleDateString('en-GB', { day: 'numeric', month: 'short' }); $('#t-hour-v').textContent = st.hour.toFixed(1) + ' h';
  }
  function sensors(sun, irr, t, flat) {
    const n = st.day + 1, m = monthOf(st.day), P = R.P, up = sun.sz > .02, hr = st.hour;
    let tamb = clim.tmean[m] + clim.trange[m] / 2 * Math.sin(2 * Math.PI * (hr - 9) / 24), rh = Math.max(15, Math.min(98, clim.rh[m] - 12 * Math.cos(2 * Math.PI * (hr - 15) / 24)));
    if (SENS.on) { tamb = SENS.temp; rh = SENS.rh; }
    const es = 0.6108 * Math.exp(17.27 * tamb / (tamb + 237.3)), vpd = es * (1 - rh / 100);
    const Q = Object.assign({}, P, { tiltMode: 'fixed', tilt: t }); let lsr = [0, 0, 0, 0], tp = tamb, pw = 0;
    if (up) { const g = S.groundLightHour(Q, sun, irr, t); for (let z = 0; z < 4; z++) lsr[z] = 100 * g.slice(z * 10, z * 10 + 10).reduce((a, b) => a + b, 0) / 10 / Math.max(irr.ghi, 1);
      const pp = S.panelPower(Q, sun, irr, t, tamb, clim.wind[m]); tp = pp.tc; pw = pp.p * (10000 * Math.min(1, P.panelW / P.pitch)) / 1e6; }
    const th = R.wb.theta.map(a => a[st.day] * 100), dec = R.ctrl && R.ctrl.detail[m] && R.ctrl.detail[m][S.winIndex(P, hr)];
    const row = (a, b, c) => `<tr><td>${a}</td><td><b>${b}</b></td><td>${c || ''}</td></tr>`;
    const lsrMean = (lsr[0] + lsr[1] + lsr[2] + lsr[3]) / 4, parUm = 2.05 * lsrMean / 100 * irr.ghi, soilTxt = SENS.on ? SENS.soil + ' %' : fmt(th.reduce((x, y) => x + y, 0) / th.length, 0) + ' % (model)';
    $('#sensors').innerHTML = `<b>YOUR SENSORS (★) drive the tilt</b><table>${row('★ Pyranometer (GHI)', fmt(irr.ghi, 0) + ' W/m²', 'sun')}${row('★ PAR under canopy', fmt(parUm, 0) + ' µmol/m²/s', fmt(lsrMean, 0) + ' % of sun')}${row('★ DHT11 temp · RH', fmt(tamb, 0) + ' °C · ' + fmt(rh, 0) + ' %', 'air')}${row('   VPD (calculated)', fmt(vpd, 1) + ' kPa', vpd > 2.5 ? 'stress' : 'ok')}${row('★ Soil moisture', soilTxt, SENS.on && SENS.soil < 20 ? 'dry' : 'ok')}${row('★ Rain sensor', flat ? 'WET' : 'dry', flat ? 'FLAT→gutter' : '')}${row('Panel temp (modelled, no sensor)', fmt(tp, 0) + ' °C', '')}${row('Power to industry (model)', fmt(pw, 2) + ' MW/ha', 'PV')}</table>`
      + `<div class="dec">${SENS.on && SENS.last ? 'Decision: ' + SENS.last.action : (flat ? 'Rain detected → motor winds panels to ' + P.rainSlope + '° fall, gutter → cistern' : (dec ? 'Decision: angle <b>' + fmt(dec.a, 1) + '°</b> · PV ' + fmt(dec.pvRel * 100, 0) + '% · crop ' + fmt(dec.cropRel * 100, 0) + '% of best' : (up ? 'Fixed stop' : 'Night: parked')))}</div>`;
  }
  function view(name) {
    const half = fieldMeta.half || 12.5, s = fieldMeta.site, mb = site.buildings.find(b => b.n === 'Main Building');
    const bc = mb ? [mb.p.reduce((a, p) => a + p[0], 0) / mb.p.length, mb.p.reduce((a, p) => a + p[1], 0) / mb.p.length] : [0, 0];
    const rel = V(bc[0] - s.c[0], 0, -(bc[1] - s.c[1])); let pos, tg;
    if (name === 'campus' && ENVS[envId]) { pos = V(-120, 140, 260); tg = V(0, 0, -60); }
    else if (name === 'campus') { const d = Math.max(160, rel.length() * 1.05); tg = rel.clone().multiplyScalar(.5); pos = tg.clone().add(V(-d * .15, d * .72, d * .82)); }
    else if (name === 'under') { pos = V(-half + (fieldMeta.bay || 12.5) / 2 + 2.6, 1.7, 22); tg = V(-half + (fieldMeta.bay || 12.5) / 2, 2.4, -6); }
    else if (name === 'top') { pos = V(0, 70, 1); tg = V(0, 0, 0); }
    else if (name === 'mech') { const hh = fieldMeta.H || 5.6; pos = V(half + 3.4, hh + .6, 12.5 + 3.6); tg = V(half - 1.8, hh - .5, 11.2); }
    else { pos = V(-30, 17, 40); tg = V(0, 2.5, 0); }
    fly = { p: pos, t: tg };
  }
  function resize() { if (!ready) return; const el = $('#three'), w = el.clientWidth, h = el.clientHeight || 520; ren.setSize(w, h); cam.aspect = w / h; cam.updateProjectionMatrix(); }
  let tprev = 0; const tmp = V(0, 0, 0);
  function animate(t) {
    requestAnimationFrame(animate); if (!ready || !R || st.tab !== 'twin') return; const dt = Math.min(.1, ((t || 0) - tprev) / 1000); tprev = t || 0;
    if (st.playing) { st.hour += dt * 1.6; if (st.hour > 19) st.hour = 5; $('#t-hour').value = st.hour; refresh(true); }
    if (fly) { cam.position.lerp(fly.p, Math.min(1, dt * 3)); ctl.target.lerp(fly.t, Math.min(1, dt * 3)); if (cam.position.distanceTo(fly.p) < .3) fly = null; }
    if (SENS.on) { SENS.timer += dt; if (SENS.timer > .9) { SENS.timer = 0; senseDecide(true); } const sz0 = S.sunVec(clim.lat, st.day + 1, st.hour).sz; lastTilt = fieldMeta.flat ? R.P.rainSlope : (sz0 < .02 ? 15 : SENS.cmd); }
    const stepD = 22 * dt, errD = lastTilt - curTilt, moving = Math.abs(errD) > .05; curTilt += Math.max(-stepD, Math.min(stepD, errD)); panels.forEach(g => g.rotation.z = -curTilt * D2R);
    if (motorLed) motorLed.material.color.setHex(moving ? 0xffb020 : 0x35e07a);
    if (flowDots.length && st.grid) flowDots.forEach(d => { d.userData.u = (d.userData.u + dt * (.02 + pvFrac * .18)) % 1; const f = d.userData.u * (flowPath.length - 1), i = Math.min(flowPath.length - 2, Math.floor(f)), k = f - i; d.position.lerpVectors(flowPath[i], flowPath[i + 1], k); d.visible = pvFrac > .02; });
    if (panels.length) {
      const pts = [driveEnds[0]]; levers.forEach((l, i) => { tmp.copy(l); panels[panels.length - 1 - i].localToWorld(tmp); pts.push(tmp.clone()); }); pts.push(driveEnds[1]);
      driveSegs.forEach((s, i) => { if (pts[i + 1]) placeSeg(s, pts[i], pts[i + 1]); });
    }
    if (rainPts.visible) { const a = rainPts.geometry.attributes.position; for (let i = 0; i < a.count; i++) { let y = a.getY(i) - dt * 16; if (y < 0) y += 26; a.setY(i, y); } a.needsUpdate = true; }
    ctl.update(); ren.render(scene, cam);
  }
  window.addEventListener('resize', () => { resize(); if (st.tab !== 'twin') renderTab(); });
  return { init, refresh, resize, view, placeSite, rebuild: () => { placeSite(); refresh(false); } };
})();
function hud() { scene3d.refresh(true); }

/* ---------------- boot ---------------- */
document.addEventListener('DOMContentLoaded', () => {
  buildControls(); applyDesign(DATA.design.active, true); scene3d.init(); compute();
  $('#mx-zone').onchange = () => tabCrops();
  $('#e-capex').oninput = e => { st.p.capexPerKWp = +e.target.value; $('#v-e-capex').textContent = '₹' + fmt(+e.target.value / 1000) + 'k'; compSoon(); };
  $('#e-tariff').oninput = e => { st.p.tariff = +e.target.value; $('#v-e-tariff').textContent = '₹' + e.target.value; compSoon(); };
  $('#e-share').oninput = e => { st.p.farmerShare = +e.target.value; $('#v-e-share').textContent = Math.round(e.target.value * 100) + '%'; compSoon(); };
  $('#e-subsidy').oninput = e => { st.p.subsidyPct = +e.target.value; $('#v-e-subsidy').textContent = e.target.value + '%'; compSoon(); };
  $('#sens-on').onchange = e => { SENS.on = e.target.checked; SENS.timer = 0; SENS.cmd = 27; $('#sens-box').style.display = SENS.on ? '' : 'none'; scene3d.refresh(true); };
  [['cloud', 'cloud', v => Math.round(v * 100) + ' %', v => v / 100], ['temp', 'temp', v => v + ' °C', v => +v], ['rh', 'rh', v => v + ' %', v => +v], ['soil', 'soil', v => v + ' %', v => +v]].forEach(([id, key, lab, cv_]) => { const el = $('#sens-' + id); el.oninput = () => { SENS[key] = cv_(+el.value); if (id === 'temp' || id === 'rh') SENS.manualTH = true; $('#v-sens-' + id).textContent = lab(+el.value); scene3d.refresh(true); }; });
  $('#sens-reset').onclick = () => { SENS.manualTH = false; SENS.cloud = 0; SENS.soil = 26; $('#sens-cloud').value = 0; $('#v-sens-cloud').textContent = '0 %'; $('#sens-soil').value = 26; $('#v-sens-soil').textContent = '26 %'; scene3d.refresh(true); };
  window.SRMC_UI = { st, SENS, get R() { return R; }, compute };
});
})();
