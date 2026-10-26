/* SRMC simulation engine — pure functions, no DOM. Works in browser and node.
 * Same equations are implemented in matlab/srmc_engine.m and cross-checked (tools/crosscheck).
 * Geometry: panel rows run North-South; cross-section is the East-West (x) / vertical (z) plane.
 */
(function (root) {
'use strict';
const D2R = Math.PI / 180;
const DIM = [31,28,31,30,31,30,31,31,30,31,30,31];
const CUM = [0,31,59,90,120,151,181,212,243,273,304,334];
const MID = [17,47,75,105,135,162,198,228,258,288,318,344];   // representative day of year per month
const MNAME = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];

const DEFAULTS = {
  // geometry (metres)
  bayLen: 12.5,        // pole spacing along rows (array spacing)
  pitch: 3.125,        // row-to-row distance (12.5 m bay / 4 rows) = continuous sealed catchment
  panelW: 3.122,        // panel row width (across the span)
  height: 5.2,         // pivot-axis height (guideline pole height 5.2 m)
  tiltMode: 'smart',   // 'smart' (SRMC-DT controller picks the tilt stop per time window) | 'fixed' (one stop-bolt angle) | 'track' (E-W tracking, research option)
  stops: [15, 20, 25, 30, 35, 40, 45, 50, 55, 60],   // wire-spec tilt stops (deg); flat = 0 in rain
  windows: Array.from({ length: 14 }, (_, i) => [5 + i, 6 + i]),   // hourly controller decisions (solar hours 5-19); motor re-positions each hour
  rainSlope: 3,        // flat/rain mode keeps a small fall (deg) towards the gutter
  farmerShare: 0.3,    // share of the industry's PPA payment that goes to the farmer
  angleStep: 0.5,      // motor/encoder angle resolution in degrees (coarse stops are refined to this step)
  energyWeight: 0.5,   // controller objective: w*PV + (1-w)*crop light value, both normalised to 0..1
  schedule: null,
  tilt: 45,            // deg, used when tiltMode = 'fixed' (positive = tilts to east)
  tiltMax: 60,         // deg, max tracking tilt
  // PV
  eff: 0.21, gamma: -0.004, noct: 45, sysLoss: 0.14,
  // rain harvest
  runoff: 0.85, firstFlush: 0.5, harvestThreshold: 5, tankM3: 300, irrEff: 0.9,
  // soil regeneration
  year: 0,
  // economics (editable assumptions, INR)
  capexPerKWp: 60000, tariff: 3.0, omPct: 0.015, cisternPerM3: 7000, subsidyPct: 0
};

/* ---------------- solar geometry & irradiance ---------------- */
function declination(n) { return 23.45 * Math.sin(D2R * 360 / 365 * (284 + n)); }
function sunVec(latDeg, n, hour) {            // hour = solar time, 12 = noon
  const d = declination(n) * D2R, ph = latDeg * D2R, w = 15 * (hour - 12) * D2R;
  const sz = Math.sin(ph) * Math.sin(d) + Math.cos(ph) * Math.cos(d) * Math.cos(w);
  const sx = -Math.cos(d) * Math.sin(w);                                   // east
  const sy = Math.sin(d) * Math.cos(ph) - Math.cos(d) * Math.cos(w) * Math.sin(ph); // north
  return { sx, sy, sz };
}
function extraterrestrialDaily(latDeg, n) {   // MJ/m2/day (FAO-56)
  const ph = latDeg * D2R, d = declination(n) * D2R;
  const dr = 1 + 0.033 * Math.cos(2 * Math.PI * n / 365);
  const x = Math.max(-1, Math.min(1, -Math.tan(ph) * Math.tan(d)));
  const ws = Math.acos(x);
  return 24 * 60 / Math.PI * 0.0820 * dr * (ws * Math.sin(ph) * Math.sin(d) + Math.cos(ph) * Math.cos(d) * Math.sin(ws));
}
function erbs(kt) {
  if (kt <= 0.22) return 1 - 0.09 * kt;
  if (kt <= 0.8) return 0.9511 - 0.1604 * kt + 4.388 * kt * kt - 16.638 * kt ** 3 + 12.336 * kt ** 4;
  return 0.165;
}
function irradiance(sz, n, kt) {              // W/m2 on horizontal / beam normal / diffuse
  if (sz < 0.02) return { ghi: 0, dni: 0, dhi: 0 };
  const g0 = 1361 * (1 + 0.033 * Math.cos(2 * Math.PI * n / 365));
  const ghi = kt * g0 * sz, dhi = erbs(kt) * ghi;
  const dni = Math.min((ghi - dhi) / Math.max(sz, 0.1), 1000);
  return { ghi, dni, dhi };
}
function hargreavesET0(latDeg, n, tmean, trange) {   // mm/day
  const ra = extraterrestrialDaily(latDeg, n) / 2.45;
  return Math.max(0, 0.0023 * (tmean + 17.8) * Math.sqrt(Math.max(trange, 0.1)) * ra);
}

/* ---------------- canopy geometry (2-D cross-section) ---------------- */
function winIndex(P, hour) { const W = P.windows; for (let i = 0; i < W.length; i++) if (hour < W[i][1]) return i; return W.length - 1; }
function tiltFor(sun, P, m, hour) {
  if (P.tiltMode === 'rain') return P.rainSlope;
  if (P.tiltMode === 'fixed') return P.tilt;
  if (P.tiltMode === 'smart') { if (P.schedule && m != null && hour != null) return P.schedule[m][winIndex(P, hour)]; return P.tilt; }
  const a = Math.atan2(sun.sx, sun.sz) / D2R;           // E-W tracking
  return Math.max(-P.tiltMax, Math.min(P.tiltMax, a));
}
function segments(P, t, K) {                            // panel rows k=-K..K (periodic canopy); K grows for low sun so long shadows are not truncated
  const c = Math.cos(t * D2R), s = Math.sin(t * D2R), h = P.panelW / 2, out = [];
  K = K || 6; for (let k = -K; k <= K; k++) {
    const xc = k * P.pitch + P.pitch / 2;
    out.push({ k, x1: xc - h * c, z1: P.height + h * s, x2: xc + h * c, z2: P.height - h * s });
  }
  return out;
}
function rayBlocked(x0, z0, dx, dz, segs, skipK) {      // does ray from (x0,z0) along (dx,dz) hit a segment
  for (const g of segs) {
    if (g.k === skipK) continue;
    const ex = g.x2 - g.x1, ez = g.z2 - g.z1;
    const den = dx * ez - dz * ex;
    if (Math.abs(den) < 1e-12) continue;
    const qx = g.x1 - x0, qz = g.z1 - z0;
    const s = (qx * ez - qz * ex) / den, u = (qx * dz - qz * dx) / den;
    if (s > 1e-9 && u >= 0 && u <= 1) return true;
  }
  return false;
}
const SKY_ANG = (() => { const a = []; for (let i = 0; i < 24; i++) a.push(-90 + (i + 0.5) * 180 / 24); return a; })();
function groundSVF(x, segs) {                           // isotropic-sky view factor on ground, 2-D (cylindrical) geometry
  let vis = 0, tot = 0;
  for (const a of SKY_ANG) {
    const w = Math.cos(a * D2R); tot += w;
    if (!rayBlocked(x, 0, Math.sin(a * D2R), Math.cos(a * D2R), segs, null)) vis += w;
  }
  return vis / tot;
}
const NS = 40;                                          // ground samples across one pitch (10 per zone strip)
function rowsFor(P, sun) { return Math.min(60, Math.max(6, Math.ceil((P.height * Math.abs(sun.sx) / Math.max(sun.sz, 0.05) + P.panelW) / P.pitch) + 2)); }
function groundLightHour(P, sun, irr, t) {              // returns per-sample W/m2 on ground + sunlit flags
  const segs = segments(P, t, rowsFor(P, sun)), out = new Array(NS);
  for (let i = 0; i < NS; i++) {
    const x = (i + 0.5) / NS * P.pitch;
    const lit = !rayBlocked(x, 0, sun.sx, sun.sz, segs, null);
    out[i] = (lit ? irr.dni * sun.sz : 0) + irr.dhi * groundSVF(x, segs);
  }
  return out;
}
function panelShadeFraction(P, sun, t) {                // self-shading of a row by its neighbours
  const segs = segments(P, t, rowsFor(P, sun)), me = segs.find(s => s.k === 0); let sh = 0; const N = 8;
  for (let i = 0; i < N; i++) {
    const u = (i + 0.5) / N, x = me.x1 + u * (me.x2 - me.x1), z = me.z1 + u * (me.z2 - me.z1);
    if (rayBlocked(x, z + 1e-6, sun.sx, sun.sz, segs, 0)) sh++;
  }
  return sh / N;
}
function panelPower(P, sun, irr, t, tamb, ws) {            // Huld (2010) c-Si model as used by PVGIS + ASHRAE incidence-angle modifier
  const tr = t * D2R, nx = Math.sin(tr), nz = Math.cos(tr), w = ws == null ? 2 : ws;
  const cosI = Math.max(0, sun.sx * nx + sun.sz * nz), fs = panelShadeFraction(P, sun, t);
  const iam = cosI > 0.02 ? Math.max(0, 1 - 0.05 * (1 / cosI - 1)) : 0;
  const gpoa = irr.dni * cosI * iam * (1 - fs) + irr.dhi * (1 + Math.cos(tr)) / 2 * 0.95;
  if (gpoa < 1) return { p: 0, gpoa, tc: tamb };
  const tc = tamb + gpoa * Math.exp(-3.473 - 0.0594 * w), g = gpoa / 1000, T = tc - 25, lg = Math.log(g);
  const rel = 1 + -0.017237 * lg + -0.040465 * lg * lg + T * (-0.004702 + 0.000149 * lg + 0.000170 * lg * lg + 0.000005 * T);
  return { p: P.eff * gpoa * Math.max(0, rel) * (1 - P.sysLoss), gpoa, tc };
}

/* ---------------- monthly light & energy ---------------- */
function monthLight(P, clim, m, tiltOverride) {
  const n = MID[m], kt = clim.kt[m], lat = clim.lat;
  const zones = new Array(NS).fill(0); let open = 0, pvWh = 0, panelWh = 0, ghiWh = 0;
  const Q = Object.assign({}, P); if (tiltOverride != null) { Q.tiltMode = 'fixed'; Q.tilt = tiltOverride; }
  for (let hh = 0; hh < 24; hh++) {
    const hour = hh + 0.5, sun = sunVec(lat, n, hour);
    if (sun.sz < 0.02) continue;
    const irr = irradiance(sun.sz, n, kt), t = tiltFor(sun, Q, m, hour);
    const g = groundLightHour(Q, sun, irr, t);
    for (let i = 0; i < NS; i++) zones[i] += g[i];
    open += irr.ghi;
    const tamb = clim.tmean[m] + clim.trange[m] / 2 * Math.sin(2 * Math.PI * (hour - 9) / 24);
    const pp = panelPower(Q, sun, irr, t, tamb, clim.wind ? clim.wind[m] : 2);
    pvWh += pp.p; ghiWh += irr.ghi; panelWh += pp.gpoa;
  }
  const strip = [0, 1, 2, 3].map(z => zones.slice(z * NS / 4, (z + 1) * NS / 4).reduce((a, b) => a + b, 0) / (NS / 4) / Math.max(open, 1e-9));
  const profile = zones.map(v => v / Math.max(open, 1e-9));
  return { strip, profile, pvKWhPerM2Day: pvWh / 1000, ghiKWhPerM2Day: ghiWh / 1000, poaKWhPerM2Day: panelWh / 1000 };
}
function annualLight(P, clim, tiltOverride) {
  const months = []; for (let m = 0; m < 12; m++) months.push(monthLight(P, clim, m, tiltOverride));
  const pvKWhPerM2 = months.reduce((a, r, m) => a + r.pvKWhPerM2Day * DIM[m], 0);
  const ghi = months.reduce((a, r, m) => a + r.ghiKWhPerM2Day * DIM[m], 0);
  const meanStrip = [0, 1, 2, 3].map(z => months.reduce((a, r, m) => a + r.strip[z] * DIM[m], 0) / 365);
  return { months, pvKWhPerM2, ghi, meanStrip, meanLight: meanStrip.reduce((a, b) => a + b, 0) / 4 };
}


/* ---------------- SRMC-DT controller: two-position wire drive, tilt stop chosen per time window ---------------- */
function windowEval(P, clim, m, angle, win) {
  const n = MID[m], kt = clim.kt[m], zones = new Array(NS).fill(0); let open = 0, pv = 0, ghiDay = 0;
  const Q = Object.assign({}, P, { tiltMode: 'fixed', tilt: angle });
  for (let hh = 0; hh < 24; hh++) {
    const hour = hh + 0.5, sun = sunVec(clim.lat, n, hour); if (sun.sz < 0.02) continue;
    const irr = irradiance(sun.sz, n, kt); ghiDay += irr.ghi;
    if (hour < win[0] || hour >= win[1]) continue;
    const g = groundLightHour(Q, sun, irr, angle); for (let i = 0; i < NS; i++) zones[i] += g[i]; open += irr.ghi;
    const tamb = clim.tmean[m] + clim.trange[m] / 2 * Math.sin(2 * Math.PI * (hour - 9) / 24);
    pv += panelPower(Q, sun, irr, angle, tamb, clim.wind ? clim.wind[m] : 2).p;
  }
  const strip = [0, 1, 2, 3].map(z => zones.slice(z * NS / 4, (z + 1) * NS / 4).reduce((a, b) => a + b, 0) / (NS / 4) / Math.max(open, 1e-9));
  return { pv: pv / 1000, strip, share: open / Math.max(ghiDay, 1e-9) };
}
function optimizeSchedule(P, clim, soil, zoneCrops) {                  // zoneCrops: 4 crop objects
  const cover = Math.min(1, P.panelW / P.pitch), sched = [], detail = [];
  const info = zoneCrops.map(c => { const si = seasonInfo(c, clim, c.sow - 1); const sf = soilFactor(soil, c, P.year).f; return { c, si, tf: tempFactor(si.tmean, c), sf }; });
  for (let m = 0; m < 12; m++) {
    const row = [], drow = [];
    P.windows.forEach(win => {
      const ev = P.stops.map(a => Object.assign({ a }, windowEval(P, clim, m, a, win)));
      const score = () => {
        const pvMax = Math.max(...ev.map(x => x.pv), 1e-9); let best = null, cropMax = 1e-9;
        ev.forEach(x => { x.crop = info.reduce((s, z, k) => s + (z.si.monthWeights[m] > 0 ? x.share * z.c.ym * lightFactor(x.strip[k], z.c) * z.tf * z.sf * z.c.price : 0), 0); cropMax = Math.max(cropMax, x.crop); });
        ev.forEach(x => { x.J = P.energyWeight * x.pv / pvMax + (1 - P.energyWeight) * x.crop / cropMax; if (!best || x.J > best.J + 1e-9) best = x; });
        return { best, pvMax, cropMax };
      };
      let sc = score;
      let res = score();
      const cs = P.stops.length > 1 ? P.stops[1] - P.stops[0] : 5;
      if (P.angleStep && P.angleStep < cs) {                       // refine around the coarse optimum at the motor's angular resolution
        const lo = Math.max(P.stops[0], res.best.a - cs), hi = Math.min(P.stops[P.stops.length - 1], res.best.a + cs);
        for (let a = lo; a <= hi + 1e-9; a += P.angleStep) { const aa = +a.toFixed(3); if (!ev.some(x => Math.abs(x.a - aa) < 1e-6)) ev.push(Object.assign({ a: aa }, windowEval(P, clim, m, aa, win))); }
        res = score();
      }
      const best = res.best, pvMax = res.pvMax, cropMax = res.cropMax;
      row.push(best.a); drow.push({ a: best.a, pvRel: best.pv / pvMax, cropRel: best.crop / cropMax, J: best.J });
    });
    sched.push(row); detail.push(drow);
  }
  return { sched, detail };
}

/* ---------------- soils, crops, suitability ---------------- */
function ocAt(soil, year) { return soil.oc0 + (soil.ocmax - soil.oc0) * (1 - Math.exp(-year / 2)); }
function clamp(x, a, b) { return Math.max(a, Math.min(b, x)); }
function lightFactor(L, c) {
  if (L >= c.lopt) return 1;
  if (L >= c.lmin) return 0.35 + 0.65 * (L - c.lmin) / (c.lopt - c.lmin);
  return 0.35 * L / c.lmin;
}
function tempFactor(T, c) { const d = T < c.t[0] ? c.t[0] - T : T > c.t[1] ? T - c.t[1] : 0; return Math.max(0.2, 1 - 0.06 * d); }
function soilFactor(soil, c, year) {
  const gap = Math.max(0, soil.ph[0] - c.ph[1], c.ph[0] - soil.ph[1]);
  const fPh = Math.max(0.5, 1 - 0.15 * gap);
  let fDr = 1;
  if (soil.drain < c.drain[0]) fDr = Math.max(0.4, 1 - 0.12 * (c.drain[0] - soil.drain));
  else if (soil.drain > c.drain[1]) fDr = Math.max(0.6, 1 - 0.06 * (soil.drain - c.drain[1]));
  const fEc = Math.max(0.3, 1 - 0.07 * Math.max(0, soil.ec - c.ec));
  const fFert = 0.8 + 0.2 * Math.min(1, ocAt(soil, year) / 1.0);
  return { fPh, fDr, fEc, fFert, f: fPh * fDr * fEc * fFert };
}
function seasonInfo(c, clim, sowMonth) {                // light/temperature averaged over the growing season
  const sowDoy = CUM[sowMonth] + 1; let tsum = 0, w = 0; const mw = new Array(12).fill(0);
  for (let d = 0; d < c.days; d++) { const doy = (sowDoy - 1 + d) % 365; let m = 11; while (CUM[m] > doy) m--; mw[m]++; }
  for (let m = 0; m < 12; m++) { tsum += clim.tmean[m] * mw[m]; w += mw[m]; }
  return { sowDoy, monthWeights: mw, tmean: tsum / w };
}
function seasonLight(zoneMonthly, mw) {                 // zoneMonthly[m] -> light fraction; weight by sunlight too (use equal weights by days)
  let s = 0, w = 0; for (let m = 0; m < 12; m++) { s += zoneMonthly[m] * mw[m]; w += mw[m]; } return s / w;
}
function potentialYield(c, soil, L, Tm, year) {         // t/ha without water stress
  const sf = soilFactor(soil, c, year);
  const lf = lightFactor(L, c), tf = tempFactor(Tm, c);
  return { yield: c.ym * lf * tf * sf.f, lf, tf, sf };
}
function rankCrops(crops, soil, L, clim, year, zoneMonthly) {
  return crops.map(c => {
    const si = seasonInfo(c, clim, c.sow - 1);
    const Lz = zoneMonthly ? seasonLight(zoneMonthly, si.monthWeights) : L;
    const py = potentialYield(c, soil, Lz, si.tmean, year);
    const net = py.yield * 1000 * c.price - c.cost;
    return { id: c.id, name: c.name, yield: py.yield, net, light: Lz, tmean: si.tmean, lf: py.lf, tf: py.tf, sf: py.sf.f };
  }).sort((a, b) => b.net - a.net);
}

/* ---------------- daily water balance ---------------- */
function rainSchedule(clim) {                           // deterministic: events spread evenly with fixed shape weights
  const rain = new Array(365).fill(0);
  for (let m = 0; m < 12; m++) {
    const nd = clim.raindays[m], tot = clim.rain[m]; if (nd < 1 || tot <= 0) continue;
    let ws = []; for (let k = 0; k < nd; k++) ws.push(1 + 0.6 * Math.sin(2.3 * (k + 1)));
    const sw = ws.reduce((a, b) => a + b, 0);
    for (let k = 0; k < nd; k++) { const day = Math.min(DIM[m] - 1, Math.floor((k + 0.5) * DIM[m] / nd)); rain[CUM[m] + day] += tot * ws[k] / sw; }
  }
  return rain;
}
function dailyET0(clim) {
  const a = []; for (let d = 0; d < 365; d++) { let m = 11; while (CUM[m] > d) m--; a.push(hargreavesET0(clim.lat, d + 1, clim.tmean[m], clim.trange[m])); } return a;
}
/* zones: array of 4 { crop, sowMonth (0-11), light:[12 monthly light fractions], area (m2) } */
function waterBalance(P, clim, soil, zones, tankM3) {
  const rain = rainSchedule(clim), et0 = dailyET0(clim);
  const landArea = 10000;                                 // modelled per hectare
  const cover = Math.min(1, P.panelW / P.pitch);
  const catchArea = landArea * cover;
  let tank = 0, harvested = 0, overflow = 0, demand = 0, supplied = 0, groundRainTot = 0;
  const tankSeries = new Array(365), irrSeries = new Array(365).fill(0), harvSeries = new Array(365).fill(0);
  const Z = zones.map(z => {
    const c = z.crop, taw = 1000 * (soil.fc - soil.wp) * c.zr;
    return { c, taw, raw: c.p * taw, Dr: 0, pend: 0, theta: new Array(365).fill(soil.fc), etc: 0, eta: 0, irr: 0, rain: 0, perc: 0, run: 0, light: z.light, sowDoy: CUM[z.sowMonth] + 1, area: z.area };
  });
  for (let d = 0; d < 365; d++) {
    let m = 11; while (CUM[m] > d) m--;
    const R = rain[d];
    let rGround = R;
    if (R >= P.harvestThreshold && R > 0) {              // canopy closes flat: catch the event
      const inM3 = Math.max(0, R - P.firstFlush) * catchArea * P.runoff / 1000;
      const room = tankM3 - tank, add = Math.min(room, inM3);
      tank += add; harvested += add; overflow += inM3 - add; harvSeries[d] = add; rGround = R * (1 - cover);
    }
    groundRainTot += rGround;
    let dayDraw = 0;
    for (const z of Z) {
      const c = z.c, inSeason = ((d - (z.sowDoy - 1) + 365) % 365) < c.days;
      if (((d - (z.sowDoy - 1) + 365) % 365) === 0) z.Dr = 0;
      const kc = inSeason ? c.kc : 0.2, L = z.light[m];
      const etc = kc * et0[d] * (0.5 + 0.5 * L);
      const ks = z.Dr > z.raw ? Math.max(0, (z.taw - z.Dr) / (z.taw - z.raw)) : 1;
      const eta = ks * etc;
      const infil = Math.min(rGround, soil.infil);
      z.run += rGround - infil; z.rain += infil;
      z.Dr = z.Dr - infil + eta;
      if (z.Dr < 0) { z.perc += -z.Dr; z.Dr = 0; }
      if (z.Dr > z.taw) z.Dr = z.taw;
      if (inSeason) {
        z.etc += etc; z.eta += eta;
        z.pend = Math.min(z.pend, z.Dr);
        if (z.Dr >= z.raw) {                             // irrigate back to field capacity
          const need = z.Dr, vol = need * z.area / 1000 / P.irrEff;
          demand += Math.max(0, need - z.pend) * z.area / 1000 / P.irrEff;   // count each mm of need once
          const give = Math.min(vol, tank); tank -= give; supplied += give; dayDraw += give;
          const net = give * P.irrEff * 1000 / z.area; z.Dr -= net; z.irr += net; z.pend = z.Dr;
        }
      }
    }
    Z.forEach(z => { z.theta[d] = soil.fc - z.Dr / (1000 * z.c.zr); });
    tankSeries[d] = tank; irrSeries[d] = dayDraw;
  }
  const out = Z.map((z, i) => {
    const c = z.c, ratio = z.etc > 0 ? z.eta / z.etc : 1;
    const si = seasonInfo(c, clim, zones[i].sowMonth);
    const L = seasonLight(z.light, si.monthWeights);
    const py = potentialYield(c, soil, L, si.tmean, P.year);
    const relWater = Math.max(0, 1 - c.ky * (1 - ratio));
    const Ya = py.yield * relWater, ha = z.area / 10000;
    return { crop: c.id, name: c.name, light: L, tmean: si.tmean, lf: py.lf, tf: py.tf, sf: py.sf.f, waterRatio: ratio, relWater,
      potYield: py.yield, yield: Ya, etc: z.etc, eta: z.eta, irrMm: z.irr, rainInfilMm: z.rain, percMm: z.perc, runoffMm: z.run,
      revenue: Ya * 1000 * c.price * ha, cost: c.cost * ha, net: (Ya * 1000 * c.price - c.cost) * ha, area: z.area };
  });
  return { theta: Z.map(z => z.theta), zones: out, tankSeries, irrSeries, harvSeries, rain, et0, harvested, overflow, demand, supplied,
    unmet: Math.max(0, demand - supplied), borewellM3: Math.max(0, demand - supplied), cover, catchArea, rainTotal: rain.reduce((a, b) => a + b, 0), groundRainTot };
}
function sizeCistern(P, clim, soil, zones) {            // smallest tank with unmet <= 5 % of demand
  const sizes = [0, 25, 50, 100, 150, 200, 300, 400, 600, 800, 1000, 1500, 2000, 3000];
  let prev = null;
  for (const s of sizes) { const r = waterBalance(P, clim, soil, zones, s); prev = { size: s, unmet: r.unmet, demand: r.demand };
    if (r.demand === 0 || r.unmet <= 0.05 * r.demand) return { size: s, curve: curve() }; }
  return { size: null, curve: curve() };
  function curve() { return sizes.map(s => { const r = waterBalance(P, clim, soil, zones, s); return { size: s, unmetPct: r.demand ? 100 * r.unmet / r.demand : 0, harvested: r.harvested }; }); }
}

/* ---------------- economics (per hectare) ---------------- */
function economics(P, clim, annual, wb, tankM3, zonesIn) {
  const cover = Math.min(1, P.panelW / P.pitch), panelArea = 10000 * cover;
  const kwp = panelArea * P.eff;                          // at 1 kW/m2 STC
  const kwh = annual.pvKWhPerM2 * panelArea;
  const capex = kwp * P.capexPerKWp * (1 - P.subsidyPct / 100) + tankM3 * P.cisternPerM3;
  const solarRev = kwh * P.tariff, om = kwp * P.capexPerKWp * P.omPct;
  const cropNet = wb.zones.reduce((a, z) => a + z.net, 0), cropRev = wb.zones.reduce((a, z) => a + z.revenue, 0);
  const annualNet = solarRev - om + cropNet;
  const kwhM = annual.months.map((r, m) => r.pvKWhPerM2Day * DIM[m] * panelArea), solarM = kwhM.map(v => v * P.tariff), farmerSolarM = solarM.map(v => v * P.farmerShare), cropM = new Array(12).fill(0);
  if (zonesIn) wb.zones.forEach((z, i) => { const zz = zonesIn[i], doy = (CUM[zz.sowMonth] + zz.crop.days) % 365; let m = 11; while (CUM[m] > doy) m--; cropM[m] += z.net; });
  const farmerM = farmerSolarM.map((v, m) => v + cropM[m]), farmerAnnual = farmerM.reduce((a, b) => a + b, 0);
  const industryNet = solarRev * (1 - P.farmerShare) - om;
  return { monthly: { kwh: kwhM, solar: solarM, farmerSolar: farmerSolarM, crop: cropM, farmer: farmerM }, farmerAnnual, farmerMonthlyAvg: farmerAnnual / 12, industryNet, co2t: kwh * 0.71 / 1000,
    kwp, kwh, specificYield: kwh / kwp, capex, solarRev, om, cropRev, cropNet, annualNet, payback: annualNet > 0 ? capex / annualNet : null,
    waterHarvestedM3: wb.harvested };
}

/* ---------------- one-call full run ---------------- */
function run(inputs) {
  let P = Object.assign({}, DEFAULTS, inputs.params || {});
  const clim = inputs.clim, soil = inputs.soil, crops = inputs.crops, sel = inputs.zoneCrops || [];
  let annual, zoneMonthly, ranking, ctrlInfo = null, zoneCropObjs;
  const pick = (ann, zm) => {
    const rk = [0, 1, 2, 3].map(z => rankCrops(crops, soil, ann.meanStrip[z], clim, P.year, zm[z]));
    const used = new Set(sel.filter(x => x && x.id).map(x => x.id)), objs = [0, 1, 2, 3].map(z => {
      let c = crops.find(q => q.id === (sel[z] && sel[z].id));
      if (!c) { const pk = rk[z].find(r => !used.has(r.id)) || rk[z][0]; used.add(pk.id); c = crops.find(q => q.id === pk.id); } return c; });
    return { rk, objs };
  };
  if (P.tiltMode === 'smart') {                         // pass 1: baseline light -> crops; pass 2: controller optimises tilt for those crops
    const base = Object.assign({}, P, { tiltMode: 'fixed' }), a0 = annualLight(base, clim);
    const zm0 = [0, 1, 2, 3].map(z => a0.months.map(r => r.strip[z])), pk = pick(a0, zm0);
    ctrlInfo = optimizeSchedule(P, clim, soil, pk.objs); P = Object.assign({}, P, { schedule: ctrlInfo.sched });
    annual = annualLight(P, clim); zoneMonthly = [0, 1, 2, 3].map(z => annual.months.map(r => r.strip[z]));
    ranking = [0, 1, 2, 3].map(z => rankCrops(crops, soil, annual.meanStrip[z], clim, P.year, zoneMonthly[z])); zoneCropObjs = pk.objs;
  } else {
    annual = annualLight(P, clim); zoneMonthly = [0, 1, 2, 3].map(z => annual.months.map(r => r.strip[z]));
    const pk = pick(annual, zoneMonthly); ranking = pk.rk; zoneCropObjs = pk.objs;
  }
  const zones = [0, 1, 2, 3].map(z => { const c = zoneCropObjs[z], sowMonth = sel[z] && sel[z].sowMonth != null ? sel[z].sowMonth : c.sow - 1; return { crop: c, sowMonth, light: zoneMonthly[z], area: 2500 }; });
  const wb = waterBalance(P, clim, soil, zones, P.tankM3), eco = economics(P, clim, annual, wb, P.tankM3, zones);
  return { P, annual, zoneMonthly, ranking, zones, wb, eco, ctrl: ctrlInfo };
}

const API = { DEFAULTS, MNAME, DIM, CUM, MID, declination, sunVec, irradiance, extraterrestrialDaily, hargreavesET0, tiltFor, rowsFor, groundLightHour, panelPower, winIndex, optimizeSchedule, windowEval, segments, rayBlocked,
  monthLight, annualLight, rankCrops, potentialYield, lightFactor, tempFactor, soilFactor, ocAt, seasonInfo, rainSchedule, dailyET0,
  waterBalance, sizeCistern, economics, run, NS };
if (typeof module !== 'undefined' && module.exports) module.exports = API; else root.SRMC = API;
})(typeof window !== 'undefined' ? window : globalThis);
