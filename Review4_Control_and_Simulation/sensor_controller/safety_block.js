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
        if (st.soilSameKey === key) { if (up && st.soilSameSince != null && t - st.soilSameSince >= cfg.soilStuckS) bad = bad || 'stuck at the same value for ' + ((t - st.soilSameSince) / 3600).toFixed(1) + ' h'; } else { st.soilSameKey = key; st.soilSameSince = t; }
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
        const exempt = d.mode === 'STOW' || d.mode === 'RAIN'; let a = d.angle; const delta = Math.abs(a - before);
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
