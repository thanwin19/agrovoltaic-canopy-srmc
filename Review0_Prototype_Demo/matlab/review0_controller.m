function d = review0_controller(S, V, P, F, cfg)
%REVIEW0_CONTROLLER  SRMC-DT controller: picks the panel tilt that co-optimises PV energy and crop light, every decision step.
%
%   MEASURED by the ESP8266/ESP32 (REAL sensors)          S.tempC  S.rh  S.soilPct  S.rain(0/1)
%   VIRTUAL sensors, set on the dashboard (SIMULATED)      V.lat  V.day  V.hour  V.kt (sky clearness 0..0.8)  V.windMS
%   P = geometry from design.json (review0_physics().designParams)    F = review0_physics()
%   cfg: .wEnergy (0..1, default 0.5)  .windStow (15 m/s)  .vpdHigh (2.5 kPa)  .zoneCrops (4 structs with lmin, lopt)  .parkAngle (15)
%
%   Priority of rules (highest first):  1 wind stow -> 2 rain harvest -> 3 night park -> 4 optimise energy + crop light
%   Optimisation: for every candidate angle a in [15, 60] deg (coarse 5 deg, then 0.5 deg around the best)
%        PV(a)   = module power per m2 of panel  (shading by neighbouring rows, incidence angle, cell temperature from the DHT11 air temperature)
%        Crop(a) = mean over the 4 crop zones of lightFactor(LSR_zone(a))      LSR = under-canopy PAR / above-canopy PAR
%        J(a)    = w * PV(a)/max(PV) + (1-w) * Crop(a)/max(Crop)
%   Plant stress (VPD from the DHT11, or dry soil) lowers the light the crops need (lmin, lopt scaled by 1 - 0.3*stress), so the controller
%   can lean towards more shade and more energy while the crop is stressed.
if nargin < 5, cfg = struct(); end
cfg = defaults5(cfg);
d = struct();
sun = F.sunVec(V.lat, V.day, V.hour); up = sun.sz > 0.02;
d.ghiClamped = false;
if isfield(V, 'ghiOverride') && ~isnan(V.ghiOverride) && up      % pyranometer reading given directly (scroll bar or a real sensor)
    g0 = 1361 * (1 + 0.033 * cos(2 * pi * V.day / 365)); ktRaw = V.ghiOverride / (g0 * sun.sz); ktEff = max(0.02, min(0.85, ktRaw)); d.ghiClamped = ktRaw > 0.85 + 1e-9;
    irr = F.irradiance(sun.sz, V.day, ktEff); if ~d.ghiClamped, irr.ghi = V.ghiOverride; end        % beam/diffuse split from the clearness index (Erbs)
else
    irr = F.irradiance(sun.sz, V.day, V.kt);
end
d.sunEl = asind(max(-1, min(1, sun.sz))); d.sunAz = mod(atan2d(sun.sx, sun.sy), 360);
d.ghi = irr.ghi; d.dni = irr.dni; d.dhi = irr.dhi;
d.parExpected = irr.ghi * 0.45 * 4.57;                   % umol m-2 s-1 : 45 % of global radiation is PAR, ~4.57 umol per J
if isfield(V, 'parOverride') && ~isnan(V.parOverride), d.parOpen = V.parOverride; else, d.parOpen = d.parExpected; end    % PAR sensor reading (scroll bar / real sensor)
d.parRatio = d.parOpen / max(d.parExpected, 1);          % 1 = PAR sensor agrees with the pyranometer; < 1 = crops see less light than the pyranometer suggests
d.parPerJ = d.parOpen / max(irr.ghi, 1);                 % umol per J of global radiation; expected about 2.06 (0.45 x 4.57)
d.plausible = ~(irr.ghi > 20) || abs(d.parRatio - 1) <= 0.25;
es = 0.6108 * exp(17.27 * S.tempC / (S.tempC + 237.3)); d.vpd = max(0, es * (1 - S.rh / 100));
sH = min(1, max(0, (d.vpd - 1.6) / (cfg.vpdHigh - 1.6)));           % air stress 0..1
sS = min(1, max(0, (cfg.soilDry - S.soilPct) / cfg.soilDry));       % root-zone stress 0..1
d.stress = max(sH, sS); d.stressAir = sH; d.stressSoil = sS;

Q = P; Q.tiltMode = 'fixed';
evalAngle = @(a) evalOne(a);
% ---- baseline numbers for comparison (same inputs) ----
pv45 = 0; crop45 = 0; pvMax = 0;
if up
    [pv45, crop45] = evalOne(45);
end
% ---- sensor-error scenarios (robust mode): pyranometer -10/+10 %, PAR -10/+10 % ----
scen = {struct('irr', irr, 'pr', d.parRatio)};
if cfg.robust && up
    g0r = 1361 * (1 + 0.033 * cos(2 * pi * V.day / 365)); mk = @(k) F.irradiance(sun.sz, V.day, max(0.02, min(0.85, irr.ghi * k / (g0r * sun.sz))));
    scen = [scen, {struct('irr', mk(0.9), 'pr', d.parRatio), struct('irr', mk(1.1), 'pr', d.parRatio), struct('irr', irr, 'pr', d.parRatio * 0.9), struct('irr', irr, 'pr', d.parRatio * 1.1)}];
end
d.robust = cfg.robust; lastG = 0; lastTc = S.tempC;
% ---- decision ----
if isfield(cfg, 'forceAngle') && ~isempty(cfg.forceAngle) && up
    a = cfg.forceAngle; mode = 'FORCED'; reason = sprintf('fixed angle %.1f deg (comparison run)', a);
elseif V.windMS >= cfg.windStow
    a = 90; mode = 'WIND STOW'; reason = sprintf('wind %.1f m/s >= %.0f m/s: panels edge-on to the wind', V.windMS, cfg.windStow);
elseif S.rain
    a = P.rainSlope; mode = 'RAIN HARVEST'; reason = sprintf('rain sensor wet: panels to %.0f deg fall towards the gutter, water to the cistern', P.rainSlope);
elseif ~up
    a = cfg.parkAngle; mode = 'NIGHT PARK'; reason = 'sun below horizon: parked at the lowest tilt stop';
else
    cand = 15:5:60; [J, ~, ~] = scoreSet(cand); [~, ib] = max(J); a0 = cand(ib);
    fine = max(15, a0 - 5):0.5:min(60, a0 + 5); [J2, pvv, cc] = scoreSet(fine); [~, ib2] = max(J2); a = fine(ib2);
    mode = 'OPTIMISED';
    reason = sprintf('w = %.2f energy / %.2f crop; stress %.2f (VPD %.1f kPa, soil %.0f %%)', cfg.wEnergy, 1 - cfg.wEnergy, d.stress, d.vpd, S.soilPct);
    pvMax = max(pvv);
end
d.mode = mode; d.angle = a; d.reason = reason;
if up
    [d.pv, d.crop, d.lsr, d.parZone] = evalOne(a);
else
    d.pv = 0; d.crop = 0; d.lsr = zeros(1,4); d.parZone = zeros(1,4);
end
d.gpoa = lastG; d.tcell = lastTc;
if cfg.wantCurve && up                                         % data for the explanation window: curves, brute-force check, strategy comparison
    ac = 15:1:60; [pvc, cc] = evalSet(ac, scen{1}); ab = 15:0.5:60; [pvb, cb] = evalSet(ab, scen{1});
    Jb = jOf(pvb, cb); [Jbest, ibb] = max(Jb); [pvA, cA] = evalOne(a); JA = cfg.wEnergy * pvA / max(pvb) + (1 - cfg.wEnergy) * cA / max(cb);
    trk = max(-60, min(60, atan2d(sun.sx, sun.sz))); sa = [15 45 trk]; sp = zeros(1, 3); sc2 = zeros(1, 3); for k = 1:3, [sp(k), sc2(k)] = evalOne(sa(k)); end
    d.curve = struct('angle', ac, 'pv', pvc, 'crop', cc, 'J', cfg.wEnergy * pvc / max(pvb) + (1 - cfg.wEnergy) * cc / max(cb), 'pvMax', max(pvb), 'cropMax', max(cb));
    d.brute = struct('angle', ab(ibb), 'J', Jbest, 'chosenJ', JA, 'gapDeg', abs(a - ab(ibb)), 'gapJpct', 100 * max(0, Jbest - JA) / max(Jbest, eps));
    d.strat = struct('name', {{'fixed 15 deg', 'fixed 45 deg', 'sun tracking', 'SRMC controller'}}, 'angle', [sa a], 'pv', [sp d.pv], 'crop', [sc2 d.crop]);
end
d.pvFixed45 = pv45; d.cropFixed45 = crop45; d.pvBest = pvMax;
d.pvGainVs45 = ifelse(pv45 > 0, 100 * (d.pv / pv45 - 1), 0);

    function [pv, crop, lsr, parZone] = evalOne(angle, sc)
        if nargin < 2, sc = struct('irr', irr, 'pr', d.parRatio); end
        Qa = Q; Qa.tilt = angle;
        if ~up, pv = 0; crop = 0; lsr = zeros(1,4); parZone = zeros(1,4); return; end
        g = F.groundLightHour(Qa, sun, sc.irr, angle);
        lsr = [mean(g(1:10)) mean(g(11:20)) mean(g(21:30)) mean(g(31:40))] / max(sc.irr.ghi, 1);
        parZone = lsr * d.parOpen;
        f = zeros(1,4);
        for z = 1:4
            c = cfg.zoneCrops(z); c.lmin = c.lmin * (1 - 0.3 * d.stress); c.lopt = c.lopt * (1 - 0.3 * d.stress);
            f(z) = F.lightFactor(lsr(z) * min(1, sc.pr), c);       % crop light = share under the canopy x how much PAR the sensor really delivers
        end
        crop = mean(f);
        [pw, lastG, lastTc] = F.panelPower(Q, sun, sc.irr, angle, S.tempC, max(V.windMS, 0.5)); pv = pw;
    end
    function [pvv, cc] = evalSet(cand, sc)
        pvv = zeros(size(cand)); cc = zeros(size(cand));
        for i = 1:numel(cand), [pvv(i), cc(i)] = evalOne(cand(i), sc); end
    end
    function J = jOf(pvv, cc), J = cfg.wEnergy * pvv / max(max(pvv), eps) + (1 - cfg.wEnergy) * cc / max(max(cc), eps); end
    function [J, pvv, cc] = scoreSet(cand)
        [pvv, cc] = evalSet(cand, scen{1}); J = jOf(pvv, cc);
        for k = 2:numel(scen)                                  % robust mode: keep the WORST score over +-10 % errors of either sensor
            [p2, c2] = evalSet(cand, scen{k}); J = min(J, jOf(p2, c2));
        end
    end
end

function cfg = defaults5(cfg)
def = struct('wantCurve', false, 'robust', false, 'wEnergy', 0.5, 'windStow', 15, 'vpdHigh', 2.5, 'parkAngle', 15, 'soilDry', 35, ...
    'zoneCrops', struct('lmin', {0.25, 0.25, 0.20, 0.20}, 'lopt', {0.50, 0.55, 0.50, 0.50}));
f = fieldnames(def); for i = 1:numel(f), if ~isfield(cfg, f{i}), cfg.(f{i}) = def.(f{i}); end, end
end
function v = ifelse(c, a, b), if c, v = a; else, v = b; end, end
