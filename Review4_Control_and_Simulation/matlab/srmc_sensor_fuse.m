function o = srmc_sensor_fuse(list)
%SRMC_SENSOR_FUSE  Median of several readings per channel (filters sensor noise). list: struct array of readings (ghi, parUm, T, RH, soil, wind, rain, day, hour).
o = list(end);
for k = {'ghi','parUm','T','RH','soil','wind'}
    f = k{1}; if isfield(list, f), v = [list.(f)]; v = v(isfinite(v)); if ~isempty(v), o.(f) = median(v); end, end
end
o.rain = sum([list.rain]) * 2 > numel(list);
end
