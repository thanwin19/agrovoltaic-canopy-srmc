function review0_make_explain_gallery()
%REVIEW0_MAKE_EXPLAIN_GALLERY  Saves the explanation window (curves + accuracy points A-F) for five situations into ../results/explain/.
here = fileparts(mfilename('fullpath')); od = fullfile(fileparts(here), 'results', 'explain'); if ~exist(od, 'dir'), mkdir(od); end
F = review0_physics(); P = F.designParams(); M = review0_mppt(); pm = M.params(); cfg = struct('wEnergy', 0.5);
sc = {'clear_noon', 12, 0.62, 31, 55, 50, 3, NaN, NaN; 'hot_dry_stress', 13, 0.62, 38, 30, 50, 3, NaN, NaN; 'partly_cloudy', 11, 0.36, 30, 55, 50, 3, NaN, NaN; 'dim_manual_sensors', 12, 0.62, 30, 55, 50, 3, 350, 720; 'afternoon_sun', 15.5, 0.62, 31, 55, 50, 3, NaN, NaN};
for i = 1:size(sc, 1)
    S = struct('tempC', sc{i, 4}, 'rh', sc{i, 5}, 'soilPct', sc{i, 6}, 'rain', 0); V = struct('lat', 9.88, 'day', 105, 'hour', sc{i, 2}, 'kt', sc{i, 3}, 'windMS', sc{i, 7}, 'ghiOverride', sc{i, 8}, 'parOverride', sc{i, 9});
    d = review0_controller(S, V, P, F, struct('wantCurve', true)); st = M.init(pm, 30); Pw = 0; for k = 1:80, [st, Pw] = M.po(st, pm, d.gpoa, d.tcell); end
    fg = review0_explain([], d, S, V, P, F, cfg, struct('pm', pm, 'M', M, 'V', st.V, 'P', Pw, 'effRun', 99.5), 'Visible', false, 'File', fullfile(od, ['explain_' sc{i, 1} '.png'])); close(fg);
    fprintf('%-20s angle %.1f  brute %.1f  gap %.1f deg  pv %.0f  crop %.2f\n', sc{i, 1}, d.angle, d.brute.angle, d.brute.gapDeg, d.pv, d.crop);
end
end
