function T = srmc_sc_accuracy()
%SRMC_SC_ACCURACY  Accuracy of the six-sensor controller measured in MATLAB.
%   Reads results/accuracy_cases.json (node ../sensor_controller/make_accuracy_cases.js): truth states, the noisy sensor readings the controller saw
%   (single reading for v1, 5 readings for v2) and the JavaScript decisions. MATLAB repeats the decisions from the SAME readings with its own controller
%   (srmc_sensor_controller + srmc_sensor_fuse), then scores every angle with MATLAB's physics against the best possible angle (perfect knowledge):
%       electricity % of best, crop light value % of best, combined score J % of best, tilt-angle error in degrees.
%   Writes results/accuracy_matlab.csv, results/accuracy_matlab.json, figures fig_matlab_accuracy.png and fig_matlab_angles.png (MATLAB figures).
here = fileparts(mfilename('fullpath')); sc = fullfile(fileparts(here), 'sensor_controller'); res = fullfile(sc, 'results');
addpath(fullfile(fileparts(fileparts(here)), 'Review0_Prototype_Demo', 'matlab'));
C = jsondecode(fileread(fullfile(res, 'accuracy_cases.json'))); F = review0_physics(); P = F.designParams();
ctx = struct('F', F, 'P', P, 'zones', C.zones, 'monthW', C.monthW, 'lat', C.lat, 'w', C.wEnergy, 'maxStep', 90, 'guard', true);
ctxNG = ctx; ctxNG.guard = false; w = C.wEnergy; n = numel(C.cases); cand = 15:0.5:60;
M = struct('ang_v1', zeros(n,1), 'ang_v2', zeros(n,1), 'orc', zeros(n,1), 'Jv1', zeros(n,1), 'Jv2', zeros(n,1), 'pv1', zeros(n,1), 'pv2', zeros(n,1), 'cr1', zeros(n,1), 'cr2', zeros(n,1), 'Jjs2', zeros(n,1), 'w', zeros(n,1));
for i = 1:n
    c = C.cases(i); sen1 = c.single; sen1.rain = false; list = C.cases(i).list; for k = 1:numel(list), list(k).rain = false; end
    d1 = srmc_sensor_controller(sen1, c.prev1, ctxNG); d2 = srmc_sensor_controller(srmc_sensor_fuse(list), c.prev2, ctx);
    % truth state: perfect sensors, scored with MATLAB physics
    sun = F.sunVec(C.lat, c.day, c.hour); irr = F.irradiance(sun.sz, c.day, c.kt);
    tr = struct('ghi', irr.ghi, 'parUm', 0, 'T', c.T, 'RH', c.RH, 'soil', c.soilPct, 'rain', false, 'wind', 3, 'day', c.day, 'hour', c.hour);
    [~, tools] = srmc_sensor_controller(tr, 30, ctx);
    E = arrayfun(@(a) tools.evalAngle(a, 1), cand); pm = max([E.pv]); cm = max([E.crop]); cr = @(e) (cm > 1e-6) * e.crop / max(cm, 1e-9) + (cm <= 1e-6);
    J = @(e) w*e.pv/pm + (1-w)*cr(e); [Jo, io] = max(arrayfun(J, E));
    e1 = tools.evalAngle(d1.angle, 1); e2 = tools.evalAngle(d2.angle, 1); ej = tools.evalAngle(c.js.v2, 1);
    M.ang_v1(i) = d1.angle; M.ang_v2(i) = d2.angle; M.orc(i) = cand(io); M.Jv1(i) = J(e1)/Jo; M.Jv2(i) = J(e2)/Jo; M.Jjs2(i) = J(ej)/Jo;
    M.pv1(i) = e1.pv/pm; M.pv2(i) = e2.pv/pm; M.cr1(i) = cr(e1); M.cr2(i) = cr(e2); M.w(i) = irr.ghi;
    if mod(i, 20) == 0, fprintf('%d / %d\n', i, n); end
end
wt = M.w / sum(M.w); S = struct();
S.v1 = struct('electricity_pct', 100*sum(wt.*M.pv1), 'crop_pct', 100*sum(wt.*M.cr1), 'J_pct', 100*sum(wt.*M.Jv1), 'angle_rmse_deg', sqrt(mean((M.ang_v1 - M.orc).^2)));
S.v2 = struct('electricity_pct', 100*sum(wt.*M.pv2), 'crop_pct', 100*sum(wt.*M.cr2), 'J_pct', 100*sum(wt.*M.Jv2), 'angle_rmse_deg', sqrt(mean((M.ang_v2 - M.orc).^2)));
js = [C.cases.js]; angJs = [js.v2]'; S.js_v2_in_matlab = struct('J_pct', 100*sum(wt.*M.Jjs2), 'angle_rmse_deg', sqrt(mean((angJs - M.orc).^2)));
S.same_angle_js_vs_matlab_v2 = struct('identical', sum(abs(angJs - M.ang_v2) < 1e-9), 'of', n, 'max_diff_deg', max(abs(angJs - M.ang_v2)));
S.cases = n; T = table({'v1: single reading, no guard'; 'v2: median of 5 + guard'}, [S.v1.electricity_pct; S.v2.electricity_pct], [S.v1.crop_pct; S.v2.crop_pct], [S.v1.J_pct; S.v2.J_pct], [S.v1.angle_rmse_deg; S.v2.angle_rmse_deg], 'VariableNames', {'version', 'electricity_pct', 'crop_pct', 'J_pct', 'angle_rmse_deg'});
writetable(T, fullfile(res, 'accuracy_matlab.csv')); fid = fopen(fullfile(res, 'accuracy_matlab.json'), 'w'); fwrite(fid, jsonencode(S, 'PrettyPrint', true)); fclose(fid); disp(T); disp(S.same_angle_js_vs_matlab_v2);
% ---- MATLAB figures
f = figure('Visible', 'off', 'Position', [100 100 1100 430]); try, theme(f, 'light'); catch, end
subplot(1,2,1); b = bar([S.v1.electricity_pct S.v2.electricity_pct; S.v1.crop_pct S.v2.crop_pct; S.v1.J_pct S.v2.J_pct]); set(gca, 'XTickLabel', {'electricity', 'crop light value', 'combined score'}); ylim([60 102]); ylabel('% of the best possible'); grid on; legend('v1: one reading', 'v2: median of 5 + fault guard', 'Location', 'southeast'); title(sprintf('MATLAB accuracy test, %d cases', n));
subplot(1,2,2); histogram(M.ang_v1 - M.orc, -30:2:30, 'FaceAlpha', 0.5); hold on; histogram(M.ang_v2 - M.orc, -30:2:30, 'FaceAlpha', 0.5); grid on; xlabel('tilt error vs best angle (deg)'); ylabel('cases'); legend('v1', 'v2'); title(sprintf('angle RMSE: v1 %.1f deg, v2 %.1f deg', S.v1.angle_rmse_deg, S.v2.angle_rmse_deg));
exportgraphics(f, fullfile(res, 'fig_matlab_accuracy.png'), 'Resolution', 160); close(f);
f = figure('Visible', 'off', 'Position', [100 100 700 520]); try, theme(f, 'light'); catch, end
plot(M.orc, M.ang_v2, 'o', 'MarkerFaceColor', [0.1 0.5 0.2], 'MarkerEdgeColor', 'none'); hold on; plot([15 60], [15 60], 'k--'); grid on; axis([10 65 10 65]); xlabel('best possible angle (deg)'); ylabel('angle chosen from noisy sensors (deg)'); title('MATLAB: sensor-chosen angle vs best angle (v2)');
exportgraphics(f, fullfile(res, 'fig_matlab_angles.png'), 'Resolution', 160); close(f);
end
