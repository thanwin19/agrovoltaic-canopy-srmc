function build_simulink_controller()
%BUILD_SIMULINK_CONTROLLER  Builds and simulates the SRMC-DT panel controller as a Simulink block diagram.
%   Inputs : solar hour, pyranometer GHI, rain gauge, wind speed;  hourly schedule row (output of the optimiser in srmc_run).
%   Logic  : priority  wind stow (90 deg) > rain (flat catchment, 3 deg fall) > night park (15 deg) > scheduled tilt stop.
%   Plant  : rate-limited drive motor (1 deg/s) + 0.5 deg encoder quantiser.
%   Output : out/simulink/srmc_controller.slx, srmc_controller_diagram.png, srmc_controller_day.png, controller_log.csv
root = rootOf(mfilename('fullpath')); od = fullfile(root,'out','simulink'); if ~exist(od,'dir'), mkdir(od); end
mdl = 'srmc_controller'; if bdIsLoaded(mdl), close_system(mdl, 0); end
% ---- schedule row for 16 April from the optimiser (0.5 deg resolution)
r = srmc_run('tce_madurai','red_sandy_loam',struct('angleStep',0.5),struct('plots',false,'quiet',true,'export',false));
sched = r.params.schedule(4,:); hrs = 5.5:1:18.5; slope = r.params.rainSlope; assignin('base','sched_hours',hrs); assignin('base','sched_angles',sched);
% ---- test day: clear morning, rain 14:00-15:00, wind gust 17:00-17:20
t = (0:60:86400)'; h = t/3600; ghi = 900*max(0,sin(pi*(h-6)/12)).^1.2; rain = zeros(size(t)); wind = 3 + 1.5*sin(2*pi*h/24); rain(h>=14 & h<15) = 12; ghi(h>=14 & h<15) = 0.15*ghi(h>=14 & h<15); wind(h>=17 & h<17.33) = 18;
assignin('base','u_ghi',timeseries(ghi,t)); assignin('base','u_rain',timeseries(rain,t)); assignin('base','u_wind',timeseries(wind,t));
new_system(mdl); open_system(mdl); set_param(mdl,'Solver','ode3','FixedStep','5','StopTime','86400');
ab = @(src, name, pos) add_block(src, [mdl '/' name], 'Position', pos);
ab('simulink/Sources/From Workspace','GHI pyranometer P1',[30 30 190 60]); set_param([mdl '/GHI pyranometer P1'],'VariableName','u_ghi');
ab('simulink/Sources/From Workspace','Rain gauge',[30 100 190 130]); set_param([mdl '/Rain gauge'],'VariableName','u_rain');
ab('simulink/Sources/From Workspace','Wind speed',[30 170 190 200]); set_param([mdl '/Wind speed'],'VariableName','u_wind');
ab('simulink/Sources/Clock','Clock',[30 250 70 280]); ab('simulink/Math Operations/Gain','to hours',[100 250 150 280]); set_param([mdl '/to hours'],'Gain','1/3600');
ab('simulink/Lookup Tables/1-D Lookup Table','Hourly tilt schedule',[210 235 360 295]); set_param([mdl '/Hourly tilt schedule'],'BreakpointsForDimension1','sched_hours','Table','sched_angles','ExtrapMethod','Clip','InterpMethod','Linear point');
ab('simulink/Logic and Bit Operations/Compare To Constant','Night test GHI lt 20',[210 30 330 60]); set_param([mdl '/Night test GHI lt 20'],'relop','<','const','20');
ab('simulink/Logic and Bit Operations/Compare To Constant','Rain test gt 1 mm per h',[210 100 360 130]); set_param([mdl '/Rain test gt 1 mm per h'],'relop','>','const','1');
ab('simulink/Logic and Bit Operations/Compare To Constant','Wind test gt 15 m per s',[210 170 360 200]); set_param([mdl '/Wind test gt 15 m per s'],'relop','>','const','15');
ab('simulink/Sources/Constant','Park angle 15 deg',[400 20 480 40]); set_param([mdl '/Park angle 15 deg'],'Value','15');
ab('simulink/Sources/Constant','Rain slope',[400 95 480 115]); set_param([mdl '/Rain slope'],'Value',num2str(slope));
ab('simulink/Sources/Constant','Stow 90 deg',[400 165 480 185]); set_param([mdl '/Stow 90 deg'],'Value','90');
ab('simulink/Signal Routing/Switch','Select night or schedule',[520 20 570 80]); set_param([mdl '/Select night or schedule'],'Criteria','u2 ~= 0');
ab('simulink/Signal Routing/Switch','Select rain',[620 90 670 150]); set_param([mdl '/Select rain'],'Criteria','u2 ~= 0');
ab('simulink/Signal Routing/Switch','Select wind stow',[720 160 770 220]); set_param([mdl '/Select wind stow'],'Criteria','u2 ~= 0');
ab('simulink/Discontinuities/Rate Limiter','Drive motor 1 deg per s',[820 165 920 195]); set_param([mdl '/Drive motor 1 deg per s'],'RisingSlewLimit','1','FallingSlewLimit','-1');
ab('simulink/Discontinuities/Quantizer','Encoder 0.5 deg',[950 165 1050 195]); set_param([mdl '/Encoder 0.5 deg'],'QuantizationInterval','0.5');
ab('simulink/Sinks/Scope','Panel angle scope',[1090 160 1130 200]);
ab('simulink/Sinks/To Workspace','log angle',[1090 220 1150 250]); set_param([mdl '/log angle'],'VariableName','angle_out','SaveFormat','Timeseries');
ab('simulink/Sinks/To Workspace','log target',[1090 270 1150 300]); set_param([mdl '/log target'],'VariableName','target_out','SaveFormat','Timeseries');
L = @(a,b) add_line(mdl, a, b, 'autorouting','on');
L('GHI pyranometer P1/1','Night test GHI lt 20/1'); L('Rain gauge/1','Rain test gt 1 mm per h/1'); L('Wind speed/1','Wind test gt 15 m per s/1');
L('Clock/1','to hours/1'); L('to hours/1','Hourly tilt schedule/1');
L('Park angle 15 deg/1','Select night or schedule/1'); L('Night test GHI lt 20/1','Select night or schedule/2'); L('Hourly tilt schedule/1','Select night or schedule/3');
L('Rain slope/1','Select rain/1'); L('Rain test gt 1 mm per h/1','Select rain/2'); L('Select night or schedule/1','Select rain/3');
L('Stow 90 deg/1','Select wind stow/1'); L('Wind test gt 15 m per s/1','Select wind stow/2'); L('Select rain/1','Select wind stow/3');
L('Select wind stow/1','Drive motor 1 deg per s/1'); L('Drive motor 1 deg per s/1','Encoder 0.5 deg/1'); L('Encoder 0.5 deg/1','Panel angle scope/1'); L('Encoder 0.5 deg/1','log angle/1'); L('Select wind stow/1','log target/1');
save_system(mdl, fullfile(od,[mdl '.slx']));
try, print(['-s' mdl], '-dpng', '-r130', fullfile(od,'srmc_controller_diagram.png')); catch ME, warning('diagram export failed: %s', ME.message); end
so = sim(mdl); ang = so.angle_out; tg = so.target_out; hh = ang.Time/3600;
f = figure('Visible','off','Position',[100 100 1000 500]); try, theme(f,'light'); catch, end
plot(hh, tg.Data, '--', 'Color', [0.6 0.6 0.6], 'LineWidth', 1.2); hold on; plot(hh, ang.Data, 'LineWidth', 2.2, 'Color', [0.1 0.37 0.68]); grid on; xlim([0 24]); ylim([-5 100]);
patch([14 15 15 14],[-5 -5 100 100],[0.6 0.8 1],'FaceAlpha',0.25,'EdgeColor','none'); patch([17 17.33 17.33 17],[-5 -5 100 100],[1 0.8 0.6],'FaceAlpha',0.35,'EdgeColor','none');
text(14.05, 92, 'rain 12 mm/h', 'FontSize', 9); text(17.38, 92, 'wind gust 18 m/s: stow', 'FontSize', 9); xlabel('Solar hour'); ylabel('Panel angle (deg)'); legend('Commanded angle','Actual angle (1 deg/s motor, 0.5 deg encoder)','Location','southwest');
title('Simulink: SRMC-DT controller on a test day (16 April, TCE)'); exportgraphics(f, fullfile(od,'srmc_controller_day.png'),'Resolution',160); close(f);
writetable(table(hh, tg.Data(:), ang.Data(:), 'VariableNames', {'solar_hour','commanded_deg','actual_deg'}), fullfile(od,'controller_log.csv'));
fprintf('Simulink controller built and simulated. Files in %s\n', od); close_system(mdl, 0);
end

function r = rootOf(p)
%ROOTOF project root: parent of the matlab folder; if the design file is not there (script copied into a Review folder), use ../_project_core
r = fileparts(fileparts(p));
if ~exist(fullfile(r,'design','design.json'),'file'), r = fullfile(fileparts(r),'_project_core'); end
end
