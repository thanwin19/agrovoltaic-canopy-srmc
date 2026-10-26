/* ---------------- Six-sensor controller (SRMC-SC): pyranometer + PAR + DHT11 + soil moisture + rain sensor + anemometer -> tilt ---------------- */
const SENS = { on: true, cloud: 0, temp: 31, rh: 55, soil: 26, manualSoil: false, wind: 3, cmd: 27, timer: 0, manualTH: false, last: null, ctl: null, ctlR: null, live: null, cal: { dry: 1000, wet: 420 }, port: null, fault: 'none', safe: null, st: null, stR: null };
function senseIrr(irr, sun) {                                  // clouds: less beam, more diffuse
  const c = SENS.cloud, ghi = irr.ghi * (1 - .72 * c), dni = irr.dni * Math.pow(1 - c, 1.6), dhi = Math.max(0, ghi - dni * Math.max(sun.sz, .05));
  return { ghi, dni, dhi };
}
function modelSoilPct() { const so = DATA.soils.find(x => x.id === st.soilId), th = R.wb.theta.map(a => a[st.day]), mean = th.reduce((a, b) => a + b, 0) / th.length; return Math.max(0, Math.min(100, 100 * (mean - so.wp) / (so.fc - so.wp))); }   // plant-available water %: 0 = wilting point, 100 = field capacity
function senseCtl() { if (SENS.ctlR !== R) { SENS.ctl = SRMC_SC.make(S, { P: R.P, clim, zones: R.zones, w: R.P.energyWeight, maxStep: 6 }); SENS.ctlR = R; SENS.safe = SENS.ctl.makeSafe(); SENS.st = SENS.safe.fresh(SENS.cmd); } return SENS.ctl; }
function cloneSt(o) { return Object.assign({}, o, { moveTimes: o.moveTimes.slice(), dayTravel: Object.assign({}, o.dayTravel), faults: Object.assign({}, o.faults) }); }
/* --- optional live mode: a real ESP board (Review 0 firmware) sends  SRMC,ms,tempC,rh,soilRaw,rainWet,rainRaw[,ghiWm2,parUmol]  at 115200 baud (Web Serial: Chrome or Edge) --- */
function liveLine(line) {
  const p = line.trim().split(','); if (p[0] !== 'SRMC' || (p.length !== 7 && p.length !== 9 && p.length !== 10)) return false; const v = p.slice(1).map(Number); if (v.some(isNaN) || !(v[4] === 0 || v[4] === 1)) return false;
  const cal = SENS.cal; SENS.live = { T: v[1], RH: v[2], soil: Math.max(0, Math.min(100, 100 * (cal.dry - v[3]) / (cal.dry - cal.wet))), rain: v[4] === 1, ghi: p.length >= 9 ? v[6] : null, par: p.length >= 9 ? v[7] : null, wind: p.length === 10 ? v[8] : null, tOk: v[1] > -100 && v[2] >= 0 && v[2] <= 100, t: Date.now() };
  const el = $('#live-status'); if (el) el.textContent = 'live: ' + (SENS.live.tOk ? SENS.live.T.toFixed(1) + ' °C, ' + SENS.live.RH.toFixed(0) + ' % RH' : 'DHT11 not read') + ', soil ' + SENS.live.soil.toFixed(0) + ' %, rain ' + (SENS.live.rain ? 'WET' : 'dry') + (SENS.live.ghi != null ? ', pyranometer ' + SENS.live.ghi.toFixed(0) + ', PAR ' + SENS.live.par.toFixed(0) : ' (pyranometer and PAR simulated)'); try { senseDecide(false); } catch (e) { } return true;
}
async function liveConnect() {
  const el = $('#live-status'); if (!('serial' in navigator)) { if (el) el.textContent = 'Web Serial needs Chrome or Edge (and a USB cable).'; return; }
  try {
    const sel = $('#live-board'); SENS.cal = sel && sel.value === 'esp32' ? { dry: 3200, wet: 1300 } : { dry: 1000, wet: 420 };
    SENS.port = await navigator.serial.requestPort(); await SENS.port.open({ baudRate: 115200 }); if (el) el.textContent = 'connected, waiting for the first SRMC line...';
    const dec = new TextDecoderStream(); SENS.port.readable.pipeTo(dec.writable); const rd = dec.readable.getReader(); let buf = '';
    (async () => { for (;;) { const { value, done } = await rd.read(); if (done) break; buf += value; let i; while ((i = buf.indexOf('\n')) >= 0) { liveLine(buf.slice(0, i)); buf = buf.slice(i + 1); } } })();
  } catch (e) { if (el) el.textContent = 'not connected: ' + e.message; }
}
function senseDecide(apply) {
  if (!R || !SENS.on) return; const P = R.P, n = st.day + 1, m = monthOf(st.day), hr = st.hour, sun = S.sunVec(clim.lat, n, hr), ctl = senseCtl();
  const irr = senseIrr(S.irradiance(sun.sz, n, clim.kt[m]), sun), lv = SENS.live && Date.now() - SENS.live.t < 5000 ? SENS.live : null;
  const mt = clim.tmean[m] + clim.trange[m] / 2 * Math.sin(2 * Math.PI * (hr - 9) / 24), mr = Math.max(15, Math.min(98, clim.rh[m] - 12 * Math.cos(2 * Math.PI * (hr - 15) / 24)));
  if (lv) { if (lv.tOk) { SENS.temp = +lv.T.toFixed(1); SENS.rh = Math.round(lv.RH); } SENS.soil = Math.round(lv.soil); SENS.manualTH = true; const a0 = $('#sens-temp'), b0 = $('#sens-rh'), c0 = $('#sens-soil'); if (a0) { a0.value = SENS.temp; $('#v-sens-temp').textContent = SENS.temp + ' °C'; } if (b0) { b0.value = SENS.rh; $('#v-sens-rh').textContent = SENS.rh + ' %'; } if (c0) { c0.value = SENS.soil; $('#v-sens-soil').textContent = SENS.soil + ' %'; } if (lv.wind != null) { SENS.wind = Math.round(lv.wind * 10) / 10; const w0 = $('#sens-wind'); if (w0) { w0.value = SENS.wind; $('#v-sens-wind').textContent = SENS.wind + ' m/s'; } }
  if (lv.ghi != null) { const k = lv.ghi / Math.max(irr.ghi, 1); irr.dni *= k; irr.dhi *= k; irr.ghi = lv.ghi; } }
  if (!lv && !SENS.manualSoil) { SENS.soil = Math.round(modelSoilPct()); const c1 = $('#sens-soil'); if (c1) { c1.value = SENS.soil; $('#v-sens-soil').textContent = SENS.soil + ' %'; } }
  if (lv) { }
  else if (!SENS.manualTH) { SENS.temp = +mt.toFixed(1); SENS.rh = Math.round(mr); const a = $('#sens-temp'), b = $('#sens-rh'); if (a) { a.value = SENS.temp; $('#v-sens-temp').textContent = SENS.temp + ' °C'; } if (b) { b.value = SENS.rh; $('#v-sens-rh').textContent = SENS.rh + ' %'; } }
  const T = SENS.temp, RH = SENS.rh, ws = clim.wind ? clim.wind[m] : 2, rain = lv ? lv.rain : st.rain, night = irr.ghi < 20 || sun.sz < .02, sr = ctl.stressOf(T, RH, SENS.soil);
  let parUm = 0, lsr = 0;
  if (!night) { lsr = ctl.evalAngle(SENS.cmd, sun, irr, T, 1, sr.s, ws).lsr; parUm = SRMC_SC.UM_PER_W * lsr * irr.ghi; if (lv && lv.par != null) { parUm = lv.par; lsr = parUm / SRMC_SC.UM_PER_W / Math.max(irr.ghi, 1); } }     // PAR: real sensor if the board sends it, else simulated from the canopy physics at the angle in use
  // injected sensor faults (for the demo) are applied to the readings; the safety layer must catch them
  const fl = SENS.fault; let soilRead = SENS.soil, rainRead = rain, soilRaw = null; if (fl === 'soilStuck') { soilRead = 12; soilRaw = 2800; } else if (fl === 'soilDead') soilRead = NaN; else if (fl === 'soilGlitch') soilRead = 3; else if (fl === 'rainWet') rainRead = true; else if (fl === 'rainDead') rainRead = false;
  const stt = apply ? SENS.st : cloneSt(SENS.st); stt.angle = SENS.cmd; const msoil = modelSoilPct();
  const d = SENS.safe.step({ ghi: irr.ghi, parUm, T, RH, soil: soilRead, soilRaw, soilModel: msoil, rain: rainRead, rainForecast: R.wb.rain[st.day] >= P.harvestThreshold, wind: SENS.wind, day: n, hour: hr, t: (n * 24 + hr) * 3600 }, stt);
  if (apply) SENS.cmd = d.angle;
  const why = []; if (sr.vpd > 1.6) why.push('VPD ' + sr.vpd.toFixed(1) + ' kPa'); if (SENS.soil < 20) why.push('soil dry ' + SENS.soil + ' %');
  const dry = SENS.soil < 20, wet = SENS.soil > 35, tag = lv ? ' <span style="color:#9ad0ff">(real board)</span>' : '';
  SENS.last = { lsr, target: d.target, vpd: sr.vpd, T, RH, par: parUm, ghi: irr.ghi, rain, night, action: d.mode + ': ' + d.reason, pvRel: d.pvRel == null ? 0 : d.pvRel, cropRel: d.cropRel == null ? 0 : d.cropRel };
  const el = $('#sens-trace'); if (el) el.innerHTML =
    `<div><b>1 Pyranometer (GHI):</b> ${irr.ghi.toFixed(0)} W/m² ${night ? '(night)' : ''}${lv && lv.ghi != null ? tag : ''}</div>
     <div><b>2 PAR sensor under the canopy:</b> ${parUm.toFixed(0)} µmol/m²/s → ${(lsr * 100).toFixed(0)} % of the sun reaches the crop${d.mode === 'OPTIMISE' ? ' (model correction ×' + d.corr.toFixed(2) + ')' : ''}${lv && lv.par != null ? tag : ''}</div>
     <div><b>3 DHT11:</b> ${T.toFixed(1)} °C, ${RH} % RH → VPD ${sr.vpd.toFixed(1)} kPa ${why.length ? '<span style="color:#ffb3a8">(stress ' + sr.s.toFixed(2) + ': ' + why.join('; ') + ')</span>' : '(no stress)'}${tag}</div>
     <div><b>4 Soil moisture (plant-available water):</b> ${SENS.soil} % ${lv ? '' : SENS.manualSoil ? '(slider)' : '(water-balance model)'} → ${dry ? '<span style="color:#ffb3a8">dry: drip irrigation ON, a little more shade</span>' : wet ? 'waterlogging risk: irrigation OFF' : 'optimal, irrigation standby'}${tag}</div>
     <div><b>5 Rain sensor:</b> ${rain ? '<span style="color:#9ad0ff">WET</span> → flat roof, gutter to cistern' : 'dry'}${tag}</div>
     <div><b>6 Anemometer (wind):</b> ${SENS.wind.toFixed(1)} m/s → ${SENS.wind >= 15 ? '<span style="color:#ffb3a8">STORM: panels edge-on at 90°</span>' : 'normal (stow at 15 m/s = 54 km/h, resume below 12 m/s)'}</div>
     <div style="margin-top:6px;color:#ffe08a"><b>Decision:</b> ${d.mode}: ${d.reason}</div>
     <div style="color:${d.safety.notes.length ? '#ffb3a8' : '#9fb0a6'}"><b>Safety:</b> ${d.safety.notes.length ? d.safety.notes.join(' | ') : 'all sensors plausible, no move limit active'}</div>
     <div style="color:#9fc7e8"><b>Motor wear:</b> ${d.safety.moves} moves, ${d.safety.travelDeg.toFixed(0)}° panel travel (${d.safety.todayTravelDeg.toFixed(0)}° today), ${d.safety.wireM.toFixed(1)} m of drive wire, ${d.safety.drumTurns.toFixed(1)} drum turns, ${d.safety.reversals} reversals; moves held by the limits: ${d.safety.heldMoves}; ${d.safety.movesLastHour}/${d.safety.cfg.maxMovesPerHour} moves in the last hour; fallbacks used: soil ${d.safety.soilFallbacks}, rain ${d.safety.rainFallbacks}</div>
     <div style="color:#b8e6a0">Panel angle <b>${SENS.cmd.toFixed(1)}°</b>${d.mode === 'OPTIMISE' ? ' · electricity ≈ <b>' + (100 * d.pvRel).toFixed(0) + ' %</b> and crop light value ≈ <b>' + (d.cropRel == null ? 'n/a (no crop growing this month)' : (100 * d.cropRel).toFixed(0) + ' %') + '</b> of the best possible at this hour' : ''}</div>`;
}
