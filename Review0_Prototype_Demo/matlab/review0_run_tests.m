function R = review0_run_tests()
%REVIEW0_RUN_TESTS  Software-in-the-loop proof for Review 0: unit tests of every rule, a full-day comparison of strategies, and figures.
%   Writes to ../results/: test_results.csv/.md, day_comparison.csv/.md, fig_*.png.
%   The inputs are simulated; this proves the DECISION LOGIC and the physics, not the sensors (those are tested on the bench, see documents/).
here = fileparts(mfilename('fullpath')); od = fullfile(fileparts(here), 'results'); if ~exist(od, 'dir'), mkdir(od); end
F = review0_physics(); P = F.designParams(); lat = 9.88;
S0 = struct('tempC', 30, 'rh', 55, 'soilPct', 50, 'rain', 0); V0 = struct('lat', lat, 'day', 105, 'hour', 12, 'kt', 0.62, 'windMS', 3);
rows = {};

% ---- T1 serial parser ----
r = review0_parse('SRMC,5231,31.0,54.0,712,0,-1'); rows(end + 1, :) = mk('T01', 'Parse a good serial line', 'tempC 31.0, rh 54, soilRaw 712, rain 0', sprintf('tempC %.1f, rh %.0f, soilRaw %d, rain %d', r.tempC, r.rh, r.soilRaw, r.rain), r.ok && r.tempC == 31 && r.rh == 54 && r.soilRaw == 712 && r.rain == 0);
r = review0_parse('SRMC,6000,-999.0,-999.0,700,1,-1'); rows(end + 1, :) = mk('T02', 'DHT11 read failure (-999) is flagged, not used', 'ok line, tempOk = false', sprintf('ok %d, tempOk %d', r.ok, r.tempOk), r.ok && ~r.tempOk);
r = review0_parse('# SRMC firmware v1 board=ESP8266'); rows(end + 1, :) = mk('T03', 'Boot/garbage line is ignored', 'ok = false', sprintf('ok %d', r.ok), ~r.ok);
% ---- T4 soil calibration ----
cal = struct('dry', 1000, 'wet', 420); pct = @(raw) min(100, max(0, 100 * (cal.dry - raw) / (cal.dry - cal.wet)));
rows(end + 1, :) = mk('T04', 'Soil calibration maps dry raw -> 0 %, wet raw -> 100 %, middle -> 50 %', '0 / 100 / 50 %', sprintf('%.0f / %.0f / %.0f %%', pct(1000), pct(420), pct(710)), pct(1000) == 0 && pct(420) == 100 && abs(pct(710) - 50) < 1e-9);
% ---- T5 VPD formula ----
d = review0_controller(struct('tempC', 30, 'rh', 50, 'soilPct', 50, 'rain', 0), V0, P, F); rows(end + 1, :) = mk('T05', 'VPD at 30 C / 50 % RH (Tetens)', '2.12 kPa +- 0.02', sprintf('%.2f kPa', d.vpd), abs(d.vpd - 2.12) < 0.02);
% ---- T6 rain rule ----
S = S0; S.rain = 1; d = review0_controller(S, V0, P, F); rows(end + 1, :) = mk('T06', 'Rain sensor wet -> rain harvest slope', 'angle 3.0 deg, mode RAIN HARVEST', sprintf('%.1f deg, %s', d.angle, d.mode), d.angle == P.rainSlope && strcmp(d.mode, 'RAIN HARVEST'));
% ---- T7 wind rule (both sides of the threshold) ----
V = V0; V.windMS = 15.0; d1 = review0_controller(S0, V, P, F); V.windMS = 14.9; d2 = review0_controller(S0, V, P, F);
rows(end + 1, :) = mk('T07', 'Wind >= 15 m/s -> stow 90 deg; 14.9 m/s -> no stow', '90 deg at 15.0; not 90 at 14.9', sprintf('%.0f deg at 15.0; %.1f deg at 14.9', d1.angle, d2.angle), d1.angle == 90 && d2.angle ~= 90);
% ---- T8 priority: wind beats rain ----
V = V0; V.windMS = 20; S = S0; S.rain = 1; d = review0_controller(S, V, P, F); rows(end + 1, :) = mk('T08', 'Priority: wind stow overrides rain mode', 'angle 90 deg', sprintf('%.0f deg, %s', d.angle, d.mode), d.angle == 90);
% ---- T9 night ----
V = V0; V.hour = 22; d = review0_controller(S0, V, P, F); rows(end + 1, :) = mk('T09', 'Night: parked, no PV', 'angle 15 deg, PV 0', sprintf('%.0f deg, PV %.0f', d.angle, d.pv), d.angle == 15 && d.pv == 0);
% ---- T10 optimiser: chosen angle has the highest J among a brute-force gA ----
cfg = struct('wEnergy', 0.5); d = review0_controller(S0, V0, P, F, cfg); gA = 15:0.5:60; pvG = zeros(size(gA)); cG = zeros(size(gA));
for i = 1:numel(gA), c2 = cfg; c2.forceAngle = gA(i); x = review0_controller(S0, V0, P, F, c2); pvG(i) = x.pv; cG(i) = x.crop; end
JG = 0.5 * pvG / max(pvG) + 0.5 * cG / max(cG); [~, ib] = max(JG);
rows(end + 1, :) = mk('T10', 'Optimiser picks the best angle of a brute-force 0.5 deg grid', sprintf('%.1f deg (grid optimum)', gA(ib)), sprintf('%.1f deg', d.angle), abs(d.angle - gA(ib)) <= 0.5);
% ---- T11 controller vs fixed 45 at noon ----
rows(end + 1, :) = mk('T11', 'Clear noon: controller PV >= fixed 45 deg PV', 'gain >= 0 %', sprintf('%+.1f %%', d.pvGainVs45), d.pvGainVs45 >= -0.01);
% ---- T12 heat/VPD stress changes the decision ----
Sh = S0; Sh.tempC = 38; Sh.rh = 30; dh = review0_controller(Sh, V0, P, F, cfg);
rows(end + 1, :) = mk('T12', 'Heat stress (VPD > 2.5 kPa) lowers required crop light: stress index 1, angle changes', 'stress = 1.00 and angle differs from the cool case', sprintf('stress %.2f, %.1f deg vs %.1f deg', dh.stress, dh.angle, d.angle), dh.stress >= 0.99 && dh.angle ~= d.angle);
% ---- T13 overcast: much less direct beam, PV lower ----
V = V0; V.kt = 0.18; do = review0_controller(S0, V, P, F, cfg); rows(end + 1, :) = mk('T13', 'Overcast sky: pyranometer GHI far below clear sky', 'GHI < 40 % of clear', sprintf('%.0f vs %.0f W/m2', do.ghi, d.ghi), do.ghi < 0.4 * d.ghi);
% ---- T14 irrigation hysteresis ----
pump = false; tank = 50; seq = [60 50 40 34 38 45 54 56 60]; st = zeros(size(seq));
for i = 1:numel(seq), [pump, tank] = review0_irrigation(pump, seq(i), tank, 0); st(i) = pump; end
rows(end + 1, :) = mk('T14', 'Pump hysteresis: OFF above 55, ON below 35, stays ON until 55 %', '0 0 0 1 1 1 1 0 0', sprintf('%d ', st), isequal(st, [0 0 0 1 1 1 1 0 0]));
% ---- T15 empty cistern stops the pump ----
pump = true; tank = 2; [pump, tank] = review0_irrigation(pump, 20, tank, 0); [pump2, ~] = review0_irrigation(pump, 20, tank, 0); rows(end + 1, :) = mk('T15', 'Pump stops when the cistern is empty', 'pump OFF with tank 0', sprintf('pump %d, tank %.0f', pump2, tank), ~pump2 && tank == 0);
% ---- T16 physics identical to the validated engine ----
sun = F.sunVec(9.88, 105, 9.5); irr = F.irradiance(sun.sz, 105, 0.58); g = F.groundLightHour(P, sun, irr, 27); zones = [mean(g(1:10)) mean(g(11:20)) mean(g(21:30)) mean(g(31:40))] / irr.ghi; pw = F.panelPower(P, sun, irr, 27, 31, 2.6);
refZ = [0.1239 0.1243 0.1275 0.1062]; rows(end + 1, :) = mk('T16', 'Zone light and PV equal the JavaScript engine (day 105, 9.5 h, 27 deg)', 'zones 0.1239 0.1243 0.1275 0.1062; PV 100.2 W/m2', sprintf('zones %s; PV %.1f', sprintf('%.4f ', zones), pw), max(abs(zones - refZ)) < 6e-5 && abs(pw - 100.2) < 0.06);
T = cell2table(rows, 'VariableNames', {'id', 'test', 'expected', 'got', 'result'}); writetable(T, fullfile(od, 'test_results.csv'));
fid = fopen(fullfile(od, 'test_results.md'), 'w'); fprintf(fid, '# Software-in-the-loop tests (simulated inputs)\n\n| id | test | expected | got | result |\n|---|---|---|---|---|\n');
for i = 1:height(T), fprintf(fid, '| %s | %s | %s | %s | **%s** |\n', T.id{i}, T.test{i}, T.expected{i}, strtrim(T.got{i}), T.result{i}); end
fprintf(fid, '\n%d of %d tests passed.\n', sum(strcmp(T.result, 'PASS')), height(T)); fclose(fid);
fprintf('%d of %d tests passed\n', sum(strcmp(T.result, 'PASS')), height(T)); disp(T(:, {'id', 'result'}));

% ================= full-day comparison =================
hrs = 6:0.5:18; conds = {'Clear day', 0.62, 30, 55; 'Partly cloudy day', 0.36, 30, 55; 'Hot clear day (VPD stress)', 0.62, 38, 30};
strats = {'Fixed 15 deg (PV-max)', struct('forceAngle', 15); 'Fixed 45 deg', struct('forceAngle', 45); 'East-west sun tracking', 'track'; 'SRMC controller (50/50)', struct('wEnergy', 0.5); 'Energy-only controller (w=1)', struct('wEnergy', 1); 'Crop-only controller (w=0)', struct('wEnergy', 0)};
res = struct(); ang = zeros(size(conds, 1), size(strats, 1), numel(hrs));
out = {};
for c = 1:size(conds, 1)
    S = struct('tempC', conds{c, 3}, 'rh', conds{c, 4}, 'soilPct', 50, 'rain', 0);
    for s = 1:size(strats, 1)
        E = 0; Cn = 0; Cd = 0;
        for hh = 1:numel(hrs)
            V = struct('lat', lat, 'day', 105, 'hour', hrs(hh), 'kt', conds{c, 2}, 'windMS', 3); cfgs = strats{s, 2};
            if ischar(cfgs) && strcmp(cfgs, 'track')
                sn = F.sunVec(lat, 105, hrs(hh)); a = max(-60, min(60, atan2d(sn.sx, sn.sz))); cfgs = struct('forceAngle', a);
            end
            dd = review0_controller(S, V, P, F, cfgs); ang(c, s, hh) = dd.angle;
            E = E + dd.pv * 0.5 / 1000; Cn = Cn + dd.crop * dd.ghi; Cd = Cd + dd.ghi;
        end
        out(end + 1, :) = {conds{c, 1}, strats{s, 1}, E, Cn / max(Cd, eps)};
    end
end
D = cell2table(out, 'VariableNames', {'condition', 'strategy', 'pv_kWh_m2_day', 'crop_light_score'});
for c = 1:size(conds, 1)
    m = strcmp(D.condition, conds{c, 1}); Em = max(D.pv_kWh_m2_day(m)); Cm = max(D.crop_light_score(m));
    D.pv_pct_of_best(m) = 100 * D.pv_kWh_m2_day(m) / Em; D.crop_pct_of_best(m) = 100 * D.crop_light_score(m) / Cm;
end
D.combined_pct = (D.pv_pct_of_best + D.crop_pct_of_best) / 2; writetable(D, fullfile(od, 'day_comparison.csv'));
fid = fopen(fullfile(od, 'day_comparison.md'), 'w'); fprintf(fid, '# One-day comparison (day 105, TCE, 6-18 h in 0.5 h steps, simulated sky)\n\nPV in kWh per m2 of panel per day; crop-light score = irradiance-weighted mean of the zone light factors (1 = every zone gets the light its crop needs). "of best" = percentage of the best strategy in that condition.\n\n| condition | strategy | PV kWh/m2/day | crop score | PV % of best | crop % of best | average of the two |\n|---|---|---|---|---|---|---|\n');
for i = 1:height(D), fprintf(fid, '| %s | %s | %.3f | %.3f | %.1f | %.1f | **%.1f** |\n', D.condition{i}, D.strategy{i}, D.pv_kWh_m2_day(i), D.crop_light_score(i), D.pv_pct_of_best(i), D.crop_pct_of_best(i), D.combined_pct(i)); end
fclose(fid); disp(D);

% ---- figures ----
f = mkfig([100 100 980 520]); hold on; cols = lines(size(strats, 1)); m = strcmp(D.condition, conds{1, 1}); sub = D(m, :);
for s = 1:size(strats, 1), scatter(sub.crop_light_score(s), sub.pv_kWh_m2_day(s), 140, cols(s, :), 'filled'); text(sub.crop_light_score(s) + 0.004, sub.pv_kWh_m2_day(s), sub.strategy{s}, 'FontSize', 9); end
xlabel('crop-light score (1 = every crop zone gets the light it needs)'); ylabel('PV energy (kWh per m^2 panel per day)'); grid on; title('Clear day: energy vs crop light for each strategy (simulated sky, TCE)');
exportgraphics(f, fullfile(od, 'fig_energy_vs_crop_clear_day.png'), 'Resolution', 150); close(f);
f = mkfig([100 100 980 520]); hold on; for c = 1:3, a = squeeze(ang(c, 4, :)); plot(hrs, a, '-o', 'LineWidth', 1.6, 'DisplayName', ['SRMC controller: ' conds{c, 1}]); end
sn = arrayfun(@(h) max(-60, min(60, atan2d(F.sunVec(lat, 105, h).sx, F.sunVec(lat, 105, h).sz))), hrs); plot(hrs, sn, 'k--', 'LineWidth', 1.4, 'DisplayName', 'pure sun tracking (east-west)');
xlabel('solar hour'); ylabel('panel angle (deg)'); legend('Location', 'best'); grid on; title('Angle chosen through the day: controller vs pure sun tracking'); exportgraphics(f, fullfile(od, 'fig_angle_through_day.png'), 'Resolution', 150); close(f);
% weight sweep at noon
w = 0:0.1:1; pvw = zeros(size(w)); cw = zeros(size(w)); aw = zeros(size(w));
for i = 1:numel(w), dd = review0_controller(S0, V0, P, F, struct('wEnergy', w(i))); pvw(i) = dd.pv; cw(i) = dd.crop; aw(i) = dd.angle; end
f = mkfig([100 100 980 480]); yyaxis left; plot(w * 100, pvw, '-o', 'LineWidth', 1.6); ylabel('PV (W/m^2 of panel)'); yyaxis right; plot(w * 100, cw, '-s', 'LineWidth', 1.6); ylabel('crop-light score'); xlabel('controller weight on energy (%)'); grid on; title('Noon, clear: moving the objective between crop and energy'); exportgraphics(f, fullfile(od, 'fig_weight_sweep_noon.png'), 'Resolution', 150); close(f);
writetable(table(w' * 100, aw', pvw', cw', 'VariableNames', {'energy_weight_pct', 'angle_deg', 'pv_Wm2', 'crop_score'}), fullfile(od, 'weight_sweep_noon.csv'));
R = struct('tests', T, 'day', D);
end

function v = ternary(c, a, b), if c, v = a; else, v = b; end, end
function f = mkfig(pos), f = figure('Visible', 'off', 'Position', pos); try, theme(f, 'light'); catch, end, end
function r = mk(id, what, expect, got, pass), r = {id, what, expect, got, ternary(pass, 'PASS', 'FAIL')}; end
