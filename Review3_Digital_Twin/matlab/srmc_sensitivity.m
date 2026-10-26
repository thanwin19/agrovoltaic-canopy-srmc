function S = srmc_sensitivity(N)
%SRMC_SENSITIVITY  How wrong can the money and water answers be if our assumptions are wrong?
%   1) one-at-a-time tornado charts   2) physics scenarios (drier year, cloudier year)   3) Monte Carlo (N draws, triangular inputs)
%   Outputs in out/matlab/: fig12..fig15 PNG, T5..T7 CSV, sensitivity_summary.md.   Run: cd matlab; srmc_sensitivity();
if nargin < 1, N = 20000; end
root = rootOf(mfilename('fullpath')); od = fullfile(root,'out','matlab'); if ~exist(od,'dir'), mkdir(od); end
Q = struct('plots',false,'quiet',true,'export',false); rng(7);
base = srmc_run('tce_madurai','red_sandy_loam',struct('angleStep',1),Q); P = base.params; e = base.eco;
cropCost = e.cropRev - e.cropNet; tank = P.tankM3*P.cisternPerM3;

% ---- economics as a function of the uncertain inputs (physics numbers kwh, cropRev, cropCost come from the base run)
f = @(x) evalEco(x, e, cropCost, tank);
x0 = struct('tariff',P.tariff,'share',P.farmerShare,'capex',P.capexPerKWp,'cropPrice',1,'kwhScale',1,'cropYield',1,'omPct',P.omPct,'subsidy',P.subsidyPct/100);
names = {'tariff','share','capex','cropPrice','kwhScale','cropYield','omPct','subsidy'};
labels = {'Industry tariff (INR/kWh)','Farmer share of payment','Capex (INR/kWp)','Crop price (x)','PV energy model error (x)','Crop yield (x)','O&M (% of capex/yr)','Capital subsidy'};
lo = [2.0 0.15 45000 0.7 0.92 0.7 0.010 0]; hi = [4.5 0.45 85000 1.3 1.05 1.2 0.025 0.30];

%% 1 tornado
r0 = f(x0); nI = numel(names); out = zeros(nI,4);
for i = 1:nI
    a = x0; a.(names{i}) = lo(i); b = x0; b.(names{i}) = hi(i); ra = f(a); rb = f(b);
    out(i,:) = [ra.farmerMonthly rb.farmerMonthly ra.payback rb.payback];
end
T5 = table(string(labels'), lo', hi', out(:,1), out(:,2), out(:,3), out(:,4), 'VariableNames', {'input','low','high','farmer_inr_month_at_low','farmer_inr_month_at_high','payback_yr_at_low','payback_yr_at_high'});
writetable(T5, fullfile(od,'T5_tornado.csv'));
tornado(labels, out(:,1:2)/1e3, r0.farmerMonthly/1e3, 'Farmer income (INR thousand / month / ha)', fullfile(od,'fig12_tornado_farmer_income.png'));
tornado(labels, out(:,3:4), r0.payback, 'Investor payback (years)', fullfile(od,'fig13_tornado_payback.png'));

%% 2 physics scenarios (re-run the full model)
sc = {'Base year', struct(); 'Drier year (rain -30 %)', struct('rainScale',0.7); 'Wetter year (rain +20 %)', struct('rainScale',1.2); 'Cloudier (sunshine -5 %)', struct('ktScale',0.95); 'Clearer (sunshine +5 %)', struct('ktScale',1.05)};
rows = cell(size(sc,1),1);
for i = 1:size(sc,1)
    p = sc{i,2}; p.angleStep = 1; r = srmc_run('tce_madurai','red_sandy_loam',p,Q); w = r.wb;
    rows{i} = struct('scenario',string(sc{i,1}),'pv_kWh_m2',r.annual.pvKWhPerM2,'rain_harvested_m3',w.harvested,'irrigation_demand_m3',w.demand,'borewell_topup_m3',w.unmet,'rain_fed_pct',100*w.supplied/max(w.demand,eps),'crop_net_lakh',r.eco.cropNet/1e5,'farmer_inr_month',r.eco.farmerMonthlyAvg);
end
T6 = struct2table([rows{:}]); writetable(T6, fullfile(od,'T6_physics_scenarios.csv'));
fg = mkfig([100 100 1000 440]); yyaxis left; bar(categorical(T6.scenario, T6.scenario), [T6.rain_harvested_m3 T6.irrigation_demand_m3]); ylabel('m^3 / ha / yr'); yyaxis right; plot(1:height(T6), T6.rain_fed_pct, '-o','LineWidth',2); ylabel('Irrigation met from rain (%)'); ylim([0 105]); grid on; legend('Harvested','Demand','Rain-fed %','Location','southwest'); title('Weather years: how much irrigation the rain harvest covers');
exportgraphics(fg, fullfile(od,'fig15_weather_scenarios.png'),'Resolution',160); close(fg);

%% 3 Monte Carlo
tri = @(a,m,b,u) (u < (m-a)/(b-a)).*(a + sqrt(u.*(b-a).*(m-a))) + (u >= (m-a)/(b-a)).*(b - sqrt((1-u).*(b-a).*(b-m)));
spec = [2.5 3.0 4.5;  0.15 0.30 0.45;  45000 60000 85000;  0.7 1.0 1.3;  0.92 1.0 1.05;  0.7 0.95 1.2;  0.010 0.015 0.025;  0 0 0.30];
X = zeros(N,nI); for i = 1:nI, X(:,i) = tri(spec(i,1), spec(i,2), spec(i,3), rand(N,1)); end
fm = zeros(N,1); pb = zeros(N,1); tot = zeros(N,1);
for k = 1:N
    x = struct('tariff',X(k,1),'share',X(k,2),'capex',X(k,3),'cropPrice',X(k,4),'kwhScale',X(k,5),'cropYield',X(k,6),'omPct',X(k,7),'subsidy',X(k,8));
    r = f(x); fm(k) = r.farmerMonthly; pb(k) = r.payback; tot(k) = r.total;
end
pr = @(v) prctile(v,[5 50 95]);
P1 = pr(fm); P2 = pr(pb(isfinite(pb))); P3 = pr(tot);
pFarm = [mean(fm >= 1e5) mean(fm >= 1.5e5) mean(fm >= 2e5)]; pPay = [mean(pb <= 15) mean(pb <= 20) mean(pb <= 25)];
rho = corr(X, fm, 'Type', 'Spearman'); rhoP = corr(X, pb, 'Type', 'Spearman', 'Rows', 'complete');
fg = mkfig([100 100 1100 430]); tiledlayout(1,3,'TileSpacing','compact');
nexttile; histogram(fm/1e3, 50, 'FaceColor', [0.45 0.72 0.19]); xline(P1/1e3, '--'); xlabel('Farmer income (INR thousand/month/ha)'); ylabel('draws'); title(sprintf('P5 %.0f  P50 %.0f  P95 %.0f', P1/1e3)); grid on;
nexttile; histogram(min(pb(isfinite(pb)),100), 0:2:100, 'FaceColor', [0.94 0.69 0.19]); xline(P2, '--'); xlabel('Investor payback (years, clipped at 100)'); title(sprintf('P5 %.1f  P50 %.1f  P95 %.1f   (%.0f %% above 100 y)', P2, 100*mean(pb>100))); grid on;
nexttile; [~, ix] = sort(abs(rho), 'descend'); barh(rho(ix), 'FaceColor', [0.29 0.62 0.91]); set(gca,'YTick',1:nI,'YTickLabel',labels(ix),'YDir','reverse'); xlabel('Spearman rank correlation with farmer income'); grid on; title('What drives farmer income');
exportgraphics(fg, fullfile(od,'fig14_montecarlo.png'),'Resolution',160); close(fg);
T7 = table(string(labels'), rho, rhoP, 'VariableNames', {'input','rank_corr_farmer_income','rank_corr_payback'}); writetable(T7, fullfile(od,'T7_montecarlo_rank_correlation.csv'));

%% 4 what tariff makes the investor case work? (break-even, base physics)
capex0 = e.kwp*P.capexPerKWp*(1-P.subsidyPct/100) + tank; om0 = e.kwp*P.capexPerKWp*P.omPct; targets = [10 15 20]; shares = [0.1 0.3 0.5]; rowsB = {};
for tg = targets, for sh = shares
    tReq = (capex0/tg + om0)/(e.kwh*(1-sh)); fIncome = (e.kwh*tReq*sh + e.cropNet)/12;
    rowsB(end+1,:) = {tg, sh, tReq, fIncome}; %#ok<AGROW>
end, end
T8 = cell2table(rowsB, 'VariableNames', {'target_investor_payback_yr','farmer_share','tariff_needed_inr_per_kwh','farmer_income_inr_month'}); writetable(T8, fullfile(od,'T8_breakeven_tariff.csv'));
S = struct('base',r0,'P_farmer',P1,'P_payback',P2,'P_total',P3,'pFarm',pFarm,'pPay',pPay,'T5',T5,'T6',T6,'T7',T7);
fid = fopen(fullfile(od,'sensitivity_summary.md'),'w');
fprintf(fid,'# Sensitivity and uncertainty study (TCE ground, per hectare)\n\nBase case: farmer income %.0f INR/month, investor payback %.1f years (industry pays INR %.1f/kWh, farmer share %.0f %%, capex INR %.0f/kWp).\n\n', r0.farmerMonthly, r0.payback, P.tariff, 100*P.farmerShare, P.capexPerKWp);
fprintf(fid,'## Monte Carlo (%d draws, triangular inputs, ranges in T5)\n\n| outcome | P5 | P50 | P95 |\n|---|---|---|---|\n| Farmer income (INR/month/ha) | %.0f | %.0f | %.0f |\n| Investor payback (years) | %.1f | %.1f | %.1f |\n| Total annual value (INR lakh/ha) | %.1f | %.1f | %.1f |\n\n', N, P1, P2, P3/1e5);
fprintf(fid,'- Probability farmer income >= INR 1.0 / 1.5 / 2.0 lakh per month: **%.0f %% / %.0f %% / %.0f %%**\n- Probability investor payback <= 15 / 20 / 25 years: **%.0f %% / %.0f %% / %.0f %%**\n\n', 100*pFarm, 100*pPay);
fprintf(fid,'## Weather scenarios (full model re-run)\n\n'); writeMd(fid, T6);
fprintf(fid,'\n## Strongest drivers of farmer income (rank correlation)\n\n'); writeMd(fid, sortrows(T7,'rank_corr_farmer_income','descend','ComparisonMethod','abs'));
fprintf(fid,'\n## Break-even: tariff the industry must pay for a given investor payback (base capex, base physics)\n\n'); writeMd(fid, T8);
fprintf(fid,'\nInput ranges are judgement-based (no market survey). Physics-model error is represented by a +-%% band around PVGIS agreement (-8 %% to +5 %%). Prices, tariff and farmer share are assumptions to be replaced with real quotes.\n'); fclose(fid);
fprintf('Sensitivity done: farmer income P5/P50/P95 = %.0f / %.0f / %.0f INR/month; investor payback P50 %.1f years\n', P1(1), P1(2), P1(3), P2(2));
end

function r = evalEco(x, e, cropCost, tank)
kwp = e.kwp; kwh = e.kwh*x.kwhScale; solarRev = kwh*x.tariff; om = kwp*x.capex*x.omPct;
cropNet = e.cropRev*x.cropPrice*x.cropYield - cropCost; farmer = solarRev*x.share + cropNet;
capex = kwp*x.capex*(1-x.subsidy) + tank; industry = solarRev*(1-x.share) - om;
r = struct('farmerMonthly', farmer/12, 'payback', capex/industry, 'total', solarRev - om + cropNet);
if industry <= 0, r.payback = Inf; end
end
function tornado(labels, V, base, xl, path)
sp = abs(V(:,2) - V(:,1)); [~, ix] = sort(sp, 'descend'); V = V(ix,:); lb = labels(ix); n = numel(lb);
fg = mkfig([100 100 960 460]); hold on;
for i = 1:n, barh(n+1-i, V(i,1)-base, 'FaceColor', [0.85 0.4 0.3], 'BaseValue', base); barh(n+1-i, V(i,2)-base, 'FaceColor', [0.3 0.6 0.85], 'BaseValue', base); end
set(gca,'YTick',1:n,'YTickLabel',flip(lb)); xline(base,'k-'); xlabel(xl); grid on; title(sprintf('One-at-a-time sensitivity (base %.1f); red = low input, blue = high input', base));
exportgraphics(fg, path, 'Resolution', 160); close(fg);
end
function f = mkfig(pos)
f = figure('Visible','off','Position',pos); try, theme(f,'light'); catch, end
end
function writeMd(fid, T)
v = T.Properties.VariableNames; fprintf(fid,'| %s |\n|%s\n', strjoin(v,' | '), repmat('---|', 1, numel(v)));
for i = 1:height(T)
    c = cell(1,numel(v));
    for j = 1:numel(v), x = T.(v{j})(i); if iscell(x), x = x{1}; end, if isnumeric(x), c{j} = sprintf('%.2f', x); else, c{j} = char(string(x)); end, end
    fprintf(fid,'| %s |\n', strjoin(c,' | '));
end
end

function r = rootOf(p)
%ROOTOF project root: parent of the matlab folder; if the design file is not there (script copied into a Review folder), use ../_project_core
r = fileparts(fileparts(p));
if ~exist(fullfile(r,'design','design.json'),'file'), r = fullfile(fileparts(r),'_project_core'); end
end
