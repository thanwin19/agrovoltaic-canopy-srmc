function M = review0_mppt()
%REVIEW0_MPPT  Maximum Power Point Tracking (MPPT) of one PV module: model, search and the Perturb & Observe (P&O) controller.
%
%   WHY MPPT: for every sunlight level and cell temperature a PV module has ONE voltage at which it gives the most power (the maximum power
%   point, MPP). That voltage MOVES when the sun or the temperature changes. A DC-DC converter run by an MPPT algorithm keeps adjusting the
%   module voltage so the panel always works at its MPP. Without it (fixed voltage) a part of the energy is lost.
%
%   Module = typical 400 W mono PERC (Isc 10.5 A, Voc 49.6 V, Imp 9.88 A, Vmp 40.5 V; coefficients typical) - REPLACE with your datasheet.
%   Model  = single-diode, Rs = 0, Rsh = inf:  I(V) = Iph - I0 (exp(V/a) - 1),  a fitted so that the curve passes through (Vmp, Imp).
%
%   M = review0_mppt();   pm = M.params();   [V, I, P] = M.iv(pm, G, Tc);   mpp = M.mpp(pm, G, Tc);
%   st = M.init(pm, 36);  [st, P] = M.po(st, pm, G, Tc);      % one Perturb&Observe step
%   R = M.simulate(pm, G(t), Tc(t));  -> tracking efficiency, energy compared with a fixed voltage
M.params = @params; M.iv = @ivCurve; M.mpp = @findMpp; M.init = @initPO; M.po = @poStep; M.simulate = @simulate;
end

function pm = params()
pm = struct('Isc', 10.5, 'Voc', 49.6, 'Imp', 9.88, 'Vmp', 40.5, 'alphaI', 0.0005, 'betaV', -0.0027, 'dV', 0.5, 'Vfixed', 40.5, 'name', 'typical 400 W module (replace with datasheet)');
f = @(a) pm.Imp / pm.Isc - (1 - (exp(pm.Vmp / a) - 1) / (exp(pm.Voc / a) - 1));
pm.a0 = fzero(f, [0.5 20]);                    % diode "ideality" voltage at 25 C
end

function [V, I, P] = ivCurve(pm, G, Tc, V)
if nargin < 4 || isempty(V), VocT = pm.Voc * (1 + pm.betaV * (Tc - 25)); V = linspace(0, VocT, 400); end
Iph = pm.Isc * max(G, 0) / 1000 * (1 + pm.alphaI * (Tc - 25)); a = pm.a0 * (Tc + 273.15) / 298.15; VocT = pm.Voc * (1 + pm.betaV * (Tc - 25));
if Iph <= 1e-6, I = zeros(size(V)); P = I; return; end
I0 = Iph / (exp(VocT / a) - 1); I = max(0, Iph - I0 * (exp(V / a) - 1)); P = V .* I;
end

function mpp = findMpp(pm, G, Tc)
[V, I, P] = ivCurve(pm, G, Tc); [pmax, k] = max(P); mpp = struct('V', V(k), 'I', I(k), 'P', pmax);
end

function st = initPO(pm, V0)
st = struct('V', V0, 'P', 0, 'dir', 1);
end

function [st, P] = poStep(st, pm, G, Tc)
% Perturb & Observe: change the voltage a little; if the power rose keep going the same way, otherwise turn round.
[~, ~, P] = ivCurve(pm, G, Tc, st.V);
if P < st.P, st.dir = -st.dir; end
st.P = P; st.V = max(1, min(pm.Voc * 1.05, st.V + st.dir * pm.dV));
end

function R = simulate(pm, Gt, Tct, V0)
% P&O every time step against the true MPP; compares with a module held at one fixed voltage (no MPPT).
n = numel(Gt); if nargin < 4, V0 = 30; end
st = initPO(pm, V0); Ptrack = zeros(1, n); Pmpp = zeros(1, n); Pfix = zeros(1, n); Vt = zeros(1, n); Vm = zeros(1, n);
for k = 1:n
    for rep = 1:5, [st, P] = poStep(st, pm, Gt(k), Tct(k)); end        % 5 perturbations per sample
    Ptrack(k) = P; Vt(k) = st.V; m = findMpp(pm, Gt(k), Tct(k)); Pmpp(k) = m.P; Vm(k) = m.V;
    [~, ~, pf] = ivCurve(pm, Gt(k), Tct(k), pm.Vfixed); Pfix(k) = pf;
end
R = struct('Ptrack', Ptrack, 'Pmpp', Pmpp, 'Pfixed', Pfix, 'Vtrack', Vt, 'Vmpp', Vm, 'effTrack', 100 * sum(Ptrack) / max(sum(Pmpp), eps), 'effFixed', 100 * sum(Pfix) / max(sum(Pmpp), eps));
R.gainPct = 100 * (sum(Ptrack) / max(sum(Pfix), eps) - 1);
end
