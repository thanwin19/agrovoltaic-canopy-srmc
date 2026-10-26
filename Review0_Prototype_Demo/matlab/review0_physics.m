function F = review0_physics()
%REVIEW0_PHYSICS  The SRMC physics functions (sun, irradiance, canopy shadow, PV module) as callable handles.
%   Extracted verbatim from matlab/srmc_run.m (the validated engine: PVGIS +5 %, Blender shading 0.010) so the Review-0 dashboard
%   uses exactly the same equations.   F = review0_physics();  P = F.designParams();   sun = F.sunVec(lat, day, hour);
names = {'declination', 'sunVec', 'extraterrestrialDaily', 'erbs', 'irradiance', 'winIndex', 'tiltFor', 'rowsFor', 'segments', 'rayBlocked', 'groundSVF', 'nsamples', 'groundLightHour', 'panelShadeFraction', 'panelPower', 'lightFactor', 'tempFactor', 'soilFactor', 'ocAt', 'defaults'};
for i = 1:numel(names), F.(names{i}) = str2func(names{i}); end
F.designParams = @designParams;
end

function P = designParams()
%DESIGNPARAMS  Geometry and module parameters of the active preset in design/design.json (same logic as srmc_run.m).
root = fileparts(fileparts(mfilename('fullpath')));
if ~exist(fullfile(root,'design','design.json'),'file'), root = fullfile(fileparts(root),'_project_core'); end
P = defaults(); dz = jsondecode(fileread(fullfile(root,'design','design.json'))); dp = dz.presets.(dz.active);
P.bayLen = dp.bayLen; P.pitch = dp.panelPitch; P.panelW = dp.panelPitch - dp.panelGap; P.rainSlope = dp.rainSlopeDeg;
P.height = dp.clearanceLowestEdge + P.panelW/2*sind(dp.maxTiltDeg); P.tankM3 = dp.cistern.m3; P.stops = dp.stopsDeg(1):5:dp.stopsDeg(2);
P.maxTilt = dp.maxTiltDeg; P.designName = dz.active;
end

function d = declination(n), d = 23.45*sind(360/365*(284+n)); end

function s = sunVec(lat, n, hour)
d = declination(n); w = 15*(hour-12);
s.sz = sind(lat)*sind(d) + cosd(lat)*cosd(d)*cosd(w);
s.sx = -cosd(d)*sind(w);
s.sy = sind(d)*cosd(lat) - cosd(d)*cosd(w)*sind(lat);
end

function ra = extraterrestrialDaily(lat, n)
ph = deg2rad(lat); d = deg2rad(declination(n)); dr = 1 + 0.033*cos(2*pi*n/365);
x = max(-1,min(1,-tan(ph)*tan(d))); ws = acos(x);
ra = 24*60/pi*0.0820*dr*(ws*sin(ph)*sin(d) + cos(ph)*cos(d)*sin(ws));
end

function fd = erbs(kt)
if kt <= 0.22, fd = 1 - 0.09*kt;
elseif kt <= 0.8, fd = 0.9511 - 0.1604*kt + 4.388*kt^2 - 16.638*kt^3 + 12.336*kt^4;
else, fd = 0.165; end
end

function irr = irradiance(sz, n, kt)
if sz < 0.02, irr = struct('ghi',0,'dni',0,'dhi',0); return; end
g0 = 1361*(1+0.033*cos(2*pi*n/365)); ghi = kt*g0*sz; dhi = erbs(kt)*ghi;
irr = struct('ghi',ghi,'dhi',dhi,'dni',min((ghi-dhi)/max(sz,0.1),1000));
end

function w = winIndex(P, hour)
w = size(P.windows,1);
for i = 1:size(P.windows,1), if hour < P.windows(i,2), w = i; return; end, end
end

function t = tiltFor(sun, P, m, hour)
if strcmp(P.tiltMode,'rain'), t = 0;
elseif strcmp(P.tiltMode,'fixed'), t = P.tilt;
elseif strcmp(P.tiltMode,'smart')
    if ~isempty(P.schedule) && nargin >= 4, t = P.schedule(m, winIndex(P,hour)); else, t = P.tilt; end
else, t = max(-P.tiltMax, min(P.tiltMax, atan2d(sun.sx, sun.sz))); end
end

function K = rowsFor(P, sun)
K = min(60, max(6, ceil((P.height*abs(sun.sx)/max(sun.sz,0.05) + P.panelW)/P.pitch) + 2));
end

function S = segments(P, t, K)
if nargin < 3, K = 6; end
c = cosd(t); s = sind(t); h = P.panelW/2; k = (-K:K)'; xc = k*P.pitch + P.pitch/2;
S = [k, xc-h*c, P.height+h*s+0*k, xc+h*c, P.height-h*s+0*k];   % [k x1 z1 x2 z2]
end

function b = rayBlocked(x0, z0, dx, dz, S, skipK)
b = false;
for i = 1:size(S,1)
    if ~isempty(skipK) && S(i,1) == skipK, continue; end
    ex = S(i,4)-S(i,2); ez = S(i,5)-S(i,3); den = dx*ez - dz*ex;
    if abs(den) < 1e-12, continue; end
    qx = S(i,2)-x0; qz = S(i,3)-z0;
    s = (qx*ez - qz*ex)/den; u = (qx*dz - qz*dx)/den;
    if s > 1e-9 && u >= 0 && u <= 1, b = true; return; end
end
end

function v = groundSVF(x, S)
ang = -90 + ((1:24)-0.5)*180/24; vis = 0; tot = 0;
for a = ang
    w = cosd(a); tot = tot + w;
    if ~rayBlocked(x,0,sind(a),cosd(a),S,[]), vis = vis + w; end
end
v = vis/tot;
end

function NS = nsamples(), NS = 40; end

function g = groundLightHour(P, sun, irr, t)
NS = nsamples(); S = segments(P,t,rowsFor(P,sun)); g = zeros(1,NS);
for i = 1:NS
    x = (i-0.5)/NS*P.pitch; lit = ~rayBlocked(x,0,sun.sx,sun.sz,S,[]);
    g(i) = lit*irr.dni*sun.sz + irr.dhi*groundSVF(x,S);
end
end

function fs = panelShadeFraction(P, sun, t)
S = segments(P,t,rowsFor(P,sun)); me = S(S(:,1)==0,:); N = 8; sh = 0;
for i = 1:N
    u = (i-0.5)/N; x = me(2)+u*(me(4)-me(2)); z = me(3)+u*(me(5)-me(3));
    if rayBlocked(x, z+1e-6, sun.sx, sun.sz, S, 0), sh = sh + 1; end
end
fs = sh/N;
end

function [p, gpoa, tc] = panelPower(P, sun, irr, t, tamb, ws)   % Huld (2010) c-Si model as used by PVGIS + ASHRAE incidence-angle modifier
if nargin < 6, ws = 2; end
cosI = max(0, sun.sx*sind(t) + sun.sz*cosd(t)); fs = panelShadeFraction(P,sun,t);
if cosI > 0.02, iam = max(0, 1 - 0.05*(1/cosI - 1)); else, iam = 0; end
gpoa = irr.dni*cosI*iam*(1-fs) + irr.dhi*(1+cosd(t))/2*0.95; tc = tamb;
if gpoa < 1, p = 0; return; end
tc = tamb + gpoa*exp(-3.473 - 0.0594*ws); g = gpoa/1000; T = tc - 25; lg = log(g);
rel = 1 - 0.017237*lg - 0.040465*lg^2 + T*(-0.004702 + 0.000149*lg + 0.000170*lg^2 + 0.000005*T);
p = P.eff*gpoa*max(0,rel)*(1-P.sysLoss);
end

function f = lightFactor(L, c)
if L >= c.lopt, f = 1;
elseif L >= c.lmin, f = 0.35 + 0.65*(L-c.lmin)/(c.lopt-c.lmin);
else, f = 0.35*L/c.lmin; end
end

function f = tempFactor(T, c)
if T < c.t(1), d = c.t(1)-T; elseif T > c.t(2), d = T-c.t(2); else, d = 0; end
f = max(0.2, 1-0.06*d);
end

function s = soilFactor(soil, c, year)
gap = max([0, soil.ph(1)-c.ph(2), c.ph(1)-soil.ph(2)]); fPh = max(0.5, 1-0.15*gap);
fDr = 1;
if soil.drain < c.drain(1), fDr = max(0.4, 1-0.12*(c.drain(1)-soil.drain));
elseif soil.drain > c.drain(2), fDr = max(0.6, 1-0.06*(soil.drain-c.drain(2))); end
fEc = max(0.3, 1-0.07*max(0, soil.ec-c.ec));
fFert = 0.8 + 0.2*min(1, ocAt(soil,year)/1.0);
s = fPh*fDr*fEc*fFert;
end

function v = ocAt(soil, year), v = soil.oc0 + (soil.ocmax-soil.oc0)*(1-exp(-year/2)); end

function P = defaults()
P = struct('bayLen',12.5,'pitch',3.125,'panelW',3.122,'height',5.2,'tiltMode','smart','tilt',45,'tiltMax',60,'stops',15:5:60,'windows',[(5:18)' (6:19)'],'energyWeight',0.5,'angleStep',0.5,'schedule',[], ...
  'eff',0.21,'gamma',-0.004,'noct',45,'sysLoss',0.14, ...
  'runoff',0.85,'firstFlush',0.5,'harvestThreshold',5,'tankM3',300,'irrEff',0.9,'year',0, ...
  'capexPerKWp',60000,'tariff',3.0,'omPct',0.015,'cisternPerM3',7000,'subsidyPct',0,'farmerShare',0.3,'rainSlope',3);
end
