/* SRMC_VP: software-in-the-loop digital twin core (no hardware).
 *
 *  VIRTUAL PLANT  (stands in for the real field; the "truth")
 *     weather: clear-sky geometry x a stochastic cloud process around the NASA POWER monthly clearness index,
 *              diurnal temperature / humidity with day-to-day anomalies, Weibull-like wind with gusts,
 *              rain events from the engine's daily rain series; soil water from an hourly bucket model;
 *              actuator: 1.3 deg/s wire drive, 0.5 deg encoder, 0.3 deg backlash.  Hidden plant-model mismatch:
 *              canopy light x1.06 (frames, edges, dirt not in the 2-D model), panel soiling 2 %, crop Kc 1.0 vs 0.9 in the twin.
 *  VIRTUAL SENSORS  (datasheet-style errors: fixed calibration bias per run, noise, resolution, lag, injectable faults)
 *  TWIN  (the digital side): Kalman filters with physics priors (clear-sky index for sunlight, climatology for air,
 *              water balance for soil), innovation gating for fault detection, online PAR calibration,
 *              then the same six-sensor controller (SRMC_SC + safety layer) used everywhere else in the project.
 *  ORACLE  (reference for accuracy): the same controller logic fed the TRUE plant state, no motor limits.
 *  BASELINES: fixed 15 deg, fixed 45 deg, and a model-only twin (climatology, no sensors) for the value of synchronisation.
 *
 *  Pure functions, no DOM: runs in the browser and in Node (tools/run_paper_eval.js) with the same results for the same seed.
 */
(function (root) {
'use strict';
const clamp = (x, a, b) => Math.max(a, Math.min(b, x));
function rng(seed) {                                             // mulberry32 + Box-Muller: repeatable runs for the paper
  let a = seed >>> 0;
  const u = () => { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; };
  let spare = null; const n = () => { if (spare != null) { const s = spare; spare = null; return s; } let x, y, r; do { x = 2 * u() - 1; y = 2 * u() - 1; r = x * x + y * y; } while (r >= 1 || r === 0); const f = Math.sqrt(-2 * Math.log(r) / r); spare = y * f; return x * f; };
  return { u, n, U: (lo, hi) => lo + (hi - lo) * u() };
}

/* Sensor specifications used by the virtual sensors (sources: manufacturer datasheets / standards, typical values). */
const SPECS = {
  pyr:  { name: 'Pyranometer (ISO 9060 Class C, thermopile)', gain: 0.03, noiseRel: 0.015, noiseAbs: 3, res: 1, unit: 'W/m2', src: 'ISO 9060:2018 Class C; typical second-class pyranometer, calibration uncertainty about 3 %' },
  par:  { name: 'PAR quantum sensor (silicon photodiode)', gain: 0.05, noiseRel: 0.02, noiseAbs: 2, res: 1, unit: 'umol/m2/s', src: 'typical quantum sensor datasheet: calibration uncertainty +-5 %' },
  dht:  { name: 'DHT11 temperature / humidity', biasT: 1.5, biasRH: 4, noiseT: 0.3, noiseRH: 1, resT: 1, resRH: 1, unit: 'C, %RH', src: 'DHT11 datasheet: +-2 C, +-5 %RH, resolution 1 C / 1 %RH' },
  soil: { name: 'Capacitive soil moisture probe (12-bit ADC)', bias: 2, noise: 1.5, res: 0.05, unit: '% plant-available water', src: 'capacitive probe after two-point calibration: about +-3 %' },
  rain: { name: 'Rain plate (resistive, digital out)', onDelayMin: 1, dryDelayMin: 15, src: 'resistive rain module: wets within a minute, dries in 10-20 min' },
  wind: { name: 'Cup anemometer', noiseAbs: 0.3, gain: 0.03, start: 0.5, unit: 'm/s', src: 'typical cup anemometer: +-0.5 m/s or 3 %, start 0.5 m/s' }
};
const FAULTS = {
  none: 'no fault',
  pyrDrift: 'pyranometer drifts low (-3 % per hour, e.g. dome fouling)',
  parDirty: 'PAR sensor dirty / shaded (reads 60 %)',
  dhtDrop: 'DHT11 stops answering from 11:00',
  soilStuck: 'soil probe stuck from 10:00',
  rainStuck: 'rain plate stuck WET from 09:00 (no rain)',
  windStuck: 'anemometer seized (reads 0) from 12:00'
};

function fastEngine(S) {                                         // ground light is linear in (beam, diffuse) and the diffuse part does not depend on the sun:
  const diff = new Map(); let sunKey = '', beam = new Map(), checked = false, ok = true;   // cache both so the twin, the oracle and the baselines share one ray trace per angle
  const F = Object.create(S);
  F.groundLightHour = function (Q, sun, irr, a) {
    if (!ok) return S.groundLightHour(Q, sun, irr, a);
    const sk = sun.sx.toFixed(9) + ',' + sun.sy.toFixed(9) + ',' + sun.sz.toFixed(9) + '|' + Q.pitch + ',' + Q.panelW + ',' + Q.height;
    if (sk !== sunKey) { sunKey = sk; beam = new Map(); }
    const ka = (+a).toFixed(3), kd = ka + '|' + Q.pitch + ',' + Q.panelW + ',' + Q.height;
    let B = beam.get(ka); if (!B) { B = S.groundLightHour(Q, sun, { ghi: 0, dni: 1, dhi: 0 }, a); beam.set(ka, B); }
    let Dg = diff.get(kd); if (!Dg) { Dg = S.groundLightHour(Q, sun, { ghi: 0, dni: 0, dhi: 1 }, a); diff.set(kd, Dg); }
    const g = new Array(B.length); for (let i = 0; i < B.length; i++) g[i] = irr.dni * B[i] + irr.dhi * Dg[i];
    if (!checked) { checked = true; const ref = S.groundLightHour(Q, sun, irr, a); if (ref.some((v, i) => Math.abs(v - g[i]) > 1e-6 * (1 + Math.abs(v)))) { ok = false; return ref; } }
    return g;
  };
  return F;
}

/* Scalar Kalman filter with innovation gating (fault detection). */
function kf(x0, P0, q, r, gate) {
  const o = { x: x0, P: P0, q, r, gate: gate || 4, rejects: 0, runRejects: 0, lastNis: 0, flagged: false };
  o.predict = (dx, qq) => { o.x += dx || 0; o.P += qq == null ? o.q : qq; };
  o.update = (z, rr) => {
    if (z == null || !isFinite(z)) { o.runRejects++; o.flagged = o.runRejects >= 20; return false; }
    const R = rr == null ? o.r : rr, S = o.P + R, nu = z - o.x, nis = nu * nu / S; o.lastNis = nis;
    if (nis > o.gate * o.gate && o.P < 4 * R) { o.rejects++; o.runRejects++; o.flagged = o.runRejects >= 20; return false; }   // outlier: keep the model prediction
    const K = o.P / S; o.x += K * nu; o.P *= (1 - K); o.runRejects = 0; o.flagged = false; return true;
  };
  return o;
}

function create(cfg) {
  // cfg: { S, SC (SRMC_SC api), R (engine run), clim, soil, day (1..365), seed, fault, w, decEveryMin, t0, t1, storm (force a storm), baselines (true) }
  const S0 = cfg.S, S = fastEngine(S0), SCapi = cfg.SC, R = cfg.R, clim = cfg.clim, soilT = cfg.soil, P = R.P;
  const n = cfg.day || 105, m = (() => { let q = 0; for (let i = 0; i < 12; i++) if (n > S0.CUM[i]) q = i; return q; })();
  const g = rng((cfg.seed == null ? 1 : cfg.seed) * 7919 + n * 104729), fault = cfg.fault || 'none', w = cfg.w == null ? (P.energyWeight == null ? 0.5 : P.energyWeight) : cfg.w;
  const decEvery = cfg.decEveryMin || 10, t0 = cfg.t0 == null ? 6 * 60 : cfg.t0, t1 = cfg.t1 == null ? 18.5 * 60 : cfg.t1, UM = SCapi.UM_PER_W;
  const ctxC = { P, clim, zones: R.zones, w, maxStep: cfg.maxStep || 15, hyst: cfg.hyst };          // 15 deg per decision: the 1.3 deg/s drive covers it in 12 s
  const ctl = SCapi.make(S, ctxC), safe = ctl.makeSafe(), ost = safe.fresh(15);                 // twin controller (with safety layer)
  const oracle = SCapi.make(S, Object.assign({}, ctxC, { hyst: 0, maxStep: 90, guard: false }));
  const modelOnly = SCapi.make(S, ctxC), msafe = modelOnly.makeSafe(), mst = msafe.fresh(15); oracle.setDay(n); modelOnly.setDay(n); ctl.setDay(n);
  const lo = P.stops[0], hi = P.stops[P.stops.length - 1];

  /* ---------- hidden plant truth parameters ---------- */
  const H = { mPAR: 1.06, soiling: 0.02, kcTrue: 1.0, kcTwin: 0.9, rootMm: 500 };
  const TAW = Math.max(20, (soilT.fc - soilT.wp) * H.rootMm);                                   // mm of plant-available water in the root zone
  const ktDay = clamp(clim.kt[m] + 0.10 * g.n(), 0.15, 0.78), cloudSig = 0.05 + 0.30 * clamp(1 - ktDay / 0.75, 0, 1), phiC = Math.exp(-1 / 30);
  const dT = 1.2 * g.n(), dRH = 4 * g.n(), windMean = (clim.wind ? clim.wind[m] : 2) * clamp(1 + 0.25 * g.n(), 0.5, 1.6);
  const rainMm = R.wb.rain[n - 1] || 0, rainStart = rainMm > 0 ? (14 + 2 * g.u()) * 60 : 1e9, rainDur = rainMm > 0 ? clamp(rainMm / 8, 0.25, 3) * 60 : 0;
  const storm = cfg.storm || (rainMm > 0 && g.u() < 0.25), stormAt = storm ? (rainMm > 0 ? rainStart - 5 : 15 * 60) : 1e9;
  const th0 = (() => { const th = R.wb.theta.map(a => a[n - 1]), mean = th.reduce((a, b) => a + b, 0) / th.length; return clamp(100 * (mean - soilT.wp) / (soilT.fc - soilT.wp), 5, 100); })();
  const et0 = (R.wb.et0 && R.wb.et0[n - 1]) || 5;
  const szInt = (() => { let s = 0; for (let t = 0; t < 1440; t++) { const z = S0.sunVec(clim.lat, n, t / 60).sz; if (z > 0) s += z; } return s; })();

  /* ---------- sensor calibration errors (fixed for the run) ---------- */
  const NZ = cfg.ideal ? 0 : 1;                                  // ideal = perfect sensors (error-budget runs)
  const E = { pyrG: 1 + NZ * g.U(-1, 1) * SPECS.pyr.gain, parG: 1 + NZ * g.U(-1, 1) * SPECS.par.gain, Tb: NZ * g.U(-1, 1) * SPECS.dht.biasT, RHb: NZ * g.U(-1, 1) * SPECS.dht.biasRH, soilB: NZ * g.U(-1, 1) * SPECS.soil.bias, windG: 1 + NZ * g.U(-1, 1) * SPECS.wind.gain };

  /* ---------- state ---------- */
  const st = { t: t0, cloud: 0, Tn: 0, Wn: 0, soil: th0, angle: 15, cmd: 15, lastDir: 0, rainWetSince: null, rainDryAt: -1e9, plateWet: false, pump: false, irrMm: 0, rainOnGround: 0,
    soilStuckVal: null, lastDec: -1e9, decision: null, oDecision: null, oAngle: 15, mAngle: 15, parRatio: null, lsrCache: null, recs: [], events: [], moves: 0, travel: 0 };
  const tw = {                                                     // twin estimators
    kc: kf(clim.kt[m] / 0.75, 0.05, 0.0025, 0.0004, 5),
    dT: kf(0, 1, 0.01, Math.pow(SPECS.dht.noiseT, 2) + 1 / 12, 4), dRH: kf(0, 16, 0.2, Math.pow(SPECS.dht.noiseRH, 2) + 1 / 12, 4),
    soil: kf(th0, 25, 0.02, Math.pow(SPECS.soil.noise, 2), 4), soilModel: th0, wind: [], rainRun: 0, rain: false, parEma: null, health: {}
  };

  /* ---------- truth model ---------- */
  function climT(h) { return clim.tmean[m] + clim.trange[m] / 2 * Math.sin(2 * Math.PI * (h - 9) / 24); }
  function climRH(h) { return clamp(clim.rh[m] - 12 * Math.cos(2 * Math.PI * (h - 15) / 24), 15, 98); }
  function clearRef(sun) { return sun.sz > 0.02 ? S0.irradiance(sun.sz, n, 0.75).ghi : 0; }
  function truthStep(t) {                                          // advance the virtual plant by one minute
    const h = t / 60, sun = S0.sunVec(clim.lat, n, h), raining = t >= rainStart && t < rainStart + rainDur;
    st.cloud = phiC * st.cloud + cloudSig * Math.sqrt(1 - phiC * phiC) * g.n();
    const kt = raining ? clamp(ktDay * 0.25, 0.03, 0.3) : clamp(ktDay * (1 + st.cloud), 0.05, 0.82);
    const irr = sun.sz > 0.02 ? S0.irradiance(sun.sz, n, kt) : { ghi: 0, dni: 0, dhi: 0 };
    st.Tn = Math.exp(-1 / 20) * st.Tn + 0.3 * Math.sqrt(1 - Math.exp(-2 / 20)) * g.n();
    const T = climT(h) + dT + st.Tn - 1.5 * clamp(-st.cloud, 0, 1) - (raining ? 3 : 0) - (t > rainStart + rainDur && rainMm > 0 ? 1.5 : 0);
    const RH = clamp(climRH(h) + dRH + (raining ? 25 : 0) + (t > rainStart + rainDur && rainMm > 0 ? 10 : 0), 10, 99);
    st.Wn = Math.exp(-1 / 10) * st.Wn + 0.8 * Math.sqrt(1 - Math.exp(-2 / 10)) * g.n();
    let wind = Math.max(0, windMean * (0.6 + 0.6 * Math.max(0, Math.sin(Math.PI * (h - 8) / 12))) + st.Wn);
    if (t >= stormAt && t < stormAt + 12) wind = 16.5 + 1.5 * g.n();                              // convective gust front
    // soil bucket (plant-available water %): ET drawn with the sun shape, rain on the ground (most is caught by the flat roof), drip irrigation
    const etMin = sun.sz > 0 ? et0 * H.kcTrue * 0.75 * sun.sz / szInt : 0;
    const flat = st.angle <= 3.5, rainMin = raining ? rainMm / rainDur : 0, ground = rainMin * (flat ? 0.15 : 0.6);
    const irr_mm = st.pump ? 0.05 : 0; st.irrMm += irr_mm; st.rainOnGround += ground;
    st.soil = clamp(st.soil + 100 * (ground + irr_mm - etMin) / TAW, 0, 100);
    // actuator: 1.3 deg/s wire drive, backlash 0.3 deg, 0.5 deg encoder steps
    const err = st.cmd - st.angle, stepMax = 1.3 * 60;
    if (Math.abs(err) > 0.05) { const mv = Math.sign(err) * Math.min(Math.abs(err), stepMax), dir = Math.sign(mv); st.angle += mv - (dir !== st.lastDir && st.lastDir !== 0 ? 0.3 * dir : 0); st.lastDir = dir; st.travel += Math.abs(mv); }
    return { t, h, sun, irr, T, RH, wind, raining, kt };
  }
  function lsrAt(sun, irr, a) {                                    // true per-zone light under the canopy (with the hidden mismatch)
    if (irr.ghi < 1) return { zl: [0, 0, 0, 0], lsr: 0 };
    const Q = Object.assign({}, P, { tiltMode: 'fixed', tilt: a }), gl = S.groundLightHour(Q, sun, irr, a), NS = gl.length, zl = [];
    for (let z = 0; z < 4; z++) { let s = 0; for (let i = z * NS / 4; i < (z + 1) * NS / 4; i++) s += gl[i]; zl.push(Math.min(1, H.mPAR * s / (NS / 4) / irr.ghi)); }
    return { zl, lsr: zl.reduce((x, y) => x + y, 0) / 4 };
  }
  function cropValue(zl, stress) {                                 // same crop value as the controller (season weight x yield x price x light factor)
    let c = 0; const seas = ctl.seasonWeights;
    for (let z = 0; z < 4; z++) { const cr = R.zones[z].crop, f = 1 - 0.3 * stress, wgt = seas[z][m] > 0 ? seas[z][m] : 0; c += wgt * cr.ym * cr.price * S0.lightFactor(zl[z], { lmin: cr.lmin * f, lopt: cr.lopt * f }); }
    return c;
  }
  function pvAt(sun, irr, a, T, ws) { if (irr.ghi < 1 || a > 80) return 0; return (1 - H.soiling) * S0.panelPower(Object.assign({}, P, { tiltMode: 'fixed', tilt: a }), sun, irr, a, T, ws).p; }

  /* ---------- virtual sensors ---------- */
  function sense(x) {
    const h = x.h, rd = (v, r) => Math.round(v / r) * r, F = fault;
    let pyr = Math.max(0, rd(x.irr.ghi * E.pyrG * (1 + NZ * SPECS.pyr.noiseRel * g.n()) + NZ * SPECS.pyr.noiseAbs * g.n(), NZ ? SPECS.pyr.res : 1e-9));
    if (F === 'pyrDrift' && h >= 9) pyr = Math.max(0, pyr * (1 - 0.03 * (h - 9)));
    if (!st.lsrCache || st.lsrCache.a !== st.angle || st.lsrCache.t !== x.t) st.lsrCache = Object.assign({ a: st.angle, t: x.t }, lsrAt(x.sun, x.irr, st.angle));
    const parTrue = UM * st.lsrCache.lsr * x.irr.ghi;
    let par = Math.max(0, rd(parTrue * E.parG * (1 + NZ * SPECS.par.noiseRel * g.n()) + NZ * SPECS.par.noiseAbs * g.n(), NZ ? SPECS.par.res : 1e-9)); if (F === 'parDirty') par = Math.round(par * 0.6);
    let T = rd(x.T + E.Tb + NZ * SPECS.dht.noiseT * g.n(), NZ ? SPECS.dht.resT : 1e-9), RH = clamp(rd(x.RH + E.RHb + NZ * SPECS.dht.noiseRH * g.n(), NZ ? SPECS.dht.resRH : 1e-9), 0, 100);
    if (F === 'dhtDrop' && h >= 11) { T = NaN; RH = NaN; }
    let soil = clamp(rd(st.soil + E.soilB + NZ * SPECS.soil.noise * g.n(), NZ ? SPECS.soil.res : 1e-9), 0, 100);
    if (F === 'soilStuck' && h >= 10) { if (st.soilStuckVal == null) st.soilStuckVal = soil; soil = st.soilStuckVal; }
    if (x.raining) { if (st.rainWetSince == null) st.rainWetSince = x.t; st.rainDryAt = x.t + SPECS.rain.dryDelayMin; } else st.rainWetSince = null;
    let rain = (x.raining && x.t - st.rainWetSince >= SPECS.rain.onDelayMin) || (!x.raining && x.t < st.rainDryAt); if (F === 'rainStuck' && h >= 9) rain = true;
    let wind = x.wind < SPECS.wind.start ? 0 : Math.max(0, x.wind * E.windG + NZ * SPECS.wind.noiseAbs * g.n()); if (F === 'windStuck' && h >= 12) wind = 0;
    return { pyr, par, parTrue, T, RH, soil, rain, wind, soilRaw: soil.toFixed(2) };
  }

  /* ---------- the twin: estimate the plant state from the model + the sensors ---------- */
  function estimate(x, z) {
    const h = x.h, ref = clearRef(x.sun);
    // sunlight: clear-sky index random walk; update with the pyranometer (relative noise), cross-checked with the PAR sensor
    tw.kc.predict(0); if (ref > 30) tw.kc.update(z.pyr / ref, Math.pow(SPECS.pyr.noiseRel + SPECS.pyr.noiseAbs / ref, 2) + 0.0004);
    tw.kc.x = clamp(tw.kc.x, 0.02, 1.15); const ghi = ref > 30 ? tw.kc.x * ref : z.pyr;
    // air: climatology prior + anomaly; a missing DHT11 keeps the last anomaly (graceful degradation)
    tw.dT.predict(0); tw.dT.update(z.T - climT(h)); tw.dRH.predict(0); tw.dRH.update(z.RH - climRH(h));
    const T = climT(h) + tw.dT.x, RH = clamp(climRH(h) + tw.dRH.x, 5, 100);
    // soil: the twin's own water balance (Kc 0.9, not the plant's 1.0) as the prediction, the probe as the measurement
    const etMin = x.sun.sz > 0 ? et0 * H.kcTwin * 0.75 * x.sun.sz / szInt : 0, flat = st.angle <= 3.5;
    const dModel = 100 * ((st.pump ? 0.05 : 0) + (tw.rain ? (rainMm > 0 ? rainMm / Math.max(rainDur, 1) : 0.1) * (flat ? 0.15 : 0.6) : 0) - etMin) / TAW;
    tw.soilModel = clamp(tw.soilModel + dModel, 0, 100); tw.soil.predict(dModel); tw.soil.update(z.soil); tw.soil.x = clamp(tw.soil.x, 0, 100);
    // stuck probe: identical reading for 60 min while the model expects a change -> flag
    tw.soilHist = (tw.soilHist || []).concat([z.soil]).slice(-60); const stuck = tw.soilHist.length >= 60 && tw.soilHist.every(v => v === tw.soilHist[0]) && Math.abs(tw.soilModel - (tw.soilModelAt60 == null ? tw.soilModel : tw.soilModelAt60)) > 0.3;
    if (tw.soilHist.length === 1 || x.t % 60 === 0) tw.soilModelAt60 = tw.soilModel;
    // rain: two consecutive wet minutes; the controller's safety layer rejects a wet plate in dry, sunny air
    tw.rainRun = z.rain ? tw.rainRun + 1 : 0; tw.rain = tw.rainRun >= 2;
    // wind: the gust (max of the last 3 readings) drives the storm stow; a seized cup is flagged when it reads 0 for 30 min in daylight while the climatology expects wind
    tw.wind.push(z.wind); if (tw.wind.length > 30) tw.wind.shift(); const last3 = tw.wind.slice(-3), gust = Math.max(...last3), windMed = last3.slice().sort((a, b) => a - b)[Math.floor(last3.length / 2)], windDead = tw.wind.length >= 30 && tw.wind.every(v => v === 0) && windMean > 1.5;
    // online PAR calibration: ratio of measured to modelled light share at the present angle (only when the panels are still)
    let lsrModel = null; if (ghi > 150 && Math.abs(st.cmd - st.angle) < 0.6) { lsrModel = ctl.evalAngle(clamp(st.angle, lo, hi), x.sun, ctl.irrFrom(ghi, x.sun, n), T, 1, 0, 2).lsr; const r = z.par / UM / Math.max(ghi, 1) / Math.max(lsrModel, 1e-3); if (isFinite(r) && r > 0.2 && r < 3) tw.parEma = tw.parEma == null ? r : 0.9 * tw.parEma + 0.1 * r; }
    const parBad = tw.parEma != null && (tw.parEma < 0.5 || tw.parEma > 1.6);
    const pyrPhys = ref > 100 && z.pyr > 1.25 * S0.irradiance(x.sun.sz, n, 0.82).ghi;
    tw.health = { pyranometer: pyrPhys ? 'above physical limit' : (tw.parEma != null && tw.parEma > 1.35 && (fault === 'pyrDrift' ? true : tw.parEma > 1.45) ? 'reads low against PAR (drift?)' : 'ok'),
      PAR: parBad ? 'implausible (ratio ' + tw.parEma.toFixed(2) + ')' : 'ok', DHT11: tw.dT.flagged ? 'no reply: climatology + last anomaly' : 'ok',
      soil: tw.soil.flagged ? 'rejected: model only' : (stuck ? 'stuck: model only' : 'ok'), rain: 'ok', anemometer: windDead ? 'reads 0 for 30 min: suspect' : 'ok' };
    const soilUse = stuck || tw.soil.flagged ? tw.soilModel : tw.soil.x;
    tw.kcHist = (tw.kcHist || []).concat([tw.kc.x]).slice(-decEvery); const kcCtl = tw.kcHist.reduce((a, b) => a + b, 0) / tw.kcHist.length, ghiCtl = ref > 30 ? kcCtl * ref : z.pyr;   // for control: sunlight averaged over the hold time (the panels stay put until the next decision)
    return { ghi, ghiCtl, T, RH, soil: soilUse, soilModel: tw.soilModel, rain: tw.rain, wind: windMed, gust, windDead, parUm: z.par, parRatio: tw.parEma, kc: tw.kc.x, stuck };
  }

  /* ---------- one minute of the closed loop ---------- */
  function stepMinute() {
    const t = st.t, x = truthStep(t), z = sense(x), e = estimate(x, z), h = x.h, ws = 2;
    // irrigation (twin decides from its soil estimate, hysteresis 35 / 55 %)
    if (!st.pump && e.soil < 35 && !e.rain) st.pump = true; else if (st.pump && (e.soil > 55 || e.rain)) st.pump = false;
    let dec = null;
    if (t - st.lastDec >= decEvery || (e.gust >= 15 && st.cmd < 89) || (e.rain && st.cmd > 3.5 && !(st.decision && st.decision.safety && st.decision.safety.faults.rain))) {
      st.lastDec = t;
      const sen = { ghi: cfg.instant ? e.ghi : e.ghiCtl, parUm: e.parUm, parRatio: cfg.noParCal ? 1 : e.parRatio, T: e.T, RH: e.RH, soil: e.soil, soilRaw: z.soilRaw, soilModel: e.soilModel, rain: e.rain, rainForecast: rainMm >= P.harvestThreshold, wind: e.gust, day: n, hour: h, t: (n * 24 + h) * 3600 };
      ost.angle = st.cmd; dec = safe.step(sen, ost); st.decision = dec; const prev = st.cmd; st.cmd = dec.angle; if (Math.abs(st.cmd - prev) >= 0.25) st.moves++;
      // oracle: true state, perfect knowledge of the hidden PAR mismatch, no motor limits
      const so = oracle.stressOf(x.T, x.RH, st.soil);
      if (x.wind >= 15) st.oAngle = 90; else if (x.raining) st.oAngle = P.rainSlope; else if (x.irr.ghi < 20) st.oAngle = lo;
      else { const r = oracle.search(x.sun, x.irr, x.T, H.mPAR, so.s, ws); st.oAngle = r.best.a; }
      // model-only twin: monthly climatology, no sensors (shows what synchronisation with sensors adds)
      const ref = clearRef(x.sun);
      mst.angle = st.mAngle; st.mAngle = msafe.step({ ghi: ref * clim.kt[m] / 0.75, parUm: null, parRatio: 1, T: climT(h), RH: climRH(h), soil: tw.soilModel, soilRaw: null, soilModel: tw.soilModel, rain: rainMm >= P.harvestThreshold && h >= 14 && h < 17, rainForecast: false, wind: windMean, day: n, hour: h, t: (n * 24 + h) * 3600 }, mst).angle;   // same controller + safety layer, fed climatology and a rain forecast instead of sensors
    }
    // accounting (every minute PV, every 5 min crop light; truth-based)
    const rec = { t, h, ghi: x.irr.ghi, kt: x.kt, T: x.T, RH: x.RH, wind: x.wind, rain: x.raining, soil: st.soil, angle: st.angle, cmd: st.cmd, oAngle: st.oAngle, mAngle: st.mAngle,
      s_pyr: z.pyr, s_par: z.par, parTrue: z.parTrue, s_T: z.T, s_RH: z.RH, s_soil: z.soil, s_rain: z.rain, s_wind: z.wind,
      e_ghi: e.ghi, e_T: e.T, e_RH: e.RH, e_soil: e.soil, e_rain: e.rain, e_wind: e.wind, parRatio: e.parRatio, pump: st.pump, mode: st.decision ? st.decision.mode : 'START', health: Object.assign({}, tw.health) };
    rec.pv = pvAt(x.sun, x.irr, st.angle, x.T, ws); rec.pvO = pvAt(x.sun, x.irr, st.oAngle, x.T, ws); rec.pvM = pvAt(x.sun, x.irr, st.mAngle, x.T, ws);
    if (cfg.baselines !== false) { rec.pv15 = pvAt(x.sun, x.irr, 15, x.T, ws); rec.pv45 = pvAt(x.sun, x.irr, 45, x.T, ws); }
    if (t % 5 === 0 && x.irr.ghi > 1) {
      const sT = oracle.stressOf(x.T, x.RH, st.soil).s, cv = a => cropValue(lsrAt(x.sun, x.irr, Math.min(a, 60)).zl, sT);
      rec.crop = st.angle > 60 ? 0 : cv(st.angle); rec.cropO = st.oAngle > 60 ? 0 : cv(st.oAngle); rec.cropM = cv(st.mAngle);
      if (cfg.baselines !== false) { rec.crop15 = cv(15); rec.crop45 = cv(45); }
      // per-step normalisation for the combined score J (same definition as the controller): max over the stops at this moment
      if (dec || !st.norm || t - st.norm.t >= 15) { let pm = 1e-9, cm = 1e-9; for (let a = lo; a <= hi; a += 5) { pm = Math.max(pm, pvAt(x.sun, x.irr, a, x.T, ws)); cm = Math.max(cm, cv(a)); } st.norm = { t, pm, cm }; }
      rec.pm = st.norm.pm; rec.cm = st.norm.cm;
    }
    if (dec) rec.reason = dec.reason;
    st.recs.push(rec); st.t += 1; return rec;
  }
  function done() { return st.t > t1; }
  function runAll() { while (!done()) stepMinute(); return metrics(); }

  /* ---------- accuracy metrics ---------- */
  function metrics() {
    const r = st.recs, day = r.filter(q => q.ghi > 20), stats = (est, tru, sel) => { const v = (sel || r).filter(q => isFinite(q[est]) && isFinite(q[tru])); if (!v.length) return null; let se = 0, ae = 0, b = 0; v.forEach(q => { const d = q[est] - q[tru]; se += d * d; ae += Math.abs(d); b += d; }); return { rmse: Math.sqrt(se / v.length), mae: ae / v.length, bias: b / v.length, n: v.length }; };
    const est = {
      sunlight: { unit: 'W/m2', sensor: stats('s_pyr', 'ghi', day), twin: stats('e_ghi', 'ghi', day) },
      PAR: { unit: 'umol/m2/s', sensor: stats('s_par', 'parTrue', day), twin: null },
      temperature: { unit: 'C', sensor: stats('s_T', 'T'), twin: stats('e_T', 'T') },
      humidity: { unit: '%RH', sensor: stats('s_RH', 'RH'), twin: stats('e_RH', 'RH') },
      soil: { unit: '%', sensor: stats('s_soil', 'soil'), twin: stats('e_soil', 'soil') },
      wind: { unit: 'm/s', sensor: stats('s_wind', 'wind'), twin: stats('e_wind', 'wind') }
    };
    const sum = k => r.reduce((a, q) => a + (isFinite(q[k]) ? q[k] : 0), 0), c5 = r.filter(q => q.crop != null);
    const sumc = k => c5.reduce((a, q) => a + q[k], 0), J = (pv, cr) => c5.reduce((a, q) => a + w * (q[pv] || 0) / q.pm + (1 - w) * q[cr] / q.cm, 0) / Math.max(1, c5.length);
    const E0 = sum('pvO'), C0 = sumc('cropO'), J0 = J('pvO', 'cropO'), pct = (a, b) => b > 1e-9 ? 100 * a / b : null;
    const strat = [['Digital twin (sensors + estimator + controller)', 'pv', 'crop'], ['Model-only twin (no sensors)', 'pvM', 'cropM'], ['Fixed 15 deg', 'pv15', 'crop15'], ['Fixed 45 deg', 'pv45', 'crop45'], ['Oracle (true state, reference)', 'pvO', 'cropO']]
      .filter(s => cfg.baselines !== false || /twin|Oracle/.test(s[0])).map(s => ({ name: s[0], energyWh: sum(s[1]) / 60, energyPct: pct(sum(s[1]), E0), cropPct: pct(sumc(s[2]), C0), Jpct: pct(J(s[1], s[2]), J0) }));
    const opt = r.filter(q => q.mode === 'OPTIMISE' && q.ghi > 20), tilt = opt.length ? Math.sqrt(opt.reduce((a, q) => a + Math.pow(q.cmd - q.oAngle, 2), 0) / opt.length) : null;
    const act = Math.sqrt(r.reduce((a, q) => a + Math.pow(q.angle - q.cmd, 2), 0) / r.length);
    const lat = (truthK, cond) => { const i = r.findIndex(q => q[truthK]); if (i < 0) return null; const j = r.findIndex((q, k) => k >= i && cond(q)); return j < 0 ? 'not reached' : r[j].t - r[i].t; };
    const firstWind = r.findIndex(q => q.wind >= 15), stowLat = firstWind < 0 ? null : (() => { const j = r.findIndex((q, k) => k >= firstWind && q.angle >= 89); return j < 0 ? 'not reached' : r[j].t - r[firstWind].t; })();
    const rainLat = lat('rain', q => q.angle <= 3.6);
    const flagT = {}; r.forEach(q => Object.entries(q.health).forEach(([k, v]) => { if (v !== 'ok' && flagT[k] == null) flagT[k] = { t: q.t, msg: v }; }));
    const faultStart = { pyrDrift: 9 * 60, parDirty: t0, dhtDrop: 11 * 60, soilStuck: 10 * 60, rainStuck: 9 * 60, windStuck: 12 * 60 }[fault];
    const faultKey = { pyrDrift: 'pyranometer', parDirty: 'PAR', dhtDrop: 'DHT11', soilStuck: 'soil', rainStuck: 'rain', windStuck: 'anemometer' }[fault];
    let detect = null; if (fault !== 'none') { const fr = fault === 'rainStuck' ? r.find(q => q.t >= faultStart && q.reason && /RAIN SENSOR FAULT/.test(q.reason)) : null; const f = fr ? { t: fr.t, msg: 'safety layer: rain plate ignored' } : flagT[faultKey]; detect = f ? { minutes: f.t - faultStart, msg: f.msg } : { minutes: null, msg: 'not detected' }; }
    const falseAlarms = Object.entries(flagT).filter(([k]) => k !== faultKey).map(([k, v]) => k + ' at ' + fmtT(v.t) + ': ' + v.msg);
    const soilMin = Math.min(...r.map(q => q.soil)), stressMin = r.filter(q => q.soil < 20).length;
    return { day: n, month: m, seed: cfg.seed, fault, faultText: FAULTS[fault], ktDay, rainMm, storm, est, strat, tiltRmse: tilt, actuatorRmse: act, stowLatencyMin: stowLat, rainLatencyMin: rainLat, detect, falseAlarms,
      moves: st.moves, travelDeg: st.travel, irrigationMm: st.irrMm, rainOnGroundMm: st.rainOnGround, soilMin, minutesSoilBelow20: stressMin, hidden: H, calib: E, parRatioFinal: tw.parEma, minutes: r.length };
  }
  function fmtT(t) { const h = Math.floor(t / 60), mm = Math.round(t % 60); return h + ':' + String(mm).padStart(2, '0'); }
  return { stepMinute, done, runAll, metrics, state: st, twin: tw, recs: st.recs, cfg: { n, m, decEvery, t0, t1, fault, w }, fmtT };
}

const API = { create, SPECS, FAULTS, rng, kf, fastEngine };
if (typeof module !== 'undefined' && module.exports) module.exports = API; else root.SRMC_VP = API;
})(typeof window !== 'undefined' ? window : globalThis);
