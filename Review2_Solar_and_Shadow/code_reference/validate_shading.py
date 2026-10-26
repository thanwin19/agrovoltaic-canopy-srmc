"""Independent check of the shading model: Cycles (3-D ray tracing, direct light only) vs the engine's 2-D ray cast.
usage: blender -b -P blender/validate_shading.py     (needs out/physics/shade_cases.json from tools/shade_ref.js)"""
import bpy, json, math, os
from mathutils import Vector
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..')); OUT = os.path.join(ROOT, 'out', 'physics')
J = json.load(open(os.path.join(OUT, 'shade_cases.json'))); D = J['design']; N = 81; PITCH = D['panelPitch']; PW = D['panelW']; H = D['pivotHeight']; HALF = N * PITCH / 2; LZ = 60.0; VIEW = D['nPanels'] * PITCH / 2      # wide canopy (periodic assumption); measure only the central field width
bpy.ops.wm.read_factory_settings(use_empty=True); scn = bpy.context.scene; coll = scn.collection
def box(name, x0, x1, y0, y1, z0, z1, parent=None):
    v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    me = bpy.data.meshes.new(name); me.from_pydata(v, [], f); me.update(); o = bpy.data.objects.new(name, me); coll.objects.link(o)
    if parent: o.parent = parent
    return o
white = bpy.data.materials.new('w'); white.use_nodes = True; white.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (1, 1, 1, 1); white.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 1
black = bpy.data.materials.new('b'); black.use_nodes = True; black.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0, 0, 0, 1)
g = box('ground', -HALF - 30, HALF + 30, -LZ / 2 - 30, LZ / 2 + 30, -0.05, 0.0); g.data.materials.append(white)
pivots = []
for k in range(N):                                           # panels as thin plates ON the pivot axis, exactly the model's geometry (no frame, no tube)
    xc = -HALF + k * PITCH + PITCH / 2; pv = bpy.data.objects.new('p%d' % k, None); pv.location = (xc, 0, H); coll.objects.link(pv)
    p = box('panel', -PW / 2, PW / 2, -LZ / 2, LZ / 2, -0.02, 0.02, pv); p.data.materials.append(black); p.visible_camera = False; pivots.append(pv)
sun = bpy.data.lights.new('sun', 'SUN'); sun.energy = 20.0; sun.angle = math.radians(0.02); so = bpy.data.objects.new('sun', sun); coll.objects.link(so)
w = bpy.data.worlds.new('w'); scn.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.0
cam = bpy.data.cameras.new('c'); cam.type = 'ORTHO'; cam.ortho_scale = 2 * VIEW; co = bpy.data.objects.new('c', cam); coll.objects.link(co); scn.camera = co
co.location = (0, 0, 40); co.rotation_euler = (0, 0, 0)
RX, RY = 1000, 120; scn.render.resolution_x, scn.render.resolution_y = RX, RY; scn.render.resolution_percentage = 100
scn.render.engine = 'CYCLES'; scn.cycles.device = 'CPU'; scn.cycles.samples = 8; scn.cycles.use_denoising = False; scn.cycles.max_bounces = 0; scn.cycles.diffuse_bounces = 0
scn.view_settings.view_transform = 'Standard'; scn.view_settings.look = 'None'; scn.render.image_settings.file_format = 'PNG'
res = []
for c in J['cases']:
    for pv in pivots: pv.rotation_euler = (0, math.radians(c['tilt']), 0)
    sd = Vector((c['sx'], c['sy'], c['sz'])).normalized(); so.rotation_euler = (-sd).to_track_quat('-Z', 'Y').to_euler()
    def grab():
        scn.render.filepath = os.path.join(OUT, 'tmp_shade.png'); bpy.ops.render.render(write_still=True)
        im = bpy.data.images.load(scn.render.filepath, check_existing=False); px = list(im.pixels); bpy.data.images.remove(im)
        return [sum(px[((y * RX) + x) * 4] for y in range(RY // 3, 2 * RY // 3)) / (RY // 3) for x in range(RX)]       # centre band only (away from the N/S ends)
    for pv in pivots:
        for ch in pv.children: ch.hide_render = True
    lit_ref = max(grab())                                                   # fully lit reference (no panels)
    for pv in pivots:
        for ch in pv.children: ch.hide_render = False
    col = grab()
    strips = [0.0] * 4; cnt = [0] * 4
    for x in range(RX):
        xm = -VIEW + (x + .5) / RX * 2 * VIEW; u = ((xm + HALF) % PITCH) / PITCH; s = min(3, int(u * 4)); strips[s] += 1.0 if col[x] > 0.5 * lit_ref else 0.0; cnt[s] += 1
    c['blender'] = [strips[i] / cnt[i] for i in range(4)]; res.append(c); print('CASE', c['hour'], c['tilt'], [round(v, 2) for v in c['engine']], [round(v, 2) for v in c['blender']])
J['cases'] = res; json.dump(J, open(os.path.join(OUT, 'shade_results.json'), 'w')); os.remove(os.path.join(OUT, 'tmp_shade.png'))
