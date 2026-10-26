// Creates a FAKE week of sensor readings in exactly the format the real logger writes, so the scoring pipeline can be rehearsed before the sensors are connected.
//   node make_fake_week.js [out.csv] [start YYYY-MM-DD]        (default week_fake.csv, 2026-10-26)
// Columns: timestamp (IST), ms, tempC, rh, soilRaw, rain, rainRaw, ghi, par, wind, angleDeg
// The panels are driven by the controller in a loop (angleDeg), the PAR sensor reads the light that reaches the crop at that angle.
// Faults are injected on purpose: DHT11 read failures (-999), a dirty PAR sensor for 3 hours on day 4, a stuck soil probe for 6 hours on day 6, a wind gust on day 5.
const fs = require('fs'), path = require('path'), { setup, solarTime, monthOfDay } = require('./common.js');
const out = process.argv[2] || path.join(__dirname, 'week_fake.csv'), start = process.argv[3] || '2026-10-26';
const { S, SC, clim, P, ctl } = setup(), lon = clim.lon, DRY = 3200, WET = 1300;               // ESP32: soil raw 3200 = dry, 1300 = wet
let seed = 12345; const rnd = () => (seed = (seed * 1664525 + 1013904223) % 4294967296) / 4294967296, gauss = () => { let u = 0; while (!u) u = rnd(); return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * rnd()); };
const rows = []; let angle = 15, soil = 62, cloud = 1, ms = 0, stuckSoil = null;
const dayCloud = [1, 0.8, 0.45, 1, 0.9, 0.6, 1];                                               // sky clearness per day
for (let day = 0; day < 7; day++) for (let min = 0; min < 24 * 60; min += 5) {
  const hh = Math.floor(min / 60), mm = min % 60, ymd = new Date(Date.parse(start + 'T00:00:00Z') + day * 864e5).toISOString().slice(0, 10), local = ymd + 'T' + String(hh).padStart(2, '0') + ':' + String(mm).padStart(2, '0') + ':00+05:30';
  const st = solarTime(local, lon), n = st.day, m = monthOfDay(n), sun = S.sunVec(clim.lat, n, st.hour);
  cloud = Math.max(0.15, Math.min(1, cloud + 0.06 * gauss() + 0.03 * (dayCloud[day] - cloud)));
  const kt = clim.kt[m] * cloud, irr = S.irradiance(sun.sz, n, kt), raining = day === 2 && hh >= 14 && hh < 15;
  const T = clim.tmean[m] + clim.trange[m] / 2 * Math.sin(2 * Math.PI * (st.hour - 9) / 24) + 0.5 * gauss(), RH = Math.max(15, Math.min(98, clim.rh[m] - 12 * Math.cos(2 * Math.PI * (st.hour - 15) / 24) + (raining ? 25 : 0) + 1.5 * gauss()));
  const wind = Math.max(0, 3 + 1.5 * Math.sin(2 * Math.PI * st.hour / 24) + 0.6 * gauss() + (day === 4 && hh === 17 && mm < 30 ? 14 : 0));
  soil = Math.max(8, soil - 0.012 * (irr.ghi / 800 + 0.1) * 5 / 5 * (Math.max(0, sun.sz) > 0 ? 1.4 : 0.3)); if (raining) soil = Math.min(95, soil + 1.6); if (hh === 6 && mm === 0 && soil < 30) soil += 35;   // evaporation, rain, a drip irrigation at 06:00 when dry
  let soilRaw = Math.round(DRY - soil / 100 * (DRY - WET) + 12 * gauss()); if (day === 5 && hh >= 8 && hh < 14) { if (stuckSoil == null) stuckSoil = soilRaw; soilRaw = stuckSoil; }
  let tempC = +(T + 0.4 * gauss()).toFixed(1), rh = +RH.toFixed(1); if (rnd() < 0.012) { tempC = -999; rh = -999; }                    // DHT11 read failures
  const up = irr.ghi >= 20; let ghi = up ? irr.ghi * (1 + 0.04 * gauss()) : Math.max(0, 2 * rnd()), par = 0;
  if (raining) ghi *= 0.2;
  if (up) { ctl.setDay(n); const tru = ctl.evalAngle(Math.min(angle, 60), sun, { ghi, dni: irr.dni * ghi / Math.max(irr.ghi, 1), dhi: irr.dhi * ghi / Math.max(irr.ghi, 1) }, T, 1, 0, 2); par = SC.UM_PER_W * tru.lsr * ghi * (1 + 0.04 * gauss()); if (day === 3 && hh >= 10 && hh < 13) par *= 0.3; }
  const reading = { ghi, parUm: par, T: tempC > -100 ? tempC : T, RH: tempC > -100 ? rh : RH, soil: 100 * (DRY - soilRaw) / (DRY - WET), rain: raining, wind, day: n, hour: st.hour };
  const angleUsed = angle, d = ctl.decide(reading, { angle }); angle = d.angle; ms += 300000;
  rows.push([local, ms, tempC, rh, soilRaw, raining ? 1 : 0, raining ? 900 : 3900, +ghi.toFixed(1), +par.toFixed(1), +wind.toFixed(1), +angleUsed.toFixed(1)]);
}
fs.writeFileSync(out, '# FAKE week for rehearsal (made by make_fake_week.js). Real logs use the same columns.\ntimestamp,ms,tempC,rh,soilRaw,rain,rainRaw,ghi,par,wind,angleDeg\n' + rows.map(r => r.join(',')).join('\n') + '\n'); console.log('wrote', out, rows.length, 'rows');
