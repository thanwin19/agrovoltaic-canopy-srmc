function [d, tools] = srmc_sensor_controller(sen, prevAngle, ctx)
%SRMC_SENSOR_CONTROLLER  Five-sensor controller (SRMC-SC) of the Agrovoltaic Canopy for Protection and Sustainable Farming.
%   Same rule as the web twin (Review4/sensor_controller/sensor_controller.js):
%     sen.ghi (pyranometer W/m2), sen.parUm (PAR under canopy umol/m2/s), sen.T and sen.RH (DHT11), sen.soil (%), sen.rain (0/1), sen.day, sen.hour
%     1 rain wet -> flat roof;  2 pyranometer < 20 W/m2 -> night park;  3 else maximise J = w PV/PVmax + (1-w) crop/cropmax over 15..60 deg
%     PAR correction: model light is scaled by (measured PAR/GHI)/(model value at the angle in use); DHT11 VPD and dry soil lower the crop light need.
%   ctx: .F (review0_physics()), .P (design params), .zones (4 structs lmin lopt ym price), .monthW (4 x 12 growing-season weights), .lat, .w (0.5), .maxStep (6), optional .guard (true), .relax (0.3)
%   [d, tools] = ...: tools.evalAngle(angle, corr) returns the PV and crop value of an angle for the sensor state given (used by the accuracy study).
tools = []; CUM = [0 31 59 90 120 151 181 212 243 273 304 334]; mo = find(sen.day > CUM, 1, 'last');
relax = 0.3; if isfield(ctx, 'relax'), relax = ctx.relax; end
UM = 2.05; lo = ctx.P.stops(1); hi = ctx.P.stops(end); F = ctx.F; P = ctx.P; w = ctx.w; maxStep = ctx.maxStep;
sun = F.sunVec(ctx.lat, sen.day, sen.hour);
es = 0.6108*exp(17.27*sen.T/(sen.T+237.3)); vpd = max(0, es*(1 - sen.RH/100));
sA = min(1, max(0, (vpd-1.6)/(2.5-1.6))); sS = min(1, max(0, (20-sen.soil)/20)); stress = max(sA, sS);
d = struct('mode','','angle',prevAngle,'stress',stress,'corr',1,'target',NaN,'fault','');
if isfield(sen, 'wind') && ~isempty(sen.wind) && (sen.wind >= 15 || (prevAngle >= 90 && sen.wind >= 12)), d.mode = 'STOW'; d.angle = 90; return; end   % anemometer: wind stow with hysteresis
if sen.rain, d.mode = 'RAIN'; d.angle = P.rainSlope; return; end
if sen.ghi < 20 || sun.sz < 0.02, d.mode = 'NIGHT'; d.angle = lo; return; end
g0 = 1361*(1+0.033*cos(2*pi*sen.day/365)); kt = min(0.85, max(0.02, sen.ghi/(g0*max(sun.sz,0.05))));
m = F.irradiance(sun.sz, sen.day, kt); k = sen.ghi/max(m.ghi, 1e-9); irr = struct('ghi', sen.ghi, 'dni', m.dni*k, 'dhi', m.dhi*k);
lsrMeas = sen.parUm/UM/max(sen.ghi,1);
cur = evalAngle(min(hi,max(lo,prevAngle)), 1);
corr = 1; d.fault = '';
if cur.lsr > 0.01 && isfinite(lsrMeas)
    ratio = lsrMeas/cur.lsr; if isfield(sen, 'parRatio') && ~isempty(sen.parRatio), ratio = sen.parRatio; end, useGuard = ~isfield(ctx, 'guard') || ctx.guard;
    if useGuard && (ratio < 0.5 || ratio > 1.6), d.fault = 'PAR';          % fault guard: ignore an implausible PAR reading
    else, corr = min(1.3, max(0.7, ratio)); end
end
coarse = lo:5:hi; ev = arrayfun(@(a) evalAngle(a, corr), coarse); best = pick(ev);
for a = max(lo,best.a-5):0.5:min(hi,best.a+5)
    if ~any(abs([ev.a]-a) < 1e-6), ev(end+1) = evalAngle(a, corr); end %#ok<AGROW>
end
best = pick(ev); a = best.a;
pm = max(max([ev.pv]), 1e-9); cm = max(max([ev.crop]), 1e-9); Jof = @(e) w*e.pv/pm + (1-w)*e.crop/cm;      % hysteresis: keep the present angle unless the best one is clearly better
if prevAngle >= lo && prevAngle <= hi, ec = evalAngle(prevAngle, corr); if Jof(best) - Jof(ec) < 0.02, a = prevAngle; end, end
dd = a - prevAngle; if abs(dd) > maxStep, a = prevAngle + sign(dd)*maxStep; end
a = min(hi, max(lo, round(a*2)/2));
d.mode = 'OPTIMISE'; d.angle = a; d.corr = corr; d.target = best.a; tools = struct('evalAngle', @evalAngle);

    function e = evalAngle(aa, cc)
        Q = P; Q.tiltMode = 'fixed'; Q.tilt = aa;
        gg = F.groundLightHour(Q, sun, irr, aa); NSg = numel(gg); zl = zeros(1,4);
        for zz = 1:4, zl(zz) = mean(gg((zz-1)*NSg/4+1 : zz*NSg/4)); end
        pw = F.panelPower(Q, sun, irr, aa, sen.T, 2); crop = 0;
        for zz = 1:4
            c = ctx.zones(zz); f = 1 - relax*stress; cs = struct('lmin', c.lmin*f, 'lopt', c.lopt*f); sw = ctx.monthW(zz, mo);
            crop = crop + sw*c.ym*c.price*F.lightFactor(min(1, max(0, zl(zz)*cc/max(irr.ghi,1))), cs);
        end
        e = struct('a', aa, 'pv', pw, 'crop', crop, 'lsr', mean(zl)/max(irr.ghi,1), 'J', 0);
    end
    function b = pick(E)
        pm = max([E.pv]); cm = max([E.crop]); pm = max(pm,1e-9); cm = max(cm,1e-9); bj = -inf; b = E(1);
        for ii = 1:numel(E), j = w*E(ii).pv/pm + (1-w)*E(ii).crop/cm; E(ii).J = j; if j > bj + 1e-9, bj = j; b = E(ii); end, end
    end
end
