function build_simulink_sensor_controller()
%BUILD_SIMULINK_SENSOR_CONTROLLER  Simulink block diagram of the five-sensor controller on a test day (16 April, TCE ground).
%   Sensors (From Workspace): pyranometer GHI, DHT11 temperature and humidity, soil moisture, rain sensor.  PAR is simulated inside the controller block
%   from the canopy physics at the angle in use.  Controller block = srmc_sensor_controller (same rule as the web twin).
%   Test day: sunny morning, cloud 11:00 to 11:30, rain 14:00 to 15:00, soil dries below 20 % after 12:00, wind gust 18 m/s 17:00 to 17:30 (stow).
%   Outputs: ../sensor_controller/results/simulink/srmc_sensor_controller.slx, diagram png, log csv, day plot data.
here = fileparts(mfilename('fullpath')); od = fullfile(fileparts(here), 'sensor_controller', 'results', 'simulink'); if ~exist(od, 'dir'), mkdir(od); end
addpath(fullfile(fileparts(fileparts(here)), 'Review0_Prototype_Demo', 'matlab'));
F = review0_physics(); clim = jsondecode(fileread(fullfile(fileparts(fileparts(here)), '_project_core', 'data', 'climates.json'))); clim = clim(1); m = 4; n = 106;
dt = 300; t = (0:dt:86400)'; h = t/3600; N = numel(t); ghi = zeros(N,1); T = zeros(N,1); RH = zeros(N,1); soil = 26*ones(N,1); rain = zeros(N,1); wind = 3 + 1.5*sin(2*pi*h/24);
for i = 1:N
    sun = F.sunVec(clim.lat, n, h(i)); kf = 1; if h(i) >= 11 && h(i) < 11.5, kf = 0.3; end
    irr = F.irradiance(sun.sz, n, clim.kt(m)*kf); ghi(i) = irr.ghi;
    T(i) = clim.tmean(m) + clim.trange(m)/2*sin(2*pi*(h(i)-9)/24); RH(i) = max(15, min(98, clim.rh(m) - 12*cos(2*pi*(h(i)-15)/24)));
    if h(i) >= 12, soil(i) = 17; end
    if h(i) >= 14 && h(i) < 15, rain(i) = 1; ghi(i) = 0.15*ghi(i); end
    if h(i) >= 17 && h(i) < 17.5, wind(i) = 18; end
end
mdl = 'srmc_sensor_controller_model'; if bdIsLoaded(mdl), close_system(mdl, 0); end
new_system(mdl); open_system(mdl); set_param(mdl, 'Solver', 'FixedStepDiscrete', 'FixedStep', num2str(dt), 'StopTime', '86400');
ab = @(src, name, pos) add_block(src, [mdl '/' name], 'Position', pos);
ab('simulink/Sources/From Workspace', 'Six sensors: GHI, T, RH, soil, rain, wind', [30 60 260 120]);
set_param([mdl '/Six sensors: GHI, T, RH, soil, rain, wind'], 'VariableName', 'sc_inputs_ts', 'SampleTime', num2str(dt));
% From Workspace wants a timeseries or [t, data] matrix
assignin('base', 'sc_inputs_ts', [t, h, ghi, T, RH, soil, rain, wind]);
ab('simulink/Discrete/Unit Delay', 'Previous angle', [560 200 620 240]); set_param([mdl '/Previous angle'], 'InitialCondition', '15', 'SampleTime', num2str(dt));
ab('simulink/User-Defined Functions/Interpreted MATLAB Function', 'SRMC-SC five-sensor controller', [400 90 560 150]);
set_param([mdl '/SRMC-SC five-sensor controller'], 'MATLABFcn', 'sl_sc_step', 'OutputDimensions', '2');
ab('simulink/Signal Routing/Demux', 'Angle and mode', [600 90 605 160]); set_param([mdl '/Angle and mode'], 'Outputs', '2');
ab('simulink/Discontinuities/Quantizer', 'Encoder 0.5 deg', [650 90 720 120]); set_param([mdl '/Encoder 0.5 deg'], 'QuantizationInterval', '0.5');
ab('simulink/Sinks/Scope', 'Panel angle scope', [770 85 810 125]);
ab('simulink/Sinks/To Workspace', 'log angle', [770 150 840 180]); set_param([mdl '/log angle'], 'VariableName', 'angle_out', 'SaveFormat', 'Array');
ab('simulink/Sinks/To Workspace', 'log mode', [770 200 840 230]); set_param([mdl '/log mode'], 'VariableName', 'mode_out', 'SaveFormat', 'Array');
% wiring: 6 sensor signals (hour, GHI, T, RH, soil, rain) + previous angle = 7 inputs of the controller block
ab('simulink/Signal Routing/Mux', 'Mux inputs', [330 90 335 180]); set_param([mdl '/Mux inputs'], 'Inputs', '2');
L = @(a, b) add_line(mdl, a, b, 'autorouting', 'on');
L('Six sensors: GHI, T, RH, soil, rain, wind/1', 'Mux inputs/1'); L('Previous angle/1', 'Mux inputs/2'); L('Mux inputs/1', 'SRMC-SC five-sensor controller/1');
L('SRMC-SC five-sensor controller/1', 'Angle and mode/1'); L('Angle and mode/1', 'Encoder 0.5 deg/1'); L('Angle and mode/1', 'Previous angle/1');
L('Encoder 0.5 deg/1', 'Panel angle scope/1'); L('Encoder 0.5 deg/1', 'log angle/1'); L('Angle and mode/2', 'log mode/1');
save_system(mdl, fullfile(od, [mdl '.slx']));
try, print(['-s' mdl], '-dpng', '-r130', fullfile(od, 'srmc_sensor_controller_diagram.png')); catch ME, warning('diagram export failed: %s', ME.message); end
so = sim(mdl); ang = so.angle_out; md = so.mode_out;
Tt = table(h(1:numel(ang)), ghi(1:numel(ang)), T(1:numel(ang)), RH(1:numel(ang)), soil(1:numel(ang)), rain(1:numel(ang)), wind(1:numel(ang)), ang, md, 'VariableNames', {'hour','ghi_Wm2','T_C','RH_pct','soil_pct','rain','wind_ms','angle_deg','mode'});
writetable(Tt, fullfile(od, 'sensor_controller_log.csv')); disp(Tt(1:12:end, :));
end
