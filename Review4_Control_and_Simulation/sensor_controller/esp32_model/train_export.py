"""Distil the six-sensor optimiser into a small neural network for an ESP32:   python train_export.py
Reads train.bin / test.bin (make_dataset.js), trains a 10-48-48-1 network, scores it against the best possible angle with the same accuracy measure as the paper,
and writes weights as a C header (float32 and int8 versions), model.json, results.json and a CSV of test inputs and Python predictions for the C check."""
import json, os, struct
import numpy as np
import torch, torch.nn as nn
HERE = os.path.dirname(os.path.abspath(__file__)); META = json.load(open(os.path.join(HERE, 'meta.json'))); NF, REC = META['NF'], META['REC']
def load(fn):
    a = np.fromfile(os.path.join(HERE, fn), dtype=np.float32).reshape(-1, REC)
    return dict(X=a[:, :NF], oracle=a[:, NF], opt=a[:, NF + 1], plan=a[:, NF + 2], pv=a[:, NF + 3:NF + 94], crop=a[:, NF + 94:NF + 185])
tr, te = load('train.bin'), load('test.bin')
torch.manual_seed(1); np.random.seed(1)
mu, sd = tr['X'].mean(0), tr['X'].std(0) + 1e-6
nrm = lambda X: ((X - mu) / sd).astype(np.float32)
Ytr = ((tr['oracle'] - 37.5) / 22.5).astype(np.float32)
H = 48
net = nn.Sequential(nn.Linear(NF, H), nn.Tanh(), nn.Linear(H, H), nn.Tanh(), nn.Linear(H, 1))
Xt, Yt = torch.tensor(nrm(tr['X'])), torch.tensor(Ytr)[:, None]
n = len(Xt); idx = np.random.permutation(n); va, trn = idx[:n // 10], idx[n // 10:]
opt = torch.optim.Adam(net.parameters(), 3e-3); sched = torch.optim.lr_scheduler.ReduceLROnPlateau(opt, factor=0.5, patience=8)
best, bs = 1e9, None
for ep in range(500):
    perm = np.random.permutation(trn)
    for i in range(0, len(perm), 512):
        b = perm[i:i + 512]; opt.zero_grad(); loss = nn.functional.smooth_l1_loss(net(Xt[b]), Yt[b], beta=0.05); loss.backward(); opt.step()
    with torch.no_grad(): v = nn.functional.mse_loss(net(Xt[va]), Yt[va]).item()
    sched.step(v)
    if v < best: best, bs = v, {k: x.clone() for k, x in net.state_dict().items()}
net.load_state_dict(bs)
W = [(net[i].weight.detach().numpy().astype(np.float32), net[i].bias.detach().numpy().astype(np.float32)) for i in (0, 2, 4)]
def forward(X, W, tanh=np.tanh):
    h = X
    for i, (w, b) in enumerate(W): h = h @ w.T + b; h = tanh(h) if i < 2 else h
    return h[:, 0]
def angle_of(X, W): return np.clip(np.round((forward(nrm(X), W) * 22.5 + 37.5) * 2) / 2, 15, 60)
def score(ang, d):                                                                         # accuracy A, electricity and crop scores on the true state of every test sample
    i = np.clip(np.round((ang - 15) / 0.5).astype(int), 0, 90); r = np.arange(len(ang))
    pm, cm = d['pv'].max(1), d['crop'].max(1); J = 0.5 * d['pv'] / pm[:, None] + 0.5 * np.where(cm[:, None] > 1e-6, d['crop'] / np.maximum(cm[:, None], 1e-9), 1)
    Jo = J.max(1); Ja = J[r, i]; g = d['X'][:, 2] * 1.0 + 1e-9     # weight: clearness * sun height ~ irradiance
    g = d['X'][:, 2] * d['X'][:, 0]
    return dict(A=float(100 * (g * Ja).sum() / (g * Jo).sum()), elec=float(100 * (d['pv'][r, i] / pm).mean()), crop=float(100 * np.where(cm > 1e-6, d['crop'][r, i] / np.maximum(cm, 1e-9), 1).mean()), rmse=float(np.sqrt(((ang - d['oracle']) ** 2).mean())), mae=float(np.abs(ang - d['oracle']).mean()))
res = {'n_train': int(n), 'n_test': int(len(te['X'])), 'params': int(sum(w.size + b.size for w, b in W))}
res['oracle (best possible)'] = score(te['oracle'], te)
res['optimiser, single noisy readings'] = score(te['opt'], te)
res['neural network (float32)'] = score(angle_of(te['X'], W), te)
res['monthly plan'] = score(te['plan'], te)
res['fixed 45 deg'] = score(np.full(len(te['X']), 45.0), te)
res['fixed 15 deg'] = score(np.full(len(te['X']), 15.0), te)
res['previous angle held'] = score(te['X'][:, 7], te)
# ---- int8 weights (per-layer scale), activations float
def q8(w): s = np.abs(w).max() / 127.0; return np.round(w / s).astype(np.int8), np.float32(s)
Q = [(q8(w), q8(b)) for w, b in W]
Wq = [((qw.astype(np.float32) * sw), (qb.astype(np.float32) * sb)) for ((qw, sw), (qb, sb)) in Q]
res['neural network (int8 weights)'] = score(angle_of(te['X'], Wq), te)
res['bytes_float32'] = res['params'] * 4; res['bytes_int8'] = res['params'] + 4 * 6
# ---- accuracy by band of sky, for the report
kt = te['X'][:, 2]; ang = angle_of(te['X'], W); bands = {}
for nm, mask in (('clear (kt > 0.55)', kt > 0.55), ('partly cloudy', (kt <= 0.55) & (kt > 0.3)), ('overcast (kt <= 0.3)', kt <= 0.3)):
    sub = {k: v[mask] for k, v in te.items()}; bands[nm] = dict(n=int(mask.sum()), nn=score(ang[mask], sub)['A'], opt=score(te['opt'][mask], sub)['A'], fixed45=score(np.full(mask.sum(), 45.0), sub)['A'])
res['by_sky'] = bands
json.dump(res, open(os.path.join(HERE, 'results.json'), 'w'), indent=1, default=float)
json.dump({'mu': mu.tolist(), 'sd': sd.tolist(), 'layers': [{'w': w.tolist(), 'b': b.tolist()} for w, b in W], 'features': META['features']}, open(os.path.join(HERE, 'model.json'), 'w'))
# ---- C header
def arr(name, a, ctype='float'):
    flat = np.asarray(a).ravel(); body = ', '.join(('%.8ef' % v if ctype == 'float' else '%d' % v) for v in flat)
    return 'static const %s %s[%d] = {%s};\n' % (ctype, name, flat.size, body)
with open(os.path.join(HERE, 'srmc_nn_weights.h'), 'w') as f:
    f.write('/* Generated by train_export.py: distilled six-sensor controller, %d parameters, float32 %d bytes, int8 about %d bytes. Do not edit. */\n#pragma once\n#define SRMC_NF %d\n#define SRMC_H %d\n' % (res['params'], res['bytes_float32'], res['bytes_int8'], NF, H))
    f.write(arr('SRMC_MU', mu)); f.write(arr('SRMC_SD', sd))
    for i, (w, b) in enumerate(W): f.write(arr('SRMC_W%d' % (i + 1), w)); f.write(arr('SRMC_B%d' % (i + 1), b))
# ---- test vectors for the C program: 400 test samples, raw features and the Python angle
sel = np.arange(0, len(te['X']), max(1, len(te['X']) // 400))[:400]
with open(os.path.join(HERE, 'test_vectors.csv'), 'w') as f:
    f.write('sz,sx,kt,T,RH,soil,lsr,prev,sin_doy,cos_doy,python_angle\n')
    for i in sel: f.write(','.join('%.7g' % v for v in te['X'][i]) + ',%.1f\n' % ang[i])
print(json.dumps({k: (v if not isinstance(v, dict) else {a: round(b, 2) if isinstance(b, float) else b for a, b in v.items()}) for k, v in res.items()}, indent=1))
