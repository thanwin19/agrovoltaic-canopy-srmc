function review0_make_screens()
%REVIEW0_MAKE_SCREENS  Renders dashboard screenshots for the standard test situations (Simulate mode) into ../results/screens/.
here = fileparts(mfilename('fullpath')); od = fullfile(fileparts(here), 'results', 'screens'); if ~exist(od, 'dir'), mkdir(od); end
sc = { 'clear_noon',   {'hour',12,'sky','Clear','rain',0,'wind',3,'temp',30,'rh',55,'soil',50}; ...
       'heat_stress',  {'hour',13,'sky','Clear','rain',0,'wind',3,'temp',38,'rh',30,'soil',50}; ...
       'dry_soil_irrigation', {'hour',10,'sky','Partly cloudy','rain',0,'wind',3,'temp',33,'rh',50,'soil',28}; ...
       'rain_harvest', {'hour',15,'sky','Overcast','rain',1,'wind',4,'temp',27,'rh',88,'soil',52}; ...
       'wind_stow',    {'hour',11,'sky','Clear','rain',0,'wind',18,'temp',31,'rh',52,'soil',50}; ...
       'morning_low_sun', {'hour',7.5,'sky','Hazy','rain',0,'wind',2,'temp',26,'rh',70,'soil',50}};
for i = 1:size(sc, 1)
    app = review0_dashboard('Headless', true, 'Visible', false);
    app.set(sc{i, 2}{:}); for k = 1:6, app.step(); end
    app.snapshot(fullfile(od, ['dashboard_' sc{i, 1} '.png'])); d = app.last();
    fprintf('%-22s %-13s angle %5.1f  pv %5.1f  ghi %4.0f  vpd %.2f\n', sc{i, 1}, d.mode, d.angle, d.pv, d.ghi, d.vpd);
    app.close();
end
end
