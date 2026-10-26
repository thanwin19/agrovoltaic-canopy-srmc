function [pump, tank] = review0_irrigation(pump, soilPct, tank, rain, cfg)
%REVIEW0_IRRIGATION  Drip-pump decision with hysteresis, fed from the harvested-rain cistern.
%   pump ON when soil moisture < cfg.soilDry (35 %) and the cistern has water; OFF when soil > cfg.soilWet (55 %) or the cistern is empty.
%   Rain fills the cistern (4 L per step, simulation units); irrigation uses 2 L per step.
if nargin < 5, cfg = struct(); end
if ~isfield(cfg, 'soilDry'), cfg.soilDry = 35; end
if ~isfield(cfg, 'soilWet'), cfg.soilWet = 55; end
if rain, tank = min(1000, tank + 4); end
if soilPct < cfg.soilDry && tank > 0, pump = true; elseif soilPct > cfg.soilWet || tank <= 0, pump = false; end
if pump, tank = max(0, tank - 2); end
end
