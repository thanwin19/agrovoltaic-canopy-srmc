function fig = review0_explain(fig, d, S, V, P, F, cfg, mp, varargin)
%REVIEW0_EXPLAIN  The "how it optimises and where the accuracy comes from" window, in plain words.
%   Panel 1: the tilt-angle search (energy, crop light, combined score)      Panel 2: this controller against other ways of tilting
%   Panel 3: MPPT (maximum power point tracking)                             Bottom : accuracy points A to F, each with the number and its meaning.
%   d = decision from review0_controller(..., struct('wantCurve', true));  mp = struct('pm', .., 'M', .., 'V', tracker voltage, 'P', tracker power, 'effRun', ..)
pa = inputParser; addParameter(pa, 'Visible', true); addParameter(pa, 'File', ''); parse(pa, varargin{:});
W = review0_words();
if isempty(fig) || ~isvalid(fig), fig = figure('Name', 'SRMC: how it optimises and where the accuracy comes from', 'NumberTitle', 'off', 'Position', [60 40 1500 860], 'Visible', ternary(pa.Results.Visible, 'on', 'off'), 'Color', 'w'); end
try, theme(fig, 'light'); catch, end
clf(fig); set(fig, 'Color', 'w');
amber = [0.90 0.55 0.05]; green = [0.25 0.62 0.20]; blue = [0.10 0.25 0.70]; red = [0.8 0.15 0.15]; grey = [0.45 0.47 0.5];
badge = @(ax, x, y, t) text(ax, x, y, t, 'FontWeight', 'bold', 'FontSize', 12, 'BackgroundColor', [1 0.92 0.45], 'EdgeColor', 'k', 'Margin', 3, 'HorizontalAlignment', 'center');
annotation(fig, 'textbox', [0.02 0.945 0.96 0.05], 'String', 'How the SRMC system decides the panel angle, and where its accuracy comes from', 'EdgeColor', 'none', 'FontSize', 18, 'FontWeight', 'bold', 'Color', [0.08 0.2 0.17]);
hasC = isfield(d, 'curve');
% ---------- panel 1: tilt search ----------
ax1 = axes(fig, 'Position', [0.055 0.545 0.285 0.345]); hold(ax1, 'on'); grid(ax1, 'on');
if hasC
    c = d.curve; plot(ax1, c.angle, c.pv / c.pvMax, '-', 'Color', amber, 'LineWidth', 2); plot(ax1, c.angle, c.crop / c.cropMax, '-', 'Color', green, 'LineWidth', 2); plot(ax1, c.angle, c.J, '-', 'Color', blue, 'LineWidth', 3);
    plot(ax1, d.angle, d.brute.chosenJ, 'p', 'MarkerSize', 17, 'MarkerFaceColor', red, 'MarkerEdgeColor', 'k'); plot(ax1, d.brute.angle, d.brute.J, 'o', 'MarkerSize', 12, 'LineWidth', 2, 'Color', 'k');
    xlim(ax1, [15 60]); ylim(ax1, [0 1.12]); badge(ax1, min(58, d.angle + 4), min(1.07, d.brute.chosenJ + 0.07), 'A');
    legend(ax1, {'electricity (1 = best)', 'crop light (1 = best)', 'COMBINED SCORE', 'angle chosen', 'best of a full search'}, 'Location', 'south', 'FontSize', 8);
end
xlabel(ax1, 'panel tilt angle (degrees)'); ylabel(ax1, 'score (1 = best possible)'); title(ax1, '1) How the tilt angle is chosen', 'FontSize', 13);
text(ax1, 15.5, 1.1, 'The controller tries every angle and keeps the highest combined score', 'FontSize', 8.5, 'Color', grey, 'VerticalAlignment', 'top');
% ---------- panel 2: strategies ----------
ax2 = axes(fig, 'Position', [0.40 0.545 0.265 0.345]); hold(ax2, 'on'); grid(ax2, 'on');
if hasC
    s = d.strat; pvp = 100 * s.pv / max(s.pv); cp = 100 * s.crop / max(s.crop); b = bar(ax2, [pvp(:) cp(:)], 'grouped'); b(1).FaceColor = amber; b(2).FaceColor = green;
    set(ax2, 'XTick', 1:4, 'XTickLabel', {'fixed 15', 'fixed 45', 'sun tracking', 'SRMC'}, 'FontSize', 9); ylim(ax2, [0 128]);
    for k = 1:4, text(ax2, k - 0.15, pvp(k) + 3, sprintf('%.0f', pvp(k)), 'HorizontalAlignment', 'center', 'FontSize', 8); text(ax2, k + 0.15, cp(k) + 3, sprintf('%.0f', cp(k)), 'HorizontalAlignment', 'center', 'FontSize', 8); end
    badge(ax2, 4, 118, 'B'); legend(ax2, {'electricity', 'crop light'}, 'Location', 'northwest', 'FontSize', 8);
end
ylabel(ax2, 'percent of the best of the four (%)'); xlabel(ax2, 'way of tilting the panels'); title(ax2, '2) Compared with other ways of tilting (this moment)', 'FontSize', 13);
% ---------- panel 3: MPPT ----------
ax3 = axes(fig, 'Position', [0.725 0.545 0.25 0.345]); hold(ax3, 'on'); grid(ax3, 'on');
pm = mp.pm; M = mp.M; G = max(d.gpoa, 1); Tc = d.tcell; [v, ~, p] = M.iv(pm, G, Tc); [v2, ~, p2] = M.iv(pm, G / 2, Tc); mpp = M.mpp(pm, G, Tc);
plot(ax3, v, p, '-', 'Color', blue, 'LineWidth', 2.5); plot(ax3, v2, p2, '--', 'Color', grey, 'LineWidth', 1.5);
plot(ax3, mpp.V, mpp.P, 'p', 'MarkerSize', 16, 'MarkerFaceColor', red, 'MarkerEdgeColor', 'k'); plot(ax3, mp.V, mp.P, 'o', 'MarkerSize', 10, 'MarkerFaceColor', green, 'MarkerEdgeColor', 'k');
vf = pm.Vfixed; [~, ~, pf] = M.iv(pm, G, Tc, vf); plot(ax3, vf, pf, 's', 'MarkerSize', 9, 'MarkerFaceColor', amber, 'MarkerEdgeColor', 'k');
legend(ax3, {sprintf('now: %.0f W/m2, cell %.0f C', G, Tc), 'half the sunlight', 'maximum power point', 'MPPT working point', 'fixed voltage (no MPPT)'}, 'Location', 'southwest', 'FontSize', 8);
badge(ax3, mpp.V * 0.55, mpp.P * 1.02, 'C'); xlabel(ax3, 'module voltage (V)'); ylabel(ax3, 'module power (W)'); title(ax3, '3) MPPT: always work at the top of the curve', 'FontSize', 13);
text(ax3, 1, max(p) * 1.12, 'The best voltage moves with sun and temperature', 'FontSize', 8.5, 'Color', grey, 'VerticalAlignment', 'top'); ylim(ax3, [0 max(p) * 1.18]);
% ---------- bottom: words ----------
axT = axes(fig, 'Position', [0.02 0.02 0.96 0.49]); axis(axT, 'off'); xlim(axT, [0 1]); ylim(axT, [0 1]);
L = {}; hd = {};
L{end + 1} = ['IN SIMPLE WORDS:  ' W.now(d, S, V)];
if hasC
    sg = d.strat; gE45 = 100 * (sg.pv(4) / sg.pv(2) - 1); gC45 = 100 * (sg.crop(4) / max(sg.crop(2), eps) - 1); gEt = 100 * (sg.pv(4) / sg.pv(3) - 1);
    if sg.crop(3) < 0.5 * sg.crop(4), trkTxt = sprintf('Sun tracking would give %.0f %% more electricity but the crops would get only %.0f %% of the light score we give them.', -gEt * (gEt < 0), 100 * sg.crop(3) / max(sg.crop(4), eps)); else, trkTxt = sprintf('Sun tracking would change the electricity by %+.0f %%.', -gEt); end
    A = sprintf('A  DECISION ACCURACY.  The controller chose %.1f degrees. We also tried every angle in 0.5-degree steps: the best is %.1f degrees. Difference = %.1f degrees, combined score within %.2f %% of the best.', d.angle, d.brute.angle, d.brute.gapDeg, d.brute.gapJpct);
    B = sprintf('B  GAIN OVER SIMPLE CHOICES.  Against a panel fixed at 45 degrees: electricity %+.1f %%, crop light %+.1f %%. %s', gE45, gC45, trkTxt);
else, A = 'A  (press "Explain + accuracy" after the first decision)'; B = 'B  -'; end
C = sprintf('C  MPPT ACCURACY.  The tracker works at %.1f V and %.0f W; the true maximum is %.1f V and %.0f W. Tracking efficiency now %.1f %%, average since start %.1f %%. A fixed voltage would give %.0f W (%.1f %% of the maximum).', mp.V, mp.P, mpp.V, mpp.P, 100 * mp.P / max(mpp.P, eps), mp.effRun, pf, 100 * pf / max(mpp.P, eps));
D = 'D  SENSOR ACCURACY (real sensors).  DHT11: temperature within 2 C and humidity within 5 % (datasheet limits). Soil moisture: calibrated with two points (dry in air, wet in water). Rain sensor: detects a drop; sensitivity set by the potentiometer. Bench numbers are measured on the day.';
E = 'E  MODEL ACCURACY (checked earlier).  Solar energy model vs the PVGIS service: +5.0 % per year (5.2 % of it is the weather data source). Shadow model vs Blender 3-D ray tracing: average difference 0.010 (about 1 %). The same functions are used here, so the decision uses validated physics.';
trust = trustText();
Fx = ['F  SIMULATED-SENSOR TRUST.  ' trust];
items = [{L{1}}, {A}, {B}, {C}, {D}, {E}, {Fx}]; y = 0.98;
for i = 1:numel(items)
    lines = W.wrap(items{i}, 175); col = ternary(i == 1, [0.08 0.2 0.17], [0.1 0.1 0.1]);
    for j = 1:numel(lines)
        fw = 'normal'; if i == 1, fw = 'bold'; end
        text(axT, 0.005, y, lines{j}, 'FontSize', 11, 'Color', col, 'FontWeight', fw, 'VerticalAlignment', 'top', 'Interpreter', 'none'); y = y - 0.047;
    end
    y = y - 0.02;
end
if ~isempty(pa.Results.File), exportgraphics(fig, pa.Results.File, 'Resolution', 120); end
end

function t = trustText()
here = fileparts(mfilename('fullpath')); f = fullfile(fileparts(here), 'results', 'sensor_trust_study.csv');
t = 'The sunlight (pyranometer) and PAR sensors are simulated (or set by the scroll bars). Press "Sensor trust test" to see what a wrong reading would cost.';
try
    T = readtable(f); m5 = strcmp(T.mode, 'plain') & T.sensor_error_pct == 5 & strcmp(T.sky, 'Clear day'); m10 = strcmp(T.mode, 'plain') & T.sensor_error_pct == 10 & strcmp(T.sky, 'Clear day');
    t = sprintf('The sunlight and PAR sensors are simulated, so we measured what a wrong reading would cost. On a clear day, if the reading is wrong by 5 %%, the farm loses %.1f %% of the electricity on average (%.1f %% at 10 %%). A real, calibrated pyranometer and PAR sensor (see their datasheet for the accuracy) will replace the simulated ones. Worst single half-hour at 10 %%: %.0f %%.', T.energy_loss_mean(m5), T.energy_loss_mean(m10), T.energy_loss_max(m10));
catch, end
end
function v = ternary(c, a, b), if c, v = a; else, v = b; end, end
