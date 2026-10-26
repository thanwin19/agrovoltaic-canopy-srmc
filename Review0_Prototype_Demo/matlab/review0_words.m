function W = review0_words()
%REVIEW0_WORDS  Plain-language sentences for the dashboard and the explanation window.   W = review0_words();  s = W.now(d, S, V);
W.now = @nowSentence; W.wrap = @wrapText; W.level = @levelWord;
end

function s = nowSentence(d, S, V)
switch d.mode
    case 'WIND STOW', s = sprintf('Strong wind (%.0f m/s). The panels are turned edge-on, to %.0f degrees, so the wind cannot damage them.', V.windMS, d.angle);
    case 'RAIN HARVEST', s = sprintf('Rain is detected. The panels tilt to %.0f degrees so the rain runs into the gutter and fills the water tank for irrigation.', d.angle);
    case 'NIGHT PARK', s = sprintf('It is night. The panels rest at %.0f degrees until the sun comes up.', d.angle);
    case 'FORCED', s = sprintf('Fixed angle %.1f degrees (comparison run).', d.angle);
    otherwise
        if d.angle >= 45, how = 'a steep angle, so more sunlight passes through the gaps and reaches the crops';
        elseif d.angle <= 25, how = 'a flat angle, so the panels make more electricity and give the crops some shade';
        else, how = 'a middle angle: a balance between electricity and light for the crops'; end
        stressTxt = ''; if d.stress > 0.5, stressTxt = ' The plants are stressed (hot, dry air or dry soil), so they need less light and the panels can shade them more.'; end
        s = sprintf('Sunlight is %s (%.0f W/m2) and the air is %s (VPD %.1f kPa). The controller chooses %.1f degrees: %s. This gives %.0f W/m2 of electricity and a crop-light score of %.2f (1 = every crop gets the light it needs).%s', ...
            levelWord(d.ghi, [250 600], {'weak', 'medium', 'strong'}), d.ghi, levelWord(d.vpd, [1.2 2.5], {'humid', 'normal', 'dry and stressful'}), d.vpd, d.angle, how, d.pv, d.crop, stressTxt);
end
end

function w = levelWord(x, edges, names)
if x < edges(1), w = names{1}; elseif x < edges(2), w = names{2}; else, w = names{3}; end
end

function L = wrapText(s, n)
words = strsplit(s, ' '); L = {}; cur = '';
for i = 1:numel(words)
    if isempty(cur), cur = words{i}; elseif numel(cur) + 1 + numel(words{i}) <= n, cur = [cur ' ' words{i}]; else, L{end + 1} = cur; cur = words{i}; end %#ok<AGROW>
end
if ~isempty(cur), L{end + 1} = cur; end
end
