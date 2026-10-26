function res = srmc_run(climId, soilId, params, opts)
%SRMC_RUN  Soil-Regeneration Microclimatic Chamber (SRMC) simulation engine - MATLAB version.
%   res = srmc_run()                          % TCE ground, red sandy loam, defaults
%   res = srmc_run('hill_ooty','hill_forest') % any climate / soil id from data/*.json
%   res = srmc_run('tce_madurai','loam',struct('pitch',12.5,'tiltMode','fixed','tilt',30))
%
%   Same equations as engine/srmc_engine.js (the live digital twin) - results are cross-checked
%   by tools/crosscheck.m. Run on MATLAB Online by uploading the srmc-twin folder.
%   srmc_run(clim, soil, params, struct('plots',false,'quiet',true,'export',false)) runs silently (used by srmc_master for sweeps).
%   Outputs: struct `res`, out/matlab_results.json, and PNG figures in out/.

if nargin < 1, climId = 'tce_madurai'; end
if nargin < 2, soilId = 'red_sandy_loam'; end
if nargin < 3, params = struct(); end
O = struct('plots', true, 'quiet', false, 'export', true); if nargin >= 4, fo = fieldnames(opts); for i = 1:numel(fo), O.(fo{i}) = opts.(fo{i}); end, end
root = rootOf(mfilename('fullpath'));
clims = jsondecode(fileread(fullfile(root,'data','climates.json')));
soils = jsondecode(fileread(fullfile(root,'data','soils.json')));
crops = jsondecode(fileread(fullfile(root,'data','crops.json')));
clim = clims(strcmp({clims.id}, climId));  soil = soils(strcmp({soils.id}, soilId));
assert(~isempty(clim) && ~isempty(soil), 'unknown climate or soil id');
clim.tmean = clim.tmean(:)'; clim.trange = clim.trange(:)'; clim.rain = clim.rain(:)';
clim.raindays = clim.raindays(:)'; clim.kt = clim.kt(:)'; clim.wind = clim.wind(:)';
if isfield(params,'ktScale'), clim.kt = min(0.85, clim.kt*params.ktScale); end      % scenario hooks used by srmc_sensitivity
if isfield(params,'rainScale'), clim.rain = clim.rain*params.rainScale; end

P = defaults();
dz = jsondecode(fileread(fullfile(root,'design','design.json'))); dp = dz.presets.(dz.active);     % geometry comes from design/design.json
P.bayLen = dp.bayLen; P.pitch = dp.panelPitch; P.panelW = dp.panelPitch - dp.panelGap; P.rainSlope = dp.rainSlopeDeg;
P.height = dp.clearanceLowestEdge + P.panelW/2*sind(dp.maxTiltDeg); P.tankM3 = dp.cistern.m3; P.stops = dp.stopsDeg(1):5:dp.stopsDeg(2);
f = fieldnames(params); for i = 1:numel(f), P.(f{i}) = params.(f{i}); end

if strcmp(P.tiltMode, 'smart')
    P0 = P; P0.tiltMode = 'fixed'; a0 = annualLight(P0, clim, []); zm0 = monthStrips(a0);
    zoneCrop = pickCrops(crops, soil, clim, P, a0, zm0);
    P.schedule = optimizeSchedule(P, clim, soil, crops(zoneCrop));
    annual = annualLight(P, clim, []); zoneMonthly = monthStrips(annual);
else
    annual = annualLight(P, clim, []); zoneMonthly = monthStrips(annual);
    zoneCrop = pickCrops(crops, soil, clim, P, annual, zoneMonthly);
end
wb  = waterBalance(P, clim, soil, crops, zoneCrop, zoneMonthly, P.tankM3);
eco = economics(P, annual, wb, P.tankM3, crops(zoneCrop));

res = struct('params',P,'clim',clim.id,'soil',soil.id,'annual',annual,'zoneMonthly',zoneMonthly, ...
             'zoneCrop',{{crops(zoneCrop).id}},'wb',wb,'eco',eco);

% ---- export numbers for cross-check against the JS twin ----
out = struct('meanStrip',annual.meanStrip,'pvKWhPerM2',annual.pvKWhPerM2,'ghi',annual.ghi, ...
    'zoneCrops',{{crops(zoneCrop).id}},'yield',[wb.zones.yield],'waterRatio',[wb.zones.waterRatio], ...
    'harvested',wb.harvested,'overflow',wb.overflow,'demand',wb.demand,'unmet',wb.unmet, ...
    'kwp',eco.kwp,'kwh',eco.kwh,'capex',eco.capex,'solarRev',eco.solarRev,'cropNet',eco.cropNet,'payback',eco.payback,'farmerAnnual',eco.farmerAnnual,'industryNet',eco.industryNet);
if O.export
    outDir = fullfile(root,'out'); if ~exist(outDir,'dir'), mkdir(outDir); end
    fid = fopen(fullfile(outDir,'matlab_results.json'),'w'); fwrite(fid, jsonencode(out,'PrettyPrint',true)); fclose(fid);
end
if ~O.quiet
    fprintf('\nSRMC  |  %s  |  %s\n', clim.name, soil.name);
    fprintf('Mean ground light per zone : %s  (fraction of open field)\n', mat2str(round(annual.meanStrip,3)));
    fprintf('PV yield                   : %.0f kWh/m2 panel/yr  (%.0f kWh/kWp)\n', annual.pvKWhPerM2, eco.kwh/eco.kwp);
    for z = 1:4, fprintf('  Zone %d  %-22s yield %6.2f t/ha  (water ratio %.2f)\n', z, wb.zones(z).name, wb.zones(z).yield, wb.zones(z).waterRatio); end
    fprintf('Rain harvested %.0f m3 | irrigation demand %.0f m3 | unmet (borewell) %.0f m3\n', wb.harvested, wb.demand, wb.unmet);
    fprintf('Payback %.1f years | farmer income %.0f INR/month (industry pays INR %.1f/kWh, farmer share %.0f%%)\n\n', eco.payback, eco.farmerMonthlyAvg, P.tariff, 100*P.farmerShare);
end
if O.plots
    tilts = 0:15:90; sweep = struct('tilts',tilts,'pv',zeros(size(tilts)),'light',zeros(size(tilts)));
    for i = 1:numel(tilts), a = annualLight(P, clim, tilts(i)); sweep.pv(i) = a.pvKWhPerM2; sweep.light(i) = a.meanLight*100; end
    res.sweep = sweep;
    srmc_plots(res, P, clim, soil, crops);
end
end

function zm = monthStrips(a)
zm = zeros(4,12); for z = 1:4, for k = 1:12, zm(z,k) = a.months(k).strip(z); end, end
end
function zoneCrop = pickCrops(crops, soil, clim, P, a, zm)
zoneCrop = zeros(1,4); used = [];
for z = 1:4
    rk = rankCrops(crops, soil, clim, P.year, zm(z,:));
    for q = 1:numel(rk)
        idx = rk(q).idx; if ~ismember(idx, used), zoneCrop(z) = idx; used(end+1) = idx; break; end %#ok<AGROW>
    end
end
end
% =====================================================================
function P = defaults()
P = struct('bayLen',12.5,'pitch',3.125,'panelW',3.122,'height',5.2,'tiltMode','smart','tilt',45,'tiltMax',60,'stops',15:5:60,'windows',[(5:18)' (6:19)'],'energyWeight',0.5,'angleStep',0.5,'schedule',[], ...
  'eff',0.21,'gamma',-0.004,'noct',45,'sysLoss',0.14, ...
  'runoff',0.85,'firstFlush',0.5,'harvestThreshold',5,'tankM3',300,'irrEff',0.9,'year',0, ...
  'capexPerKWp',60000,'tariff',3.0,'omPct',0.015,'cisternPerM3',7000,'subsidyPct',0,'farmerShare',0.3,'rainSlope',3);
end
function v = DIM(), v = [31 28 31 30 31 30 31 31 30 31 30 31]; end
function v = CUM(), v = [0 31 59 90 120 151 181 212 243 273 304 334]; end
function v = MID(), v = [17 47 75 105 135 162 198 228 258 288 318 344]; end

% ---------------- solar geometry & irradiance ----------------
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
function et = hargreaves(lat, n, tmean, trange)
et = max(0, 0.0023*(tmean+17.8)*sqrt(max(trange,0.1))*extraterrestrialDaily(lat,n)/2.45);
end

% ---------------- canopy geometry (East-West cross-section) ----------------
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

% ---------------- monthly light & energy ----------------
function r = monthLight(P, clim, m, tiltOverride)
NS = nsamples(); n = MID(); n = n(m); kt = clim.kt(m); zones = zeros(1,NS); open = 0; pvWh = 0; ghiWh = 0; poaWh = 0;
Q = P; if ~isempty(tiltOverride), Q.tiltMode = 'fixed'; Q.tilt = tiltOverride; end
for hh = 0:23
    hour = hh + 0.5; sun = sunVec(clim.lat, n, hour);
    if sun.sz < 0.02, continue; end
    irr = irradiance(sun.sz, n, kt); t = tiltFor(sun, Q, m, hour);
    zones = zones + groundLightHour(Q, sun, irr, t); open = open + irr.ghi;
    tamb = clim.tmean(m) + clim.trange(m)/2*sin(2*pi*(hour-9)/24);
    [p, gpoa] = panelPower(Q, sun, irr, t, tamb, clim.wind(m));
    pvWh = pvWh + p; ghiWh = ghiWh + irr.ghi; poaWh = poaWh + gpoa;
end
strip = zeros(1,4);
for z = 1:4, strip(z) = mean(zones((z-1)*NS/4+1 : z*NS/4)) / max(open,1e-9); end
r = struct('strip',strip,'profile',zones/max(open,1e-9),'pvKWhPerM2Day',pvWh/1000,'ghiKWhPerM2Day',ghiWh/1000,'poaKWhPerM2Day',poaWh/1000);
end
function a = annualLight(P, clim, tiltOverride)
for m = 1:12, months(m) = monthLight(P, clim, m, tiltOverride); end %#ok<AGROW>
d = DIM();
a.months = months;
a.pvKWhPerM2 = sum([months.pvKWhPerM2Day].*d);
a.ghi = sum([months.ghiKWhPerM2Day].*d);
strips = reshape([months.strip],4,12);
a.meanStrip = (strips*d')'/365;
a.meanLight = mean(a.meanStrip);
end


% ---------------- SRMC-DT controller ----------------
function ev = windowEval(P, clim, m, angle, win)
NS = nsamples(); mid = MID(); n = mid(m); kt = clim.kt(m); zones = zeros(1,NS); open = 0; pv = 0; ghiDay = 0;
Q = P; Q.tiltMode = 'fixed'; Q.tilt = angle;
for hh = 0:23
    hour = hh + 0.5; sun = sunVec(clim.lat, n, hour); if sun.sz < 0.02, continue; end
    irr = irradiance(sun.sz, n, kt); ghiDay = ghiDay + irr.ghi;
    if hour < win(1) || hour >= win(2), continue; end
    zones = zones + groundLightHour(Q, sun, irr, angle); open = open + irr.ghi;
    tamb = clim.tmean(m) + clim.trange(m)/2*sin(2*pi*(hour-9)/24);
    pw = panelPower(Q, sun, irr, angle, tamb, clim.wind(m)); pv = pv + pw;
end
strip = zeros(1,4);
for z = 1:4, strip(z) = mean(zones((z-1)*NS/4+1 : z*NS/4)) / max(open,1e-9); end
ev = struct('pv', pv/1000, 'strip', strip, 'share', open/max(ghiDay,1e-9));
end
function sched = optimizeSchedule(P, clim, soil, zc)      % zc: 4 crop structs
sched = zeros(12, size(P.windows,1)); info = cell(1,4);
for k = 1:4
    c = zc(k); [mw, tm] = seasonInfo(c, clim, c.sow-1);
    info{k} = struct('c', c, 'mw', mw, 'tf', tempFactor(tm, c), 'sf', soilFactor(soil, c, P.year));
end
for m = 1:12
    for w = 1:size(P.windows,1)
        ang = P.stops(:)'; pv = zeros(1,0); crop = zeros(1,0); sh = zeros(1,0); strips = zeros(0,4);
        for ia = 1:numel(ang), ev = windowEval(P, clim, m, ang(ia), P.windows(w,:)); pv(ia) = ev.pv; sh(ia) = ev.share; strips(ia,:) = ev.strip; end
        [J, crop, pvMax, cropMax] = scoreAll(P, info, m, pv, sh, strips);
        best = 1; for ia = 2:numel(ang), if J(ia) > J(best) + 1e-9, best = ia; end, end
        cs = P.stops(2) - P.stops(1);
        if P.angleStep < cs
            lo = max(P.stops(1), ang(best) - cs); hi = min(P.stops(end), ang(best) + cs); a = lo;
            while a <= hi + 1e-9
                aa = round(a*1000)/1000;
                if ~any(abs(ang - aa) < 1e-6)
                    ev = windowEval(P, clim, m, aa, P.windows(w,:)); ang(end+1) = aa; pv(end+1) = ev.pv; sh(end+1) = ev.share; strips(end+1,:) = ev.strip; %#ok<AGROW>
                end
                a = a + P.angleStep;
            end
            [J, crop, pvMax, cropMax] = scoreAll(P, info, m, pv, sh, strips);   %#ok<ASGLU>
            best = 1; for ia = 2:numel(ang), if J(ia) > J(best) + 1e-9, best = ia; end, end
        end
        sched(m,w) = ang(best);
    end
end
end

function [J, crop, pvMax, cropMax] = scoreAll(P, info, m, pv, sh, strips)
n = numel(pv); crop = zeros(1,n);
for ia = 1:n
    for k = 1:4
        z = info{k}; if z.mw(m) > 0
            crop(ia) = crop(ia) + sh(ia)*z.c.ym*lightFactor(strips(ia,k), z.c)*z.tf*z.sf*z.c.price;
        end
    end
end
pvMax = max(max(pv),1e-9); cropMax = max(max(crop),1e-9);
J = P.energyWeight*pv/pvMax + (1-P.energyWeight)*crop/cropMax;
end

% ---------------- soils, crops ----------------
function v = ocAt(soil, year), v = soil.oc0 + (soil.ocmax-soil.oc0)*(1-exp(-year/2)); end
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
function [mw, tmean] = seasonInfo(c, clim, sowMonth0)
cum = CUM(); sowDoy = cum(sowMonth0+1)+1; mw = zeros(1,12);
for d = 0:c.days-1
    doy = mod(sowDoy-1+d, 365); m = find(cum <= doy, 1, 'last'); mw(m) = mw(m)+1;
end
tmean = sum(clim.tmean.*mw)/sum(mw);
end
function [y, lf, tf, sf] = potentialYield(c, soil, L, Tm, year)
sf = soilFactor(soil,c,year); lf = lightFactor(L,c); tf = tempFactor(Tm,c); y = c.ym*lf*tf*sf;
end
function R = rankCrops(crops, soil, clim, year, zoneMonthly)
net = zeros(1,numel(crops));
for i = 1:numel(crops)
    c = crops(i); [mw, Tm] = seasonInfo(c, clim, c.sow-1); L = sum(zoneMonthly.*mw)/sum(mw);
    y = potentialYield(c, soil, L, Tm, year); net(i) = y*1000*c.price - c.cost;
end
[~, order] = sort(net, 'descend'); R = struct('idx', num2cell(order));
end

% ---------------- daily water balance ----------------
function rain = rainSchedule(clim)
rain = zeros(1,365); d = DIM(); cum = CUM();
for m = 1:12
    nd = clim.raindays(m); tot = clim.rain(m); if nd < 1 || tot <= 0, continue; end
    k = 0:nd-1; w = 1 + 0.6*sin(2.3*(k+1)); w = w/sum(w);
    for kk = k
        day = min(d(m)-1, floor((kk+0.5)*d(m)/nd)); rain(cum(m)+day+1) = rain(cum(m)+day+1) + tot*w(kk+1);
    end
end
end
function et0 = dailyET0(clim)
et0 = zeros(1,365); cum = CUM();
for d = 0:364, m = find(cum <= d, 1, 'last'); et0(d+1) = hargreaves(clim.lat, d+1, clim.tmean(m), clim.trange(m)); end
end
function wb = waterBalance(P, clim, soil, crops, zoneCrop, zoneMonthly, tankM3)
rain = rainSchedule(clim); et0 = dailyET0(clim); cum = CUM();
cover = min(1, P.panelW/P.pitch); catchArea = 10000*cover; area = 2500;
tank = 0; harvested = 0; overflow = 0; demand = 0; supplied = 0;
tankSeries = zeros(1,365); harvSeries = zeros(1,365); irrSeries = zeros(1,365);
for z = 1:4
    c = crops(zoneCrop(z)); taw = 1000*(soil.fc-soil.wp)*c.zr;
    Z(z) = struct('c',c,'taw',taw,'raw',c.p*taw,'Dr',0,'pend',0,'etc',0,'eta',0,'irr',0,'rain',0,'perc',0,'run',0, ...
        'sowDoy',cum(c.sow)+1); %#ok<AGROW>
end
for d = 0:364
    m = find(cum <= d, 1, 'last'); R = rain(d+1); rGround = R;
    if R >= P.harvestThreshold && R > 0
        inM3 = max(0,R-P.firstFlush)*catchArea*P.runoff/1000; add = min(tankM3-tank, inM3);
        tank = tank + add; harvested = harvested + add; overflow = overflow + inM3 - add;
        harvSeries(d+1) = add; rGround = R*(1-cover);
    end
    dayDraw = 0;
    for z = 1:4
        c = Z(z).c; ph = mod(d-(Z(z).sowDoy-1)+365, 365); inSeason = ph < c.days;
        if ph == 0, Z(z).Dr = 0; end
        if inSeason, kc = c.kc; else, kc = 0.2; end
        L = zoneMonthly(z,m); etc = kc*et0(d+1)*(0.5+0.5*L);
        if Z(z).Dr > Z(z).raw, ks = max(0,(Z(z).taw-Z(z).Dr)/(Z(z).taw-Z(z).raw)); else, ks = 1; end
        eta = ks*etc; infil = min(rGround, soil.infil);
        Z(z).run = Z(z).run + rGround - infil; Z(z).rain = Z(z).rain + infil;
        Z(z).Dr = Z(z).Dr - infil + eta;
        if Z(z).Dr < 0, Z(z).perc = Z(z).perc - Z(z).Dr; Z(z).Dr = 0; end
        if Z(z).Dr > Z(z).taw, Z(z).Dr = Z(z).taw; end
        if inSeason
            Z(z).etc = Z(z).etc + etc; Z(z).eta = Z(z).eta + eta;
            Z(z).pend = min(Z(z).pend, Z(z).Dr);
            if Z(z).Dr >= Z(z).raw
                need = Z(z).Dr; vol = need*area/1000/P.irrEff;
                demand = demand + max(0, need-Z(z).pend)*area/1000/P.irrEff;
                give = min(vol, tank); tank = tank - give; supplied = supplied + give; dayDraw = dayDraw + give;
                net = give*P.irrEff*1000/area; Z(z).Dr = Z(z).Dr - net; Z(z).irr = Z(z).irr + net; Z(z).pend = Z(z).Dr;
            end
        end
    end
    tankSeries(d+1) = tank; irrSeries(d+1) = dayDraw;
end
for z = 1:4
    c = Z(z).c; if Z(z).etc > 0, ratio = Z(z).eta/Z(z).etc; else, ratio = 1; end
    [mw, Tm] = seasonInfo(c, clim, c.sow-1); L = sum(zoneMonthly(z,:).*mw)/sum(mw);
    [py, lf, tf, sf] = potentialYield(c, soil, L, Tm, P.year);
    relW = max(0, 1-c.ky*(1-ratio)); Ya = py*relW; ha = area/10000;
    zs(z) = struct('crop',c.id,'name',c.name,'light',L,'tmean',Tm,'lf',lf,'tf',tf,'sf',sf,'waterRatio',ratio,'relWater',relW, ...
        'potYield',py,'yield',Ya,'etc',Z(z).etc,'eta',Z(z).eta,'irrMm',Z(z).irr,'revenue',Ya*1000*c.price*ha, ...
        'cost',c.cost*ha,'net',(Ya*1000*c.price-c.cost)*ha); %#ok<AGROW>
end
wb = struct('zones',zs,'tankSeries',tankSeries,'harvSeries',harvSeries,'irrSeries',irrSeries,'rain',rain,'et0',et0, ...
    'harvested',harvested,'overflow',overflow,'demand',demand,'supplied',supplied,'unmet',max(0,demand-supplied), ...
    'cover',cover,'catchArea',catchArea);
end

% ---------------- economics (per hectare) ----------------
function e = economics(P, annual, wb, tankM3, zc)
cover = min(1, P.panelW/P.pitch); panelArea = 10000*cover; kwp = panelArea*P.eff; kwh = annual.pvKWhPerM2*panelArea;
capex = kwp*P.capexPerKWp*(1-P.subsidyPct/100) + tankM3*P.cisternPerM3;
solarRev = kwh*P.tariff; om = kwp*P.capexPerKWp*P.omPct;
cropNet = sum([wb.zones.net]); cropRev = sum([wb.zones.revenue]); annualNet = solarRev - om + cropNet;
if annualNet > 0, pb = capex/annualNet; else, pb = NaN; end
dm = DIM(); cum = CUM(); kwhM = [annual.months.pvKWhPerM2Day].*dm*panelArea; solarM = kwhM*P.tariff; farmerSolarM = solarM*P.farmerShare; cropM = zeros(1,12);
for z = 1:4                                                  % crop income arrives in the harvest month, solar income every month
    c = zc(z); doy = mod(cum(c.sow) + c.days, 365); m = find(cum <= doy, 1, 'last'); cropM(m) = cropM(m) + wb.zones(z).net;
end
farmerM = farmerSolarM + cropM; farmerAnnual = sum(farmerM);
e = struct('kwp',kwp,'kwh',kwh,'specificYield',kwh/kwp,'capex',capex,'solarRev',solarRev,'om',om, ...
    'cropRev',cropRev,'cropNet',cropNet,'annualNet',annualNet,'payback',pb, ...
    'monthly',struct('kwh',kwhM,'solar',solarM,'farmerSolar',farmerSolarM,'crop',cropM,'farmer',farmerM), ...
    'farmerAnnual',farmerAnnual,'farmerMonthlyAvg',farmerAnnual/12,'industryNet',solarRev*(1-P.farmerShare)-om,'co2t',kwh*0.71/1000);
end

function r = rootOf(p)
%ROOTOF project root: parent of the matlab folder; if the design file is not there (script copied into a Review folder), use ../_project_core
r = fileparts(fileparts(p));
if ~exist(fullfile(r,'design','design.json'),'file'), r = fullfile(fileparts(r),'_project_core'); end
end
