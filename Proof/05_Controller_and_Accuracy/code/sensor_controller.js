/* SRMC-SC: six-sensor controller for the agrovoltaic canopy.
 *
 * Inputs it reads every decision step
 *   pyranometer  ghi        W/m2 above the canopy
 *   PAR sensor   parUm      umol/m2/s under the canopy (zone average)
 *   DHT11        T, RH      C, %
 *   soil sensor  soil       % volumetric
 *   rain sensor  rain       true / false
 *   anemometer   wind       m/s (optional sixth sensor: wind protection)
 *   clock        day, hour  solar time (ESP32 RTC or NTP)
 *
 * Rules (highest priority first)
 *   0 anemometer >= 15 m/s         -> wind stow, panels edge-on at 90 deg (resume below 12 m/s)
 *   1 rain wet                     -> flat roof, rainSlope (3 deg), water to the gutter and cistern
 *   2 pyranometer < 20 W/m2        -> night park (lowest stop)
 *   3 otherwise: choose the angle that maximises  J = w * PV/PVmax + (1-w) * crop/cropmax   (w = 0.5 by default)
 *       PV(a)   panel power from the measured irradiance split (Huld model, row shading)
 *       crop(a) price-weighted light factor of the 4 crop zones.  The light each zone gets is the model value times a
 *               correction c = (PAR measured / pyranometer) / (same ratio predicted by the model at the angle now in use).
 *               So the PAR sensor corrects the model for dirt, cloud pattern and any shading error.
 *       DHT11 (VPD) and soil moisture set a stress s in 0..1; stress lowers the light the crop needs (lmin, lopt x (1 - 0.3 s)),
 *               so the controller accepts more shade (and gives more to the panels' protection) while the crop is stressed.
 *   4 motor limits: max step per decision, 0.5 deg encoder resolution, 15 to 60 deg stops.
 * Used by the digital twin (browser) and by the year-long evaluation (Node).
 */
(function (root) {
  'use strict';
  const UM_PER_W = 2.05;                                   // umol/m2/s of PAR per W/m2 of broadband sunlight (about 45 % PAR x 4.57 umol/J)
  const clamp = (x, a, b) => Math.max(a, Math.min(b, x));
  function make(S, ctx) {
    // ctx: { P (engine params incl. stops, rainSlope), clim, zones: [{crop:{lmin,lopt,ym,price}}...] (4), w (energy weight), maxStep (deg per decision), vpdLow, vpdHigh, soilDry }
    const P = ctx.P, w = ctx.w == null ? 0.5 : ctx.w, lo = P.stops[0], hi = P.stops[P.stops.length - 1], clim = ctx.clim;
    const relax = ctx.relax == null ? 0.3 : ctx.relax, guard = ctx.guard !== false, hyst = ctx.hyst == null ? 0.02 : ctx.hyst, vpdLow = ctx.vpdLow || 1.6, vpdHigh = ctx.vpdHigh || 2.5, soilDry = ctx.soilDry || 20, maxStep = ctx.maxStep || 6;
    const crops = ctx.zones.map(z => z.crop);
    const NSZ = 4;
    const monthOfDay = n => { let m = 0; for (let i = 0; i < 12; i++) if (n > S.CUM[i]) m = i; return m; };
    const seas = ctx.zones.map((z, k) => ctx.monthW ? ctx.monthW[k] : S.seasonInfo(z.crop, clim, z.sowMonth != null ? z.sowMonth : z.crop.sow - 1).monthWeights);   // crop value counts only in the growing season of each zone
    let curM = 0; function setDay(n) { curM = monthOfDay(n); }
    function vpdOf(T, RH) { const es = 0.6108 * Math.exp(17.27 * T / (T + 237.3)); return Math.max(0, es * (1 - RH / 100)); }
    function stressOf(T, RH, soil) {
      const v = vpdOf(T, RH), sA = clamp((v - vpdLow) / (vpdHigh - vpdLow), 0, 1), sS = clamp((soilDry - soil) / soilDry, 0, 1);
      return { s: Math.max(sA, sS), sA, sS, vpd: v };
    }
    function irrFrom(ghi, sun, n) {                         // pyranometer GHI -> beam / diffuse split (Erbs on the clearness index)
      const g0 = 1361 * (1 + 0.033 * Math.cos(2 * Math.PI * n / 365)), kt = clamp(ghi / (g0 * Math.max(sun.sz, 0.05)), 0.02, 0.85);
      const m = S.irradiance(sun.sz, n, kt), k = ghi / Math.max(m.ghi, 1e-9);
      return { ghi, dni: m.dni * k, dhi: m.dhi * k };
    }
    function zoneLsr(g) {                                    // per-zone mean light fraction from ground samples
      const NSg = g.length, out = [];
      for (let z = 0; z < NSZ; z++) out.push(g.slice(z * NSg / NSZ, (z + 1) * NSg / NSZ).reduce((a, b) => a + b, 0) / (NSg / NSZ));
      return out;
    }
    function lightFactorS(L, c, stress) {                    // engine lightFactor with thresholds relaxed by stress
      const f = 1 - relax * stress, cc = { lmin: c.lmin * f, lopt: c.lopt * f };
      return S.lightFactor(L, cc);
    }
    function evalAngle(a, sun, irr, T, corr, stress, ws) {
      const Q = Object.assign({}, P, { tiltMode: 'fixed', tilt: a });
      const g = S.groundLightHour(Q, sun, irr, a), zl = zoneLsr(g), pv = S.panelPower(Q, sun, irr, a, T, ws).p;
      let crop = 0; for (let z = 0; z < NSZ; z++) crop += (seas[z][curM] > 0 ? seas[z][curM] : 0) * crops[z].ym * crops[z].price * lightFactorS(clamp(zl[z] * corr / Math.max(irr.ghi, 1), 0, 1), crops[z], stress);
      return { a, pv, crop, lsr: zl.reduce((x, y) => x + y, 0) / NSZ / Math.max(irr.ghi, 1) };
    }
    function search(sun, irr, T, corr, stress, ws, center) {   // coarse 5 deg, then 0.5 deg around the best (the motor resolution)
      const coarse = []; for (let a = lo; a <= hi + 1e-9; a += 5) coarse.push(a);
      let ev = coarse.map(a => evalAngle(a, sun, irr, T, corr, stress, ws));
      const score = () => { const pm = Math.max(...ev.map(x => x.pv), 1e-9), cm = Math.max(...ev.map(x => x.crop), 1e-9); ev.forEach(x => x.J = w * x.pv / pm + (1 - w) * x.crop / cm); return ev.reduce((b, x) => (!b || x.J > b.J + 1e-9) ? x : b, null); };
      let best = score();
      for (let a = Math.max(lo, best.a - 5); a <= Math.min(hi, best.a + 5) + 1e-9; a += 0.5) { const aa = +a.toFixed(3); if (!ev.some(x => Math.abs(x.a - aa) < 1e-6)) ev.push(evalAngle(aa, sun, irr, T, corr, stress, ws)); }
      best = score(); return { best, ev };
    }
    function decide(sen, st) {                               // sen: sensor readings; st: { angle (current), day, hour }
      const n = sen.day; setDay(n); const sun = S.sunVec(clim.lat, n, sen.hour), prev = st.angle == null ? lo : st.angle, ws = ctx.wind == null ? 2 : ctx.wind;
      const sr = stressOf(sen.T, sen.RH, sen.soil), out = { stress: sr.s, vpd: sr.vpd, sA: sr.sA, sS: sr.sS, mode: '', angle: prev, reason: '', corr: 1, lsrMeas: null, lsrModel: null, target: null };
      const stowAt = ctx.windStow || 15, resumeAt = ctx.windResume || 12, stowAngle = ctx.stowAngle || 90;            // anemometer: stow edge-on in a storm, resume with hysteresis
      if (sen.wind != null && (sen.wind >= stowAt || (st.angle >= stowAngle && sen.wind >= resumeAt))) { out.mode = 'STOW'; out.angle = stowAngle; out.reason = 'anemometer ' + sen.wind.toFixed(1) + ' m/s >= ' + stowAt + ' m/s: panels edge-on at ' + stowAngle + ' deg'; return out; }
      if (sen.rain) { out.mode = 'RAIN'; out.angle = P.rainSlope; out.reason = 'rain sensor wet: flat roof ' + P.rainSlope + ' deg to the gutter'; return out; }
      if (sen.ghi < 20 || sun.sz < 0.02) { out.mode = 'NIGHT'; out.angle = lo; out.reason = 'pyranometer ' + sen.ghi.toFixed(0) + ' W/m2: night, parked at ' + lo + ' deg'; return out; }
      const irr = irrFrom(sen.ghi, sun, n);
      let corr = 1;                                          // PAR correction against the model at the angle now in use
      const lsrMeas = sen.parUm / UM_PER_W / Math.max(sen.ghi, 1);
      const cur = evalAngle(clamp(prev, lo, hi), sun, irr, sen.T, 1, sr.s, ws);
      if (cur.lsr > 0.01 && isFinite(lsrMeas)) {
        const ratio = sen.parRatio != null ? sen.parRatio : lsrMeas / cur.lsr;      // callers that filter several readings taken at different angles pass the median of the per-reading ratios
        if (guard && (ratio < 0.5 || ratio > 1.6)) { corr = 1; out.fault = 'PAR sensor implausible (reads ' + ratio.toFixed(2) + ' x the model): ignored'; }   // fault guard: a stuck, dirty or shaded PAR sensor must not steer the panels
        else corr = clamp(ratio, 0.7, 1.3);
      }
      const r = search(sun, irr, sen.T, corr, sr.s, ws);
      const pmx = Math.max(...r.ev.map(x => x.pv), 1e-9), cmx = Math.max(...r.ev.map(x => x.crop), 1e-9), Jof = x => w * x.pv / pmx + (1 - w) * x.crop / cmx;
      let a = r.best.a, held = false;                         // hysteresis: keep the present angle unless the best angle is clearly better (protects the motor)
      if (st.angle != null && prev >= lo && prev <= hi) { const Jc = Jof(evalAngle(prev, sun, irr, sen.T, corr, sr.s, ws)); if (Jof(r.best) - Jc < hyst) { a = prev; held = true; } }
      const d = a - prev;
      if (Math.abs(d) > maxStep) a = prev + Math.sign(d) * maxStep;
      a = clamp(Math.round(a * 2) / 2, lo, hi);
      out.mode = 'OPTIMISE'; out.angle = a; out.corr = corr; out.lsrMeas = lsrMeas; out.lsrModel = cur.lsr; out.best = r.best; out.target = r.best.a;
      const pvMaxC = Math.max(...r.ev.map(x => x.pv), 1e-9), cropMaxC = Math.max(...r.ev.map(x => x.crop), 1e-9); out.pvRel = r.best.pv / pvMaxC; out.cropRel = cropMaxC > 1e-6 ? r.best.crop / cropMaxC : null;
      out.held = held; out.reason = (held ? 'HOLD (gain < ' + (100 * hyst).toFixed(0) + ' %), ' : '') + 'J-best ' + r.best.a.toFixed(1) + ' deg (PV ' + (100 * out.pvRel).toFixed(0) + ' % of max, ' + (out.cropRel == null ? 'no crop in season: electricity only' : 'crop ' + (100 * out.cropRel).toFixed(0) + ' % of max') + '); stress ' + sr.s.toFixed(2) + '; PAR correction x' + corr.toFixed(2) + (out.fault ? '; FAULT: ' + out.fault : '');
      return out;
    }
    function fuse(list) {                                    // median of several readings per channel (filters the noise of DHT11, PAR, pyranometer, soil)
      const med = k => { const v = list.map(x => x[k]).filter(x => x != null && isFinite(x)).sort((p, q) => p - q); return v.length ? (v.length % 2 ? v[(v.length - 1) / 2] : (v[v.length / 2 - 1] + v[v.length / 2]) / 2) : null; };
      const o = Object.assign({}, list[list.length - 1]); ['ghi', 'parUm', 'parRatio', 'T', 'RH', 'soil', 'wind'].forEach(k => { const m = med(k); if (m != null) o[k] = m; });
      o.rain = list.filter(x => x.rain).length * 2 > list.length; return o;
    }
    /* ---------------- controller safety: sensor-failure fallbacks (rain, soil), motor wear count, limits on how often the panels may move ---------------- */
    function makeSafe(cfg) {
      cfg = Object.assign({ minHoldS: 120, maxMovesPerHour: 12, maxTravelPerDay: 900, soilJump: 40, soilStuckS: 3 * 3600, rainStuckS: 1800, armM: 0.44, drumDiaM: 0.12 }, cfg || {});
      const drumC = Math.PI * cfg.drumDiaM, wireAt = th => cfg.armM * 1000 * Math.sin((th - 45) * Math.PI / 180);
      function fresh(angle) { return { angle: angle == null ? lo : angle, lastMoveT: -1e9, moveTimes: [], dayTravel: {}, moves: 0, reversals: 0, lastDir: 0, travelDeg: 0, wireMm: 0, rainWetSince: null, lastRainT: -1e9, soilLast: null, soilLastT: null, soilSameSince: null, soilSameKey: null, faults: {}, held: 0, fallbackSoil: 0, fallbackRain: 0 }; }
      function step(sen, st) {
        const t = sen.t != null ? sen.t : (sen.day * 24 + sen.hour) * 3600, notes = [], s2 = Object.assign({}, sen); const day = Math.floor(t / 86400);
        const sun = S.sunVec(clim.lat, sen.day, sen.hour), clear = sun.sz > 0.02 ? S.irradiance(sun.sz, sen.day, 0.85).ghi : 0, up = clear > 100;
        // ---- soil probe: range, jump, stuck; fallback = water-balance model estimate (sen.soilModel) else the last good value else 50 %
        let bad = null; const key = sen.soilRaw != null ? String(sen.soilRaw) : (sen.soil != null && isFinite(sen.soil) ? sen.soil.toFixed(1) : 'nan');
        if (sen.soil == null || !isFinite(sen.soil)) bad = 'no reading'; else if (sen.soil < 0 || sen.soil > 100) bad = 'reading out of range (' + sen.soil.toFixed(0) + ' %)';
        else if (st.soilLast != null && t - st.soilLastT <= 3600 && Math.abs(sen.soil - st.soilLast) > cfg.soilJump && t - st.lastRainT > 3600 && !sen.irrigating) bad = 'jump of ' + Math.abs(sen.soil - st.soilLast).toFixed(0) + ' points in under an hour';
        if (sen.soilRaw == null) { st.soilSameKey = null; } else if (st.soilSameKey === key) { if (up && st.soilSameSince != null && t - st.soilSameSince >= cfg.soilStuckS) bad = bad || 'stuck at the same value for ' + ((t - st.soilSameSince) / 3600).toFixed(1) + ' h'; } else { st.soilSameKey = key; st.soilSameSince = t; }
        if (bad) { const est = sen.soilModel != null && isFinite(sen.soilModel) ? sen.soilModel : (st.soilLast != null ? st.soilLast : 50); s2.soil = est; st.fallbackSoil++; notes.push('SOIL PROBE FAULT (' + bad + '): using ' + (sen.soilModel != null ? 'the water-balance model' : 'the last good value') + ' ' + est.toFixed(0) + ' %'); st.faults.soil = bad; } else { st.soilLast = sen.soil; st.soilLastT = t; delete st.faults.soil; }
        // ---- rain sensor: stuck wet in dry sunny air is ignored; a dead-dry sensor is backed up by the rain forecast / model when the air is saturated and the sun is gone
        let rain = !!sen.rain;
        if (rain) { st.lastRainT = t; if (st.rainWetSince == null) st.rainWetSince = t;
          const implausible = sen.ghi > 0.6 * clear && clear > 300 && sen.RH < 65;                       // wet plate under strong sun and dry air
          if (implausible && t - st.rainWetSince >= cfg.rainStuckS) { rain = false; st.fallbackRain++; st.faults.rain = 'wet for ' + ((t - st.rainWetSince) / 60).toFixed(0) + ' min in dry sunny air'; notes.push('RAIN SENSOR FAULT (stuck wet in dry sunny air, RH ' + sen.RH.toFixed(0) + ' %): ignored, panels keep tracking'); }
          else if (!implausible) delete st.faults.rain;
        } else { st.rainWetSince = null; if (sen.rainForecast && sen.RH >= 90 && clear > 100 && sen.ghi < 0.2 * clear) { rain = true; st.fallbackRain++; notes.push('RAIN FALLBACK: sensor dry but rain forecast, RH ' + sen.RH.toFixed(0) + ' % and sky dark: flat roof'); } else delete st.faults.rain; }
        s2.rain = rain;
        const before = st.angle; st.angle = before; const d = decide(s2, st);
        // ---- limits on how often the panels may move (safety modes STOW and RAIN are exempt)
        const exempt = d.mode === 'STOW' || d.mode === 'RAIN' || d.mode === 'NIGHT'; let a = d.angle; const delta = Math.abs(a - before);
        if (delta >= 0.5 && !exempt) { st.moveTimes = st.moveTimes.filter(x => t - x < 3600); const dt = st.dayTravel[day] || 0; let why = null;
          if (t - st.lastMoveT < cfg.minHoldS) why = 'hold: moved ' + Math.round(t - st.lastMoveT) + ' s ago (minimum ' + cfg.minHoldS + ' s)'; else if (st.moveTimes.length >= cfg.maxMovesPerHour) why = 'hold: ' + st.moveTimes.length + ' moves in the last hour (limit ' + cfg.maxMovesPerHour + ')'; else if (dt + delta > cfg.maxTravelPerDay) why = 'hold: daily travel limit ' + cfg.maxTravelPerDay + ' deg reached';
          if (why) { a = before; st.held++; d.limit = why; notes.push('MOVE LIMIT (' + why + ')'); d.angle = a; } }
        // ---- wear count
        const mv = Math.abs(a - before); if (mv >= 0.25) { st.moves++; st.travelDeg += mv; st.dayTravel[day] = (st.dayTravel[day] || 0) + mv; st.wireMm += Math.abs(wireAt(Math.min(90, a)) - wireAt(Math.min(90, before))); const dir = Math.sign(a - before); if (st.lastDir && dir !== st.lastDir) st.reversals++; st.lastDir = dir; st.lastMoveT = t; st.moveTimes.push(t); }
        st.angle = a; d.safety = { notes, faults: Object.assign({}, st.faults), moves: st.moves, travelDeg: st.travelDeg, wireM: st.wireMm / 1000, drumTurns: st.wireMm / 1000 / drumC, reversals: st.reversals, heldMoves: st.held, soilFallbacks: st.fallbackSoil, rainFallbacks: st.fallbackRain, todayTravelDeg: st.dayTravel[day] || 0, movesLastHour: st.moveTimes.length, cfg };
        if (notes.length) d.reason = notes.join('; ') + (d.reason ? '; ' + d.reason : ''); return d;
      }
      return { step, fresh, cfg };
    }

    return { decide, fuse, makeSafe, setDay, seasonWeights: seas, evalAngle, irrFrom, stressOf, vpdOf, search, UM_PER_W };
  }
  const API = { make, UM_PER_W };
  if (typeof module !== 'undefined' && module.exports) module.exports = API; else root.SRMC_SC = API;
})(typeof window !== 'undefined' ? window : globalThis);
