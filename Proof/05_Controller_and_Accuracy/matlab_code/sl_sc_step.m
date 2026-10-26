function y = sl_sc_step(u)
%SL_SC_STEP  One controller step for the Simulink model (Interpreted MATLAB Function block).
%   u = [hour; ghi; T; RH; soil; rain; wind; prevAngle]  (day of year fixed to 106, 16 April).  The simulated PAR sensor is computed from the
%   canopy physics at the angle now in use, exactly as the web twin does.   y = [angle; mode code (0 night, 1 optimise, 2 rain, 3 wind stow)].
persistent ctx
if isempty(ctx)
    here = fileparts(mfilename('fullpath')); addpath(fullfile(fileparts(fileparts(here)), 'Review0_Prototype_Demo', 'matlab'));
    sc = fullfile(fileparts(here), 'sensor_controller', 'results', 'crosscheck_cases.json'); C = jsondecode(fileread(sc));
    F = review0_physics(); ctx = struct('F', F, 'P', F.designParams(), 'zones', C.zones, 'monthW', C.monthW, 'lat', C.lat, 'w', 0.5, 'maxStep', 6);
end
sen = struct('ghi', u(2), 'T', u(3), 'RH', u(4), 'soil', u(5), 'rain', u(6) > 0.5, 'wind', u(7), 'day', 106, 'hour', u(1), 'parUm', 0);
if sen.ghi >= 20 && ~sen.rain
    sun = ctx.F.sunVec(ctx.lat, 106, u(1)); g0 = 1361*(1+0.033*cos(2*pi*106/365)); kt = min(0.85, max(0.02, sen.ghi/(g0*max(sun.sz,0.05))));
    m = ctx.F.irradiance(sun.sz, 106, kt); k = sen.ghi/max(m.ghi,1e-9); irr = struct('ghi', sen.ghi, 'dni', m.dni*k, 'dhi', m.dhi*k);
    Q = ctx.P; Q.tiltMode = 'fixed'; Q.tilt = min(60,u(8)); gg = ctx.F.groundLightHour(Q, sun, irr, min(60,u(8))); sen.parUm = 2.05*mean(gg);
end
d = srmc_sensor_controller(sen, u(8), ctx);
code = 1; if strcmp(d.mode, 'NIGHT'), code = 0; elseif strcmp(d.mode, 'RAIN'), code = 2; elseif strcmp(d.mode, 'STOW'), code = 3; end
y = [d.angle; code];
end
