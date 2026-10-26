function r = review0_parse(line)
%REVIEW0_PARSE  Parses one serial line from the ESP8266/ESP32:   SRMC,ms,tempC,rh,soilRaw,rainWet,rainRaw[,ghiWm2,parUmol]
%   r.ok = false for any other line (boot messages, noise).  r.tempOk = false when the DHT11 read failed (-999).
%   The last two fields are optional: a real pyranometer and PAR sensor add them, and the dashboard then uses them instead of the simulated ones.
r = struct('ok', false, 'ms', NaN, 'tempC', NaN, 'rh', NaN, 'soilRaw', NaN, 'rain', 0, 'rainRaw', -1, 'tempOk', false, 'ghi', NaN, 'par', NaN);
parts = strsplit(strtrim(char(line)), ',');
if ~(numel(parts) == 7 || numel(parts) == 9 || numel(parts) == 10) || ~strcmp(parts{1}, 'SRMC'), return; end
v = str2double(parts(2:end));
if any(isnan(v)) || ~(v(5) == 0 || v(5) == 1), return; end
r.ok = true; r.ms = v(1); r.tempC = v(2); r.rh = v(3); r.soilRaw = v(4); r.rain = v(5); r.rainRaw = v(6);
r.tempOk = r.tempC > -100 && r.rh >= 0 && r.rh <= 100;
if numel(v) >= 8, r.ghi = v(7); r.par = v(8); end; r.wind = NaN; if numel(v) == 9, r.wind = v(9); end
end
