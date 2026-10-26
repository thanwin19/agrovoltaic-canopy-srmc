"""Builds the stand-alone 3D mechanism viewer (three.js r128 inlined, works offline).  python build_mechanism_3d.py"""
import os
here = os.path.dirname(os.path.abspath(__file__)); root = os.path.abspath(os.path.join(here, '..'))
three = open(os.path.join(here, 'three.min.js.txt'), encoding='utf8').read().strip()
if three.startswith('<script>'): three = three[len('<script>'):]
html = open(os.path.join(here, 'mechanism3d_template.html'), encoding='utf8').read()
app = open(os.path.join(here, 'mechanism3d.js'), encoding='utf8').read()
html = html.replace('/*THREE_LIB*/', three.replace('</script', '<\\/script'), 1).replace('/*APP*/', app, 1)
out = os.path.join(root, 'results', 'mechanism_3d'); os.makedirs(out, exist_ok=True)
p = os.path.join(out, 'SRMC_Mechanism_3D.html'); open(p, 'w', encoding='utf8').write(html); print(p, os.path.getsize(p) // 1024, 'KB')
