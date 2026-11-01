function app = review0_dashboard(varargin)
%REVIEW0_DASHBOARD  Review 0 dashboard: six simulated real-model sensors (every one adjustable by hand) -> SRMC tilt decision.
%
%   review0_dashboard                         open the window (live loop starts by itself)
%   app = review0_dashboard('Headless',true)  no window timer: used for screenshots and tests
%
%   Everything runs on the computer. Each sensor is SIMULATED after a real, named device (datasheet values in the "Sensors and panels" tab):
%     Apogee SP-110 pyranometer | Apogee SQ-110 PAR sensor | DHT11 (air temperature + humidity) | DFRobot SEN0193 soil moisture |
%     YL-83 / FC-37 rain sensor | Adafruit 1733 anemometer.      PV modules: 8 x JinkoSolar Tiger Pro JKM550M-72HL4-V (550 Wp).
%   Every sensor can be set by hand (slider or typed number). Until you touch a sensor it follows the day / sky model (AUTO).
%   Decision (review0_controller): wind stow > rain 3 deg > night park > optimise energy + crop light.
p = inputParser; addParameter(p, 'Headless', false); addParameter(p, 'Visible', true); parse(p, varargin{:}); headless = p.Results.Headless;
F = review0_physics(); P = F.designParams();
logDir = fullfile(fileparts(fileparts(mfilename('fullpath'))), 'results', 'live_logs'); if ~exist(logDir, 'dir'), mkdir(logDir); end

% ---------------- state ----------------
SKYNAMES = {'Clear', 'Hazy', 'Partly cloudy', 'Overcast'}; SKYKT = [0.62 0.50 0.36 0.18];      % clearness index of each sky
cfg = struct('wEnergy', 0.5, 'windStow', 15, 'vpdHigh', 2.5, 'soilDry', 35, 'soilWet', 55);
KEYS = {'ghi', 'par', 'temp', 'rh', 'soil', 'wind'};
st = struct('tempC', 31, 'rh', 55, 'soilPct', 48, 'soilSim', 48, 'rain', 0, 'simRain', false, 'tank', 120, 'pump', false, 'play', false, 'hist', zeros(0, 14), 'n', 0, ...
    't0', tic, 'lat', 9.88, 'lastMsg', 'ready', 'exFig', [], 'mppt', [], 'man', struct('ghi', false, 'par', false, 'temp', false, 'rh', false, 'soil', false, 'wind', false), ...
    'lastKey', [], 'same', 0, 'curveKey', [], 'cKey', [], 'mKey', [], 'staleDay', true, 'DA', [], 'busy', false);
NMOD = 8; MODAREA = 2.278 * 1.134;                    % 8 modules, area of one module (m2)
% sensor catalogue: key, heading, real device, unit, slider min, max, value format, spec line
SEN = struct('key', {'ghi', 'par', 'temp', 'rh', 'soil', 'wind'}, ...
    'head', {'1  PYRANOMETER: sunlight', '2  PAR SENSOR: plant light', '3  AIR TEMPERATURE', '4  AIR HUMIDITY', '5  SOIL MOISTURE', '7  WIND SPEED'}, ...
    'dev', {'Apogee SP-110', 'Apogee SQ-110', 'DHT11', 'DHT11 (same chip)', 'DFRobot SEN0193', 'Adafruit 1733 anemometer'}, ...
    'unit', {'W/m2', 'umol/m2/s', 'deg C', '% RH', '% water', 'm/s'}, 'lo', {0, 0, 0, 20, 0, 0}, 'hi', {1200, 2400, 50, 90, 100, 25}, 'fmt', {'%.0f', '%.0f', '%.1f', '%.0f', '%.0f', '%.1f'}, ...
    'spec', {'real range 0-2000 W/m2, +-5 %, 0.20 mV per W/m2', 'real range 0-4000 umol/m2/s, +-5 %, 0.20 mV per umol', 'real range 0-50 C, +-2 C, digital', 'real range 20-90 % RH, +-5 % RH, digital', 'capacitive probe, output 2.5 V dry to 1.2 V wet', 'real range 0-32.4 m/s, +-1 m/s, output 0.4-2.0 V'});

% ---------------- figure ----------------
BG = [0.94 0.95 0.97]; NAVY = [0.07 0.15 0.27]; GREEN = [0.13 0.55 0.28]; AMBER = [0.95 0.62 0.08]; GREY = [0.38 0.42 0.47]; INK = [0.10 0.13 0.18];
fig = figure('Name', 'SRMC Review 0 dashboard', 'NumberTitle', 'off', 'Color', BG, 'Position', [10 10 1500 880], 'Visible', ternary(p.Results.Visible, 'on', 'off'), 'MenuBar', 'none', 'ToolBar', 'none');
try, theme(fig, 'light'); catch, end
T = @(par, pos, str, varargin) uicontrol(par, 'Style', 'text', 'Units', 'normalized', 'Position', pos, 'String', str, 'BackgroundColor', BG, 'ForegroundColor', INK, 'HorizontalAlignment', 'left', 'FontSize', 10, varargin{:});
U = @(pos, style, str, cb, varargin) uicontrol(fig, 'Style', style, 'Units', 'normalized', 'Position', pos, 'String', str, 'Callback', cb, 'BackgroundColor', [1 1 1], 'HorizontalAlignment', 'center', 'FontSize', 10, varargin{:});
% header
uicontrol(fig, 'Style', 'text', 'Units', 'normalized', 'Position', [0 0.935 1 0.065], 'String', '  SRMC Agrovoltaic Canopy  |  six-sensor smart tilt controller', 'BackgroundColor', NAVY, 'ForegroundColor', 'w', 'FontSize', 17, 'FontWeight', 'bold', 'HorizontalAlignment', 'left');
uicontrol(fig, 'Style', 'text', 'Units', 'normalized', 'Position', [0.55 0.935 0.45 0.05], 'String', 'Review 0  |  100 % computer simulation, sensors modelled on real datasheets', 'BackgroundColor', NAVY, 'ForegroundColor', [0.75 0.88 1], 'FontSize', 10, 'HorizontalAlignment', 'right');

% ---------------- left: sensors ----------------
x0 = 0.008; w = 0.258;
T(fig, [x0 0.905 w 0.026], 'TIME AND WEATHER', 'FontWeight', 'bold', 'ForegroundColor', GREEN);
T(fig, [x0 0.877 0.07 0.024], 'day of year'); h.day = uicontrol(fig, 'Style', 'slider', 'Units', 'normalized', 'Position', [x0 + 0.075 0.88 0.183 0.02], 'Min', 1, 'Max', 365, 'Value', 105, 'Callback', @(~, ~) onTime());
T(fig, [x0 0.851 0.07 0.024], 'solar hour'); h.hour = uicontrol(fig, 'Style', 'slider', 'Units', 'normalized', 'Position', [x0 + 0.075 0.854 0.183 0.02], 'Min', 5, 'Max', 19, 'Value', 12, 'Callback', @(~, ~) onTime());
T(fig, [x0 0.823 0.07 0.024], 'sky'); h.sky = U([x0 + 0.075 0.825 0.12 0.028], 'popupmenu', SKYNAMES, @(~, ~) onTime());
h.play = uicontrol(fig, 'Style', 'checkbox', 'Units', 'normalized', 'Position', [x0 + 0.2 0.826 0.06 0.026], 'String', 'play', 'BackgroundColor', BG, 'Callback', @(s, ~) setPlay(s.Value), 'TooltipString', 'the hour advances by itself');
T(fig, [x0 0.793 w 0.026], 'SENSORS (move a slider or type a value)', 'FontWeight', 'bold', 'ForegroundColor', GREEN);
h.sl = struct(); h.ed = struct(); h.sig = struct(); h.tag = struct();
y = 0.790;
for i = 1:6
    k = SEN(i).key; yy = y - (i - 1 + (i >= 6)) * 0.0905;          % block 6 is the rain sensor, so the wind sensor is block 7
    h.tag.(k) = uicontrol(fig, 'Style', 'text', 'Units', 'normalized', 'Position', [x0 + 0.19 yy - 0.024 0.068 0.022], 'String', 'AUTO', 'BackgroundColor', [0.85 0.93 0.86], 'ForegroundColor', GREEN, 'FontSize', 8, 'FontWeight', 'bold');
    T(fig, [x0 yy - 0.024 0.19 0.024], [SEN(i).head ' (' SEN(i).dev ')'], 'FontWeight', 'bold', 'FontSize', 8.5);
    h.sl.(k) = uicontrol(fig, 'Style', 'slider', 'Units', 'normalized', 'Position', [x0 yy - 0.047 0.185 0.02], 'Min', SEN(i).lo, 'Max', SEN(i).hi, 'Value', SEN(i).lo, 'Callback', @(~, ~) onSlider(k), 'TooltipString', [SEN(i).dev ': ' SEN(i).spec]);
    h.ed.(k) = uicontrol(fig, 'Style', 'edit', 'Units', 'normalized', 'Position', [x0 + 0.19 yy - 0.050 0.068 0.025], 'String', '', 'BackgroundColor', 'w', 'Callback', @(~, ~) onEdit(k), 'TooltipString', ['type a value in ' SEN(i).unit ' and press Enter']);
    h.sig.(k) = T(fig, [x0 yy - 0.073 w 0.022], '', 'FontSize', 8, 'ForegroundColor', GREY);
end
yr = y - 5 * 0.0905;                          % rain sensor block
T(fig, [x0 yr - 0.024 0.19 0.024], '6  RAIN SENSOR (YL-83 / FC-37)', 'FontWeight', 'bold', 'FontSize', 8.5);
h.tag.rain = uicontrol(fig, 'Style', 'text', 'Units', 'normalized', 'Position', [x0 + 0.19 yr - 0.024 0.068 0.022], 'String', 'dry', 'BackgroundColor', [0.85 0.93 0.86], 'ForegroundColor', GREEN, 'FontSize', 8, 'FontWeight', 'bold');
h.rainBtn = uicontrol(fig, 'Style', 'togglebutton', 'Units', 'normalized', 'Position', [x0 yr - 0.054 w 0.03], 'String', 'RAIN: dry (press to make it rain)', 'FontSize', 10, 'Callback', @(s, ~) setSimRain(s.Value), 'TooltipString', 'wet plate: the sensor output goes LOW and the controller flattens the panels to harvest the rain');
h.sig.rain = T(fig, [x0 yr - 0.078 w 0.022], '', 'FontSize', 8, 'ForegroundColor', GREY);
T(fig, [x0 0.145 w 0.024], 'controller weight: energy share / crop share (%)', 'FontWeight', 'bold', 'FontSize', 9);
h.w = uicontrol(fig, 'Style', 'slider', 'Units', 'normalized', 'Position', [x0 0.122 0.185 0.02], 'Min', 0, 'Max', 1, 'Value', 0.5, 'Callback', @(~, ~) onWeight());
h.wTxt = T(fig, [x0 + 0.19 0.12 0.068 0.024], '', 'FontSize', 9);
h.preset = U([x0 0.072 0.13 0.03], 'popupmenu', {'Weather presets', 'Clear noon', 'Passing clouds', 'Hot dry afternoon', 'Rain', 'Storm 20 m/s', 'Night'}, @(s, ~) onPreset(s.Value));
h.auto = U([x0 + 0.135 0.072 0.123 0.03], 'pushbutton', 'All sensors AUTO', @(~, ~) onAuto(), 'TooltipString', 'hand every sensor back to the day / sky model');

% ---------------- centre: canopy + decision ----------------
cx = 0.275; cw = 0.325;
h.axC = axes(fig, 'Position', [cx 0.545 cw 0.345]);
h.kpiT = cell(1, 4); kk = {'PANEL ANGLE', 'ELECTRICITY', 'CROP LIGHT', 'CLOSE TO BEST'};
for q = 1:4
    xx = cx + (q - 1) * (cw / 4);
    uicontrol(fig, 'Style', 'text', 'Units', 'normalized', 'Position', [xx 0.495 cw / 4 - 0.004 0.04], 'String', kk{q}, 'BackgroundColor', [0.85 0.88 0.93], 'ForegroundColor', GREY, 'FontSize', 8, 'FontWeight', 'bold');
    h.kpiT{q} = uicontrol(fig, 'Style', 'text', 'Units', 'normalized', 'Position', [xx 0.44 cw / 4 - 0.004 0.052], 'String', '-', 'BackgroundColor', [1 1 1], 'ForegroundColor', INK, 'FontSize', 15, 'FontWeight', 'bold');
end
h.mode = uicontrol(fig, 'Style', 'text', 'Units', 'normalized', 'Position', [cx 0.385 cw 0.05], 'String', '', 'BackgroundColor', BG, 'FontSize', 10, 'FontWeight', 'bold', 'HorizontalAlignment', 'left');
h.words = uicontrol(fig, 'Style', 'text', 'Units', 'normalized', 'Position', [cx 0.275 cw 0.108], 'String', '', 'BackgroundColor', [1 1 1], 'ForegroundColor', INK, 'FontSize', 9, 'HorizontalAlignment', 'left');
h.expl = U([cx 0.232 0.105 0.036], 'pushbutton', 'Explain the decision', @(~, ~) openExplain());
h.trust = U([cx + 0.108 0.232 0.105 0.036], 'pushbutton', 'Sensor error test', @(~, ~) runTrust(), 'TooltipString', 'what if a sensor reads 5-20 % wrong?');
h.save = U([cx + 0.216 0.232 0.109 0.036], 'pushbutton', 'Save evidence', @(~, ~) saveEvidence(), 'TooltipString', 'PNG of this window and CSV of the readings');
h.read = uicontrol(fig, 'Style', 'listbox', 'Units', 'normalized', 'Position', [cx 0.03 cw 0.195], 'FontName', 'Consolas', 'FontSize', 9, 'BackgroundColor', [0.10 0.13 0.18], 'ForegroundColor', [0.80 0.95 0.82], 'Max', 1);
h.run = uicontrol(fig, 'Style', 'togglebutton', 'Units', 'normalized', 'Position', [0.52 0.005 0.08 0.022], 'String', 'STOP live loop', 'FontSize', 8, 'Value', 1, 'Callback', @(s, ~) setRun(s.Value));
h.log = T(fig, [cx 0.003 0.24 0.022], '', 'FontSize', 8, 'ForegroundColor', GREY);

% ---------------- right: graph tabs ----------------
tg = uitabgroup(fig, 'Units', 'normalized', 'Position', [0.608 0.03 0.388 0.895], 'FontSize', 10);
tb = {uitab(tg, 'Title', 'Sensors through a day'), uitab(tg, 'Title', 'Panel angle and output'), uitab(tg, 'Title', 'Accuracy'), uitab(tg, 'Title', 'Sensors and panels')};
for q = 1:4, tb{q}.BackgroundColor = BG; end
G = struct(); NOW = gobjects(0); DYN = gobjects(0);
cap1 = {'WHAT IT SHOWS: how strong the sun is from sunrise to sunset on the chosen day and sky. Orange = all sunlight (pyranometer, W/m2). Green = only the light plants can use (PAR sensor). The dots are the values you hold right now.', ...
        'WHAT IT SHOWS: the DHT11 chip reads air temperature (red) and humidity (blue). Hot, dry air stresses plants, so the controller lets the panels shade them more.', ...
        'WHAT IT SHOWS: soil moisture (green) falls as the sun dries the soil; below 35 % the irrigation valve opens with water from the roof tank. The blue band appears when the rain sensor is wet.', ...
        'WHAT IT SHOWS: wind speed from the anemometer. Above the dashed line (15 m/s) the panels turn edge-on (90 deg) so the wind passes through and cannot damage them.'};
ttl1 = {'Sunlight sensors through the day', 'Air sensor (DHT11): temperature and humidity', 'Soil moisture and rain sensors', 'Wind sensor (anemometer)'};
for q = 1:4, [G.a1(q), G.c1(q)] = mkGraph(tb{1}, 0.765 - (q - 1) * 0.245, 0.235, ttl1{q}, cap1{q}); end
cap2 = {'WHAT IT SHOWS: the tilt the controller picks each hour (blue) against a fixed 45 deg panel (grey). It follows the sun, the plant stress, the rain and the wind. A fixed panel cannot do this.', ...
        'WHAT IT SHOWS: electricity from one square metre of panel. Compare the amber line (controller) with the fixed 45 deg panel.', ...
        'WHAT IT SHOWS: how well the crops are lit (1 = every crop gets all the light it needs). The controller gives up a little electricity to keep this high.'};
ttl2 = {'Panel angle chosen by the controller', 'Electricity made (W per m2 of panel)', 'Crop-light score (1 = best)'};
for q = 1:3, [G.a2(q), G.c2(q)] = mkGraph(tb{2}, 0.675 - (q - 1) * 0.335, 0.325, ttl2{q}, cap2{q}); end
cap3 = {'', '', ''}; ttl3 = {'Accuracy of the co-optimisation through the day', 'Average accuracy for the whole day', 'How far the chosen angle is from the best angle'};
for q = 1:3, [G.a3(q), G.c3(q)] = mkGraph(tb{3}, 0.675 - (q - 1) * 0.335, 0.325, ttl3{q}, cap3{q}); end
tg.SelectionChangedFcn = @(~, e) onTab(e.NewValue);
buildProofTab(tb{4});

% ---------------- MPPT with the real module values ----------------
MP = review0_mppt(); pm = MP.params();
pm.Isc = 14.03; pm.Voc = 49.62; pm.Imp = 13.45; pm.Vmp = 40.90; pm.Vfixed = 40.90; pm.name = 'JinkoSolar Tiger Pro JKM550M-72HL4-V (550 Wp)';
fa = @(a) pm.Imp / pm.Isc - (1 - (exp(pm.Vmp / a) - 1) / (exp(pm.Voc / a) - 1)); pm.a0 = fzero(fa, [0.5 20]);
st.mppt = struct('M', MP, 'pm', pm, 'st', MP.init(pm, 36), 'V', 36, 'P', 0, 'Pmpp', 0, 'Vmpp', 0, 'sumP', 0, 'sumM', 0, 'effRun', 100, 'eff', 100);
WD = review0_words(); lastD = []; lastS = []; lastV = [];
tm = [];
if ~headless
    tm = timer('ExecutionMode', 'fixedSpacing', 'Period', 0.5, 'TimerFcn', @(~, ~) step(), 'BusyMode', 'drop');
    fig.CloseRequestFcn = @onClose;
end
for q = 1:6, setSensor(SEN(q).key, 0); end
A0 = autoVals(h.hour.Value, 105, SKYKT(1)); for q = 1:6, setSensor(SEN(q).key, A0.(SEN(q).key)); end
initCanopy(); onWeight(); drawSensorDay(); step();
if ~headless, start(tm); end

app = struct('fig', fig, 'step', @step, 'set', @setState, 'snapshot', @snapshot, 'state', @getState, 'last', @getLast, 'trust', @runTrust, 'explain', @openExplain, 'day', @computeDay, 'tab', @(k) set(tg, 'SelectedTab', tb{k}), 'close', @() delete(fig));

% ================= callbacks and helpers =================
    function [ax, cp] = mkGraph(par, b, hgt, ttl, cap)
        ax = axes('Parent', par, 'Position', [0.10 b + hgt * 0.40 0.78 hgt * 0.47], 'Box', 'on', 'FontSize', 9, 'Color', 'w'); grid(ax, 'on'); title(ax, ttl, 'FontSize', 10.5, 'FontWeight', 'bold', 'Interpreter', 'none');
        cp = uicontrol(par, 'Style', 'text', 'Units', 'normalized', 'Position', [0.03 b 0.94 hgt * 0.32], 'String', cap, 'BackgroundColor', [1 1 0.93], 'ForegroundColor', INK, 'FontSize', 9, 'HorizontalAlignment', 'left');
    end
    function onTime()
        st.staleDay = true; drawSensorDay(); step();
    end
    function onWeight()
        cfg.wEnergy = h.w.Value; h.wTxt.String = sprintf('%.0f/%.0f', 100 * cfg.wEnergy, 100 * (1 - cfg.wEnergy)); st.staleDay = true; if ~isempty(lastD), step(); end
    end
    function onSlider(k)
        st.man.(k) = true; setSensor(k, h.sl.(k).Value); if any(strcmp(k, {'temp', 'rh', 'soil', 'wind'})), st.staleDay = true; end
        if strcmp(k, 'wind'), drawSensorDay(); end
        step();
    end
    function onEdit(k)
        v = str2double(h.ed.(k).String); i = find(strcmp({SEN.key}, k)); if isnan(v), setSensor(k, h.sl.(k).Value); return; end
        v = min(SEN(i).hi, max(SEN(i).lo, v)); st.man.(k) = true; setSensor(k, v); st.staleDay = true; if strcmp(k, 'wind'), drawSensorDay(); end
        step();
    end
    function setSensor(k, v)                      % write a value to the slider, the number box and the signal line of one sensor
        i = find(strcmp({SEN.key}, k)); v = min(SEN(i).hi, max(SEN(i).lo, v)); h.sl.(k).Value = v; h.ed.(k).String = sprintf(SEN(i).fmt, v);
        switch k
            case 'ghi', s = sprintf('signal %.0f mV  (0.20 mV per W/m2)   [+-5 %%]', 0.2 * v);
            case 'par', s = sprintf('signal %.0f mV  (0.20 mV per umol)   [0-4000 umol, +-5 %%]', 0.2 * v);
            case 'temp', s = sprintf('digital word, 1 C steps -> %.0f C   [+-2 C]', round(v));
            case 'rh', s = sprintf('digital word -> %.0f %% RH   [+-5 %% RH]', round(v));
            case 'soil', s = sprintf('signal %.2f V  (2.5 V dry ... 1.2 V wet)', 2.5 - v / 100 * 1.3);
            case 'wind', s = sprintf('signal %.2f V  (0.4 V = 0 m/s, 2.0 V = 32.4 m/s)   [+-1 m/s]', 0.4 + 1.6 * v / 32.4);
            otherwise, s = '';
        end
        h.sig.(k).String = s;
        h.tag.(k).String = ternary(st.man.(k), 'MANUAL', 'AUTO'); h.tag.(k).BackgroundColor = ternary(st.man.(k), [1 0.90 0.60], [0.85 0.93 0.86]); h.tag.(k).ForegroundColor = ternary(st.man.(k), [0.6 0.3 0], GREEN);
    end
    function A = autoVals(hr, day, kt)           % what each sensor would read from the day and sky model (used until the sensor is set by hand)
        sun = F.sunVec(st.lat, day, hr); ghi = 0;
        if sun.sz > 0.02, irr = F.irradiance(sun.sz, day, kt); ghi = irr.ghi; end
        A = struct('ghi', ghi, 'par', ghi * 0.45 * 4.57, 'temp', 31 + 3 * sin(2 * pi * (hr - 9) / 24), 'rh', 56 - 12 * cos(2 * pi * (hr - 15) / 24), 'soil', st.soilSim, 'wind', 3);
    end
    function setSimRain(v)
        st.simRain = logical(v); st.man.rain = true; setRainUi(); st.staleDay = true; drawSensorDay(); step();
    end
    function setRainUi()
        h.rainBtn.Value = st.simRain; h.rainBtn.String = ternary(st.simRain, 'RAIN: WET (press to dry it)', 'RAIN: dry (press to make it rain)');
        h.rainBtn.BackgroundColor = ternary(st.simRain, [0.62 0.80 0.98], [0.94 0.94 0.94]);
        h.sig.rain.String = ternary(st.simRain, 'digital pin = LOW (wet plate), analog value drops', 'digital pin = HIGH (dry plate)');
        h.tag.rain.String = ternary(st.simRain, 'WET', 'dry'); h.tag.rain.BackgroundColor = ternary(st.simRain, [0.62 0.80 0.98], [0.85 0.93 0.86]);
    end
    function onAuto()
        for q = 1:6, st.man.(SEN(q).key) = false; end
        st.simRain = false; setRainUi(); st.soilSim = 48; h.sl.wind.Value = 3; st.staleDay = true; drawSensorDay(); step();
    end
    function onPreset(k)                          % one click sets all the sensors
        if k < 2, return; end
        switch k
            case 2, setState('day', 105, 'hour', 12, 'sky', 'Clear', 'rain', 0, 'wind', 3, 'temp', 31, 'rh', 55, 'soil', 48);
            case 3, setState('day', 105, 'hour', 11, 'sky', 'Overcast', 'rain', 0, 'wind', 3, 'temp', 29, 'rh', 70, 'soil', 48);
            case 4, setState('day', 105, 'hour', 14, 'sky', 'Clear', 'rain', 0, 'wind', 3, 'temp', 40, 'rh', 25, 'soil', 12);
            case 5, setState('day', 220, 'hour', 14, 'sky', 'Overcast', 'rain', 1, 'wind', 5, 'temp', 26, 'rh', 90, 'soil', 55);
            case 6, setState('day', 105, 'hour', 15, 'sky', 'Partly cloudy', 'rain', 0, 'wind', 20, 'temp', 30, 'rh', 60, 'soil', 48);
            case 7, setState('day', 105, 'hour', 19, 'sky', 'Clear', 'rain', 0, 'wind', 2, 'temp', 26, 'rh', 70, 'soil', 48);
        end
        for q = 1:6, if ~any(strcmp(SEN(q).key, {'temp', 'rh', 'soil', 'wind'})), st.man.(SEN(q).key) = false; end, end     % sunlight sensors follow the new sky
        h.preset.Value = 1; st.staleDay = true; drawSensorDay(); step();
    end
    function setState(varargin)                   % app.set('hour',12,'sky','Clear','rain',1,'wind',3,'temp',31,'rh',55,'soil',48,'pyr',500,'par',1000,'w',0.5,'day',105)
        for i = 1:2:numel(varargin)
            k = varargin{i}; v = varargin{i + 1};
            switch k
                case 'hour', h.hour.Value = v; case 'day', h.day.Value = v; case 'w', h.w.Value = v; cfg.wEnergy = v; h.wTxt.String = sprintf('%.0f/%.0f', 100 * v, 100 * (1 - v));
                case 'sky', h.sky.Value = find(strcmp(h.sky.String, v));
                case 'rain', st.simRain = logical(v); setRainUi();
                case 'wind', st.man.wind = true; setSensor('wind', v);
                case 'temp', st.man.temp = true; setSensor('temp', v); st.tempC = v;
                case 'rh', st.man.rh = true; setSensor('rh', v);
                case 'soil', st.man.soil = true; st.soilSim = v; setSensor('soil', v);
                case 'tank', st.tank = v;
                case 'smode', st.man.ghi = (v == 2); st.man.par = (v == 2);
                case 'pyr', st.man.ghi = true; setSensor('ghi', v);
                case 'par', st.man.par = true; setSensor('par', v);
            end
        end
        st.staleDay = true; drawSensorDay();
    end
    function setPlay(v), st.play = logical(v); end
    function setRun(v)
        if isempty(tm), return; end
        if v, start(tm); h.run.String = 'STOP live loop'; else, stop(tm); h.run.String = 'START live loop'; end
    end
    function onClose(~, ~)
        try, stop(tm); delete(tm); catch, end
        delete(fig);
    end
    function snapshot(file), drawnow; fr = getframe(fig); imwrite(fr.cdata, file); end
    function d = getLast(), d = lastD; end
    function s2 = getState(), s2 = st; end
    function onTab(newTab)
        if ~st.staleDay || isempty(newTab), return; end
        if newTab == tb{2} || newTab == tb{3}, computeDay(); end
    end

    function step()
        if st.busy, return; end
        st.busy = true; cl = onCleanup(@() setBusy(false)); %#ok<NASGU>
        try, stepInner(); catch err, st.lastMsg = ['step error: ' err.message]; try, h.log.String = ['status: ' st.lastMsg]; catch, end, end
    end
    function setBusy(v), st.busy = v; end
    function stepInner()
        if ~isvalid(fig), return; end
        if st.play, h.hour.Value = h.hour.Value + 0.05; if h.hour.Value >= 19, h.hour.Value = 5; end, end
        hr = h.hour.Value; day = round(h.day.Value); skyName = SKYNAMES{h.sky.Value}; kt = SKYKT(h.sky.Value);
        A = autoVals(hr, day, kt);
        if ~st.man.soil
            if st.pump, st.soilSim = min(100, st.soilSim + 1.2); else, st.soilSim = max(0, st.soilSim - 0.05); end
            if st.simRain, st.soilSim = min(100, st.soilSim + 0.3); end
            A.soil = st.soilSim;
        else, st.soilSim = h.sl.soil.Value; end
        for q = 1:6, k = SEN(q).key; if ~st.man.(k), setSensor(k, A.(k)); end, end
        st.tempC = h.sl.temp.Value; st.rh = h.sl.rh.Value; st.soilPct = h.sl.soil.Value; st.rain = double(st.simRain);
        S = struct('tempC', st.tempC, 'rh', st.rh, 'soilPct', st.soilPct, 'rain', st.rain);
        V = struct('lat', st.lat, 'day', day, 'hour', hr, 'kt', kt, 'windMS', h.sl.wind.Value, 'ghiOverride', h.sl.ghi.Value, 'parOverride', h.sl.par.Value);
        key = round([hr * 20 day kt * 100 S.tempC * 2 S.rh S.soilPct S.rain V.windMS * 2 V.ghiOverride V.parOverride cfg.wEnergy * 100]);
        if isempty(st.lastKey) || ~isequal(key, st.lastKey) || isempty(lastD)       % something changed: one fast decision (about 0.1 s)
            d = review0_controller(S, V, P, F, cfg); st.lastKey = key; st.same = 0; st.curveKey = []; d.gTag = ternary(st.man.ghi || st.man.par, 'SIM-MANUAL', 'SIM'); lastD = d; lastS = S; lastV = V;
        else
            st.same = st.same + 1; d = lastD;
            if st.same >= 3 && isempty(st.curveKey) && ~st.play                      % idle for 3 steps: do the slow check against the best angle once
                c2 = cfg; c2.wantCurve = true; d = review0_controller(S, V, P, F, c2); st.curveKey = key; d.gTag = lastD.gTag; lastD = d;
            end
        end
        [st.pump, st.tank] = review0_irrigation(st.pump, st.soilPct, st.tank, st.rain, cfg);
        mt = st.mppt;
        if d.gpoa > 20 && ~strcmp(d.mode, 'NIGHT PARK')
            for kk = 1:20, [mt.st, mt.P] = mt.M.po(mt.st, mt.pm, d.gpoa, d.tcell); end
            mm = mt.M.mpp(mt.pm, d.gpoa, d.tcell); mt.V = mt.st.V; mt.Pmpp = mm.P; mt.Vmpp = mm.V; mt.sumP = mt.sumP + mt.P; mt.sumM = mt.sumM + mm.P; mt.effRun = 100 * mt.sumP / max(mt.sumM, eps); mt.eff = 100 * mt.P / max(mm.P, eps);
        else, mt.P = 0; mt.Pmpp = 0; mt.eff = NaN; end
        st.mppt = mt;
        st.n = st.n + 1; st.hist = [st.hist; toc(st.t0), st.tempC, st.rh, d.vpd, st.soilPct, st.rain, d.ghi, d.parOpen, d.angle, d.pv, double(st.pump), st.tank, d.crop, V.windMS];
        if size(st.hist, 1) > 300, st.hist(1, :) = []; end
        draw(d, S, V, skyName); drawnow limitrate;
    end

    function draw(d, S, V, skyName)
        % ---- KPI boxes and words ----
        mcol = containers.Map({'OPTIMISED', 'WIND STOW', 'RAIN HARVEST', 'NIGHT PARK', 'FORCED'}, {[0.13 0.55 0.28], [0.80 0.20 0.20], [0.15 0.45 0.85], [0.45 0.45 0.50], [0.4 0.4 0.4]});
        c = mcol(d.mode);
        h.kpiT{1}.String = sprintf('%.1f deg', d.angle); h.kpiT{1}.ForegroundColor = c;
        h.kpiT{2}.String = sprintf('%.0f W/m2', d.pv); gain = d.pvGainVs45; h.kpiT{2}.TooltipString = sprintf('%+.1f %% against a fixed 45 deg panel', gain);
        h.kpiT{3}.String = ternary(d.crop > 0 || d.ghi > 20, sprintf('%.2f', d.crop), '-');
        if isfield(d, 'brute') && d.ghi > 20, h.kpiT{4}.String = sprintf('%.1f %%', 100 - d.brute.gapJpct); elseif d.ghi > 20, h.kpiT{4}.String = '...'; else, h.kpiT{4}.String = '-'; end
        h.mode.String = {['DECISION: ' d.mode], d.reason}; h.mode.ForegroundColor = c;
        words = WD.wrap(WD.now(d, S, V), 72); h.words.String = ['IN SIMPLE WORDS:  ' strjoin(words, ' ')];
        % ---- sensor and array readout ----
        mt = st.mppt; Im = mt.P / max(mt.V, 1);
        L = {sprintf('SENSOR READINGS (simulated, as the real devices report)'), ...
            sprintf('1 SP-110 pyranometer  %7.0f W/m2   -> %5.0f mV', d.ghi, 0.2 * d.ghi), ...
            sprintf('2 SQ-110 PAR sensor    %7.0f umol    -> %5.0f mV', d.parOpen, 0.2 * d.parOpen), ...
            sprintf('3 DHT11 temperature    %7.1f C       (VPD %.2f kPa)', S.tempC, d.vpd), ...
            sprintf('4 DHT11 humidity       %7.0f %%RH', S.rh), ...
            sprintf('5 SEN0193 soil         %7.0f %%       -> %.2f V   valve %s, tank %.0f L', S.soilPct, 2.5 - S.soilPct / 100 * 1.3, ternary(st.pump, 'OPEN', 'closed'), st.tank), ...
            sprintf('6 YL-83 rain plate     %7s', ternary(S.rain, 'WET', 'dry')), ...
            sprintf('7 Adafruit 1733 wind   %7.1f m/s     -> %.2f V', V.windMS, 0.4 + 1.6 * V.windMS / 32.4), ...
            sprintf('PV ARRAY: %d x JKM550M-72HL4-V (550 Wp, 4.4 kWp)', NMOD), ...
            sprintf('  one module at its MPP: %.1f V x %.2f A = %.0f W   (tracking %.1f %%)', mt.V, Im, mt.P, ternary(isnan(mt.eff), 0, mt.eff)), ...
            sprintf('  all %d modules: %.2f kW DC now', NMOD, NMOD * mt.P / 1000), ...
            sprintf('  vs fixed 45 deg: electricity %+.1f %%, crop light %.2f -> %.2f', d.pvGainVs45, d.cropFixed45, d.crop)};
        h.read.String = L; h.read.Value = 1;
        % ---- canopy drawing (only when something visible changed; few graphics objects, so it is fast) ----
        ck = [round(d.angle * 2) round(V.hour * 4) round(V.day) round(V.windMS >= 8) S.rain ~strcmp(skyName, 'Clear') double(d.sunEl > 0) length(d.mode)];
        if ~isequal(ck, st.cKey) || S.rain, st.cKey = ck; drawCanopy(d, S, V, skyName); end
        % ---- "now" markers on the day graphs ----
        mk2 = round([V.hour * 20 d.ghi d.parOpen]);
        if ~isequal(mk2, st.mKey), st.mKey = mk2; updateMarkers(d); end
        h.log.String = ['status: ' st.lastMsg '   |   samples: ' num2str(st.n)];
    end

    function updateMarkers(d)
        hr = h.hour.Value;
        if numel(NOW) ~= 9 || ~all(isvalid(NOW))                      % (re)create the markers after a graph was redrawn
            delete(NOW(isvalid(NOW))); NOW = gobjects(1, 9); axs = [G.a1 G.a2 G.a3(1) G.a3(3)];
            for q = 1:numel(axs), NOW(q) = xline(axs(q), hr, '--', 'Color', [0.3 0.3 0.3], 'LineWidth', 1, 'HandleVisibility', 'off'); end
            yyaxis(G.a1(1), 'left'); hold(G.a1(1), 'on'); NOW(8) = plot(G.a1(1), hr, d.ghi, 'o', 'MarkerFaceColor', AMBER, 'MarkerEdgeColor', 'k', 'MarkerSize', 8, 'HandleVisibility', 'off'); NOW(9) = plot(G.a1(1), hr, d.parOpen / 2, 's', 'MarkerFaceColor', GREEN, 'MarkerEdgeColor', 'k', 'MarkerSize', 7, 'HandleVisibility', 'off');
        else
            for q = 1:7, NOW(q).Value = hr; end
            NOW(8).XData = hr; NOW(8).YData = d.ghi; NOW(9).XData = hr; NOW(9).YData = d.parOpen / 2;
        end
    end

    function initCanopy()
        ax = h.axC; hold(ax, 'on'); axis(ax, 'equal'); ax.XLim = [-9 9]; ax.YLim = [-1.0 12]; ax.XTick = []; ax.YTick = []; ax.Box = 'on';
        rectangle(ax, 'Position', [-9 -1 18 1], 'FaceColor', [0.55 0.33 0.20], 'EdgeColor', 'none');
        zc = [0.45 0.72 0.19; 0.17 0.77 0.77; 0.94 0.69 0.19; 0.75 0.52 0.98];
        for k = -3:3, for z = 1:4, rectangle(ax, 'Position', [k * P.pitch + (z - 1) * P.pitch / 4 - P.pitch / 2, 0, P.pitch / 4, 0.55], 'FaceColor', zc(z, :) * 0.85, 'EdgeColor', 'none'); end, end
        for xx = [-8 8], plot(ax, [xx xx], [0 P.height + 0.7], '-', 'LineWidth', 3, 'Color', [0.45 0.47 0.5]); end
        plot(ax, [-8 8], [P.height + 0.6 P.height + 0.6], '-', 'Color', [0.7 0.72 0.75], 'LineWidth', 1);
    end
    function drawCanopy(d, S, V, skyName)
        ax = h.axC; delete(DYN(isvalid(DYN))); DYN = gobjects(0); ax.Color = skyColor(d, skyName);
        a = deg2rad(d.angle); xs = (-3:3) * P.pitch; dx = P.panelW / 2 * cos(a); dz = P.panelW / 2 * sin(a); nn = nan(size(xs));
        X = [xs - dx; xs + dx; nn]; Zp = [P.height + dz + 0 * xs; P.height - dz + 0 * xs; nn];
        DYN(end + 1) = plot(ax, X(:), Zp(:), '-', 'LineWidth', 5, 'Color', [0.10 0.20 0.55]);
        if d.sunEl > 0
            sx = cosd(d.sunEl) * sind(d.sunAz); sz = sind(d.sunEl); R = 9.5; px = max(-7.5, min(7.5, R * sx / hypot(sx, sz))); py = max(8.2, min(11.3, R * sz / hypot(sx, sz) + 4));
            drawSun(ax, px, py, 0.7, ~strcmp(skyName, 'Overcast'));
            if strcmp(skyName, 'Partly cloudy'), drawCloud(ax, px - 0.9, py - 0.5, 0.9, [0.93 0.93 0.95]); end
            if strcmp(skyName, 'Overcast'), drawCloud(ax, px, py, 1.4, [0.62 0.64 0.68]); drawCloud(ax, px + 1.6, py - 0.3, 1.0, [0.7 0.72 0.76]); end
            if strcmp(skyName, 'Hazy'), drawCloud(ax, px + 1.7, py - 0.7, 0.8, [0.9 0.9 0.88]); end
        else, DYN(end + 1) = text(ax, -8.5, 10.5, 'night', 'Color', 'w', 'FontSize', 12); end
        if S.rain, xr = -8.5 + 17 * rand(1, 30); yr2 = 3 + 7 * rand(1, 30); XR = [xr; xr - 0.25; nan(1, 30)]; YR = [yr2; yr2 - 0.9; nan(1, 30)]; DYN(end + 1) = plot(ax, XR(:), YR(:), '-', 'Color', [0.2 0.45 0.9]); end
        if V.windMS >= 8, x1 = -8.5 + 1.2 * (1:4); y1 = 10.8 - 0.5 * (1:4); XW = [x1; x1 + 2; nan(1, 4)]; YW = [y1; y1; nan(1, 4)]; DYN(end + 1) = plot(ax, XW(:), YW(:), '-', 'Color', [0.95 0.95 0.95], 'LineWidth', 1.5); DYN(end + 1) = text(ax, 4.8, 11.5, sprintf('wind %.0f m/s', V.windMS), 'FontSize', 10, 'FontWeight', 'bold', 'Color', [0.7 0.1 0.1]); end
        DYN(end + 1) = text(ax, -8.8, -0.45, sprintf('panel angle %.1f deg   |   %s', d.angle, d.mode), 'FontWeight', 'bold', 'Color', 'w', 'FontSize', 11);
        DYN(end + 1) = text(ax, -8.8, 11.6, 'Side view: blue bars = solar panels, coloured strip = 4 crop zones', 'FontSize', 9);
        title(ax, sprintf('Live canopy: day %d, solar hour %.1f, %s sky', V.day, V.hour, lower(skyName)), 'FontSize', 11);
    end

    function dm = dayModel(hrs)
        day = round(h.day.Value); kt = SKYKT(h.sky.Value); n = numel(hrs); dm = struct('hrs', hrs, 'ghi', zeros(1, n), 'par', zeros(1, n), 'T', zeros(1, n), 'RH', zeros(1, n), 'soil', zeros(1, n));
        s = ternary(st.man.soil, h.sl.soil.Value, 60);
        for i = 1:n
            hr = hrs(i); sun = F.sunVec(st.lat, day, hr); g = 0; if sun.sz > 0.02, irr = F.irradiance(sun.sz, day, kt); g = irr.ghi; end
            dm.ghi(i) = g; dm.par(i) = g * 0.45 * 4.57;
            dm.T(i) = ternary(st.man.temp, h.sl.temp.Value, 31 + 3 * sin(2 * pi * (hr - 9) / 24)); dm.RH(i) = ternary(st.man.rh, h.sl.rh.Value, 56 - 12 * cos(2 * pi * (hr - 15) / 24));
            if ~st.man.soil && i > 1, s = s - 3.5 * g / 800 * (hrs(i) - hrs(i - 1)); if s < cfg.soilDry, s = s + 18 * (hrs(i) - hrs(i - 1)); end, if st.simRain, s = s + 4 * (hrs(i) - hrs(i - 1)); end, end
            dm.soil(i) = min(100, max(0, s));
        end
    end
    function drawSensorDay()
        hrs = 5:0.25:19; dm = dayModel(hrs); for q = 1:3, clr(G.a1(q)); end
        a = G.a1(1); cla(a); hold(a, 'on'); yyaxis(a, 'left'); plot(a, hrs, dm.ghi, '-', 'Color', AMBER, 'LineWidth', 2); ylabel(a, 'sunlight W/m2'); ylim(a, [0 1250]);
        yyaxis(a, 'right'); plot(a, hrs, dm.par, '-', 'Color', GREEN, 'LineWidth', 2); ylabel(a, 'PAR umol/m2/s'); ylim(a, [0 2500]); a.XLim = [5 19]; legend(a, {'pyranometer', 'PAR'}, 'Location', 'north', 'Box', 'off', 'Orientation', 'horizontal');
        a.YAxis(1).Color = AMBER; a.YAxis(2).Color = GREEN;
        a = G.a1(2); cla(a); hold(a, 'on'); yyaxis(a, 'left'); plot(a, hrs, dm.T, '-', 'Color', [0.85 0.2 0.15], 'LineWidth', 2); ylabel(a, 'temperature C'); ylim(a, [0 50]); yyaxis(a, 'right'); plot(a, hrs, dm.RH, '-', 'Color', [0.15 0.4 0.85], 'LineWidth', 2); ylabel(a, 'humidity %'); ylim(a, [0 100]); a.XLim = [5 19]; a.YAxis(1).Color = [0.85 0.2 0.15]; a.YAxis(2).Color = [0.15 0.4 0.85];
        a = G.a1(3); cla(a); hold(a, 'on'); yyaxis(a, 'left'); if st.simRain, patch(a, [5 19 19 5], [0 0 100 100], [0.6 0.8 1], 'FaceAlpha', 0.35, 'EdgeColor', 'none'); end
        plot(a, hrs, dm.soil, '-', 'Color', GREEN, 'LineWidth', 2); yline(a, cfg.soilDry, ':', 'valve opens below 35 %', 'Color', [0.2 0.2 0.2]); ylabel(a, 'soil water %'); ylim(a, [0 100]); a.XLim = [5 19]; yyaxis(a, 'right'); ylim(a, [0 100]); a.YAxis(2).Visible = 'off';
        st.mKey = []; a = G.a1(4); cla(a); hold(a, 'on'); wv = h.sl.wind.Value; plot(a, [5 19], [wv wv], '-', 'Color', [0.3 0.3 0.4], 'LineWidth', 2); yline(a, cfg.windStow, '--', 'storm limit 15 m/s', 'Color', [0.8 0.15 0.15], 'LineWidth', 1.5); ylabel(a, 'wind m/s'); ylim(a, [0 26]); a.XLim = [5 19];
        text(a, 5.3, wv + 1.6, 'the value you hold (drag the wind slider to change it)', 'FontSize', 8, 'Color', GREY);
    end

    function clr(a)
        yyaxis(a, 'right'); cla(a); yyaxis(a, 'left'); cla(a);
    end
    function computeDay()
        if st.busy, return; end
        wb = []; if ~headless, try, wb = waitbar(0.1, 'Calculating the day graphs (about 10 seconds)...'); catch, end, end
        hrs = 6:1:18; n = numel(hrs); day = round(h.day.Value); kt = SKYKT(h.sky.Value); w = cfg.wEnergy; dm = dayModel(hrs);
        rng(7); Z = max(-2, min(2, randn(n, 5)));                         % one fixed set of random sensor errors: sigma = half of the datasheet +- limit
        R = struct('hrs', hrs, 'angle', nan(1, n), 'angleBest', nan(1, n), 'pv', nan(1, n), 'crop', nan(1, n), 'pv45', nan(1, n), 'crop45', nan(1, n), 'accS', nan(1, n), 'accP', nan(1, n), 'acc45', nan(1, n), 'accT', nan(1, n), 'angleS', nan(1, n), 'mode', {cell(1, n)});
        for i = 1:n
            Sx = struct('tempC', dm.T(i), 'rh', dm.RH(i), 'soilPct', dm.soil(i), 'rain', double(st.simRain)); Vx = struct('lat', st.lat, 'day', day, 'hour', hrs(i), 'kt', kt, 'windMS', h.sl.wind.Value, 'ghiOverride', dm.ghi(i), 'parOverride', dm.par(i));
            c2 = cfg; c2.wantCurve = true; dT = review0_controller(Sx, Vx, P, F, c2); R.mode{i} = dT.mode; R.angle(i) = dT.angle; R.pv(i) = dT.pv; R.crop(i) = dT.crop; R.pv45(i) = dT.pvFixed45; R.crop45(i) = dT.cropFixed45;
            if strcmp(dT.mode, 'OPTIMISED') && isfield(dT, 'curve')
                c = dT.curve; Jf = @(aa) w * interp1(c.angle, c.pv, aa, 'linear', 'extrap') / c.pvMax + (1 - w) * interp1(c.angle, c.crop, aa, 'linear', 'extrap') / c.cropMax; Jb = dT.brute.J;
                Ss = Sx; Vs = Vx; Vs.ghiOverride = dm.ghi(i) * (1 + 0.025 * Z(i, 1)); Vs.parOverride = dm.par(i) * (1 + 0.025 * Z(i, 2)); Ss.tempC = Sx.tempC + 1.0 * Z(i, 3); Ss.rh = min(100, max(0, Sx.rh + 2.5 * Z(i, 4))); Ss.soilPct = min(100, max(0, Sx.soilPct + 1.5 * Z(i, 5)));
                dS = review0_controller(Ss, Vs, P, F, struct('wEnergy', w)); trk = max(15, min(60, dT.strat.angle(3)));
                R.angleBest(i) = dT.brute.angle; R.accS(i) = 100 * Jf(dS.angle) / Jb; R.accP(i) = 100 * dT.brute.chosenJ / Jb; R.acc45(i) = 100 * Jf(45) / Jb; R.accT(i) = 100 * Jf(trk) / Jb;
                R.angleS(i) = dS.angle; R.pv(i) = interp1(c.angle, c.pv, dS.angle, 'linear', 'extrap'); R.crop(i) = interp1(c.angle, c.crop, dS.angle, 'linear', 'extrap');
            else, R.angleS(i) = dT.angle; end
            if ~isempty(wb) && isvalid(wb), try, waitbar(0.1 + 0.85 * i / n, wb); catch, end, end
        end
        st.DA = R; st.staleDay = false; if ~isempty(wb), try, close(wb); catch, end, end
        drawDay(R);
    end
    function drawDay(R)
        hrs = R.hrs; ok = ~isnan(R.accS);
        a = G.a2(1); cla(a); hold(a, 'on'); plot(a, hrs, 45 * ones(size(hrs)), '-', 'Color', [0.6 0.6 0.6], 'LineWidth', 2); plot(a, hrs, R.angleS, '-o', 'Color', [0.1 0.25 0.7], 'LineWidth', 2, 'MarkerFaceColor', [0.1 0.25 0.7]); ylabel(a, 'panel angle (deg)'); ylim(a, [0 95]); a.XLim = [5.5 18.5];
        legend(a, {'fixed 45 deg', 'controller'}, 'Location', 'northeast', 'Box', 'off');
        a = G.a2(2); cla(a); hold(a, 'on'); plot(a, hrs, R.pv45, '-', 'Color', [0.6 0.6 0.6], 'LineWidth', 2); plot(a, hrs, R.pv, '-o', 'Color', AMBER, 'LineWidth', 2, 'MarkerFaceColor', AMBER); ylabel(a, 'W per m2 of panel'); a.XLim = [5.5 18.5]; legend(a, {'fixed 45 deg', 'controller'}, 'Location', 'north', 'Box', 'off');
        a = G.a2(3); cla(a); hold(a, 'on'); plot(a, hrs, R.crop45, '-', 'Color', [0.6 0.6 0.6], 'LineWidth', 2); plot(a, hrs, R.crop, '-o', 'Color', GREEN, 'LineWidth', 2, 'MarkerFaceColor', GREEN); ylabel(a, 'crop-light score'); ylim(a, [0 1.05]); a.XLim = [5.5 18.5]; legend(a, {'fixed 45 deg', 'controller'}, 'Location', 'south', 'Box', 'off');
        st.mKey = []; eg = 100 * (sum(R.pv, 'omitnan') / max(sum(R.pv45, 'omitnan'), eps) - 1); cg = 100 * (sum(R.crop, 'omitnan') / max(sum(R.crop45, 'omitnan'), eps) - 1);
        G.c2(1).String = sprintf('WHAT IT SHOWS: the tilt the controller picks each hour (blue) against a fixed 45 deg panel (grey). It follows the sun, plant stress, rain and wind. Over today the controller makes %+.1f %% electricity and %+.1f %% crop light compared with the fixed panel.', eg, cg);
        a = G.a3(1); cla(a); hold(a, 'on'); plot(a, hrs, R.acc45, '-', 'Color', [0.6 0.6 0.6], 'LineWidth', 1.5); plot(a, hrs, R.accT, '-', 'Color', AMBER, 'LineWidth', 1.5); plot(a, hrs, R.accP, '--', 'Color', GREEN, 'LineWidth', 2); plot(a, hrs, R.accS, '-o', 'Color', [0.1 0.25 0.7], 'LineWidth', 2.2, 'MarkerFaceColor', [0.1 0.25 0.7]);
        ylabel(a, 'accuracy %'); a.XLim = [5.5 18.5]; ylim(a, [min(70, floor(min([R.acc45 R.accT R.accS], [], 'omitnan')) - 2) 101]); legend(a, {'fixed 45 deg', 'sun tracking', 'controller, perfect sensors', 'controller, real sensor errors'}, 'Location', 'southwest', 'Box', 'off', 'FontSize', 7);
        m = [mean(R.acc45(ok)) mean(R.accT(ok)) mean(R.accP(ok)) mean(R.accS(ok))]; lbl = {'fixed 45', 'tracking', 'ctrl perfect', 'ctrl real'};
        a = G.a3(2); cla(a); b = bar(a, categorical(lbl, lbl), m, 0.6); b.FaceColor = 'flat'; b.CData = [0.6 0.6 0.6; AMBER; GREEN; 0.1 0.25 0.7]; ylim(a, [min(m) - 8, 101]); ylabel(a, 'average accuracy %'); for q = 1:4, text(a, q, m(q) + 0.6, sprintf('%.1f %%', m(q)), 'HorizontalAlignment', 'center', 'FontWeight', 'bold'); end
        a = G.a3(3); cla(a); hold(a, 'on'); dg = R.angleS - R.angleBest; bar(a, hrs, abs(dg), 0.6, 'FaceColor', [0.1 0.25 0.7]); ylabel(a, 'degrees off the best'); a.XLim = [5.5 18.5];
        G.c3(1).String = 'ACCURACY = how close the angle is to the best possible angle on the combined score (half electricity, half crop light). 100 % = the best of every angle from 15 to 60 deg. Blue includes datasheet-sized sensor errors (sunlight +-5 %, DHT11 +-2 C, +-5 %RH, soil +-3 %). Rain, storm and night hours use the safety rules and are left out.';
        G.c3(2).String = sprintf('DAY AVERAGE: with real sensor errors the controller reaches %.1f %% of the best possible score, against %.1f %% for a fixed 45 deg panel and %.1f %% for plain sun tracking. This is the main result: choosing the angle from sensors.', m(4), m(1), m(2));
        G.c3(3).String = sprintf('Degrees between the chosen angle and the best angle each hour (smaller is better). Largest miss today %.1f deg, average %.1f deg. Measured in simulation against the controller''s own goal, not against real crop yield.', max(abs(dg(ok))), mean(abs(dg(ok))));
    end

    function buildProofTab(par)
        T(par, [0.02 0.955 0.96 0.04], 'THE SIX SENSORS: real devices that this simulation is modelled on (datasheet numbers)', 'FontWeight', 'bold', 'FontSize', 10, 'ForegroundColor', GREEN);
        D = {'1', 'Sunlight', 'Apogee SP-110 pyranometer', '0-2000 W/m2', '+-5 %', '0.20 mV per W/m2'; ...
             '2', 'Plant light', 'Apogee SQ-110 PAR sensor', '0-4000 umol/m2/s', '+-5 %', '0.20 mV per umol'; ...
             '3', 'Air temp.', 'DHT11', '0-50 deg C', '+-2 deg C', 'digital'; ...
             '4', 'Humidity', 'DHT11 (same chip)', '20-90 % RH', '+-5 % RH', 'digital'; ...
             '5', 'Soil water', 'DFRobot SEN0193 v1.2', '2.5 V dry-1.2 V wet', 'calibrate dry/wet', 'analog 1.2-2.5 V'; ...
             '6', 'Rain', 'YL-83 / FC-37 + LM393', 'wet or dry', 'trimmer threshold', 'digital LOW = wet'; ...
             '7', 'Wind', 'Adafruit 1733 anemometer', '0.5-32.4 m/s', '+-1 m/s worst', 'analog 0.4-2.0 V'};
        uitable(par, 'Units', 'normalized', 'Position', [0.02 0.62 0.96 0.33], 'Data', D, 'ColumnName', {'#', 'Role', 'Real device', 'Range', 'Accuracy', 'Signal'}, 'RowName', [], 'FontSize', 9, 'ColumnWidth', {20, 70, 150, 105, 95, 100}, 'ColumnEditable', false);
        T(par, [0.02 0.575 0.96 0.04], 'THE SOLAR PANELS: 8 modules of one real type (datasheet numbers)', 'FontWeight', 'bold', 'FontSize', 10, 'ForegroundColor', GREEN);
        M = {'Model', 'JinkoSolar Tiger Pro JKM550M-72HL4-V'; 'Type', 'monocrystalline silicon'; 'Number of panels', '8  (2 rows x 4, landscape) = 4.4 kWp'; 'Size / weight', '2274 x 1134 x 35 mm / 28.9 kg'; ...
             'Pmax (test conditions)', '550 Wp'; 'Vmp / Imp', '40.90 V / 13.45 A'; 'Voc / Isc', '49.62 V / 14.03 A'; 'Efficiency', '21.33 %'; 'Tilt used here', '15-60 deg, rain 3 deg, storm 90 deg'};
        uitable(par, 'Units', 'normalized', 'Position', [0.02 0.22 0.96 0.35], 'Data', M, 'ColumnName', {'Item', 'Value'}, 'RowName', [], 'FontSize', 9, 'ColumnWidth', {140, 380});
        uicontrol(par, 'Style', 'text', 'Units', 'normalized', 'Position', [0.02 0.01 0.96 0.2], 'BackgroundColor', [1 1 0.93], 'ForegroundColor', INK, 'FontSize', 9, 'HorizontalAlignment', 'left', 'String', ...
            ['PROOF: every number above, its source link and the way each sensor is simulated is in documents/SENSOR_AND_PANEL_PROOF.md (and Proof/10_Review0_Sensors_and_Panels). ' ...
             'HONEST NOTE: the sensors here are software models of these real devices. The readings are generated or typed by you, not measured. Panel values are the manufacturer''s test-condition values; the temperature coefficients in the MPPT model are typical, not from this datasheet.']);
    end

    function runTrust()
        try
            if isempty(lastD), step(); end
            f = fullfile(logDir, ['trust_' datestr(now, 'yyyymmdd_HHMMSS') '.png']);
            o = review0_sensor_trust(lastS, lastV, P, F, cfg, 'Plot', true, 'File', f, 'Visible', ~headless);
            st.lastMsg = sprintf('SENSOR ERROR TEST: +-10 %% sensor error -> energy loss <= %.1f %%, crop loss <= %.1f %%; +-20 %% -> %.1f %% / %.1f %%', o.maxLoss10(1), o.maxLoss10(2), o.maxLoss20(1), o.maxLoss20(2));
        catch err, st.lastMsg = ['trust test error: ' err.message]; end
        try, h.log.String = ['status: ' st.lastMsg]; catch, end
    end
    function openExplain()
        try
            if isempty(lastS), step(); end
            c2 = cfg; c2.wantCurve = true; dd = review0_controller(lastS, lastV, P, F, c2); dd.gTag = lastD.gTag;
            mp = struct('pm', st.mppt.pm, 'M', st.mppt.M, 'V', st.mppt.V, 'P', st.mppt.P, 'effRun', st.mppt.effRun);
            st.exFig = review0_explain(st.exFig, dd, lastS, lastV, P, F, cfg, mp, 'Visible', ~headless);
        catch err, st.lastMsg = ['explain window error: ' err.message]; end
    end
    function saveEvidence()
        stamp = datestr(now, 'yyyymmdd_HHMMSS'); f1 = fullfile(logDir, ['dashboard_' stamp '.png']); f2 = fullfile(logDir, ['sensors_' stamp '.csv']);
        exportgraphics(fig, f1, 'Resolution', 130);
        Tb = array2table(st.hist, 'VariableNames', {'t_s', 'tempC', 'rh', 'vpd_kPa', 'soilPct', 'rain', 'ghi_sim', 'par_sim', 'angle_deg', 'pv_Wm2', 'pump', 'tank_L', 'cropScore', 'wind_sim'}); writetable(Tb, f2);
        st.lastMsg = ['saved ' f1];
    end

    function c = skyColor(d, skyName)
        if d.sunEl <= 0, c = [0.07 0.09 0.2]; return; end
        switch skyName, case 'Clear', c = [0.55 0.78 0.98]; case 'Hazy', c = [0.72 0.82 0.9]; case 'Partly cloudy', c = [0.62 0.8 0.95]; otherwise, c = [0.66 0.7 0.75]; end
    end
    function drawSun(ax, x, y, r, bright)
        col = ternary(bright, [1 0.82 0.1], [0.95 0.85 0.5]); an = (0:7) * pi / 4;
        XR = [x + 1.25 * r * cos(an); x + 1.9 * r * cos(an); nan(1, 8)]; YR = [y + 1.25 * r * sin(an); y + 1.9 * r * sin(an); nan(1, 8)];
        DYN(end + 1) = plot(ax, XR(:), YR(:), '-', 'Color', col, 'LineWidth', 2);
        DYN(end + 1) = rectangle(ax, 'Position', [x - r y - r 2 * r 2 * r], 'Curvature', [1 1], 'FaceColor', col, 'EdgeColor', [0.9 0.6 0]);
    end
    function drawCloud(ax, x, y, s, col)
        for q = [-0.7 0 0.7 0.35 -0.35], DYN(end + 1) = rectangle(ax, 'Position', [x + q * s - 0.55 * s, y + 0.1 * abs(q) * s - 0.35 * s, 1.1 * s, 0.8 * s], 'Curvature', [1 1], 'FaceColor', col, 'EdgeColor', 'none'); end
    end
end

function v = ternary(c, a, b), if c, v = a; else, v = b; end, end
