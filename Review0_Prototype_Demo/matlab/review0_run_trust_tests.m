function R = review0_run_trust_tests()
%REVIEW0_RUN_TRUST_TESTS  Tests of the scroll-bar (manual) sensors, the plausibility check, the real-sensor serial fields, the MPPT and the explanation window.
%   Writes ../results/sensor_and_mppt_tests.md/.csv.  (The original 16 decision-logic tests are in review0_run_tests.m and are unchanged.)
here = fileparts(mfilename('fullpath')); od = fullfile(fileparts(here), 'results'); F = review0_physics(); P = F.designParams(); M = review0_mppt(); pm = M.params();
S0 = struct('tempC', 30, 'rh', 55, 'soilPct', 50, 'rain', 0); V0 = struct('lat', 9.88, 'day', 105, 'hour', 12, 'kt', 0.62, 'windMS', 3, 'ghiOverride', NaN, 'parOverride', NaN);
rows = {}; mk = @(id, what, expect, got, pass) {id, what, expect, got, ternary(pass, 'PASS', 'FAIL')};
dM = review0_controller(S0, V0, P, F);
% ---- manual scroll bars ----
V = V0; V.ghiOverride = dM.ghi; V.parOverride = dM.parOpen; d = review0_controller(S0, V, P, F);
rows(end + 1, :) = mk('S01', 'Scroll bars set to the model values give the same decision as the model', 'same angle and PV', sprintf('%.1f vs %.1f deg; %.1f vs %.1f W/m2', d.angle, dM.angle, d.pv, dM.pv), abs(d.angle - dM.angle) < 0.6 && abs(d.pv - dM.pv) < 0.02 * dM.pv);
V = V0; V.ghiOverride = 0.5 * dM.ghi; V.parOverride = 0.5 * dM.parOpen; d = review0_controller(S0, V, P, F, struct('forceAngle', dM.angle)); dm = review0_controller(S0, V0, P, F, struct('forceAngle', dM.angle));
rows(end + 1, :) = mk('S02', 'Half the pyranometer reading -> about half the electricity (same angle)', 'PV ratio 0.40 to 0.60', sprintf('%.2f', d.pv / dm.pv), d.pv / dm.pv > 0.40 && d.pv / dm.pv < 0.60);
V = V0; V.ghiOverride = 300; V.parOverride = 620; dDim = review0_controller(S0, V, P, F); V.ghiOverride = 1000; V.parOverride = 2050; dBri = review0_controller(S0, V, P, F);
rows(end + 1, :) = mk('S03', 'Dim sky (300 W/m2) vs bright sky (1000 W/m2): the angle changes and electricity rises', 'different angle, PV bright > PV dim', sprintf('%.1f vs %.1f deg; %.0f vs %.0f W/m2', dDim.angle, dBri.angle, dDim.pv, dBri.pv), dDim.angle ~= dBri.angle && dBri.pv > dDim.pv);
V = V0; V.ghiOverride = dM.ghi; V.parOverride = 0.5 * dM.parOpen; dLow = review0_controller(S0, V, P, F, struct('forceAngle', dM.angle));
rows(end + 1, :) = mk('S04', 'PAR reading at 50 % of what the pyranometer implies lowers the crop-light score (same angle)', 'lower than the consistent case', sprintf('%.2f vs %.2f', dLow.crop, dm.crop), dLow.crop < dm.crop);
rows(end + 1, :) = mk('S05', 'Plausibility check: PAR/GHI far from 2.06 umol/J is flagged', 'consistent = true, 50 % PAR = false', sprintf('%d / %d', dm.plausible, dLow.plausible), dm.plausible && ~dLow.plausible);
V = V0; V.ghiOverride = 1300; dHi = review0_controller(S0, V, P, F);
rows(end + 1, :) = mk('S06', 'A pyranometer value above the clear-sky limit is flagged', 'ghiClamped = true', sprintf('%d', dHi.ghiClamped), dHi.ghiClamped);
% ---- real sensors on the serial line ----
r = review0_parse('SRMC,100,30.5,50.0,700,0,-1,812,1650'); r7 = review0_parse('SRMC,100,30.5,50.0,700,0,-1');
rows(end + 1, :) = mk('S07', 'Serial line with two extra fields (real pyranometer, PAR) is read; 7-field line leaves them empty', 'ghi 812, par 1650; NaN', sprintf('%.0f, %.0f; %d', r.ghi, r.par, isnan(r7.ghi)), r.ok && r.ghi == 812 && r.par == 1650 && isnan(r7.ghi) && r7.ok);
% ---- MPPT ----
mp = M.mpp(pm, 1000, 25); [v, ~, p] = M.iv(pm, 1000, 25); rows(end + 1, :) = mk('M01', 'Module model at 1000 W/m2, 25 C gives about 400 W at about 41 V', '390-410 W; 39-43 V', sprintf('%.1f W at %.1f V', mp.P, mp.V), mp.P > 390 && mp.P < 410 && mp.V > 39 && mp.V < 43 && abs(max(p) - mp.P) < 1e-9);
m1 = M.mpp(pm, 800, 25); m2 = M.mpp(pm, 800, 65); rows(end + 1, :) = mk('M02', 'Best voltage moves with temperature (hotter cell -> lower voltage)', 'Vmpp(65 C) < Vmpp(25 C) by > 3 V', sprintf('%.1f V vs %.1f V', m2.V, m1.V), m1.V - m2.V > 3);
st = M.init(pm, 30); for k = 1:200, [st, Pw] = M.po(st, pm, 800, 45); end; mm = M.mpp(pm, 800, 45); rows(end + 1, :) = mk('M03', 'P&O tracker settles within 1 % of the true maximum (constant sun)', '>= 99 %', sprintf('%.2f %%', 100 * Pw / mm.P), Pw / mm.P >= 0.99);
t = 0:0.5:60; G = 800 * ones(size(t)); G(t > 20) = 400; G(t > 40) = 900; Tc = 45 * ones(size(t)); Rm = M.simulate(pm, G, Tc);
rows(end + 1, :) = mk('M04', 'Cloud transient (800 -> 400 -> 900 W/m2): tracking efficiency over the run', '>= 98 %', sprintf('%.2f %% (fixed voltage %.2f %%)', Rm.effTrack, Rm.effFixed), Rm.effTrack >= 98);
rows(end + 1, :) = mk('M05', 'MPPT beats a fixed voltage in that run', 'gain > 0 %', sprintf('%+.2f %%', Rm.gainPct), Rm.gainPct > 0);
% ---- explanation window ----
try
    S1 = S0; S1.tempC = 33; S1.rh = 42; dx = review0_controller(S1, V0, P, F, struct('wantCurve', true)); st2 = M.init(pm, 30); for k = 1:60, [st2, Pw2] = M.po(st2, pm, dx.gpoa, dx.tcell); end
    fg = review0_explain([], dx, S1, V0, P, F, struct('wEnergy', 0.5), struct('pm', pm, 'M', M, 'V', st2.V, 'P', Pw2, 'effRun', 99), 'Visible', false); ok = ishandle(fg); close(fg);
    rows(end + 1, :) = mk('X01', 'Explanation window builds; decision equals the full 0.5-degree search', 'gap 0.0 deg', sprintf('gap %.1f deg, score gap %.2f %%', dx.brute.gapDeg, dx.brute.gapJpct), ok && dx.brute.gapDeg <= 0.5);
catch err, rows(end + 1, :) = mk('X01', 'Explanation window builds', 'no error', err.message, false); end
T = cell2table(rows, 'VariableNames', {'id', 'test', 'expected', 'got', 'result'}); writetable(T, fullfile(od, 'sensor_and_mppt_tests.csv'));
fid = fopen(fullfile(od, 'sensor_and_mppt_tests.md'), 'w'); fprintf(fid, '# Tests: scroll-bar sensors, plausibility, real-sensor fields, MPPT, explanation window\n\n| id | test | expected | got | result |\n|---|---|---|---|---|\n');
for i = 1:height(T), fprintf(fid, '| %s | %s | %s | %s | **%s** |\n', T.id{i}, T.test{i}, T.expected{i}, strtrim(T.got{i}), T.result{i}); end
fprintf(fid, '\n%d of %d tests passed.\n', sum(strcmp(T.result, 'PASS')), height(T)); fclose(fid);
fprintf('%d of %d tests passed\n', sum(strcmp(T.result, 'PASS')), height(T)); disp(T(:, {'id', 'result', 'got'})); R = T;
end
function v = ternary(c, a, b), if c, v = a; else, v = b; end, end
