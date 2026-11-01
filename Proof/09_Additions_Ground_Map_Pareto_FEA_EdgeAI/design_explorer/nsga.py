"""Many-objective design explorer (NSGA-III, pymoo) on top of the digital-twin engine.   python nsga.py [population] [generations]
Decision variables : ground coverage ratio (panel width / row pitch, 0.45 to 1.0), clearance of the lowest panel edge (3.5 to 6.0 m), upper tilt stop (30 to 60 deg), electricity weight w of the controller (0.1 to 0.9)
Objectives         : maximise solar net income, maximise crop net income, minimise structural steel (t per hectare), maximise the share of irrigation met from harvested rain
All four come from eval_server.js (the same engine as the twin, Madurai, one year, per hectare, assumed prices; steel from the column, tube and rope sizes of the final design, screening only)."""
import json, os, subprocess, sys
import numpy as np
from pymoo.algorithms.moo.nsga3 import NSGA3
from pymoo.core.problem import Problem
from pymoo.optimize import minimize
from pymoo.util.ref_dirs import get_reference_directions
HERE = os.path.dirname(os.path.abspath(__file__)); POP = int(sys.argv[1]) if len(sys.argv) > 1 else 48; GEN = int(sys.argv[2]) if len(sys.argv) > 2 else 30
proc = subprocess.Popen(['node', os.path.join(HERE, 'eval_server.js')], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)
cache = {}; log = []
def evaluate(x):
    key = tuple(np.round(x, 3))
    if key in cache: return cache[key]
    d = dict(gcr=float(x[0]), clearance=float(x[1]), tiltMax=float(x[2]), w=float(x[3])); proc.stdin.write(json.dumps(d) + '\n'); proc.stdin.flush()
    r = json.loads(proc.stdout.readline()); assert 'error' not in r, r
    cache[key] = r; log.append(dict(vars=d, **r)); return r
class Design(Problem):
    def __init__(self): super().__init__(n_var=4, n_obj=4, xl=np.array([0.45, 3.5, 30.0, 0.1]), xu=np.array([1.0, 6.0, 60.0, 0.9]))
    def _evaluate(self, X, out, *a, **k):
        F = []
        for x in X: r = evaluate(x); F.append([-r['solar'], -r['crop'], r['steel_t'], -r['rainfed']])
        out['F'] = np.array(F)
ref = get_reference_directions('das-dennis', 4, n_partitions=3)                                     # 20 reference directions
algo = NSGA3(pop_size=max(POP, len(ref)), ref_dirs=ref)
res = minimize(Design(), algo, ('n_gen', GEN), seed=1, verbose=True)
proc.stdin.close()
front = []
for x, f in zip(res.X, res.F):
    r = evaluate(x); front.append(dict(gcr=round(float(x[0]), 3), clearance=round(float(x[1]), 2), tilt_max=int(round(float(x[2]) / 5) * 5), w=round(float(x[3]), 2), **r))
front.sort(key=lambda d: -d['crop'])
ref_design = dict(name='final design (checked)', gcr=0.9988, clearance=4.5, tilt_max=60, w=0.5, solar=52.47, crop=2.53, steel_t=201.15, rainfed=93.87, pv=238.1, light=33.65)
json.dump(dict(population=POP, generations=GEN, evaluations=len(log), reference=ref_design, front=front, all=log), open(os.path.join(HERE, 'design_explorer.json'), 'w'), indent=1)
with open(os.path.join(HERE, 'T25_design_pareto.csv'), 'w') as f:
    f.write('ground coverage,clearance m,upper tilt stop deg,electricity weight,pitch m,pivot height m,solar net INR lakh/ha,crop net INR lakh/ha,steel t/ha,rain-fed %,energy kWh/m2,mean crop light %\n')
    for d in front: f.write('%.3f,%.2f,%d,%.2f,%.2f,%.2f,%.2f,%.2f,%.1f,%.1f,%.1f,%.1f\n' % (d['gcr'], d['clearance'], d['tilt_max'], d['w'], d['pitch'], d['height'], d['solar'], d['crop'], d['steel_t'], d['rainfed'], d['pv'], d['light']))
print('front size', len(front), 'evaluations', len(log))
