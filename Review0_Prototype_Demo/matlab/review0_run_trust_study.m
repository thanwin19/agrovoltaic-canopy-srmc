function R = review0_run_trust_study()
%REVIEW0_RUN_TRUST_STUDY  Day-wide answer to "can we trust the two simulated sensors?"
%   For every half hour of a clear day and of a partly cloudy day (7-17 h), the controller decides with a pyranometer or PAR reading that is
%   wrong by -20 ... +20 %, and the decision is judged under the true conditions (see review0_sensor_trust).  Plain and robust mode are compared.
%   Writes ../results/sensor_trust_study.csv/.md and fig_sensor_trust_day.png.
here = fileparts(mfilename('fullpath')); od = fullfile(fileparts(here), 'results'); if ~exist(od, 'dir'), mkdir(od); end
F = review0_physics(); P = F.designParams(); S = struct('tempC', 30, 'rh', 55, 'soilPct', 50, 'rain', 0);
hours = 7:0.5:17; skies = {'Clear day', 0.62; 'Partly cloudy day', 0.36}; modes = {'plain', false; 'robust (+-10 % worst case)', true}; errs = [5 10 20];
rows = {}; per = struct();
for sk = 1:size(skies, 1)
    for md = 1:size(modes, 1)
        cfg = struct('robust', modes{md, 2}); E = zeros(numel(hours), numel(errs)); C = E; Sh = E;
        for ih = 1:numel(hours)
            V = struct('lat', 9.88, 'day', 105, 'hour', hours(ih), 'kt', skies{sk, 2}, 'windMS', 3);
            o = review0_sensor_trust(S, V, P, F, cfg);
            for ie = 1:numel(errs)
                m = abs(o.T.sensor_error_pct) == errs(ie); E(ih, ie) = max(o.T.energy_loss_pct(m)); C(ih, ie) = max(o.T.crop_loss_pct(m)); Sh(ih, ie) = max(abs(o.T.angle_shift_deg(m)));
            end
        end
        for ie = 1:numel(errs)
            rows(end + 1, :) = {skies{sk, 1}, modes{md, 1}, errs(ie), mean(E(:, ie)), prctile(E(:, ie), 90), max(E(:, ie)), mean(C(:, ie)), prctile(C(:, ie), 90), mean(Sh(:, ie))}; %#ok<AGROW>
        end
        per(sk, md).E = E; per(sk, md).C = C; %#ok<AGROW>
    end
end
T = cell2table(rows, 'VariableNames', {'sky', 'mode', 'sensor_error_pct', 'energy_loss_mean', 'energy_loss_p90', 'energy_loss_max', 'crop_loss_mean', 'crop_loss_p90', 'angle_shift_mean_deg'});
writetable(T, fullfile(od, 'sensor_trust_study.csv'));
fid = fopen(fullfile(od, 'sensor_trust_study.md'), 'w'); fprintf(fid, '# Can the simulated pyranometer and PAR sensor be trusted? (day-wide sensitivity)\n\nFor every half hour from 7 to 17 h on day 105 (TCE) the controller decides with a sensor reading that is wrong by the stated percentage (either sensor, either sign); the decision is then judged under the true conditions. Loss = what the farm gives up compared with the decision from a perfect reading (energy: PV per m2 of panel; crop: crop-light score). Mean, 90th percentile and maximum over the 21 half-hours.\n\n| sky | mode | sensor error | energy loss mean | p90 | max | crop loss mean | p90 | mean angle shift |\n|---|---|---|---|---|---|---|---|---|\n');
for i = 1:height(T), fprintf(fid, '| %s | %s | +-%d %% | %.1f %% | %.1f %% | %.1f %% | %.1f %% | %.1f %% | %.1f deg |\n', T.sky{i}, T.mode{i}, T.sensor_error_pct(i), T.energy_loss_mean(i), T.energy_loss_p90(i), T.energy_loss_max(i), T.crop_loss_mean(i), T.crop_loss_p90(i), T.angle_shift_mean_deg(i)); end
fclose(fid); disp(T);
f = figure('Visible', 'off', 'Position', [100 100 1050 480]); try, theme(f, 'light'); catch, end
for sk = 1:2
    subplot(1, 2, sk); hold on; plot(hours, per(sk, 1).E(:, 2), '-o', 'LineWidth', 1.5); plot(hours, per(sk, 2).E(:, 2), '-s', 'LineWidth', 1.5); plot(hours, per(sk, 1).C(:, 2), '--o', 'LineWidth', 1.2); plot(hours, per(sk, 2).C(:, 2), '--s', 'LineWidth', 1.2);
    grid on; xlabel('solar hour'); ylabel('loss with a +-10 % sensor error (%)'); title(skies{sk, 1}); if sk == 1, legend('energy, plain', 'energy, robust', 'crop, plain', 'crop, robust', 'Location', 'best'); end
end
sgtitle('Loss caused by a 10 % error in the pyranometer or PAR reading, hour by hour'); exportgraphics(f, fullfile(od, 'fig_sensor_trust_day.png'), 'Resolution', 150); close(f);
R = T;
end
