function srmc_plots(res, P, clim, soil, crops)
%SRMC_PLOTS  Report-quality figures for the SRMC results (saved to out/*.png).
root = rootOf(mfilename('fullpath')); outDir = fullfile(root,'out');
if ~exist(outDir,'dir'), mkdir(outDir); end
mon = {'Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'};
mid = [17 47 75 105 135 162 198 228 258 288 318 344]; dim = [31 28 31 30 31 30 31 31 30 31 30 31];
G = [0.45 0.72 0.19]; B = [0.1 0.37 0.68]; T = [0.1 0.65 0.65]; A = [0.9 0.65 0.15];
tag = sprintf('%s | %s', clim.name, soil.name);

% 1 --- sun path (azimuth vs elevation) ---------------------------------
f = mkfig([100 100 900 520]); hold on; grid on;
cols = parula(12);
for m = [1 3 6 9 12]
    az = []; el = [];
    for h = 5:0.25:19
        d = 23.45*sind(360/365*(284+mid(m))); w = 15*(h-12);
        sz = sind(clim.lat)*sind(d)+cosd(clim.lat)*cosd(d)*cosd(w);
        sx = -cosd(d)*sind(w); sy = sind(d)*cosd(clim.lat)-cosd(d)*cosd(w)*sind(clim.lat);
        if sz > 0, el(end+1) = asind(sz); az(end+1) = mod(atan2d(sx,sy),360); end %#ok<AGROW>
    end
    plot(az, el, '.', 'Color', cols(m,:), 'MarkerSize', 8, 'DisplayName', mon{m});
end
xlabel('Azimuth (deg from North, clockwise)'); ylabel('Solar elevation (deg)'); legend('Location','northeastoutside');
title({'Sun path', tag}); xlim([0 360]); ylim([0 90]);
exportgraphics(f, fullfile(outDir,'fig1_sunpath.png'),'Resolution',160); close(f);

% 2 --- monthly light heat-map per zone ----------------------------------
f = mkfig([100 100 900 380]);
imagesc(res.zoneMonthly*100); colormap(summer); cb = colorbar; cb.Label.String = '% of open-field light';
set(gca,'XTick',1:12,'XTickLabel',mon,'YTick',1:4,'YTickLabel',{'Zone 1','Zone 2','Zone 3','Zone 4'});
for z = 1:4, for m = 1:12, text(m,z,sprintf('%.0f',res.zoneMonthly(z,m)*100),'HorizontalAlignment','center'); end, end
title({'Ground light under the canopy by zone and month', tag});
exportgraphics(f, fullfile(outDir,'fig2_zone_light.png'),'Resolution',160); close(f);

% 3 --- tilt trade-off: PV energy vs crop light ---------------------------
tilts = res.sweep.tilts; pv = res.sweep.pv; lg = res.sweep.light;
f = mkfig([100 100 900 440]);
yyaxis left; plot(tilts, pv, '-o','Color',A,'LineWidth',2); ylabel('PV energy (kWh / m^2 panel / yr)');
yyaxis right; plot(tilts, lg, '-s','Color',G,'LineWidth',2); ylabel('Mean ground light (% of open field)'); ax = gca; ax.YAxis(1).Color = A; ax.YAxis(2).Color = G;
xlabel('Fixed panel tilt (deg)'); grid on; title({'Agrivoltaic trade-off: electricity vs crop light', tag});
exportgraphics(f, fullfile(outDir,'fig3_tilt_tradeoff.png'),'Resolution',160); close(f);

% 4 --- water balance --------------------------------------------------
cum = [0 cumsum(dim)]; mr = zeros(1,12); mh = mr; mi = mr;
for m = 1:12, r = cum(m)+1:cum(m+1); mr(m) = sum(res.wb.rain(r)); mh(m) = sum(res.wb.harvSeries(r)); mi(m) = sum(res.wb.irrSeries(r)); end
f = mkfig([100 100 950 700]);
subplot(2,1,1); bar(1:12, mr, 'FaceColor', B); ylabel('Rain (mm)'); set(gca,'XTick',1:12,'XTickLabel',mon); grid on;
title({'Rainfall (NASA POWER climatology) and rain-harvest', tag});
subplot(2,1,2); area(1:365, res.wb.tankSeries, 'FaceColor', T, 'FaceAlpha', 0.5); hold on;
plot(1:365, cumsum(res.wb.harvSeries)/10, 'Color', B, 'LineWidth', 1.5);
xlabel('Day of year'); ylabel('Cistern level (m^3)'); grid on;
legend('Cistern level','Cumulative harvest / 10','Location','northwest');
title(sprintf('Cistern %.0f m^3 | harvested %.0f m^3 | irrigation demand %.0f m^3 | borewell top-up %.0f m^3', P.tankM3, res.wb.harvested, res.wb.demand, res.wb.unmet));
exportgraphics(f, fullfile(outDir,'fig4_water_balance.png'),'Resolution',160); close(f);

% 5 --- zone yields ----------------------------------------------------
f = mkfig([100 100 900 420]);
names = {res.wb.zones.name}; bar(categorical(names, names), [res.wb.zones.potYield; res.wb.zones.yield]');
legend('Potential (no water stress)','Actual','Location','northeast'); ylabel('Yield (t/ha)'); grid on;
title({'Crop yield per zone', tag});
exportgraphics(f, fullfile(outDir,'fig5_zone_yield.png'),'Resolution',160); close(f);
end

function f = mkfig(pos)
f = figure('Visible','off','Position',pos); try, theme(f,'light'); catch, end
end

function r = rootOf(p)
%ROOTOF project root: parent of the matlab folder; if the design file is not there (script copied into a Review folder), use ../_project_core
r = fileparts(fileparts(p));
if ~exist(fullfile(r,'design','design.json'),'file'), r = fullfile(fileparts(r),'_project_core'); end
end
