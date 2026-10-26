"""Tidies E:\\final year project\\srmc-twin: backups, scratch and one-off helper files go to _archive (nothing is deleted except Python caches). Prints what moved.  python tidy_folder.py"""
import os, shutil
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')); A = os.path.join(ROOT, '_archive'); moved = []
def mv(src, sub):
    if not os.path.exists(src): return
    dst = os.path.join(A, sub, os.path.relpath(src, ROOT)); os.makedirs(os.path.dirname(dst), exist_ok=True)
    if os.path.exists(dst): shutil.rmtree(dst) if os.path.isdir(dst) else os.remove(dst)
    shutil.move(src, dst); moved.append((os.path.relpath(src, ROOT), sub))
for dp, dn, fn in os.walk(ROOT):
    if os.path.abspath(dp).startswith(A) or os.path.abspath(dp).startswith(os.path.join(ROOT, 'Proof')): dn[:] = []; continue
    for d in list(dn):
        if d in ('_before_update', '_old'): mv(os.path.join(dp, d), 'backups_of_files_before_the_final_update'); dn.remove(d)
        elif d == '__pycache__': shutil.rmtree(os.path.join(dp, d), ignore_errors=True); dn.remove(d)
for rel in ['_a', '_a24_rubric.py', 'A24_backup_before_rubric.pptx', '17b570d6-3b18-43b5-985c-f853931385ae.png', '_proof_tmp']: mv(os.path.join(ROOT, rel), 'scratch_and_temporary')
S4 = os.path.join(ROOT, 'Review4_Control_and_Simulation', 'sensor_controller')
for f in ['rename_six.py', 'fix_readmes_block.py', 'fix_sens_block.py', 'scan_decks.py', 'edit_updates.py']: mv(os.path.join(S4, f), 'one_off_helper_scripts')
for rel in ['Review0_Prototype_Demo/matlab/debug.log', 'Review4_Control_and_Simulation/results/simulink/debug.log']: mv(os.path.join(ROOT, *rel.split('/')), 'scratch_and_temporary')
print('moved', len(moved), 'items to _archive'); [print('  ', a, '->', b) for a, b in moved]
