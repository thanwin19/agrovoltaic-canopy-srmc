function T = srmc_sc_crosscheck()
%SRMC_SC_CROSSCHECK  Run the MATLAB five-sensor controller on the 40 states written by make_crosscheck_cases.js and compare with the JS twin.
%   Needs results/crosscheck_cases.json (run:  node ../sensor_controller/make_crosscheck_cases.js).  Writes results/crosscheck_sc_matlab_vs_js.txt
here = fileparts(mfilename('fullpath')); sc = fullfile(fileparts(here), 'sensor_controller');
addpath(fullfile(fileparts(fileparts(here)), 'Review0_Prototype_Demo', 'matlab'));
C = jsondecode(fileread(fullfile(sc, 'results', 'crosscheck_cases.json')));
F = review0_physics(); P = F.designParams(); ctx = struct('F', F, 'P', P, 'zones', C.zones, 'monthW', C.monthW, 'lat', C.lat, 'w', C.wEnergy, 'maxStep', C.maxStep);
n = numel(C.cases); rows = cell(n, 6); dAng = zeros(n,1); sameMode = true(n,1);
for i = 1:n
    cs = C.cases(i); sen = cs.sen; sen.rain = logical(sen.rain);
    d = srmc_sensor_controller(sen, cs.prev, ctx);
    dAng(i) = abs(d.angle - cs.js.angle); sameMode(i) = strcmp(d.mode, cs.js.mode);
    rows(i,:) = {i, cs.js.mode, cs.js.angle, d.mode, d.angle, dAng(i)};
end
T = cell2table(rows, 'VariableNames', {'case','js_mode','js_angle','matlab_mode','matlab_angle','abs_diff_deg'});
out = fullfile(sc, 'results', 'crosscheck_sc_matlab_vs_js.txt'); fid = fopen(out, 'w');
fprintf(fid, 'Five-sensor controller: MATLAB vs JavaScript twin, %d random sensor states\n', n);
fprintf(fid, 'same mode: %d of %d;  angle differences: max %.2f deg, mean %.3f deg, %d cases identical, %d within 0.5 deg\n', sum(sameMode), n, max(dAng), mean(dAng), sum(dAng < 1e-9), sum(dAng <= 0.5 + 1e-9));
for i = 1:n, fprintf(fid, '%2d  JS %-8s %5.1f   MATLAB %-8s %5.1f   diff %.1f\n', i, rows{i,2}, rows{i,3}, rows{i,4}, rows{i,5}, rows{i,6}); end
fclose(fid); type(out);
end
