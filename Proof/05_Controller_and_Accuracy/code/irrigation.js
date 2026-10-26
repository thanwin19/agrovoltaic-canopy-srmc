/* Water link: the SOIL PROBE decides when irrigation runs (drip from the cistern, borewell top-up), compared with a conventional TIMER.
 * Same daily soil-water balance as the twin's engine (FAO-56 style: depletion Dr, readily available water RAW, ETc = Kc x ET0 x light factor, rain from the monthly rain schedule,
 * harvested rain fills the cistern). Only the irrigation DECISION differs:
 *   probe : irrigate a zone when its probe says plant-available water is at or below the trigger (1 - p of the crop, the readily-available-water limit);
 *           refill to field capacity; an event never exceeds capMm per day (the drip controller's maximum run time)
 *   timer : every `interval` days during the crop season apply a fixed depth (the seasonal mean ETc x interval), whatever the rain and the soil
 * Probe faults (noise, stuck dry, stuck wet, dead) with and without the fallback (stuck for 3 days or dead -> run the conservative timer schedule).
 * Output: applied water m3/ha, cistern and borewell volumes, events, stress days, relative yield from water stress, percolation losses, and the water SAVED against the timer. */
(function (root) {
  'use strict';
  function simulate(S, ctx, pol) {
    pol = Object.assign({ type: 'probe', interval: 4, capMm: 25, noise: 0, fault: null, fallback: false, etBias: 0.85, seed: 1 }, pol || {});
    const { P, clim, soil, zones, tankM3 } = ctx, CUM = S.CUM, rain = S.rainSchedule(clim), et0 = S.dailyET0(clim), cover = Math.min(1, P.panelW / P.pitch), catchArea = 10000 * cover;
    let seed = pol.seed >>> 0; const rnd = () => { seed = (seed * 1664525 + 1013904223) >>> 0; return seed / 4294967296; }, gauss = () => { let u = 0; while (!u) u = rnd(); return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * rnd()); };
    let tank = 0, harvested = 0, suppliedTank = 0, borewell = 0, applied = 0, events = 0;
    const tankSeries = new Array(365), irrSeries = new Array(365).fill(0), availSeries = [[], [], [], []], probeSeries = [[], [], [], []];
    const Z = zones.map(z => { const c = z.crop, taw = 1000 * (soil.fc - soil.wp) * c.zr; return { c, z, taw, raw: c.p * taw, Dr: 0, Dm: 0, etc: 0, eta: 0, perc: 0, stress: 0, sowDoy: CUM[z.sowMonth] + 1, light: z.light, area: z.area, same: 0, lastRead: null, bad: false, evts: 0 }; });
    // timer depth: mean seasonal ETc per day x interval (a typical farmer rule of thumb)
    Z.forEach(z => { let s = 0, n = 0; for (let d = 0; d < 365; d++) { const doy = ((d - (z.sowDoy - 1) + 365) % 365); if (doy < z.c.days) { let m = 11; while (CUM[m] > d) m--; s += z.c.kc * et0[d] * (0.5 + 0.5 * z.light[m]); n++; } } z.timerMm = n ? s / n * pol.interval : 0; });
    for (let d = 0; d < 365; d++) {
      let m = 11; while (CUM[m] > d) m--; const R = rain[d]; let rGround = R;
      if (R >= P.harvestThreshold && R > 0) { const inM3 = Math.max(0, R - P.firstFlush) * catchArea * P.runoff / 1000, add = Math.min(tankM3 - tank, inM3); tank += add; harvested += add; rGround = R * (1 - cover); }
      let dayDraw = 0, dayBore = 0;
      Z.forEach((z, k) => {
        const c = z.c, doy = ((d - (z.sowDoy - 1) + 365) % 365), inSeason = doy < c.days; if (doy === 0) { z.Dr = 0; z.Dm = 0; }
        const kc = inSeason ? c.kc : 0.2, L = z.light[m], etc = kc * et0[d] * (0.5 + 0.5 * L), ks = z.Dr > z.raw ? Math.max(0, (z.taw - z.Dr) / (z.taw - z.raw)) : 1, eta = ks * etc, infil = Math.min(rGround, soil.infil);
        z.Dr = z.Dr - infil + eta; if (z.Dr < 0) { z.perc += -z.Dr; z.Dr = 0; } if (z.Dr > z.taw) z.Dr = z.taw;
        const etM = kc * et0[d] * pol.etBias * (0.5 + 0.5 * L), ksM = z.Dm > z.raw ? Math.max(0, (z.taw - z.Dm) / (z.taw - z.raw)) : 1; z.Dm = Math.max(0, Math.min(z.taw, z.Dm - infil + ksM * etM));        // open-loop model estimate
        if (inSeason) { z.etc += etc; z.eta += eta; if (ks < 0.999) z.stress++; }
        // ---- the probe reading (plant-available water %, 0 = wilting point, 100 = field capacity)
        let read = 100 * (1 - z.Dr / z.taw), flt = null;
        if (pol.fault === 'dead') read = NaN; else if (pol.fault === 'stuckDry') read = 12; else if (pol.fault === 'stuckWet') read = 85; else if (pol.noise) read += pol.noise * gauss();
        probeSeries[k][d] = read; z.same = (z.lastRead != null && Math.abs(read - z.lastRead) < 1e-9) ? z.same + 1 : 0; z.lastRead = read;
        let useRead = read, usedModel = false; if (pol.fallback && (isNaN(read) || z.same >= 3)) { useRead = 100 * (1 - z.Dm / z.taw); usedModel = true; }     // stuck for 3 days or dead: fall back to the water-balance model
        const trigger = 100 * (1 - (usedModel ? 0.7 * c.p : c.p)); let give = 0, need = 0;      // on the model estimate irrigate earlier (70 % of the allowed depletion) because the estimate is less certain
        if (inSeason) {
          if (pol.type === 'timer' || usedModel) {      // fallback when the probe is dead or stuck: run the conservative timer schedule (an open-loop model estimate drifts)
             if (doy % pol.interval === 0 && doy > 0) { need = z.timerMm; give = need / P.irrEff * z.area / 1000; } }
          else { const isDry = isNaN(useRead) ? false : useRead <= trigger; if (isDry) { need = Math.min(pol.capMm, usedModel ? z.Dm : (pol.fault === 'stuckDry' ? pol.capMm : z.Dr)); give = need / P.irrEff * z.area / 1000; } }
        }
        if (give > 0) { const fromTank = Math.min(give, tank); tank -= fromTank; suppliedTank += fromTank; const bore = give - fromTank; borewell += bore; dayDraw += fromTank; dayBore += bore; applied += give; events++; z.evts++;
          const net = give * P.irrEff * 1000 / z.area; z.Dr -= net; if (z.Dr < 0) { z.perc += -z.Dr; z.Dr = 0; } z.Dm = Math.max(0, z.Dm - net); }
        availSeries[k][d] = 100 * (1 - z.Dr / z.taw);
      });
      tankSeries[d] = tank; irrSeries[d] = dayDraw + dayBore;
    }
    const rel = Z.map(z => { const ratio = z.etc > 0 ? z.eta / z.etc : 1; return Math.max(0, 1 - z.c.ky * (1 - ratio)); });
    return { policy: pol, irrSeries, tankSeries, availSeries, probeSeries, appliedM3: applied, cisternM3: suppliedTank, borewellM3: borewell, harvestedM3: harvested, events, stressDays: Z.reduce((a, z) => a + z.stress, 0) / Z.length, relYield: rel.reduce((a, b) => a + b, 0) / rel.length, relYieldZ: rel, percMm: Z.reduce((a, z) => a + z.perc, 0) / Z.length };
  }
  function compare(S, ctx) {
    const timer = simulate(S, ctx, { type: 'timer' }), rows = [['Timer (every 4 days, fixed depth)', timer], ['Soil probe decides (ideal probe)', simulate(S, ctx, { type: 'probe' })], ['Soil probe, noisy (+-3 points)', simulate(S, ctx, { type: 'probe', noise: 3 })],
      ['Probe stuck DRY, no fallback', simulate(S, ctx, { type: 'probe', fault: 'stuckDry' })], ['Probe stuck DRY, with fallback', simulate(S, ctx, { type: 'probe', fault: 'stuckDry', fallback: true })], ['Probe stuck WET, no fallback', simulate(S, ctx, { type: 'probe', fault: 'stuckWet' })], ['Probe stuck WET, with fallback', simulate(S, ctx, { type: 'probe', fault: 'stuckWet', fallback: true })], ['Probe dead (no reading), with fallback', simulate(S, ctx, { type: 'probe', fault: 'dead', fallback: true })]];
    return { timer, rows: rows.map(([name, r]) => ({ name, applied_m3_ha: Math.round(r.appliedM3), cistern_m3: Math.round(r.cisternM3), borewell_m3: Math.round(r.borewellM3), events: r.events, stress_days: +r.stressDays.toFixed(1), relative_yield_from_water: +r.relYield.toFixed(3), percolation_loss_mm: Math.round(r.percMm), water_saved_vs_timer_m3: Math.round(timer.appliedM3 - r.appliedM3), water_saved_vs_timer_pct: +(100 * (timer.appliedM3 - r.appliedM3) / Math.max(1, timer.appliedM3)).toFixed(1) })), sims: rows };
  }
  const API = { simulate, compare };
  if (typeof module !== 'undefined' && module.exports) module.exports = API; else root.SRMC_IRR = API;
})(typeof window !== 'undefined' ? window : globalThis);
