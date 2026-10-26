function srmc_master(fast)
%SRMC_MASTER  Runs the whole final-year-project simulation study and writes figures, tables and a summary.
%   srmc_master()        full study (0.5 deg motor resolution)  - about 15-25 minutes
%   srmc_master(true)    quick study (1 deg resolution)
%   Outputs in out/matlab/: fig*.png, T1..T4 *.csv, summary.md
%   Every number comes from srmc_run.m (the same equations as the browser twin) and structural_check.m.
if nargin < 1, fast = false; end
root = rootOf(mfilename('fullpath')); od = fullfile(root,'out','matlab'); if ~exist(od,'dir'), mkdir(od); end
Q = struct('plots',false,'quiet',true,'export',false); step = 0.5; if fast, step = 1; end
t0 = tic; G = [0.45 0.72 0.19]; A = [0.94 0.69 0.19]; B = [0.29 0.62 0.91]; Tl = [0.16 0.77 0.77]; R = [1 0.5 0.5];
mon = {'Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'};

%% 1 baseline run (TCE ground) with the standard figures
fprintf('[1/7] baseline TCE run + standard figures\n');
base = srmc_run('tce_madurai','red_sandy_loam',struct('angleStep',step),struct('plots',true,'quiet',false,'export',true));
for f = {'fig1_sunpath.png','fig2_zone_light.png','fig3_tilt_tradeoff.png','fig4_water_balance.png','fig5_zone_yield.png'}
    if exist(fullfile(root,'out',f{1}),'file'), movefile(fullfile(root,'out',f{1}), fullfile(od,f{1}), 'f'); end
end

%% 2 controller comparison (the novelty): SRMC-DT vs fixed designs
fprintf('[2/7] controller comparison\n');
cases = {'SRMC-DT controller (50% energy / 50% crop)', struct('angleStep',step);
         'Fixed 45 deg tilt stop',                      struct('tiltMode','fixed','tilt',45);
         'PV-max fixed 15 deg',                         struct('tiltMode','fixed','tilt',15);
         'Crop-max controller (w = 0)',                 struct('energyWeight',0,'angleStep',step);
         'PV-max controller (w = 1)',                   struct('energyWeight',1,'angleStep',step)};
rows = cell(size(cases,1),1); runs = cell(size(cases,1),1);
for i = 1:size(cases,1)
    if i == 1, r = base; else, r = srmc_run('tce_madurai','red_sandy_loam',cases{i,2},Q); end
    runs{i} = r; rows{i} = summaryRow(cases{i,1}, r);
end
T1 = struct2table([rows{:}]); writetable(T1, fullfile(od,'T1_controller_comparison.csv')); disp(T1(:,{'design','pv_kWh_m2','mean_light_pct','solar_net_lakh','crop_net_lakh','total_lakh','rain_fed_pct','farmer_inr_month'}));
f = mkfig([100 100 980 460]); bar(categorical(T1.design, T1.design), [T1.solar_net_lakh T1.crop_net_lakh], 'stacked'); ylabel('INR lakh / ha / yr'); grid on; legend('Solar (after O&M)','Crop net','Location','northwest');
title('Controller vs fixed designs: annual value per hectare (TCE ground)'); exportgraphics(f, fullfile(od,'fig6_controller_comparison.png'),'Resolution',160); close(f);

%% 3 energy/crop weighting (Pareto front of the controller objective)
fprintf('[3/7] objective weighting sweep\n');
W = [0 0.25 0.5 0.75 1]; pvW = zeros(size(W)); cropW = zeros(size(W)); lightW = zeros(size(W));
for k = 1:numel(W)
    if W(k) == 0.5, r = base; elseif W(k) == 0, r = runs{4}; elseif W(k) == 1, r = runs{5}; else, r = srmc_run('tce_madurai','red_sandy_loam',struct('energyWeight',W(k),'angleStep',step),Q); end
    pvW(k) = r.annual.pvKWhPerM2; cropW(k) = r.eco.cropNet/1e5; lightW(k) = r.annual.meanLight*100;
end
f = mkfig([100 100 880 460]); yyaxis left; plot(W*100, pvW, '-o','Color',A,'LineWidth',2); ylabel('PV energy (kWh/m^2 panel/yr)'); yyaxis right; plot(W*100, cropW, '-s','Color',G,'LineWidth',2); ylabel('Crop net (INR lakh/ha/yr)'); ax = gca; ax.YAxis(1).Color = A; ax.YAxis(2).Color = G;
xlabel('Controller weight on energy (%)'); grid on; title('Energy vs crop: moving the controller objective'); exportgraphics(f, fullfile(od,'fig7_pareto.png'),'Resolution',160); close(f);
T1b = table(W'*100, pvW', lightW', cropW', 'VariableNames', {'energy_weight_pct','pv_kWh_m2','mean_light_pct','crop_net_lakh'}); writetable(T1b, fullfile(od,'T1b_weight_sweep.csv'));

%% 4 controller schedule and farmer income
fprintf('[4/7] schedule and farmer income figures\n');
sc = base.params.schedule; hrs = 5.5:1:18.5;
f = mkfig([100 100 900 440]); imagesc(hrs, 1:12, sc); colormap(summer); cb = colorbar; cb.Label.String = 'tilt angle (deg)'; set(gca,'YTick',1:12,'YTickLabel',mon); xlabel('Solar hour (hourly decision)');
for m = 1:12, for h = 1:numel(hrs), text(hrs(h), m, sprintf('%.0f', sc(m,h)), 'HorizontalAlignment','center','FontSize',7); end, end
title('SRMC-DT controller: tilt angle chosen each hour of each month'); exportgraphics(f, fullfile(od,'fig8_controller_schedule.png'),'Resolution',160); close(f);
mo = base.eco.monthly; f = mkfig([100 100 900 440]); bar(1:12, [mo.farmerSolar; mo.crop]'/1e3, 'stacked'); set(gca,'XTick',1:12,'XTickLabel',mon); ylabel('INR thousand / ha'); grid on; legend('Solar share paid monthly by the industry','Crop income at harvest');
title(sprintf('Farmer income by month (industry pays INR %.1f/kWh, farmer share %.0f%%)', base.params.tariff, 100*base.params.farmerShare)); exportgraphics(f, fullfile(od,'fig9_farmer_income.png'),'Resolution',160); close(f);

%% 5 universal: every climate preset with its typical soil
fprintf('[5/7] universal climate sweep\n');
clims = jsondecode(fileread(fullfile(root,'data','climates.json'))); rowsU = cell(numel(clims),1);
for i = 1:numel(clims)
    r = srmc_run(clims(i).id, clims(i).suggest_soil, struct('angleStep',1), Q); rowsU{i} = summaryRow(clims(i).name, r); rowsU{i}.soil = string(clims(i).suggest_soil); rowsU{i}.crops = string(strjoin(r.zoneCrop, ', ')); rowsU{i}.rain_mm = sum(clims(i).rain);
end
T2 = struct2table([rowsU{:}]); writetable(T2, fullfile(od,'T2_universal_climates.csv'));
f = mkfig([100 100 1000 480]); names = cellfun(@(s) strtok(s,'('), T2.design, 'UniformOutput', false); yyaxis left; bar(categorical(names, names), T2.pv_kWh_m2, 'FaceColor', A); ylabel('PV energy (kWh/m^2 panel/yr)'); yyaxis right; plot(1:numel(names), T2.farmer_inr_month/1e3, '-o', 'Color', G, 'LineWidth', 2); ylabel('Farmer income (INR thousand / month / ha)'); grid on; ax = gca; ax.YAxis(1).Color = A; ax.YAxis(2).Color = G;
title('Same design, different places: energy and farmer income'); exportgraphics(f, fullfile(od,'fig10_universal_climates.png'),'Resolution',160); close(f);

%% 6 universal: every soil at TCE
fprintf('[6/7] universal soil sweep\n');
soils = jsondecode(fileread(fullfile(root,'data','soils.json'))); rowsS = cell(numel(soils),1);
for i = 1:numel(soils)
    r = srmc_run('tce_madurai', soils(i).id, struct('angleStep',1), Q); rowsS{i} = summaryRow(soils(i).name, r); rowsS{i}.crops = string(strjoin(r.zoneCrop, ', ')); rowsS{i}.yield_z1_z4 = string(sprintf('%.1f / %.1f / %.1f / %.1f', r.wb.zones.yield));
end
T3 = struct2table([rowsS{:}]); writetable(T3, fullfile(od,'T3_universal_soils.csv'));
f = mkfig([100 100 1000 480]); bar(categorical(T3.design, T3.design), T3.crop_net_lakh, 'FaceColor', G); ylabel('Crop net (INR lakh/ha/yr)'); grid on; xtickangle(25); title('Same canopy, different soils (TCE climate)'); exportgraphics(f, fullfile(od,'fig11_universal_soils.png'),'Resolution',160); close(f);

%% 7 structure
fprintf('[7/7] structural checks\n');
T4 = structural_check(); writetable(T4, fullfile(od,'T4_structural.csv'));

%% summary
fid = fopen(fullfile(od,'summary.md'),'w'); fprintf(fid,'# SRMC simulation study - summary\n\nGenerated by `matlab/srmc_master.m` in %.0f s. Site: TCE ground, Madurai (NASA POWER climate).\n\n', toc(t0));
fprintf(fid,'## Baseline (design preset `%s`, SRMC-DT controller)\n\n', jsondecode(fileread(fullfile(root,'design','design.json'))).active);
fprintf(fid,'- PV %.0f kWh/m2 panel/yr (%.0f kWh/kWp); mean crop light %.0f %%\n- Rain harvested %.0f m3 of %.0f m3 irrigation demand; borewell top-up %.0f m3\n- Farmer income %.0f INR/month/ha (assumed: industry pays INR %.1f/kWh, farmer share %.0f %%)\n- Crops: %s\n\n', base.annual.pvKWhPerM2, base.eco.specificYield, base.annual.meanLight*100, base.wb.harvested, base.wb.demand, base.wb.unmet, base.eco.farmerMonthlyAvg, base.params.tariff, 100*base.params.farmerShare, strjoin(base.zoneCrop, ', '));
fprintf(fid,'## Controller vs fixed designs\n\n'); writeMd(fid, T1(:,{'design','pv_kWh_m2','mean_light_pct','solar_net_lakh','crop_net_lakh','total_lakh','rain_fed_pct','farmer_inr_month'}));
fprintf(fid,'\n## Universal climates (typical soil of each place)\n\n'); writeMd(fid, T2(:,{'design','soil','crops','pv_kWh_m2','mean_light_pct','rain_fed_pct','farmer_inr_month'}));
fprintf(fid,'\n## Universal soils (TCE climate)\n\n'); writeMd(fid, T3(:,{'design','crops','yield_z1_z4','crop_net_lakh','rain_fed_pct'}));
fprintf(fid,'\n## Structure (screening level, IS 875 wind)\n\n'); writeMd(fid, T4(:,{'preset','bay_m','tube_util','wire_util','stay_util','col_util'}));
for ff = {'pv_validation.txt','shading_validation.txt'}
    p = fullfile(root,'out','physics',ff{1}); if exist(p,'file'), fprintf(fid,'\n## Validation: %s\n\n```\n%s\n```\n', ff{1}, fileread(p)); end
end
fprintf(fid,'\n## Limits\n\nMonthly-mean sky; isotropic diffuse; typical soil/crop parameters; assumed prices, tariff and farmer share; rope strengths indicative; no certified structural design.\n'); fclose(fid);
fprintf('\nDONE in %.0f s. See %s\n', toc(t0), od);
end

function s = summaryRow(name, r)
e = r.eco; w = r.wb;
s = struct('design', string(name), 'pv_kWh_m2', r.annual.pvKWhPerM2, 'mean_light_pct', r.annual.meanLight*100, 'solar_net_lakh', (e.solarRev-e.om)/1e5, 'crop_net_lakh', e.cropNet/1e5, ...
    'total_lakh', (e.solarRev-e.om+e.cropNet)/1e5, 'rain_fed_pct', 100*(w.demand>0)*(w.supplied/max(w.demand,eps)) + 100*(w.demand<=0), 'harvested_m3', w.harvested, 'farmer_inr_month', e.farmerMonthlyAvg, 'payback_yr', e.payback);
end
function writeMd(fid, T)
v = T.Properties.VariableNames; fprintf(fid,'| %s |\n|%s\n', strjoin(v,' | '), repmat('---|', 1, numel(v)));
for i = 1:height(T)
    c = cell(1,numel(v));
    for j = 1:numel(v), x = T.(v{j})(i); if iscell(x), x = x{1}; end, if isnumeric(x), c{j} = sprintf('%.2f', x); else, c{j} = char(string(x)); end, end
    fprintf(fid,'| %s |\n', strjoin(c,' | '));
end
end

function f = mkfig(pos)
f = figure('Visible','off','Position',pos); try, theme(f,'light'); catch, end
end

function r = rootOf(p)
%ROOTOF project root: parent of the matlab folder; if the design file is not there (script copied into a Review folder), use ../_project_core
r = fileparts(fileparts(p));
if ~exist(fullfile(r,'design','design.json'),'file'), r = fullfile(fileparts(r),'_project_core'); end
end
