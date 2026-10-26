function T = structural_check(presetName)
%STRUCTURAL_CHECK  First-order structural physics of the wire-tension canopy for every design preset.
%   Wind (IS 875 Part 3 style), panel tube bending, carrier wire-rope tension from sag, stay + anchor, column load.
%   Screening-level hand calculations (ULS), NOT a substitute for a certified structural design.
%   Assumptions are listed in the printed report. Run:  cd matlab; structural_check();   or structural_check('smallholder')
root = rootOf(mfilename('fullpath'));
dz = jsondecode(fileread(fullfile(root,'design','design.json')));
names = fieldnames(dz.presets); if nargin > 0, names = {presetName}; end

% ---- site and material assumptions (edit here) ----
Vb = 39;          % m/s basic wind speed, Madurai (IS 875 Part 3 map value; verify for the site)
k1 = 1.0; k3 = 1.0; k4 = 1.0;                         % risk, topography, importance
g  = 0.20;        % kN/m2 dead load of module + tube clamps
cpDn = 1.0; cpUp = -1.3;                              % net pressure coefficients of a free-standing monopitch roof, held position (conservative)
E = 210e3; fy = 355;                                  % MPa, S355 hot-dip galvanised steel
mbl_k = 0.60;     % kN/mm2: indicative SS316 7x19 rope breaking load = k*d^2  (CHECK the supplier datasheet)
fos = 2.0;        % ULS rope load must stay below MBL/fos
tubes = struct('name',{'CHS 60.3x3 (spec)','CHS 88.9x4','CHS 114.3x4','CHS 139.7x5'},'D',{60.3,88.9,114.3,139.7},'t',{3,4,4,5});

lines = {}; rows = [];
for ip = 1:numel(names)
    p = dz.presets.(names{ip}); sagRatio = p.sagRatio; PW = p.panelPitch - p.panelGap; H = p.clearanceLowestEdge + PW/2*sind(p.maxTiltDeg);
    bay = p.bayLen; sy = bay;                                      % square column grid: carrier lines every 'bay' metres along the panels
    k2 = 0.98; Vz = Vb*k1*k2*k3*k4; pz = 0.6*Vz^2/1000;            % kN/m2 design pressure
    wDn = 1.35*g + 1.5*pz*cpDn; wUp = 1.5*pz*abs(cpUp) - 0.9*g;    % kN/m2 ULS down / net uplift
    % --- pivot tube, continuous over carrier lines spaced sy (support moment ~ wL^2/8)
    D = p.tube.D; t = p.tube.t; Z = pi*(D^4-(D-2*t)^4)/(32*D); MRd = Z*fy/1e6;       % kNm
    wTube = wDn*PW; Mtube = wTube*sy^2/8; utTube = Mtube/MRd; smax = sqrt(8*MRd/wTube);
    % --- carrier wire rope (interior line): uniform load q over span 'bay', sag = ratio*span
    q = wDn*sy; s = sagRatio*bay; Hh = q*bay^2/(8*s); Tw = sqrt(Hh^2 + (q*bay/2)^2); MBL = mbl_k*p.wires.carrierDiaMm^2; utWire = Tw/(MBL/fos);
    % wire utilisation if the sag were increased to L/12
    s12 = bay/12; H12 = q*bay^2/(8*s12); T12 = sqrt(H12^2+(q*bay/2)^2); ut12 = T12/(MBL/fos);
    % --- stay at the outer column balances the end-span horizontal pull Hh; slope of stay to ground
    th = atan2(H+1.05, 6.5); Tstay = Hh/cos(th); MBLs = mbl_k*p.wires.braceDiaMm^2; utStay = Tstay/(MBLs/fos); Vanc = Tstay*sin(th);
    % --- interior column: vertical load from two bays x two lines, pinned-pinned Euler buckling of RHS 220x220x6 (or the preset column size)
    b = p.columnSize*1000; tc = 6; Icol = (b^4-(b-2*tc)^4)/12; Acol = b^2-(b-2*tc)^2; Hc = H+1.15; Ncol = wDn*bay*sy;
    Pcr = pi^2*E*Icol/(Hc*1000)^2/1e3; utCol = Ncol/(0.6*Pcr); utSq = Ncol*1e3/(Acol*fy);
    % --- maximum bay that keeps the carrier wire <= 1.0 (sag ratio fixed)
    Lmax = 8*sagRatio*(MBL/fos)/(wDn*1); % since T ~ H = q L^2/(8 s) = q L/(8 r), q = wDn*L (square grid) -> L = 8 r (MBL/fos)/wDn  (valid for sy = L)
    Lmax12 = sqrt(8*(1/12)*(MBL/fos)/wDn);                                   % same with sag L/12 (T ~ wDn L^2 /(8*(1/12)*L) ... square grid: q = wDn*L, H = q L/(8 r)
    rows = [rows; {names{ip}, bay, H, pz, wDn, utTube, smax, Tw, MBL, utWire, ut12, Tstay, utStay, Vanc, Ncol, utCol, Lmax}]; %#ok<AGROW>
    lines{end+1} = sprintf(['\n==== preset: %s  (%s)\n' ...
        '  panel %.3f m, pivot height %.2f m, bay %.1f m, carrier lines every %.1f m\n' ...
        '  wind: Vz = %.1f m/s, pz = %.2f kN/m2;  ULS down = %.2f kN/m2, net uplift = %.2f kN/m2\n' ...
        '  pivot tube CHS %.1fx%.1f: M = %.1f kNm vs capacity %.2f kNm -> utilisation %.1f  (max support spacing %.2f m; the preset uses %.1f m)\n' ...
        '  carrier rope %d mm: tension %.0f kN vs allowed %.0f kN (MBL %.0f / %.1f) -> utilisation %.2f;  with sag L/12 -> %.2f\n' ...
        '  stay %d mm: %.0f kN -> utilisation %.2f;  anchor pull %.0f kN vertical\n' ...
        '  interior column load %.0f kN vs 0.6 Pcr (%.0f kN) -> utilisation %.2f\n' ...
        ''], ...
        names{ip}, p.label, PW, H, bay, sy, Vz, pz, wDn, wUp, p.tube.D, p.tube.t, Mtube, MRd, utTube, smax, sy, p.wires.carrierDiaMm, Tw, MBL/fos, MBL, fos, utWire, ut12, ...
        p.wires.braceDiaMm, Tstay, utStay, Vanc, Ncol, 0.6*Pcr, utCol); %#ok<AGROW>
    ok = max([utTube utWire utStay utCol]) <= 1.0; lines{end+1} = sprintf('  VERDICT: %s\n', ternary(ok, 'ALL CHECKS PASS (screening level)', 'FAILS - redesign needed')); %#ok<AGROW>
end
% ---- tube options for the first (or only) preset
p = dz.presets.(names{1}); PW = p.panelPitch - p.panelGap; k2 = 0.98; Vz = Vb*k1*k2*k3*k4; pz = 0.6*Vz^2/1000; wDn = 1.35*g + 1.5*pz*cpDn; wTube = wDn*PW;
lines{end+1} = sprintf('\n---- pivot tube options (S355, wTube = %.2f kN/m): maximum support spacing ----\n', wTube);
for it = 1:numel(tubes)
    D = tubes(it).D; t = tubes(it).t; Z = pi*(D^4-(D-2*t)^4)/(32*D); MRd = Z*fy/1e6; I = pi*(D^4-(D-2*t)^4)/64; smaxM = sqrt(8*MRd/wTube); smaxD = (384*E*I/(5*(wTube/1.5)*200))^(1/3)/1e3*1e0;  % deflection L/200, service load
    lines{end+1} = sprintf('  %-18s Z = %5.1f cm3, M_Rd = %5.2f kNm -> bending limit %.1f m ; deflection(L/200) limit %.1f m\n', tubes(it).name, Z/1e3, MRd, smaxM, smaxD); %#ok<AGROW>
end
note = ['\n---- assumptions ----\n' ...
 '  Vb = 39 m/s (IS 875-3, verify), k2 = 0.98, pressure 0.6 Vz^2; held-position net Cp = +1.0 / -1.3 (monopitch roof, conservative); g = 0.20 kN/m2\n' ...
 '  rope MBL = 0.60 d^2 kN (indicative, verify datasheet); ULS rope load limited to MBL/2; Euler column pinned-pinned; tube continuous, M = wL^2/8\n' ...
 '  Not included: dynamic/fatigue wind, snow, seismic, connection design, foundation soil tests, galloping of long ropes.\n'];
lines{end+1} = sprintf(note);
txt = [lines{:}];
fprintf('%s', txt);
od = fullfile(root,'out','physics'); if ~exist(od,'dir'), mkdir(od); end
fid = fopen(fullfile(od,'structural_report.txt'),'w'); fwrite(fid, txt); fclose(fid);
T = cell2table(rows, 'VariableNames', {'preset','bay_m','pivot_height_m','pz_kN_m2','wULS_kN_m2','tube_util','tube_max_span_m','wire_T_kN','wire_MBL_kN','wire_util','wire_util_sagL12','stay_T_kN','stay_util','anchor_V_kN','col_N_kN','col_util','max_bay_m'});
writetable(T, fullfile(od,'structural_summary.csv'));
end

function s = ternary(c, a, b)
if c, s = a; else, s = b; end
end

function r = rootOf(p)
%ROOTOF project root: parent of the matlab folder; if the design file is not there (script copied into a Review folder), use ../_project_core
r = fileparts(fileparts(p));
if ~exist(fullfile(r,'design','design.json'),'file'), r = fullfile(fileparts(r),'_project_core'); end
end
