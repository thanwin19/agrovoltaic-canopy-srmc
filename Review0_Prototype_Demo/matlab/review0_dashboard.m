function app = review0_dashboard(varargin)
%REVIEW0_DASHBOARD  Live dashboard for Review 0: ESP8266/ESP32 sensors + virtual pyranometer/PAR -> SRMC-DT tilt decision.
%
%   review0_dashboard                       open the window (source = Simulate; choose Serial and the COM port to use the real board)
%   app = review0_dashboard('Headless',true)    no window timer: used for screenshots and tests
%
%   REAL sensors (from the ESP, labelled REAL):   DHT11 temperature + humidity, soil moisture, rain
%   VIRTUAL sensors (software, labelled SIM):     pyranometer (W/m2), PAR above and under the canopy, wind.  Set with the sliders and the sky icon.
%   Decision (review0_controller): wind stow > rain 3 deg > night park > optimise energy + crop light.   Tilt is shown on the drawing only.
p = inputParser; addParameter(p, 'Headless', false); addParameter(p, 'Visible', true); parse(p, varargin{:}); headless = p.Results.Headless;
F = review0_physics(); P = F.designParams();
root = fileparts(fileparts(fileparts(mfilename('fullpath')))); if ~exist(fullfile(root, 'Review0_Prototype_Demo'), 'dir'), root = fileparts(fileparts(mfilename('fullpath'))); end
logDir = fullfile(fileparts(fileparts(mfilename('fullpath'))), 'results', 'live_logs'); if ~exist(logDir, 'dir'), mkdir(logDir); end

% ---------------- state ----------------
st = struct('src', 'Simulate', 'sp', [], 'tempC', 30, 'rh', 55, 'soilRaw', 700, 'rain', 0, 'okT', false, ...
    'cal', struct('dry', 1000, 'wet', 420), 'soilSim', 48, 'tank', 120, 'pump', false, 'simRain', false, 'rainOv', false, 'play', false, ...
    'hist', zeros(0, 14), 'n', 0, 't0', tic, 'lastRawSoil', 700, 'lat', 9.88, 'sky', 'Clear', 'lastMsg', '', 'realGhi', NaN, 'realPar', NaN, 'nLines', 0, 'tLast', NaN, 'exFig', [], 'mppt', []);
SKYNAMES = {'Clear', 'Hazy', 'Partly cloudy', 'Overcast'}; SKYKT = [0.62 0.50 0.36 0.18];      % clearness index of each sky (ratio of ground to top-of-atmosphere radiation)
cfg = struct('wEnergy', 0.5, 'windStow', 15, 'vpdHigh', 2.5, 'soilDry', 35, 'soilWet', 55);

% ---------------- figure and controls ----------------
fig = figure('Name', 'SRMC Review 0 dashboard', 'NumberTitle', 'off', 'Color', [0.97 0.97 0.96], 'Position', [20 20 1400 780], 'Visible', ternary(p.Results.Visible, 'on', 'off'), 'MenuBar', 'none', 'ToolBar', 'none');
U = @(pos, style, str, cb, varargin) uicontrol(fig, 'Style', style, 'Units', 'normalized', 'Position', pos, 'String', str, 'Callback', cb, 'BackgroundColor', [0.97 0.97 0.96], 'HorizontalAlignment', 'left', 'FontSize', 10, varargin{:});
try, theme(fig, 'light'); catch, end
x0 = 0.008; w = 0.185;
U([x0 0.965 w 0.03], 'text', 'SRMC Review 0  -  control panel', [], 'FontWeight', 'bold');
h.src = U([x0 0.925 w 0.035], 'popupmenu', {'Simulate', 'Serial (ESP)'}, @onSource);
h.board = U([x0 0.89 w 0.035], 'popupmenu', {'ESP8266 NodeMCU (10-bit)', 'ESP32 (12-bit)'}, @onBoard);
ports = serialportlist('available'); if isempty(ports), ports = {'(no port found)'}; end
h.port = U([x0 0.855 0.12 0.035], 'popupmenu', cellstr(ports), []);
h.conn = U([x0 + 0.125 0.857 0.06 0.033], 'pushbutton', 'Connect', @onConnect);
U([x0 0.82 0.07 0.03], 'text', 'baud', []); h.baud = U([x0 + 0.07 0.825 0.08 0.03], 'edit', '115200', []);
U([x0 0.785 w 0.03], 'text', 'VIRTUAL sensors (simulated)', [], 'FontWeight', 'bold');
U([x0 0.757 0.07 0.03], 'text', 'day of year', []); h.day = uicontrol(fig, 'Style', 'slider', 'Units', 'normalized', 'Position', [x0 + 0.075 0.762 0.11 0.022], 'Min', 1, 'Max', 365, 'Value', 105, 'Callback', @(~, ~) step());
U([x0 0.729 0.07 0.03], 'text', 'solar hour', []); h.hour = uicontrol(fig, 'Style', 'slider', 'Units', 'normalized', 'Position', [x0 + 0.075 0.734 0.11 0.022], 'Min', 5, 'Max', 19, 'Value', 12, 'Callback', @(~, ~) step());
U([x0 0.701 0.07 0.03], 'text', 'sky', []); h.sky = U([x0 + 0.075 0.703 0.11 0.03], 'popupmenu', SKYNAMES, @(~, ~) step());
U([x0 0.673 0.07 0.03], 'text', 'wind m/s', []); h.wind = uicontrol(fig, 'Style', 'slider', 'Units', 'normalized', 'Position', [x0 + 0.075 0.678 0.11 0.022], 'Min', 0, 'Max', 25, 'Value', 3, 'Callback', @(~, ~) step());
h.smode = U([x0 0.637 w 0.032], 'popupmenu', {'Sensors from sun + sky model', 'MANUAL: use the two scroll bars'}, @onSensorMode);
h.pyrLbl = U([x0 0.607 w 0.028], 'text', '', [], 'FontWeight', 'bold');
h.pyr = uicontrol(fig, 'Style', 'slider', 'Units', 'normalized', 'Position', [x0 0.588 w 0.02], 'Min', 0, 'Max', 1200, 'Value', 800, 'Enable', 'off', 'Callback', @(~, ~) step());
h.parLbl = U([x0 0.558 w 0.028], 'text', '', [], 'FontWeight', 'bold');
h.par = uicontrol(fig, 'Style', 'slider', 'Units', 'normalized', 'Position', [x0 0.539 w 0.02], 'Min', 0, 'Max', 2400, 'Value', 1650, 'Enable', 'off', 'Callback', @(~, ~) step());
h.play = uicontrol(fig, 'Style', 'checkbox', 'Units', 'normalized', 'Position', [x0 0.505 w 0.03], 'String', 'play the day (hour advances)', 'BackgroundColor', [0.97 0.97 0.96], 'Callback', @(s, ~) setPlay(s.Value));
U([x0 0.472 w 0.03], 'text', 'REAL sensors', [], 'FontWeight', 'bold');
h.rainOv = uicontrol(fig, 'Style', 'togglebutton', 'Units', 'normalized', 'Position', [0.985 0.004 0.012 0.02], 'String', '.', 'BackgroundColor', [0.94 0.94 0.94], 'ForegroundColor', [0.8 0.8 0.8], 'Callback', @(s, ~) setRainOv(s.Value));   % small backup switch: forces rain = wet even when serial data is live (shown as SIM in the text panel)
h.rain = U([x0 0.437 w 0.035], 'togglebutton', 'Simulate rain (when Simulate)', @(s, ~) setSimRain(s.Value));
U([x0 0.403 w 0.03], 'text', 'soil calibration (raw ADC)', []);
h.capDry = U([x0 0.368 0.09 0.033], 'pushbutton', 'Capture DRY', @(~, ~) capture('dry')); h.capWet = U([x0 + 0.095 0.368 0.09 0.033], 'pushbutton', 'Capture WET', @(~, ~) capture('wet'));
h.calTxt = U([x0 0.337 w 0.03], 'text', '', []);
U([x0 0.305 w 0.03], 'text', 'controller weight: energy share', []); h.w = uicontrol(fig, 'Style', 'slider', 'Units', 'normalized', 'Position', [x0 0.283 w 0.022], 'Min', 0, 'Max', 1, 'Value', 0.5, 'Callback', @(~, ~) step());
h.wTxt = U([x0 0.253 w 0.03], 'text', '', []);
h.expl = U([x0 0.205 w 0.04], 'pushbutton', 'Explain + accuracy window', @(~, ~) openExplain());
h.trust = U([x0 0.162 w 0.04], 'pushbutton', 'Sensor trust test (+-5 to 20 %)', @(~, ~) runTrust());
h.save = U([x0 0.119 w 0.04], 'pushbutton', 'Save evidence (PNG + CSV)', @(~, ~) saveEvidence());
h.run = U([x0 0.076 w 0.04], 'togglebutton', 'START live loop', @(s, ~) setRun(s.Value));
h.note = uicontrol(fig, 'Style', 'text', 'Units', 'normalized', 'Position', [x0 0.002 w 0.07], 'String', {'SIM = simulated or scroll bar.', 'REAL = from the ESP over USB.', 'DEMO = generated for rehearsal.'}, 'BackgroundColor', [0.97 0.97 0.96], 'ForegroundColor', [0.6 0.1 0.1], 'HorizontalAlignment', 'left', 'FontSize', 9);

h.axC = axes(fig, 'Position', [0.215 0.49 0.40 0.46]); h.axT = axes(fig, 'Position', [0.64 0.79 0.345 0.17]); h.axS = axes(fig, 'Position', [0.64 0.565 0.345 0.17]); h.axR = axes(fig, 'Position', [0.64 0.34 0.345 0.17]); h.axA = axes(fig, 'Position', [0.64 0.115 0.345 0.17]);
h.txt = uicontrol(fig, 'Style', 'listbox', 'Units', 'normalized', 'Position', [0.215 0.03 0.40 0.40], 'FontName', 'Consolas', 'FontSize', 10, 'BackgroundColor', 'white', 'Max', 1);
h.log = uicontrol(fig, 'Style', 'text', 'Units', 'normalized', 'Position', [0.64 0.01 0.345 0.07], 'String', '', 'BackgroundColor', [0.97 0.97 0.96], 'HorizontalAlignment', 'left', 'FontSize', 9);
tm = [];
if ~headless
    tm = timer('ExecutionMode', 'fixedSpacing', 'Period', 1, 'TimerFcn', @(~, ~) step(), 'BusyMode', 'drop');
    fig.CloseRequestFcn = @onClose;
end
lastD = []; lastS = []; lastV = [];
MP = review0_mppt(); pmP = MP.params(); st.mppt = struct('M', MP, 'pm', pmP, 'st', MP.init(pmP, 30), 'V', 30, 'P', 0, 'Pmpp', 0, 'Vmpp', 0, 'sumP', 0, 'sumM', 0, 'effRun', 100, 'eff', 100);
WD = review0_words();
updateCalText(); step();

% ---------------- API for headless use ----------------
app = struct('fig', fig, 'step', @step, 'set', @setState, 'snapshot', @snapshot, 'state', @getState, 'last', @getLast, 'trust', @runTrust, 'explain', @openExplain, 'close', @() delete(fig));

% ================= callbacks and helpers =================
    function onSource(s, ~), st.src = s.String{s.Value}; if contains(st.src, 'Serial'), st.src = 'Serial'; else, st.src = 'Simulate'; end, end
    function onBoard(s, ~), if s.Value == 1, st.cal.dry = 1000; st.cal.wet = 420; else, st.cal.dry = 3200; st.cal.wet = 1300; end, updateCalText(); end
    function onConnect(~, ~)
        try
            if ~isempty(st.sp), delete(st.sp); st.sp = []; h.conn.String = 'Connect'; return; end
            pl = serialportlist('available'); if ~isempty(pl), cur = h.port.String{h.port.Value}; h.port.String = cellstr(pl); k = find(strcmp(h.port.String, cur), 1); h.port.Value = ternary(isempty(k), 1, k); end
            prt = h.port.String{h.port.Value}; st.sp = serialport(prt, str2double(h.baud.String)); st.sp.Timeout = 2; configureTerminator(st.sp, 'LF'); flush(st.sp);
            h.conn.String = 'Disconnect'; h.src.Value = 2; st.src = 'Serial'; st.lastMsg = ['connected ' prt];
        catch err
            st.lastMsg = ['serial error: ' err.message]; st.sp = [];
        end
    end
    function onSensorMode(~, ~)
        man = h.smode.Value == 2;
        if man && ~isempty(lastD), h.pyr.Value = min(1200, max(0, lastD.ghi)); h.par.Value = min(2400, max(0, lastD.parOpen)); end     % start from the current model values
        h.pyr.Enable = ternary(man, 'on', 'off'); h.par.Enable = ternary(man, 'on', 'off'); step();
    end
    function runTrust()
        try
            if isempty(lastD), step(); end
            f = fullfile(logDir, ['trust_' datestr(now, 'yyyymmdd_HHMMSS') '.png']);
            o = review0_sensor_trust(lastS, lastV, P, F, cfg, 'Plot', true, 'File', f, 'Visible', ~headless); st.trust = o;
            st.lastMsg = sprintf('TRUST TEST: sensor error +-10 %% -> energy loss <= %.1f %%, crop loss <= %.1f %%, angle moves <= %.1f deg; +-20 %% -> %.1f %% / %.1f %% / %.1f deg', o.maxLoss10(1), o.maxLoss10(2), o.maxShift10, o.maxLoss20(1), o.maxLoss20(2), o.maxShift20);
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
    function setPlay(v), st.play = logical(v); end
    function setSimRain(v), st.simRain = logical(v); end
    function setRainOv(v), st.rainOv = logical(v); end
    function setRun(v)
        if isempty(tm), return; end
        if v, start(tm); h.run.String = 'STOP live loop'; else, stop(tm); h.run.String = 'START live loop'; end
    end
    function capture(which)
        st.cal.(which) = st.lastRawSoil; updateCalText(); st.lastMsg = sprintf('captured %s = %d', upper(which), round(st.lastRawSoil));
    end
    function updateCalText(), h.calTxt.String = sprintf('dry raw = %d    wet raw = %d', round(st.cal.dry), round(st.cal.wet)); end
    function onClose(~, ~)
        try, stop(tm); delete(tm); catch, end
        try, if ~isempty(st.sp), delete(st.sp); end, catch, end
        delete(fig);
    end
    function setState(varargin)             % app.set('hour',12,'sky','Clear','rain',1,'wind',3,'temp',31,'rh',55,'soil',48,'w',0.5,'day',105)
        for i = 1:2:numel(varargin)
            k = varargin{i}; v = varargin{i + 1};
            switch k
                case 'hour', h.hour.Value = v; case 'day', h.day.Value = v; case 'wind', h.wind.Value = v; case 'w', h.w.Value = v;
                case 'sky', h.sky.Value = find(strcmp(h.sky.String, v)); case 'rain', st.simRain = logical(v); h.rain.Value = logical(v);
                case 'temp', st.tempC = v; st.fixT = true; case 'rh', st.rh = v; st.fixRH = true; case 'soil', st.soilSim = v; st.fixSoil = true; case 'tank', st.tank = v; case 'smode', h.smode.Value = v; onSensorMode(); case 'pyr', h.pyr.Value = v; case 'par', h.par.Value = v;
            end
        end
    end
    function snapshot(file), drawnow; fr = getframe(fig); imwrite(fr.cdata, file); end
    function d = getLast(), d = lastD; end
    function s2 = getState(), s2 = st; end

    function readSensors()
        if strcmp(st.src, 'Serial') && ~isempty(st.sp)
            try
                while st.sp.NumBytesAvailable > 0
                    r = review0_parse(readline(st.sp)); if ~r.ok, continue; end
                    if r.tempOk, st.tempC = r.tempC; st.rh = r.rh; st.okT = true; else, st.okT = false; end
                    st.lastRawSoil = r.soilRaw; st.rain = r.rain; st.soilRaw = r.soilRaw; st.realGhi = r.ghi; st.realPar = r.par; st.nLines = st.nLines + 1; st.tLast = toc(st.t0);     % a real pyranometer/PAR sensor adds two optional fields
                end
            catch err, st.lastMsg = ['read error: ' err.message]; end
            if st.rainOv, st.rain = 1; end
            st.soilPct = min(100, max(0, 100 * (st.cal.dry - st.soilRaw) / (st.cal.dry - st.cal.wet)));
        else                                                         % Simulate: slow drift + manual rain
            if ~isfield(st, 'fixT') || ~st.fixT, st.tempC = 31 + 3 * sin(2 * pi * (h.hour.Value - 9) / 24) + 0.15 * randn; end
            if ~isfield(st, 'fixRH') || ~st.fixRH, st.rh = 56 - 12 * cos(2 * pi * (h.hour.Value - 15) / 24) + 0.4 * randn; end
            st.rain = double(st.simRain);
            if st.pump, st.soilSim = min(100, st.soilSim + 1.2); else, st.soilSim = max(0, st.soilSim - 0.05); end
            if st.rain, st.soilSim = min(100, st.soilSim + 0.3); end
            st.soilPct = st.soilSim; st.soilRaw = st.cal.dry - st.soilPct / 100 * (st.cal.dry - st.cal.wet); st.lastRawSoil = st.soilRaw; st.okT = true;
        end
    end

    function step()
        try, stepInner(); catch err, st.lastMsg = ['step error: ' err.message]; try, h.log.String = ['status: ' st.lastMsg]; catch, end, end
    end
    function stepInner()
        if ~isvalid(fig), return; end
        if st.play, h.hour.Value = h.hour.Value + 0.05; if h.hour.Value >= 19, h.hour.Value = 5; end, end
        readSensors();
        skyName = SKYNAMES{h.sky.Value}; kt = SKYKT(h.sky.Value);
        S = struct('tempC', st.tempC, 'rh', st.rh, 'soilPct', st.soilPct, 'rain', st.rain);
        V = struct('lat', st.lat, 'day', round(h.day.Value), 'hour', h.hour.Value, 'kt', kt, 'windMS', h.wind.Value, 'ghiOverride', NaN, 'parOverride', NaN);
        man = h.smode.Value == 2; realOn = ~isnan(st.realGhi) && strcmp(st.src, 'Serial'); gTag = 'SIM';
        if realOn, V.ghiOverride = st.realGhi; V.parOverride = st.realPar; gTag = 'REAL';        % real sensors on the serial line win
        elseif man, V.ghiOverride = h.pyr.Value; V.parOverride = h.par.Value; gTag = 'SIM-MANUAL'; end
        cfg.wEnergy = h.w.Value; h.wTxt.String = sprintf('energy %.0f %%  /  crop %.0f %%', 100 * cfg.wEnergy, 100 * (1 - cfg.wEnergy));
        d = review0_controller(S, V, P, F, cfg); lastD = d; lastS = S; lastV = V; d.gTag = gTag; lastD = d;
        if ~man && ~realOn, h.pyr.Value = min(1200, max(0, d.ghi)); h.par.Value = min(2400, max(0, d.parOpen)); end
        h.pyrLbl.String = sprintf('pyranometer %.0f W/m2  [%s]', d.ghi, gTag); h.parLbl.String = sprintf('PAR %.0f umol/m2/s  [%s]', d.parOpen, gTag);
        % irrigation with hysteresis from the harvested water
        [st.pump, st.tank] = review0_irrigation(st.pump, st.soilPct, st.tank, st.rain, cfg);
        mt = st.mppt;                                                          % MPPT: 20 perturb-and-observe steps per update, judged against the true maximum
        if d.gpoa > 20 && ~strcmp(d.mode, 'NIGHT PARK')
            for kk = 1:20, [mt.st, mt.P] = mt.M.po(mt.st, mt.pm, d.gpoa, d.tcell); end
            mm = mt.M.mpp(mt.pm, d.gpoa, d.tcell); mt.V = mt.st.V; mt.Pmpp = mm.P; mt.Vmpp = mm.V; mt.sumP = mt.sumP + mt.P; mt.sumM = mt.sumM + mm.P; mt.effRun = 100 * mt.sumP / max(mt.sumM, eps); mt.eff = 100 * mt.P / max(mm.P, eps);
        else, mt.P = 0; mt.Pmpp = 0; mt.eff = NaN; end
        st.mppt = mt;
        st.n = st.n + 1; hr = [toc(st.t0), st.tempC, st.rh, d.vpd, st.soilPct, st.rain, d.ghi, d.parOpen, d.angle, d.pv, double(st.pump), st.tank, d.crop, h.wind.Value];
        st.hist = [st.hist; hr]; if size(st.hist, 1) > 300, st.hist(1, :) = []; end
        draw(d, S, V, skyName); drawnow limitrate;
        if ~headless && ~isempty(st.exFig) && isvalid(st.exFig) && mod(st.n, 4) == 0, openExplain(); end
    end

    function draw(d, S, V, skyName)
        % ---- text panel ----
        tag = @(b) ternary(b, 'ok', 'READ FAILED');
        rT = ternary(strcmp(st.src, 'Serial') && ~isempty(st.sp), 'REAL', 'DEMO');
        if rT(1) == 'R', espL = sprintf('ESP LIVE: receiving real sensor lines over USB (%d lines so far, last %.1f s ago)', st.nLines, toc(st.t0) - st.tLast); else, espL = 'ESP not connected: values below are DEMO (generated)'; end
        words = WD.wrap(['IN SIMPLE WORDS: ' WD.now(d, S, V)], 74);
        L = [{espL, ''}, words, {'', sprintf('== DECISION ==  %s  ->  panel angle %.1f deg', d.mode, d.angle), ['   ' d.reason], '', ...
            sprintf('%-6s DHT11   : %.1f C   RH %.0f %%   (%s)', rT, S.tempC, S.rh, tag(st.okT)), ...
            sprintf('%-6s soil    : raw %d  ->  %.0f %% moisture   pump %s   cistern %.0f L', rT, round(st.soilRaw), S.soilPct, ternary(st.pump, 'ON', 'off'), st.tank), ...
            sprintf('%-6s rain    : %s', ternary(st.rainOv, 'SIM', rT), ternary(S.rain, ['WET  (harvest mode)' ternary(st.rainOv, '  [manual override]', '')], 'dry')), ...
            sprintf('%-6s pyranometer GHI %.0f W/m2   (sky: %s, sun el %.1f deg, az %.0f deg)', d.gTag, d.ghi, skyName, d.sunEl, d.sunAz), ...
            sprintf('%-6s PAR above canopy %.0f umol/m2/s     under canopy by zone: %s', d.gTag, d.parOpen, sprintf('%.0f ', d.parZone)), ...
            sprintf('       light share (LSR) by zone: %s %%   crop-light score %.2f', sprintf('%.0f ', 100 * d.lsr), d.crop), ...
            sprintf('SIM    wind %.1f m/s  (stow at >= %.0f m/s)', V.windMS, cfg.windStow), ...
            sprintf('TRUST  PAR/GHI = %.2f umol/J (expected 2.06): %s%s', d.parPerJ, ternary(d.plausible, 'the two sensors agree', 'CHECK SENSORS - they disagree'), ternary(d.ghiClamped, '; pyranometer ABOVE the clear-sky limit', '')), ...
            '       SIM sensor accuracy: GHI model +-5 % (vs PVGIS), PAR = 45-50 % of GHI; press Sensor trust test', ...
            sprintf('CALC   VPD %.2f kPa   stress index %.2f (air %.2f, soil %.2f)', d.vpd, d.stress, d.stressAir, d.stressSoil), ...
            sprintf('MPPT   module %.1f V -> %.0f W (true maximum %.0f W at %.1f V): tracking %.1f %%, average %.1f %%', st.mppt.V, st.mppt.P, st.mppt.Pmpp, st.mppt.Vmpp, st.mppt.eff, st.mppt.effRun), ...
            '', sprintf('PV power at this angle   : %.0f W/m2 of panel', d.pv), ...
            sprintf('PV power if fixed at 45  : %.0f W/m2   (controller %+.1f %%)', d.pvFixed45, d.pvGainVs45), ...
            sprintf('crop score fixed 45 deg  : %.2f   (controller %.2f)', d.cropFixed45, d.crop)}];
        h.txt.String = L; h.txt.Value = 1;
        % ---- canopy drawing ----
        ax = h.axC; cla(ax); hold(ax, 'on'); axis(ax, 'equal'); ax.XLim = [-9 9]; ax.YLim = [-1.0 12]; ax.XTick = []; ax.YTick = []; ax.Box = 'on'; ax.Color = skyColor(d, skyName);
        rectangle(ax, 'Position', [-9 -1 18 1], 'FaceColor', [0.55 0.33 0.20], 'EdgeColor', 'none');
        zc = [0.45 0.72 0.19; 0.17 0.77 0.77; 0.94 0.69 0.19; 0.75 0.52 0.98];
        for k = -3:3, for z = 1:4, rectangle(ax, 'Position', [k * P.pitch + (z - 1) * P.pitch / 4 - P.pitch / 2, 0, P.pitch / 4, 0.55], 'FaceColor', zc(z, :) * 0.85, 'EdgeColor', 'none'); end, end
        a = deg2rad(d.angle);
        for k = -3:3
            xc = k * P.pitch; dx = P.panelW / 2 * cos(a); dz = P.panelW / 2 * sin(a);
            plot(ax, [xc - dx xc + dx], [P.height + dz P.height - dz], '-', 'LineWidth', 5, 'Color', [0.10 0.20 0.55]);
        end
        for xx = [-8 8], plot(ax, [xx xx], [0 P.height + 0.7], '-', 'LineWidth', 3, 'Color', [0.45 0.47 0.5]); end
        plot(ax, [-8 8], [P.height + 0.6 P.height + 0.6], '-', 'Color', [0.7 0.72 0.75], 'LineWidth', 1);
        % sun and sky icons placed by sun position in the east-west plane
        if d.sunEl > 0
            sx = cosd(d.sunEl) * sind(d.sunAz); sz = sind(d.sunEl); R = 9.5; px = max(-7.5, min(7.5, R * sx / hypot(sx, sz))); py = max(8.2, min(11.3, R * sz / hypot(sx, sz) + 4));
            drawSun(ax, px, py, 0.7, ~strcmp(skyName, 'Overcast'));
            if strcmp(skyName, 'Partly cloudy'), drawCloud(ax, px - 0.9, py - 0.5, 0.9, [0.93 0.93 0.95]); end
            if strcmp(skyName, 'Overcast'), drawCloud(ax, px, py, 1.4, [0.62 0.64 0.68]); drawCloud(ax, px + 1.6, py - 0.3, 1.0, [0.7 0.72 0.76]); end
            if strcmp(skyName, 'Hazy'), drawCloud(ax, px + 1.7, py - 0.7, 0.8, [0.9 0.9 0.88]); end
        else, text(ax, -8.5, 10.5, 'night', 'Color', 'w', 'FontSize', 12); end
        if S.rain, for i = 1:30, xr = -8.5 + 17 * rand; yr = 3 + 7 * rand; plot(ax, [xr xr - 0.25], [yr yr - 0.9], '-', 'Color', [0.2 0.45 0.9]); end, end
        text(ax, -8.8, -0.45, sprintf('panel angle %.1f deg   |   %s', d.angle, d.mode), 'FontWeight', 'bold', 'Color', 'w', 'FontSize', 11);
        text(ax, -8.8, 11.6, 'Side view: blue bars = solar panels, coloured strip = 4 crop zones', 'FontSize', 9);
        title(ax, sprintf('SRMC canopy: day %d, solar hour %.1f', V.day, V.hour), 'FontSize', 11);
        % ---- time series ----
        n = size(st.hist, 1); t = st.hist(:, 1); if n < 2, t = [0; 1]; end
        ts = @(axx, ttl) title(axx, ttl, 'FontSize', 9, 'Interpreter', 'none');
        cla(h.axT); yyaxis(h.axT, 'left'); plot(h.axT, t(1:n), st.hist(:, 2), 'r-', 'LineWidth', 1.3); ylabel(h.axT, 'temperature (C)'); yyaxis(h.axT, 'right'); plot(h.axT, t(1:n), st.hist(:, 3), 'b-', 'LineWidth', 1.3); ylabel(h.axT, 'humidity (%)'); ts(h.axT, [rT ' sensor DHT11: air temperature (red) and humidity (blue)']); xlabel(h.axT, 'time since start (seconds)'); grid(h.axT, 'on');
        cla(h.axS); yyaxis(h.axS, 'left'); plot(h.axS, t(1:n), st.hist(:, 5), 'Color', [0.2 0.55 0.2], 'LineWidth', 1.3); ylim(h.axS, [0 100]); ylabel(h.axS, 'soil water (%)'); yyaxis(h.axS, 'right'); stairs(h.axS, t(1:n), st.hist(:, 11) + 2 * st.hist(:, 6), 'm-'); ylim(h.axS, [-0.2 3.2]); ylabel(h.axS, 'pump ON = 1, raining = 2'); ts(h.axS, [rT ' sensors: soil water (green), rain (2 = raining), pump (1 = ON)']); xlabel(h.axS, 'time since start (seconds)'); grid(h.axS, 'on');
        cla(h.axR); yyaxis(h.axR, 'left'); plot(h.axR, t(1:n), st.hist(:, 7), 'Color', [0.9 0.55 0], 'LineWidth', 1.3); ylabel(h.axR, 'sunlight (W/m2)'); yyaxis(h.axR, 'right'); plot(h.axR, t(1:n), st.hist(:, 8), 'Color', [0.1 0.6 0.3], 'LineWidth', 1.3); ylabel(h.axR, 'plant light PAR (umol/m2/s)'); ts(h.axR, [d.gTag ' sensors: sunlight (orange) and plant light PAR (green)']); xlabel(h.axR, 'time since start (seconds)'); grid(h.axR, 'on');
        cla(h.axA); yyaxis(h.axA, 'left'); plot(h.axA, t(1:n), st.hist(:, 9), 'Color', [0.1 0.2 0.6], 'LineWidth', 1.5); ylim(h.axA, [0 95]); ylabel(h.axA, 'panel angle (degrees)'); yyaxis(h.axA, 'right'); plot(h.axA, t(1:n), st.hist(:, 10), 'Color', [0.8 0.2 0.2], 'LineWidth', 1.3); ylabel(h.axA, 'electricity (W per m2 panel)'); xlabel(h.axA, 'time since start (seconds)'); ts(h.axA, 'DECISION: panel angle (blue) and electricity made (red)'); grid(h.axA, 'on');
        h.log.String = ['status: ' st.lastMsg '   |   samples: ' num2str(st.n)];
    end

    function c = skyColor(d, skyName)
        if d.sunEl <= 0, c = [0.07 0.09 0.2]; return; end
        switch skyName, case 'Clear', c = [0.55 0.78 0.98]; case 'Hazy', c = [0.72 0.82 0.9]; case 'Partly cloudy', c = [0.62 0.8 0.95]; otherwise, c = [0.66 0.7 0.75]; end
    end
    function drawSun(ax, x, y, r, bright)
        col = ternary(bright, [1 0.82 0.1], [0.95 0.85 0.5]);
        for k = 0:7, an = k * pi / 4; plot(ax, [x + 1.25 * r * cos(an) x + 1.8 * r * sin(an + pi / 2) * 0 + 1.9 * r * cos(an)], [y + 1.25 * r * sin(an) y + 1.9 * r * sin(an)], '-', 'Color', col, 'LineWidth', 2); end
        rectangle(ax, 'Position', [x - r y - r 2 * r 2 * r], 'Curvature', [1 1], 'FaceColor', col, 'EdgeColor', [0.9 0.6 0]);
    end
    function drawCloud(ax, x, y, s, col)
        for q = [-0.7 0 0.7 0.35 -0.35], rectangle(ax, 'Position', [x + q * s - 0.55 * s, y + 0.1 * abs(q) * s - 0.35 * s, 1.1 * s, 0.8 * s], 'Curvature', [1 1], 'FaceColor', col, 'EdgeColor', 'none'); end
    end

    function saveEvidence()
        stamp = datestr(now, 'yyyymmdd_HHMMSS'); f1 = fullfile(logDir, ['dashboard_' stamp '.png']); f2 = fullfile(logDir, ['sensors_' stamp '.csv']);
        exportgraphics(fig, f1, 'Resolution', 130);
        T = array2table(st.hist, 'VariableNames', {'t_s', 'tempC', 'rh', 'vpd_kPa', 'soilPct', 'rain', 'ghi_sim', 'par_sim', 'angle_deg', 'pv_Wm2', 'pump', 'tank_L', 'cropScore', 'wind_sim'}); writetable(T, f2);
        st.lastMsg = ['saved ' f1];
    end
end

function v = ternary(c, a, b), if c, v = a; else, v = b; end, end
