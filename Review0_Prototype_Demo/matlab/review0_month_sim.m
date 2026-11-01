function review0_month_sim()
%REVIEW0_MONTH_SIM  One SIMULATED month (October 2023, TCE) driven by REAL NASA POWER hourly weather.
%   Inputs that are real data: sunlight, PAR, air temperature, humidity, wind and rain (NASA POWER, 9.88 N 78.08 E).
%   Everything else is simulated: the six sensors read the real weather plus datasheet-sized random errors, the soil is a simple water balance,
%   the controller decides from the (noisy) sensor values and its decision is scored under the TRUE weather.
%   This is NOT a field measurement. Outputs go to Proof/11_Simulated_Month_Oct2023/ and every file says SIMULATED.
root = fileparts(fileparts(fileparts(mfilename('fullpath')))); out = fullfile(root, 'Proof', '11_Simulated_Month_Oct2023'); if ~exist(out, 'dir'), mkdir(out); end
F = review0_physics(); P = F.designParams(); lat = 9.88;
J = jsondecode(fileread(fullfile(root, 'Proof', '10_Review0_Sensors_and_Panels', 'sunlight_datasets', 'NASA_POWER_hourly_2023_full_year_TCE.json'))); p = J.properties.parameter;
vec = @(s) cell2mat(struct2cell(s)); K = 1e6 / 3600;
G = vec(p.ALLSKY_SFC_SW_DWN) * K; PARw = vec(p.ALLSKY_SFC_PAR_TOT) * K; T = vec(p.T2M); RH = vec(p.RH2M); WS = vec(p.WS10M); RN = vec(p.PRECTOTCORR);
d0 = 274; d1 = 304; rng(11); cfg = struct('wEnergy', 0.5);
rows = []; soil = 50; pump = false; hdr = {'day_of_year', 'date', 'solar_hour', 'ghi_Wm2', 'par_umol', 'T_C', 'RH_pct', 'wind_ms', 'rain_mmh', 'soil_pct_true', 'mode', 'angle_deg', 'pv_Wm2_ctrl', 'pv_Wm2_fixed45', 'crop_ctrl', 'crop_fixed45', 'par_under_ctrl_umol', 'par_under_fixed45_umol', 'pump_on'};
for day = d0:d1
    for h = 0:23
        i = (day - 1) * 24 + h + 1; g = G(i); sh = h + 0.5; sun = F.sunVec(lat, day, sh);
        et = 0.45 * g / 800; soil = max(0, min(100, soil - et + 3 * RN(i) + 6 * pump)); if soil < 35, pump = true; elseif soil > 55, pump = false; end
        if g < 20 || sun.sz < 0.02, continue; end
        S = struct('tempC', T(i), 'rh', RH(i), 'soilPct', soil, 'rain', double(RN(i) >= 0.5));
        V = struct('lat', lat, 'day', day, 'hour', sh, 'kt', 0.5, 'windMS', WS(i), 'ghiOverride', g, 'parOverride', PARw(i) * 4.57);
        z = max(-2, min(2, randn(1, 6)));                               % one draw per hour: sigma = half of the datasheet limit
        Ss = S; Vs = V; Vs.ghiOverride = g * (1 + 0.025 * z(1)); Vs.parOverride = V.parOverride * (1 + 0.025 * z(2)); Ss.tempC = S.tempC + 1.0 * z(3); Ss.rh = min(100, max(0, S.rh + 2.5 * z(4))); Ss.soilPct = min(100, max(0, soil + 1.5 * z(5))); Vs.windMS = max(0, WS(i) + 0.5 * z(6));
        dS = review0_controller(Ss, Vs, P, F, cfg);
        c1 = cfg; c1.forceAngle = dS.angle; dC = review0_controller(S, V, P, F, c1); c2 = cfg; c2.forceAngle = 45; dF = review0_controller(S, V, P, F, c2);
        rows = [rows; {day, datestr(datetime(2023, 1, 1) + days(day - 1), 'yyyy-mm-dd'), sh, g, V.parOverride, S.tempC, S.rh, V.windMS, RN(i), soil, dS.mode, dS.angle, dC.pv, dF.pv, dC.crop, dF.crop, mean(dC.parZone), mean(dF.parZone), double(pump)}]; %#ok<AGROW>
    end
    if mod(day - d0, 5) == 0, fprintf('day %d done\n', day); end
end
Tb = cell2table(rows, 'VariableNames', hdr); writetable(Tb, fullfile(out, 'SIMULATED_hourly_Oct2023_TCE.csv'));
fprintf('rows %d\n', height(Tb));
end
