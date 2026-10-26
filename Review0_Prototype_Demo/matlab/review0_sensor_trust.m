function out = review0_sensor_trust(S, V, P, F, cfg, varargin)
%REVIEW0_SENSOR_TRUST  How much does it matter if the simulated pyranometer or PAR sensor is wrong?
%   The decision is taken with a sensor reading that is off by e % (e = -20 ... +20); the result is then judged under the TRUE conditions.
%   regret = what the farm loses compared with the decision taken from a perfect reading.
%     energy loss % = (PV at the right angle - PV at the chosen angle) / PV at the right angle
%     crop loss %   = same for the crop-light score
%   out.T table, out.maxLoss10 / out.maxLoss20 = largest energy and crop loss for errors of +-10 % / +-20 %.
%   review0_sensor_trust(S,V,P,F,cfg,'Plot',true,'File','x.png') also draws and saves the figure.
pa = inputParser; addParameter(pa, 'Plot', false); addParameter(pa, 'File', ''); addParameter(pa, 'Visible', true); parse(pa, varargin{:});
if nargin < 5 || isempty(cfg), cfg = struct(); end
errs = [-20 -10 -5 0 5 10 20];
V0 = V; if ~isfield(V0, 'ghiOverride'), V0.ghiOverride = NaN; end, if ~isfield(V0, 'parOverride'), V0.parOverride = NaN; end      % the truth = model values, or the manual / real readings if those are set
dTrue = review0_controller(S, V0, P, F, cfg);                           % decision with perfect sensors
ghiTrue = dTrue.ghi; parTrue = dTrue.parOpen; aTrue = dTrue.angle;
rows = {};
for sensor = {'pyranometer', 'PAR'}
    for e = errs
        Vw = V0; if strcmp(sensor{1}, 'pyranometer'), Vw.ghiOverride = ghiTrue * (1 + e / 100); Vw.parOverride = parTrue;     % PAR sensor still reads the truth
        else, Vw.ghiOverride = ghiTrue; Vw.parOverride = parTrue * (1 + e / 100); end
        dW = review0_controller(S, Vw, P, F, cfg);                          % decision taken with the wrong reading
        c2 = cfg; c2.forceAngle = dW.angle; dEval = review0_controller(S, V0, P, F, c2);   % judged under the true conditions
        pvLoss = 100 * max(0, (dTrue.pv - dEval.pv)) / max(dTrue.pv, eps); cropLoss = 100 * max(0, (dTrue.crop - dEval.crop)) / max(dTrue.crop, eps);
        rows(end + 1, :) = {sensor{1}, e, dW.angle, dW.angle - aTrue, pvLoss, cropLoss}; %#ok<AGROW>
    end
end
T = cell2table(rows, 'VariableNames', {'sensor', 'sensor_error_pct', 'angle_chosen_deg', 'angle_shift_deg', 'energy_loss_pct', 'crop_loss_pct'});
m10 = abs(T.sensor_error_pct) <= 10; m20 = abs(T.sensor_error_pct) <= 20;
out = struct('T', T, 'aTrue', aTrue, 'ghi', ghiTrue, 'par', parTrue, 'maxLoss10', [max(T.energy_loss_pct(m10)) max(T.crop_loss_pct(m10))], 'maxLoss20', [max(T.energy_loss_pct(m20)) max(T.crop_loss_pct(m20))], ...
    'maxShift10', max(abs(T.angle_shift_deg(m10))), 'maxShift20', max(abs(T.angle_shift_deg(m20))));
if pa.Results.Plot
    f = figure('Visible', ternary(pa.Results.Visible, 'on', 'off'), 'Position', [100 100 1050 520], 'Name', 'Sensor trust test'); try, theme(f, 'light'); catch, end
    sn = {'pyranometer', 'PAR'};
    subplot(1, 2, 1); hold on; for k = 1:2, m = strcmp(T.sensor, sn{k}); plot(T.sensor_error_pct(m), T.angle_shift_deg(m), '-o', 'LineWidth', 1.8); end
    grid on; xlabel('sensor error (%)'); ylabel('change of the chosen angle (deg)'); legend('pyranometer wrong', 'PAR wrong', 'Location', 'best'); title(sprintf('Angle chosen with a wrong reading (true angle %.1f deg)', aTrue));
    subplot(1, 2, 2); hold on; cols = [0.9 0.55 0; 0.2 0.6 0.2];
    for k = 1:2, m = strcmp(T.sensor, sn{k}); plot(T.sensor_error_pct(m), T.energy_loss_pct(m), '-o', 'Color', cols(1, :) * (k == 1) + [0.2 0.4 0.8] * (k == 2), 'LineWidth', 1.8); plot(T.sensor_error_pct(m), T.crop_loss_pct(m), '--s', 'Color', cols(2, :) * (k == 1) + [0.7 0.2 0.6] * (k == 2), 'LineWidth', 1.8); end
    grid on; xlabel('sensor error (%)'); ylabel('what the farm loses (%)'); legend('energy, pyranometer wrong', 'crop light, pyranometer wrong', 'energy, PAR wrong', 'crop light, PAR wrong', 'Location', 'northwest'); title('Loss caused by the wrong reading');
    sgtitle(sprintf('Can the simulated sensors be trusted?  +-10 %% error costs at most %.1f %% energy and %.1f %% crop light; +-20 %% costs %.1f %% and %.1f %%', out.maxLoss10, out.maxLoss20), 'FontSize', 11);
    if ~isempty(pa.Results.File), exportgraphics(f, pa.Results.File, 'Resolution', 130); end
    out.fig = f; if ~pa.Results.Visible, close(f); out.fig = []; end
end
end
function v = ternary(c, a, b), if c, v = a; else, v = b; end, end
