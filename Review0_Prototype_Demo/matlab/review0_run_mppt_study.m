function R = review0_run_mppt_study()
%REVIEW0_RUN_MPPT_STUDY  Figures and numbers that show what MPPT does and how accurate it is.   Writes ../results/fig_mppt_*.png, mppt_study.csv/.md
here = fileparts(mfilename('fullpath')); od = fullfile(fileparts(here), 'results'); M = review0_mppt(); pm = M.params();
blue = [0.10 0.25 0.70]; red = [0.8 0.15 0.15]; green = [0.25 0.62 0.20]; amber = [0.9 0.55 0.05]; grey = [0.45 0.47 0.5];
% ---------- Figure 1: the maximum power point moves ----------
f = mkfig([80 80 1250 520]); ax = subplot(1, 2, 1); hold on; grid on; cols = lines(4); Gs = [200 500 800 1000];
for k = 1:4, [v, ~, p] = M.iv(pm, Gs(k), 45); m = M.mpp(pm, Gs(k), 45); plot(v, p, 'Color', cols(k, :), 'LineWidth', 2); plot(m.V, m.P, 'p', 'MarkerSize', 14, 'MarkerFaceColor', red, 'MarkerEdgeColor', 'k', 'HandleVisibility', 'off'); text(m.V - 1, m.P + 14, sprintf('%.0f W', m.P), 'HorizontalAlignment', 'right', 'FontSize', 9); end
xlabel('module voltage (V)'); ylabel('module power (W)'); title('More sunlight = more power, and the top of the curve (red star) stays near the same voltage'); legend(arrayfun(@(g) sprintf('%d W/m2', g), Gs, 'UniformOutput', false), 'Location', 'northwest');
text(2, 20, 'Red star = maximum power point (MPP). MPPT keeps the panel exactly there.', 'FontSize', 9, 'Color', grey);
ax2 = subplot(1, 2, 2); hold on; grid on; Ts = [25 45 65]; cols2 = [0.2 0.6 0.9; 0.9 0.55 0.1; 0.8 0.2 0.2]; vv = zeros(1, 3); pp = zeros(1, 3);
for k = 1:3, [v, ~, p] = M.iv(pm, 800, Ts(k)); m = M.mpp(pm, 800, Ts(k)); vv(k) = m.V; pp(k) = m.P; plot(v, p, 'Color', cols2(k, :), 'LineWidth', 2); plot(m.V, m.P, 'p', 'MarkerSize', 14, 'MarkerFaceColor', red, 'MarkerEdgeColor', 'k', 'HandleVisibility', 'off'); end
xlabel('module voltage (V)'); ylabel('module power (W)'); title(sprintf('A hotter panel gives less power AND its best voltage drops (%.1f V -> %.1f V)', vv(1), vv(3))); legend(arrayfun(@(t) sprintf('cell %d C', t), Ts, 'UniformOutput', false), 'Location', 'southwest');
text(2, 20, 'A fixed voltage cannot follow this shift: that is why a tracker is needed.', 'FontSize', 9, 'Color', grey);
exportgraphics(f, fullfile(od, 'fig_mppt_curves.png'), 'Resolution', 140); close(f);
% ---------- Figure 2: tracking a cloud ----------
t = 0:0.5:80; G = 850 * ones(size(t)); G(t > 25 & t <= 45) = 380; G(t > 45) = 900; Tc = 46 * ones(size(t)); Rm = M.simulate(pm, G, Tc);
f = mkfig([80 80 1150 760]); subplot(3, 1, 1); plot(t, G, 'Color', amber, 'LineWidth', 2); grid on; ylabel('sunlight (W/m2)'); title('A cloud passes: sunlight drops from 850 to 380 W/m2 and returns to 900 W/m2'); ylim([0 1100]);
subplot(3, 1, 2); hold on; grid on; plot(t, Rm.Pmpp, 'k--', 'LineWidth', 2); plot(t, Rm.Ptrack, '-', 'Color', green, 'LineWidth', 2); plot(t, Rm.Pfixed, '-', 'Color', red, 'LineWidth', 1.5); ylabel('module power (W)');
legend('true maximum possible', 'with MPPT (Perturb & Observe)', 'fixed voltage (no MPPT)', 'Location', 'southwest'); title(sprintf('MPPT keeps %.2f %% of the maximum energy; a fixed voltage keeps %.2f %%  (MPPT gain %+.2f %%)', Rm.effTrack, Rm.effFixed, Rm.gainPct));
text(47, max(Rm.Pmpp) * 0.62, sprintf('ACCURACY POINT: tracking efficiency %.2f %%', Rm.effTrack), 'BackgroundColor', [1 0.92 0.45], 'EdgeColor', 'k', 'FontWeight', 'bold');
subplot(3, 1, 3); hold on; grid on; plot(t, Rm.Vmpp, 'k--', 'LineWidth', 2); plot(t, Rm.Vtrack, '-', 'Color', green, 'LineWidth', 2); yline(pm.Vfixed, '-', 'fixed voltage', 'Color', red); xlabel('time (seconds)'); ylabel('module voltage (V)'); legend('best voltage', 'tracker voltage', 'Location', 'southeast'); title('The tracker follows the best voltage after every change (it starts from 30 V)');
exportgraphics(f, fullfile(od, 'fig_mppt_tracking.png'), 'Resolution', 140); close(f);
% ---------- table over sun and temperature ----------
rows = {}; Gl = [200 400 600 800 1000]; Tl = [25 45 65];
for g = Gl, for tc = Tl
    n = 40; Gt = g * ones(1, n); Tt = tc * ones(1, n); r = M.simulate(pm, Gt, Tt, 30); m = M.mpp(pm, g, tc); [~, ~, pf] = M.iv(pm, g, tc, pm.Vfixed);
    rows(end + 1, :) = {g, tc, m.P, m.V, 100 * r.Ptrack(end) / m.P, 100 * pf / m.P}; %#ok<AGROW>
end, end
T = cell2table(rows, 'VariableNames', {'sunlight_Wm2', 'cell_temp_C', 'max_power_W', 'best_voltage_V', 'mppt_efficiency_pct', 'fixed_voltage_efficiency_pct'}); writetable(T, fullfile(od, 'mppt_study.csv'));
fid = fopen(fullfile(od, 'mppt_study.md'), 'w'); fprintf(fid, '# MPPT study (typical 400 W module model, replace parameters with the datasheet)\n\nCloud transient: tracking efficiency %.2f %%, fixed voltage %.2f %%, gain %+.2f %%.\n\n| sunlight W/m2 | cell C | max power W | best voltage V | MPPT efficiency %% | fixed-voltage efficiency %% |\n|---|---|---|---|---|---|\n', Rm.effTrack, Rm.effFixed, Rm.gainPct);
for i = 1:height(T), fprintf(fid, '| %d | %d | %.0f | %.1f | %.2f | %.2f |\n', T.sunlight_Wm2(i), T.cell_temp_C(i), T.max_power_W(i), T.best_voltage_V(i), T.mppt_efficiency_pct(i), T.fixed_voltage_efficiency_pct(i)); end
fclose(fid); fprintf('MPPT: cloud run efficiency %.2f %% vs fixed %.2f %% (gain %+.2f %%); steady-state mean %.2f %% vs %.2f %%\n', Rm.effTrack, Rm.effFixed, Rm.gainPct, mean(T.mppt_efficiency_pct), mean(T.fixed_voltage_efficiency_pct)); R = T;
end
function f = mkfig(pos), f = figure('Visible', 'off', 'Position', pos); try, theme(f, 'light'); catch, end, end
