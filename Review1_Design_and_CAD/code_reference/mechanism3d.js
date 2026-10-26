/* SRMC 3D tilt-mechanism viewer: real-scale model (metres) of the final design. Needs THREE r128 (inlined by build_mechanism_3d.py). */
(function () {
'use strict';
const D2R = Math.PI / 180, V3 = (x, y, z) => new THREE.Vector3(x, y, z);
const P = { L: 0.44, OFF: 45 * D2R, REST: 3, DRUM_D: 0.12, ROWS: [1.25, 3.75, 6.25, 8.75], ZS: [0, 5, 10], XN: -1.25, XS: 11.25, HTOP: 6.73, SAG: 1.15, ZW: 10.58, TUBE_R: 0.057, WIRE_VIS: 0.015, ROPE_VIS: 0.022 };
const ropeY = x => P.HTOP - 4 * P.SAG * (x - P.XN) * (P.XS - x) / Math.pow(P.XS - P.XN, 2);
const pivotY = x => ropeY(x) + 0.16;
const Q = new URLSearchParams(location.search);
const $ = id => document.getElementById(id);

/* ---------------- scenarios (illustrative controller outputs) ---------------- */
const SCEN = {
  night:  { name: 'Night park', tilt: 15, sun: -8, sky: 'night', rain: 0, wind: 0.3, text: 'No sun: the panels park at 15 deg.' },
  morning:{ name: 'Morning', tilt: 45, sun: 32, sky: 'clear', rain: 0, wind: 2, text: 'Low sun: tilted up to face it; the crop still gets light between rows.' },
  noon:   { name: 'Clear noon', tilt: 18, sun: 72, sky: 'clear', rain: 0, wind: 3, text: 'Sun nearly overhead: a shallow tilt gives the panels the sun at nearly right angles (best power) and the crop the rest.' },
  hot:    { name: 'Hot, dry soil', tilt: 42, sun: 72, sky: 'clear', rain: 0, wind: 3, text: 'Hot dry air or dry soil: the crop needs less light, so the panels tilt up to give more shade and more power.' },
  rain:   { name: 'Rain', tilt: 3, sun: 55, sky: 'rain', rain: 1, wind: 5, text: 'Rain sensor wet: panels go flat (3 deg), the roof is sealed and the water runs to the gutter and cistern.' },
  storm:  { name: 'Storm stow', tilt: 90, sun: 45, sky: 'storm', rain: 0, wind: 16, text: 'Anemometer reads 15 m/s (54 km/h) or more: panels turn edge-on (90 deg) so the wind passes through. Released below 12 m/s.' }
};
const AMB = {
  clear: { exp: 1.0, top: 0x4f8fe0, bot: 0xcfe6f7, sun: 2.3, hemi: 0.42, fog: 0xcfe6f7 },
  rain:  { exp: 0.72, top: 0x6c7684, bot: 0xaab3bd, sun: 0.6, hemi: 0.6, fog: 0xaab3bd },
  storm: { exp: 0.68, top: 0x4c5560, bot: 0x8d96a0, sun: 0.5, hemi: 0.55, fog: 0x8d96a0 },
  night: { exp: 0.55, top: 0x050a18, bot: 0x16203a, sun: 0.0, hemi: 0.2, fog: 0x16203a }
};

/* ---------------- renderer / scene ---------------- */
const cv = $('c');
const renderer = new THREE.WebGLRenderer({ canvas: cv, antialias: true, preserveDrawingBuffer: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.outputEncoding = THREE.sRGBEncoding; renderer.toneMapping = THREE.ACESFilmicToneMapping;
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(40, 1, 0.1, 400);

/* sky dome + environment */
const skyU = { top: { value: new THREE.Color(AMB.clear.top) }, bot: { value: new THREE.Color(AMB.clear.bot) } };
const sky = new THREE.Mesh(new THREE.SphereGeometry(250, 32, 16), new THREE.ShaderMaterial({ side: THREE.BackSide, depthWrite: false, uniforms: skyU,
  vertexShader: 'varying vec3 vP; void main(){ vP = position; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }',
  fragmentShader: 'uniform vec3 top; uniform vec3 bot; varying vec3 vP; void main(){ float h = clamp(normalize(vP).y*1.4+0.1,0.0,1.0); gl_FragColor = vec4(mix(bot, top, pow(h,0.6)),1.0); }' }));
scene.add(sky);
/* no PMREM environment: it rendered black on some software GL drivers; metals are lit by extra lights instead */
scene.fog = new THREE.Fog(AMB.clear.fog, 70, 230);

const hemi = new THREE.HemisphereLight(0xdcecff, 0x6b5a40, 0.42); scene.add(hemi);
const fillA = new THREE.DirectionalLight(0xbfd8ff, 0.32); fillA.position.set(-20, 14, 25); const fillB = new THREE.DirectionalLight(0xffe2c0, 0.22); fillB.position.set(30, 8, -20); const fillC = new THREE.DirectionalLight(0xffffff, 0.2); fillC.position.set(10, 30, 40); scene.add(fillA, fillB, fillC);
const sun = new THREE.DirectionalLight(0xfff2dd, 2.3); sun.castShadow = true;
sun.shadow.mapSize.set(2048, 2048); { const c = sun.shadow.camera; c.left = -17; c.right = 17; c.top = 17; c.bottom = -17; c.near = 1; c.far = 120; }
sun.shadow.bias = -0.0004; sun.shadow.normalBias = 0.03; sun.target.position.set(5, 0, 5); scene.add(sun, sun.target);

/* ---------------- materials ---------------- */
const M = {
  ss: new THREE.MeshStandardMaterial({ color: 0xc4cad1, metalness: 0.55, roughness: 0.32 }),
  ssDark: new THREE.MeshStandardMaterial({ color: 0x8e959d, metalness: 0.55, roughness: 0.42 }),
  galv: new THREE.MeshStandardMaterial({ color: 0x9ea6ac, metalness: 0.55, roughness: 0.5 }),
  concrete: new THREE.MeshStandardMaterial({ color: 0x9a9893, roughness: 0.95, metalness: 0.00 }),
  wire: new THREE.MeshStandardMaterial({ color: 0xffb020, metalness: 0.30, roughness: 0.4, emissive: 0x442600 }),
  rope: new THREE.MeshStandardMaterial({ color: 0xd5d9de, metalness: 0.55, roughness: 0.3 }),
  paintBlue: new THREE.MeshStandardMaterial({ color: 0x1f5fbf, metalness: 0.40, roughness: 0.45 }),
  paintGreen: new THREE.MeshStandardMaterial({ color: 0x1f7a4a, metalness: 0.40, roughness: 0.5 }),
  red: new THREE.MeshStandardMaterial({ color: 0xc23a2e, metalness: 0.30, roughness: 0.5 }),
  white: new THREE.MeshStandardMaterial({ color: 0xf2f2ee, metalness: 0.10, roughness: 0.55 }),
  black: new THREE.MeshStandardMaterial({ color: 0x15171a, metalness: 0.30, roughness: 0.6 }),
  brass: new THREE.MeshStandardMaterial({ color: 0xc8a24a, metalness: 0.55, roughness: 0.35 }),
  arm: new THREE.MeshStandardMaterial({ color: 0xe8edf2, metalness: 0.55, roughness: 0.25 }),
  led: new THREE.MeshBasicMaterial({ color: 0x35ff7a })
};
function cvTex(w, h, fn, rep) { const c = document.createElement('canvas'); c.width = w; c.height = h; fn(c.getContext('2d'), w, h); const t = new THREE.CanvasTexture(c); t.encoding = THREE.sRGBEncoding; t.anisotropy = 8; if (rep) { t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(rep[0], rep[1]); } return t; }
const cellTex = cvTex(512, 512, (g, w, h) => {
  g.fillStyle = '#c9ced2'; g.fillRect(0, 0, w, h); g.fillStyle = '#0d1b3d'; g.fillRect(10, 10, w - 20, h - 20);
  const n = 10, cw = (w - 36) / n; for (let i = 0; i < n; i++) for (let j = 0; j < n; j++) { const x = 18 + i * cw, y = 18 + j * cw; const gr = g.createLinearGradient(x, y, x + cw, y + cw); gr.addColorStop(0, '#1b3a7a'); gr.addColorStop(1, '#10285a'); g.fillStyle = gr; g.fillRect(x + 1.5, y + 1.5, cw - 3, cw - 3); g.strokeStyle = 'rgba(190,205,230,.55)'; g.lineWidth = 1; for (let k = 1; k <= 2; k++) { g.beginPath(); g.moveTo(x + 1.5, y + k * cw / 3); g.lineTo(x + cw - 1.5, y + k * cw / 3); g.stroke(); } }
});
const PM = { frame: new THREE.MeshStandardMaterial({ color: 0xcfd3d6, metalness: 0.55, roughness: 0.4 }), glass: new THREE.MeshStandardMaterial({ map: cellTex, metalness: 0.35, roughness: 0.18 }), back: new THREE.MeshStandardMaterial({ color: 0xe9eaec, roughness: 0.7 }) };
const panelMats = [PM.frame, PM.frame, PM.glass, PM.back, PM.frame, PM.frame];
Object.values(M).forEach(m => { if (m.color && !m.isMeshBasicMaterial) m.color.convertSRGBToLinear(); if (m.emissive) m.emissive.convertSRGBToLinear(); }); [PM.frame, PM.back].forEach(m => m.color.convertSRGBToLinear());
function setXray(on) { [PM.frame, PM.glass, PM.back].forEach(m => { m.transparent = on; m.opacity = on ? 0.22 : 1; m.depthWrite = !on; m.needsUpdate = true; }); }

/* ---------------- helpers ---------------- */
const unitY = V3(0, 1, 0);
function mk(geo, mat, x, y, z, cast) { const m = new THREE.Mesh(geo, mat); m.position.set(x || 0, y || 0, z || 0); m.castShadow = cast !== false; m.receiveShadow = true; return m; }
function cylZ(r, len, mat, x, y, z) { const g = new THREE.CylinderGeometry(r, r, len, 20); g.rotateX(Math.PI / 2); return mk(g, mat, x, y, z); }
function cylX(r, len, mat, x, y, z) { const g = new THREE.CylinderGeometry(r, r, len, 20); g.rotateZ(Math.PI / 2); return mk(g, mat, x, y, z); }
function place(mesh, a, b) { const d = b.clone().sub(a), l = d.length(); mesh.position.copy(a).addScaledVector(d, 0.5); mesh.scale.set(1, Math.max(l, 1e-4), 1); mesh.quaternion.setFromUnitVectors(unitY, d.normalize()); }
const unitCyl = (r, mat) => { const m = new THREE.Mesh(new THREE.CylinderGeometry(r, r, 1, 8), mat); m.castShadow = true; return m; };
function rodBetween(a, b, r, mat, parent) { const m = unitCyl(r, mat); place(m, a, b); (parent || scene).add(m); return m; }

/* ---------------- ground, crop ---------------- */
const soilTex = cvTex(1024, 1024, (g, w, h) => {
  g.fillStyle = '#8a6a48'; g.fillRect(0, 0, w, h); for (let i = 0; i < 9000; i++) { const v = 90 + Math.random() * 60; g.fillStyle = 'rgba(' + v + ',' + (v * .75) + ',' + (v * .5) + ',.35)'; g.fillRect(Math.random() * w, Math.random() * h, 3, 3); }
  for (let i = 0; i < 16; i++) { const y = 32 + i * 64; g.fillStyle = 'rgba(60,40,22,.55)'; g.fillRect(0, y - 6, w, 12); g.fillStyle = 'rgba(40,110,50,.30)'; g.fillRect(0, y - 14, w, 6); }
}, [14, 14]);
const ground = mk(new THREE.PlaneGeometry(400, 400), new THREE.MeshStandardMaterial({ map: soilTex, roughness: 1, metalness: 0.00 }), 5, 0, 5, false); ground.rotation.x = -Math.PI / 2; ground.receiveShadow = true; scene.add(ground);
const cropGroup = new THREE.Group(); scene.add(cropGroup);
{
  const geo = new THREE.IcosahedronGeometry(0.11, 1); geo.scale(1, 0.7, 1); const cols = [0x2f8a3c, 0x3b9a49, 0x4aa957, 0x2a7a37];
  const rows = []; for (let x = -2.2; x <= 12.8; x += 0.62) for (let z = -2; z <= 12.2; z += 0.34) { if (x > 10.4 && z > 9.6) continue; rows.push([x + (Math.random() - .5) * .08, z + (Math.random() - .5) * .08]); }
  const inst = new THREE.InstancedMesh(geo, new THREE.MeshStandardMaterial({ roughness: 0.8 }), rows.length); const d = new THREE.Object3D(), c = new THREE.Color();
  rows.forEach((r, i) => { const s = 0.8 + Math.random() * 0.6; d.position.set(r[0], 0.08 * s, r[1]); d.scale.set(s, s * (0.8 + Math.random() * .5), s); d.rotation.y = Math.random() * 6; d.updateMatrix(); inst.setMatrixAt(i, d.matrix); c.setHex(cols[i % 4]).convertSRGBToLinear(); inst.setColorAt(i, c); });
  inst.receiveShadow = true; cropGroup.add(inst);
}

/* ---------------- columns, ropes, stays, anchors ---------------- */
const struct = new THREE.Group(); scene.add(struct);
const colTops = [];
[P.XN, P.XS].forEach(x => P.ZS.forEach(z => {
  const col = mk(new THREE.BoxGeometry(0.2, P.HTOP + 0.4, 0.2), M.galv, x, (P.HTOP - 0.4) / 2 + 0.0, z); col.position.y = (P.HTOP + 0.4) / 2 - 0.4; struct.add(col);
  const pad = mk(new THREE.BoxGeometry(0.9, 0.7, 0.9), M.concrete, x, -0.25, z); struct.add(pad);
  const plate = mk(new THREE.BoxGeometry(0.34, 0.025, 0.34), M.ssDark, x, 0.11, z); struct.add(plate);
  const cap = mk(new THREE.BoxGeometry(0.28, 0.06, 0.28), M.ssDark, x, P.HTOP + 0.03, z); struct.add(cap);
  const eye = cylZ(0.035, 0.12, M.ss, x, P.HTOP - 0.05, z); struct.add(eye);
  colTops.push([x, z]);
  /* stay to ground anchor */
  const dir = x < 5 ? -1 : 1, ax = x + dir * 4.2; rodBetween(V3(x, P.HTOP - 0.1, z), V3(ax, 0.12, z), 0.016, M.rope, struct);
  struct.add(mk(new THREE.BoxGeometry(1.1, 0.5, 1.1), M.concrete, ax, -0.1, z));
  const tb = cylX(0.03, 0.4, M.ss, x + dir * 0.6, P.HTOP - 0.1 - 0.6 * (P.HTOP / 4.2), z); tb.rotation.z = Math.atan2(-P.HTOP, dir * 4.2); struct.add(tb);
  if (z === 0 || z === 10) { const dz = z === 0 ? -1 : 1, az = z + dz * 4.2; rodBetween(V3(x, P.HTOP - 0.1, z), V3(x, 0.12, az), 0.016, M.rope, struct); struct.add(mk(new THREE.BoxGeometry(1.1, 0.5, 1.1), M.concrete, x, -0.1, az)); }
}));
P.ZS.forEach(z => {
  const pts = []; for (let x = P.XN; x <= P.XS + 1e-6; x += 0.25) pts.push(V3(x, ropeY(x), z));
  struct.add(mk(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts), 90, P.ROPE_VIS, 8, false), M.rope, 0, 0, 0));
});

/* ---------------- torque tubes + panels + lever arms ---------------- */
const rowsG = [];
const armShape = new THREE.Shape(); armShape.moveTo(0, -0.045); armShape.lineTo(P.L, -0.024); armShape.lineTo(P.L, 0.024); armShape.lineTo(0, 0.045); armShape.lineTo(-0.02, 0); armShape.closePath();
{ const hole = new THREE.Path(); hole.absarc(P.L - 0.003, 0, 0.011, 0, Math.PI * 2, true); armShape.holes.push(hole); }
const armGeo = new THREE.ExtrudeGeometry(armShape, { depth: 0.014, bevelEnabled: false });
const ZA = 10.36;
P.ROWS.forEach((xc, i) => {
  const H = pivotY(xc), g = new THREE.Group(); g.position.set(xc, H, 0); scene.add(g);
  const tg = new THREE.CylinderGeometry(P.TUBE_R, P.TUBE_R, 10.6, 24); tg.rotateX(Math.PI / 2); tg.translate(0, 0, 5.15); g.add(mk(tg, M.ss));
  [-0.6, 0.6].forEach(rx => g.add(mk(new THREE.BoxGeometry(0.05, 0.05, 10.0), M.galv, rx, 0.10, 5.0)));
  [0.4, 2.5, 5, 7.5, 9.6].forEach(z => { g.add(mk(new THREE.BoxGeometry(1.3, 0.04, 0.07), M.galv, 0, 0.075, z)); g.add(mk(new THREE.BoxGeometry(0.16, 0.12, 0.08), M.ssDark, 0, 0.03, z)); });
  [1.25, 3.75, 6.25, 8.75].forEach(z => g.add(mk(new THREE.BoxGeometry(2.45, 0.04, 2.35), panelMats, 0, 0.14, z)));
  /* lever arm assembly */
  const col = cylZ(0.082, 0.12, M.ssDark, 0, 0, ZA); g.add(col);
  const arm = new THREE.Mesh(armGeo, M.arm); arm.castShadow = true; arm.position.z = ZA + 0.06; arm.rotation.z = -Math.PI / 4; g.add(arm);
  const tx = P.L * Math.sin(P.OFF), ty = -P.L * Math.cos(P.OFF);
  g.add(cylZ(0.011, 0.2, M.ss, tx, ty, ZA + 0.16));
  const clamp = mk(new THREE.BoxGeometry(0.05, 0.05, 0.035), M.brass, tx, ty, P.ZW); g.add(clamp);
  g.add(mk(new THREE.SphereGeometry(0.022, 12, 8), M.red, 0, 0, ZA + 0.17));
  rowsG.push({ g, xc, H, tipLocal: V3(tx, ty, P.ZW) });
  /* static bearing rings clamped on the carrier rope */
  P.ZS.forEach(z => {
    struct.add(mk(new THREE.TorusGeometry(0.082, 0.016, 10, 28), M.ssDark, xc, H, z));
    struct.add(mk(new THREE.BoxGeometry(0.07, 0.085, 0.09), M.ssDark, xc, H - 0.11, z));
    struct.add(mk(new THREE.BoxGeometry(0.1, 0.03, 0.12), M.ss, xc, ropeY(xc) + 0.01, z));
  });
});

/* ---------------- guide sheaves, drum, winch ---------------- */
const SH = { N: { c: V3(-0.9, 5.15, P.ZW), r: 0.15 }, S1: { c: V3(11.41, 5.35, P.ZW), r: 0.1 }, S2: { c: V3(11.29, 4.9, P.ZW), r: 0.1 }, D: V3(11.45, 1.25, P.ZW) };
function sheave(c, r) { const g = new THREE.Group(); g.position.copy(c); const w = new THREE.CylinderGeometry(r + 0.015, r + 0.015, 0.03, 28); w.rotateX(Math.PI / 2); g.add(mk(w, M.ss)); const hub = cylZ(0.03, 0.06, M.ssDark, 0, 0, 0); g.add(hub); scene.add(g); return g; }
const shN = sheave(SH.N.c, SH.N.r), shS1 = sheave(SH.S1.c, SH.S1.r), shS2 = sheave(SH.S2.c, SH.S2.r);
/* sheave brackets */
struct.add(mk(new THREE.BoxGeometry(0.05, 0.6, 0.03), M.galv, -0.9, 5.15, P.ZW + 0.04)); struct.add(rodBetween(V3(-0.9, 5.15, P.ZW + 0.04), V3(-1.25, 5.3, 10.12), 0.02, M.galv));
struct.add(mk(new THREE.BoxGeometry(0.45, 0.04, 0.03), M.galv, 11.35, 5.1, P.ZW + 0.04)); rodBetween(V3(11.35, 5.1, P.ZW + 0.04), V3(11.25, 5.1, 10.12), 0.02, M.galv);
/* winch */
const winch = new THREE.Group(); scene.add(winch);
winch.add(mk(new THREE.BoxGeometry(1.5, 0.12, 1.5), M.concrete, 11.55, 0.06, 11.0));
[[11.0, 10.4], [11.0, 11.6], [11.9, 10.4], [11.9, 11.6]].forEach(p => winch.add(mk(new THREE.BoxGeometry(0.07, 1.2, 0.07), M.paintBlue, p[0], 0.7, p[1])));
winch.add(mk(new THREE.BoxGeometry(1.0, 0.07, 1.4), M.paintBlue, 11.45, 1.18 - 0.2, 11.0));
const drum = new THREE.Group(); drum.position.copy(SH.D); scene.add(drum);
const drumTex = cvTex(256, 64, (g, w, h) => { g.fillStyle = '#b9c0c8'; g.fillRect(0, 0, w, h); g.strokeStyle = '#3d444c'; g.lineWidth = 3; for (let i = 0; i < 20; i++) { g.beginPath(); g.moveTo(i * 14, 0); g.lineTo(i * 14 + 14, h); g.stroke(); } g.fillStyle = '#ffb020'; g.fillRect(0, 0, 10, h); });
{ const dg = new THREE.CylinderGeometry(P.DRUM_D / 2, P.DRUM_D / 2, 0.3, 32); dg.rotateX(Math.PI / 2); drum.add(mk(dg, new THREE.MeshStandardMaterial({ map: drumTex, metalness: 0.55, roughness: 0.4 })));
  [-0.16, 0.16].forEach(z => { const fg = new THREE.CylinderGeometry(0.11, 0.11, 0.02, 32); fg.rotateX(Math.PI / 2); drum.add(mk(fg, M.ssDark, 0, 0, z)); });
  const key = mk(new THREE.BoxGeometry(0.04, 0.14, 0.02), M.red, 0, 0.1, 0.17); drum.add(key); }
winch.add(cylZ(0.03, 0.8, M.ss, 11.45, 1.25, 10.9)); /* shaft */
winch.add(mk(new THREE.BoxGeometry(0.28, 0.3, 0.3), M.paintBlue, 11.45, 1.25, 10.62 + 0.55 - 0.02));   /* worm gearbox */
const motorBody = cylZ(0.115, 0.4, M.paintGreen, 11.45, 1.25, 11.55); winch.add(motorBody);
{ const fins = []; for (let i = 0; i < 8; i++) fins.push(cylZ(0.12, 0.012, M.paintGreen, 11.45, 1.25, 11.38 + i * 0.05)); fins.forEach(f => winch.add(f)); }
const fanG = new THREE.Group(); fanG.position.set(11.45, 1.25, 11.8); { for (let i = 0; i < 6; i++) { const b = mk(new THREE.BoxGeometry(0.2, 0.025, 0.012), M.black, 0, 0, 0, false); b.rotation.z = i * Math.PI / 3; b.position.set(0, 0, 0); fanG.add(b); } } winch.add(fanG);
winch.add(cylZ(0.13, 0.05, M.black, 11.45, 1.25, 11.83));
winch.add(cylZ(0.09, 0.06, M.red, 11.45, 1.25, 10.34));   /* brake drum */
winch.add(mk(new THREE.BoxGeometry(0.1, 0.1, 0.08), M.black, 11.45, 1.42, 10.3));   /* limit switch + encoder */
winch.add(mk(new THREE.SphereGeometry(0.02, 8, 6), new THREE.MeshBasicMaterial({ color: 0xff6a3a }), 11.5, 1.47, 10.26));
/* controller cabinet */
{ const cab = new THREE.Group(); cab.position.set(12.45, 1.3, 11.2); scene.add(cab); cab.add(mk(new THREE.BoxGeometry(0.55, 0.75, 0.28), M.white)); cab.add(mk(new THREE.BoxGeometry(0.5, 0.7, 0.01), M.galv, 0, 0, -0.145));
  cab.add(mk(new THREE.SphereGeometry(0.018, 8, 6), M.led, -0.2, 0.28, -0.15, false)); cab.add(mk(new THREE.BoxGeometry(0.28, 0.14, 0.01), M.black, 0, 0.12, -0.145, false));
  const ant = mk(new THREE.CylinderGeometry(0.008, 0.008, 0.4, 6), M.black, 0.2, 0.55, 0); cab.add(ant);
  [-0.22, 0.22].forEach(dx => scene.add(mk(new THREE.BoxGeometry(0.06, 1.0, 0.06), M.galv, 12.45 + dx, 0.5, 11.2)));
  rodBetween(V3(12.45, 1.0, 11.05), V3(11.55, 1.25, 11.55), 0.012, M.black); }

/* ---------------- sensors ---------------- */
const cups = new THREE.Group();
{ const mast = mk(new THREE.CylinderGeometry(0.04, 0.05, 3.0, 12), M.galv, P.XN, P.HTOP + 1.5, 0); struct.add(mast);
  cups.position.set(P.XN, P.HTOP + 3.08, 0); const hub = mk(new THREE.CylinderGeometry(0.03, 0.03, 0.14, 12), M.black, 0, 0, 0); cups.add(hub);
  for (let i = 0; i < 3; i++) { const a = i * Math.PI * 2 / 3, arm = cylX(0.008, 0.24, M.black, 0.12, 0, 0); arm.rotation.y = 0; const holder = new THREE.Group(); holder.rotation.y = a; holder.add(arm); const cup = mk(new THREE.SphereGeometry(0.06, 14, 8, 0, Math.PI), M.white, 0.25, 0, 0); cup.rotation.y = Math.PI / 2; holder.add(cup); cups.add(holder); }
  scene.add(cups);
  /* pyranometer + rain sensor on a side arm */
  struct.add(mk(new THREE.BoxGeometry(0.5, 0.03, 0.03), M.galv, P.XN + 0.25, P.HTOP + 2.3, 0));
  const pyr = new THREE.Group(); pyr.position.set(P.XN + 0.5, P.HTOP + 2.35, 0); pyr.add(mk(new THREE.CylinderGeometry(0.07, 0.07, 0.05, 20), M.white, 0, 0, 0)); pyr.add(mk(new THREE.SphereGeometry(0.045, 14, 8, 0, Math.PI * 2, 0, Math.PI / 2), new THREE.MeshStandardMaterial({ color: 0xcfe6ff, transparent: true, opacity: 0.7, roughness: 0.05 }), 0, 0.025, 0)); struct.add(pyr);
  const rain = mk(new THREE.BoxGeometry(0.13, 0.012, 0.09), M.brass, P.XN + 0.25, P.HTOP + 1.7, 0); rain.rotation.z = 0.25; struct.add(rain); struct.add(mk(new THREE.BoxGeometry(0.04, 0.04, 0.04), M.black, P.XN + 0.25, P.HTOP + 1.6, 0));
  /* sensor stake under the canopy: PAR, DHT11, soil probe */
  const sx = 4.4, sz = -1.2; struct.add(mk(new THREE.BoxGeometry(0.05, 1.9, 0.05), M.galv, sx, 0.95, sz));
  struct.add(mk(new THREE.CylinderGeometry(0.05, 0.05, 0.03, 16), M.white, sx, 1.45, sz)); struct.add(mk(new THREE.SphereGeometry(0.035, 12, 8, 0, Math.PI * 2, 0, Math.PI / 2), M.white, sx, 1.465, sz)); /* PAR */
  for (let i = 0; i < 4; i++) struct.add(mk(new THREE.CylinderGeometry(0.075, 0.075, 0.012, 16), M.white, sx + 0.12, 1.78 - i * 0.04, sz)); /* DHT shield */
  struct.add(mk(new THREE.BoxGeometry(0.03, 0.4, 0.012), M.black, sx + 0.07, -0.15, sz + 0.08)); struct.add(mk(new THREE.BoxGeometry(0.05, 0.05, 0.05), M.black, sx + 0.07, 0.07, sz + 0.08));
}

/* ---------------- gutter + cistern ---------------- */
{ const gu = new THREE.Group(); const sh = new THREE.Shape(); sh.moveTo(-0.18, 0.1); sh.lineTo(-0.18, -0.1); sh.lineTo(0.18, -0.1); sh.lineTo(0.18, 0.1); sh.lineTo(0.165, 0.1); sh.lineTo(0.165, -0.085); sh.lineTo(-0.165, -0.085); sh.lineTo(-0.165, 0.1); sh.closePath();
  const gg = new THREE.ExtrudeGeometry(sh, { depth: 10.8, bevelEnabled: false }); gg.translate(0, 0, -0.3); const gm = mk(gg, M.galv, 10.3, 5.95, 0); scene.add(gm);
  [0, 5, 10].forEach(z => rodBetween(V3(10.3, 5.85, z), V3(11.25, 5.6, z), 0.012, M.galv));
  rodBetween(V3(10.3, 5.85, -0.15), V3(10.3, 0.9, -0.15), 0.045, M.paintBlue);
  const tank = mk(new THREE.CylinderGeometry(0.75, 0.75, 1.0, 28), M.paintBlue, 10.3, 0.5, -0.15); scene.add(tank); scene.add(mk(new THREE.CylinderGeometry(0.78, 0.78, 0.04, 28), M.ssDark, 10.3, 1.02, -0.15)); }

/* ---------------- drive wire (continuous loop on drum) ---------------- */
function arcPts(c, r, a0, a1, n) { const o = []; for (let i = 0; i <= n; i++) { const a = (a0 + (a1 - a0) * i / n) * D2R; o.push(V3(c.x + r * Math.cos(a), c.y + r * Math.sin(a), P.ZW)); } return o; }
const wirePool = []; const wireGrp = new THREE.Group(); scene.add(wireGrp);
function wirePath(tips) {
  const p = [];
  p.push(V3(SH.D.x + 0.06, SH.D.y, P.ZW)); p.push(...arcPts(SH.S1.c, SH.S1.r, 0, 90, 6));
  tips.slice().reverse().forEach(t => p.push(t));
  p.push(...arcPts(SH.N.c, SH.N.r, 90, 270, 14));
  p.push(...arcPts(SH.S2.c, SH.S2.r, 90, 0, 6)); p.push(V3(SH.D.x - 0.06, SH.D.y, P.ZW));
  return p;
}
function updateWire(tips) {
  const p = wirePath(tips);
  while (wirePool.length < p.length - 1) { const m = unitCyl(P.WIRE_VIS, M.wire); wireGrp.add(m); wirePool.push(m); }
  wirePool.forEach((m, i) => { if (i < p.length - 1) { m.visible = true; place(m, p[i], p[i + 1]); } else m.visible = false; });
  /* cumulative length for travelling dots */
  const cum = [0]; for (let i = 1; i < p.length; i++) cum.push(cum[i - 1] + p[i].distanceTo(p[i - 1]));
  wirePathData = { p, cum };
}
let wirePathData = null;
const dots = []; { const dm = new THREE.MeshBasicMaterial({ color: 0xfff1a8 }); for (let i = 0; i < 14; i++) { const d = new THREE.Mesh(new THREE.SphereGeometry(0.035, 8, 6), dm); d.visible = false; scene.add(d); dots.push(d); } }
function moveDots(dir, t) { if (!wirePathData || !dir) { dots.forEach(d => d.visible = false); return; } const { p, cum } = wirePathData, tot = cum[cum.length - 1]; dots.forEach((d, i) => { let s = ((i / dots.length + t * 0.18 * dir) % 1 + 1) % 1 * tot, k = 1; while (k < cum.length - 1 && cum[k] < s) k++; const f = (s - cum[k - 1]) / Math.max(1e-6, cum[k] - cum[k - 1]); d.position.copy(p[k - 1]).lerp(p[k], f); d.visible = true; }); }

/* ---------------- rain + wind particles ---------------- */
const rainGeo = new THREE.BufferGeometry(); const NR = 1400, rp = new Float32Array(NR * 6), rv = new Float32Array(NR);
for (let i = 0; i < NR; i++) { const x = -5 + Math.random() * 22, y = Math.random() * 12, z = -4 + Math.random() * 19; rp.set([x, y, z, x + 0.05, y - 0.55, z], i * 6); rv[i] = 9 + Math.random() * 5; }
rainGeo.setAttribute('position', new THREE.BufferAttribute(rp, 3));
const rainLines = new THREE.LineSegments(rainGeo, new THREE.LineBasicMaterial({ color: 0xcfe3ff, transparent: true, opacity: 0.55 })); rainLines.visible = false; rainLines.frustumCulled = false; scene.add(rainLines);
const windGeo = new THREE.BufferGeometry(); const NW = 260, wp = new Float32Array(NW * 6), wv = new Float32Array(NW);
for (let i = 0; i < NW; i++) { const x = -4 + Math.random() * 20, y = 0.5 + Math.random() * 9, z = -4 + Math.random() * 19; wp.set([x, y, z, x, y, z + 1.6], i * 6); wv[i] = 0.7 + Math.random() * 0.6; }
windGeo.setAttribute('position', new THREE.BufferAttribute(wp, 3));
const windLines = new THREE.LineSegments(windGeo, new THREE.LineBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.35 })); windLines.visible = false; windLines.frustumCulled = false; scene.add(windLines);

/* ---------------- sun ray indicator (above row 2) ---------------- */
const rays = new THREE.Group(); scene.add(rays);
const rayMat = new THREE.LineBasicMaterial({ color: 0xffd34d }); const rayLines = [];
for (let i = 0; i < 5; i++) { const g = new THREE.BufferGeometry().setFromPoints([V3(), V3(0, 1, 0)]); const l = new THREE.Line(g, rayMat); rays.add(l); rayLines.push(l); }
function setRays(e, row) { const dir = V3(Math.cos(e * D2R), Math.sin(e * D2R), 0); rayLines.forEach((l, i) => { const z = 1.2 + i * 1.6; const tgt = V3(row.xc, row.H + 0.2, z); const a = tgt.clone().addScaledVector(dir, 5.5); l.geometry.setFromPoints([a, tgt]); }); rays.visible = e > 0 && S.rays && SCEN[S.sc].sky === 'clear'; }

/* ---------------- halos ---------------- */
const haloTex = cvTex(128, 128, (g, w, h) => { const gr = g.createRadialGradient(64, 64, 4, 64, 64, 62); gr.addColorStop(0, 'rgba(255,230,120,.95)'); gr.addColorStop(0.45, 'rgba(255,200,60,.35)'); gr.addColorStop(1, 'rgba(255,200,60,0)'); g.fillStyle = gr; g.fillRect(0, 0, w, h); });
const halo = new THREE.Sprite(new THREE.SpriteMaterial({ map: haloTex, transparent: true, depthTest: false, blending: THREE.AdditiveBlending })); halo.visible = false; halo.renderOrder = 10; scene.add(halo);

/* ---------------- state ---------------- */
const S = { tilt: 3, target: 3, speed: 8, sc: 'noon', scName: 'noon', cur: 0, step: 0, playing: false, demoT: 0, demoI: 0, labels: true, rays: true, xray: false, crops: true, motorDir: 0, time: 0, drumRot: 0 };
let amb = { exp: 1.0, top: new THREE.Color(AMB.clear.top), bot: new THREE.Color(AMB.clear.bot), sun: 2.3, hemi: 0.42, fog: new THREE.Color(AMB.clear.fog) }, ambT = AMB.clear;
const travelFlat = th => P.L * (Math.sin((th - 45) * D2R) - Math.sin((P.REST - 45) * D2R));   /* wire travel from flat, metres */
function applyTilt(th) {
  rowsG.forEach(r => { r.g.rotation.z = -th * D2R; });
  scene.updateMatrixWorld(true);
  const tips = rowsG.map(r => r.g.localToWorld(r.tipLocal.clone()));
  updateWire(tips);
  const d = travelFlat(th); S.drumRot = d / (P.DRUM_D / 2);
  drum.rotation.z = S.drumRot; shS1.rotation.z = -d / SH.S1.r * 0; shN.rotation.z = d / SH.N.r;
  const e = SCEN[S.sc].sun; setRays(e, rowsG[1]); tips.forEach((t, i) => rowsG[i].tip = t);
}
function setScenario(k, move) {
  const s = SCEN[k]; S.sc = k; ambT = AMB[s.sky]; const e = s.sun; sun.position.set(5 + 45 * Math.cos(Math.max(e, 3) * D2R), 45 * Math.sin(Math.max(e, 3) * D2R), 5 + 8);
  rainLines.visible = s.rain > 0; windLines.visible = s.wind >= 10; if (move !== false) S.target = s.tilt;
  document.querySelectorAll('[data-sc]').forEach(b => b.classList.toggle('on', b.dataset.sc === k)); $('scText2').textContent = s.text; $('sc-name').textContent = s.name;
}

/* ---------------- camera rig ---------------- */
const CAM = { target: V3(5, 3.5, 5), az: 42 * D2R, el: 20 * D2R, d: 27, fov: 40 };
const VIEWS = {
  overview: { t: [5.4, 3.0, 6.0], az: 42, el: 21, d: 31, label: 'Overview' },
  winch:    { t: [11.5, 2.2, 11.0], az: 38, el: 14, d: 6.2, label: 'Motor and drum' },
  tips:     { t: [4.2, 5.4, 10.4], az: 30, el: 12, d: 9.5, label: 'Lever arms and wire' },
  arm:      { t: [3.75, 5.4, 10.4], az: 18, el: 5, d: 3.2, label: 'One lever arm' },
  bearing:  { t: [3.75, 5.55, 0.0], az: 168, el: 10, d: 3.4, label: 'Rope bearing' },
  side:     { t: [5.0, 3.4, 5.0], az: 0, el: 1, d: 78, fov: 14, label: 'Side section' },
  top:      { t: [5.0, 0, 5.0], az: 0, el: 88, d: 80, fov: 16, label: 'From above' },
  sensors:  { t: [0.6, 8.0, 0.2], az: 50, el: 18, d: 7.5, label: 'Weather mast' },
  ground:   { t: [5.0, 1.8, 5.0], az: 70, el: 8, d: 14, label: 'Crop level' }
};
let camAnim = null;
function goView(k, instant) { const v = VIEWS[k]; if (!v) return; const to = { t: V3(...v.t), az: v.az * D2R, el: v.el * D2R, d: v.d, fov: v.fov || 40 }; document.querySelectorAll('[data-view]').forEach(b => b.classList.toggle('on', b.dataset.view === k)); if (instant) { CAM.target.copy(to.t); CAM.az = to.az; CAM.el = to.el; CAM.d = to.d; CAM.fov = to.fov; camAnim = null; } else camAnim = { from: { t: CAM.target.clone(), az: CAM.az, el: CAM.el, d: CAM.d, fov: CAM.fov }, to, t: 0 }; }
function applyCam() { if (Math.abs(camera.fov - CAM.fov) > 0.01) { camera.fov = CAM.fov; camera.updateProjectionMatrix(); } const ce = Math.cos(CAM.el); camera.position.set(CAM.target.x + CAM.d * ce * Math.sin(CAM.az), CAM.target.y + CAM.d * Math.sin(CAM.el), CAM.target.z + CAM.d * ce * Math.cos(CAM.az)); camera.lookAt(CAM.target); }
{ let mode = null, lx = 0, ly = 0, pinch = 0; const pts = new Map();
  cv.addEventListener('contextmenu', e => e.preventDefault());
  cv.addEventListener('pointerdown', e => { cv.setPointerCapture(e.pointerId); pts.set(e.pointerId, [e.clientX, e.clientY]); lx = e.clientX; ly = e.clientY; mode = (e.button === 2 || e.shiftKey) ? 'pan' : 'orbit'; camAnim = null; if (pts.size === 2) { const a = [...pts.values()]; pinch = Math.hypot(a[0][0] - a[1][0], a[0][1] - a[1][1]); } });
  cv.addEventListener('pointermove', e => { if (!pts.has(e.pointerId)) return; pts.set(e.pointerId, [e.clientX, e.clientY]);
    if (pts.size === 2) { const a = [...pts.values()], d = Math.hypot(a[0][0] - a[1][0], a[0][1] - a[1][1]); CAM.d = Math.min(130, Math.max(1.5, CAM.d * pinch / d)); pinch = d; return; }
    const dx = e.clientX - lx, dy = e.clientY - ly; lx = e.clientX; ly = e.clientY;
    if (mode === 'orbit') { CAM.az -= dx * 0.006; CAM.el = Math.min(1.5, Math.max(-0.05, CAM.el + dy * 0.006)); }
    else { const k = CAM.d * 0.0016, r = V3(Math.cos(CAM.az), 0, -Math.sin(CAM.az)); CAM.target.addScaledVector(r, -dx * k); CAM.target.y += dy * k; } });
  const up = e => { pts.delete(e.pointerId); mode = null; }; cv.addEventListener('pointerup', up); cv.addEventListener('pointercancel', up);
  cv.addEventListener('wheel', e => { e.preventDefault(); camAnim = null; CAM.d = Math.min(130, Math.max(1.5, CAM.d * Math.exp(e.deltaY * 0.0012))); }, { passive: false }); }

/* ---------------- steps, labels, side panel ---------------- */
const STEPS = [
  { k: '1', title: 'Sensors read the weather', view: 'sensors', at: () => V3(P.XN + 0.3, P.HTOP + 2.5, 0), txt: 'Pyranometer (sun power), PAR sensor under the panels (light the crop gets), DHT11 (air temperature and humidity), soil moisture probe, rain sensor and a cup anemometer (wind) on a 3 m mast. Cables run down the column to the cabinet.' },
  { k: '2', title: 'Controller picks the angle', view: 'winch', at: () => V3(12.45, 1.95, 11.2), txt: 'The controller in the weatherproof cabinet runs the SRMC rule: rain = flat 3 deg, night = park 15 deg, wind of 15 m/s or more = stow 90 deg, otherwise the angle (15 to 60 deg) that gives the best mix of electricity and crop light. It sends one target angle to the motor drive.' },
  { k: '3', title: 'Motor and worm gearbox', view: 'winch', at: () => V3(11.45, 1.55, 11.5), txt: 'A 0.25 kW motor (10 kN winch) turns the drum through a self-locking worm gearbox, so the panels stay where they are when the motor stops, even in wind. A brake, limit switches and an angle encoder sit on the other end of the drum shaft.' },
  { k: '4', title: 'Drum winds one wire in, pays one out', view: 'winch', at: () => V3(11.45, 1.45, 10.58), txt: 'The drum (diameter 120 mm) has both ends of the drive wire fastened to it. Turning it one way winds one strand in and pays the other out, so the wire both pulls and pushes: no spring is needed. The whole tilt range takes about 1.1 turns of the drum.' },
  { k: '5', title: 'One drive wire reaches every row', view: 'tips', at: () => V3(2.5, 5.7, P.ZW), txt: 'A single 6 mm stainless 7x19 wire runs from the drum, up the column over two sheaves, and is clamped to the tip of the lever arm of every row. All the rows are moved by the same wire, by the same distance, so they tilt together.' },
  { k: '6', title: 'Sheaves turn the wire around', view: 'tips', at: () => V3(-0.9, 5.15, P.ZW), txt: 'Sheaves (pulleys with a groove for the wire) at both ends send the wire back so it forms a closed loop. The far-end sheave (150 mm radius) turns as the wire moves.' },
  { k: '7', title: 'Lever arm turns pull into rotation', view: 'arm', at: () => rowsG[1].tip ? rowsG[1].tip.clone() : V3(3.75, 5.5, P.ZW), txt: 'Each tube end carries a 0.44 m lever arm fixed at 45 deg. When the wire pulls its tip sideways by d, the tube turns: d = 0.44 x [sin 45 + sin(angle - 45)]. The 45 deg offset keeps a lever of at least 0.31 m even at the 90 deg storm stow.' },
  { k: '8', title: 'Torque tube carries the panels', view: 'bearing', at: () => V3(3.75, rowsG[1].H + 0.02, -0.12), txt: 'A 114 x 4 mm steel tube turns inside bearing rings that are clamped to the carrier rope. Two rails along the tube hold the panels, so the panels turn with the tube like a gate on its hinge.' },
  { k: '9', title: 'Carrier rope holds the weight', view: 'bearing', at: () => V3(3.75, rowsG[1].H - 0.27, 0.0), txt: 'The 16 mm stainless carrier rope spans column to column (sag about span / 12) and carries the tubes and panels. Columns are 200 x 200 mm hollow sections on concrete pads, held by 20 mm stay ropes to buried anchors.' },
  { k: '10', title: 'All panels tilt together', view: 'side', at: () => V3(5.0, rowsG[1].H + 1.0, 2.5), txt: 'All four rows of the 8-panel set tilt by the same angle. Lowest panel edge stays 4.5 m or more above the ground at every angle up to 60 deg, so tractors and people pass underneath and the crop gets light between and beneath the panels.' },
  { k: '11', title: 'Gutter and cistern', view: 'overview', at: () => V3(10.3, 5.95, 2.0), txt: 'When the panels go flat (3 deg), the rows seal together into a roof that drains south into the gutter, then down the pipe into the cistern. That stored water is used for irrigation when the soil probe says the soil is dry.' }
];
const labelBox = $('labels'); STEPS.forEach((st, i) => { const d = document.createElement('div'); d.className = 'lb'; d.textContent = st.k; d.title = st.title; d.onclick = () => selectStep(i); labelBox.appendChild(d); st.el = d; });
const listBox = $('steps'); STEPS.forEach((st, i) => { const d = document.createElement('div'); d.className = 'st'; d.innerHTML = '<b>' + st.k + '</b><div><div class="t">' + st.title + '</div><div class="x">' + st.txt + '</div></div>'; d.onclick = () => selectStep(i); listBox.appendChild(d); st.li = d; });
function selectStep(i) { S.step = i; STEPS.forEach((st, j) => { st.li.classList.toggle('on', j === i); st.el.classList.toggle('on', j === i); }); goView(STEPS[i].view); halo.visible = true; const li = STEPS[i].li; li.scrollIntoView({ block: 'nearest', behavior: 'smooth' }); }
function projectLabels() {
  const w = cv.clientWidth, h = cv.clientHeight, v = V3();
  STEPS.forEach(st => { const p = st.at(); v.copy(p).project(camera); const vis = S.labels && v.z < 1 && Math.abs(v.x) < 1.05 && Math.abs(v.y) < 1.05; st.el.style.display = vis ? 'flex' : 'none'; if (vis) st.el.style.transform = 'translate(' + ((v.x * .5 + .5) * w - 12) + 'px,' + ((-v.y * .5 + .5) * h - 12) + 'px)'; });
}
/* little 2D diagram of the arm */
function drawArm() {
  const c = $('armCv'), g = c.getContext('2d'), w = c.width, h = c.height; g.clearRect(0, 0, w, h);
  const cx = w * 0.62, cy = h * 0.22, s = 190, th = S.tilt * D2R;
  const tip = a => [cx + s * P.L * Math.sin(a - P.OFF) * -1, cy + s * P.L * Math.cos(a - P.OFF)];
  const rest = tip(P.REST * D2R), now = tip(th);
  g.strokeStyle = 'rgba(160,175,190,.5)'; g.setLineDash([4, 4]); g.beginPath(); g.arc(cx, cy, s * P.L, 0, 7); g.stroke(); g.setLineDash([]);
  g.strokeStyle = '#7d8a99'; g.lineWidth = 2; g.setLineDash([5, 4]); g.beginPath(); g.moveTo(cx, cy); g.lineTo(rest[0], rest[1]); g.stroke(); g.setLineDash([]);
  /* panel line */
  const pa = th, dx = Math.cos(pa) * 62, dz = -Math.sin(pa) * 62; g.strokeStyle = '#4f86d6'; g.lineWidth = 6; g.lineCap = 'round'; g.beginPath(); g.moveTo(cx - dx, cy - dz - 0); g.lineTo(cx + dx, cy + dz); g.stroke();
  g.strokeStyle = '#e8edf2'; g.lineWidth = 5; g.beginPath(); g.moveTo(cx, cy); g.lineTo(now[0], now[1]); g.stroke();
  g.fillStyle = '#ffb020'; g.beginPath(); g.arc(now[0], now[1], 6, 0, 7); g.fill(); g.fillStyle = '#e8edf2'; g.beginPath(); g.arc(cx, cy, 6, 0, 7); g.fill();
  const yb = Math.max(rest[1], now[1]) + 22; g.strokeStyle = '#7CFFB2'; g.lineWidth = 3; g.beginPath(); g.moveTo(rest[0], yb); g.lineTo(now[0], yb); g.stroke();
  g.fillStyle = '#7CFFB2'; g.font = '12px system-ui,sans-serif'; g.fillText('d = ' + (travelFlat(S.tilt) * 1000).toFixed(0) + ' mm', Math.min(rest[0], now[0]) - 4, yb + 16);
  g.fillStyle = '#aab6c4'; g.fillText('pivot', cx + 8, cy - 6); g.fillText('wire pulls the tip this way', 8, 16); g.fillText('flat position', rest[0] - 24, rest[1] - 10);
}

/* ---------------- UI ---------------- */
function bind() {
  const sl = $('tilt'); sl.oninput = () => { S.target = +sl.value; S.playing = false; $('play').textContent = 'Play a day'; $('play').classList.remove('on'); };
  document.querySelectorAll('[data-sc]').forEach(b => b.onclick = () => { S.playing = false; $('play').textContent = 'Play a day'; $('play').classList.remove('on'); setScenario(b.dataset.sc); });
  document.querySelectorAll('[data-view]').forEach(b => b.onclick = () => goView(b.dataset.view));
  $('play').onclick = () => { S.playing = !S.playing; S.demoT = 0; S.demoI = 0; $('play').textContent = S.playing ? 'Stop' : 'Play a day'; $('play').classList.toggle('on', S.playing); if (S.playing) setScenario(DEMO[0]); };
  $('tLab').onchange = e => { S.labels = e.target.checked; }; $('tRay').onchange = e => { S.rays = e.target.checked; }; $('tXray').onchange = e => { S.xray = e.target.checked; setXray(S.xray); }; $('tCrop').onchange = e => { cropGroup.visible = e.target.checked; };
  $('speed').oninput = e => { S.speed = +e.target.value; };
  $('info').onclick = () => document.body.classList.toggle('side');
  window.addEventListener('keydown', e => { if (e.key === 'ArrowRight' || e.key === 'ArrowDown') selectStep((S.step + 1) % STEPS.length); if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') selectStep((S.step + STEPS.length - 1) % STEPS.length); });
}
const DEMO = ['night', 'morning', 'noon', 'hot', 'rain', 'noon', 'storm', 'night'];

/* ---------------- loop ---------------- */
function resize() { const w = cv.parentElement.clientWidth, h = cv.parentElement.clientHeight; renderer.setSize(w, h, false); cv.style.width = w + 'px'; cv.style.height = h + 'px'; camera.aspect = w / h; camera.updateProjectionMatrix(); }
window.addEventListener('resize', resize);
const ease = t => t < .5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;
function step(dt) {
  S.time += dt;
  if (S.playing) { S.demoT += dt; if (S.demoT > 5.2) { S.demoT = 0; S.demoI = (S.demoI + 1) % DEMO.length; setScenario(DEMO[S.demoI]); } }
  /* tilt motion */
  const diff = S.target - S.tilt; S.motorDir = 0;
  if (Math.abs(diff) > 0.01) { const mv = Math.min(Math.abs(diff), S.speed * dt) * Math.sign(diff); S.tilt += mv; S.motorDir = Math.sign(diff); if (Math.abs(S.target - S.tilt) < 0.02) S.tilt = S.target; applyTilt(S.tilt); $('tilt').value = Math.round(S.tilt); }
  fanG.rotation.z -= S.motorDir * dt * 30; moveDots(S.motorDir, S.time);
  cups.rotation.y += dt * (0.5 + SCEN[S.sc].wind * 1.6);
  /* ambience */
  const k = 1 - Math.exp(-dt * 3); amb.exp += (ambT.exp - amb.exp) * k; amb.sun += (ambT.sun - amb.sun) * k; amb.hemi += (ambT.hemi - amb.hemi) * k; amb.top.lerp(new THREE.Color(ambT.top), k); amb.bot.lerp(new THREE.Color(ambT.bot), k); amb.fog.lerp(new THREE.Color(ambT.fog), k);
  fillA.intensity = 0.32 * amb.hemi / 0.42; fillB.intensity = 0.22 * amb.hemi / 0.42; fillC.intensity = 0.2 * amb.hemi / 0.42; renderer.toneMappingExposure = amb.exp; sun.intensity = amb.sun; hemi.intensity = amb.hemi; skyU.top.value.copy(amb.top); skyU.bot.value.copy(amb.bot); scene.fog.color.copy(amb.fog);
  /* particles */
  if (rainLines.visible) { const a = rainGeo.attributes.position.array; for (let i = 0; i < NR; i++) { const dy = rv[i] * dt; a[i * 6 + 1] -= dy; a[i * 6 + 4] -= dy; if (a[i * 6 + 4] < 0) { a[i * 6 + 1] += 12; a[i * 6 + 4] += 12; } } rainGeo.attributes.position.needsUpdate = true; }
  if (windLines.visible) { const a = windGeo.attributes.position.array; for (let i = 0; i < NW; i++) { const dz = -wv[i] * 14 * dt; a[i * 6 + 2] += dz; a[i * 6 + 5] += dz; if (a[i * 6 + 5] < -5) { a[i * 6 + 2] += 20; a[i * 6 + 5] += 20; } } windGeo.attributes.position.needsUpdate = true; }
  /* camera */
  if (camAnim) { camAnim.t = Math.min(1, camAnim.t + dt / 1.3); const e = ease(camAnim.t), f = camAnim.from, t = camAnim.to; CAM.target.lerpVectors(f.t, t.t, e); let da = t.az - f.az; da = Math.atan2(Math.sin(da), Math.cos(da)); CAM.az = f.az + da * e; CAM.el = f.el + (t.el - f.el) * e; CAM.d = f.d + (t.d - f.d) * e; CAM.fov = f.fov + (t.fov - f.fov) * e; if (camAnim.t >= 1) camAnim = null; }
  applyCam();
  /* halo */
  if (halo.visible) { const p = STEPS[S.step].at(); halo.position.copy(p); const sc = (0.7 + 0.12 * Math.sin(S.time * 4)) * Math.max(0.5, CAM.d / 10); halo.scale.set(sc, sc, 1); }
  /* readouts */
  const d = travelFlat(S.tilt);
  $('rTilt').textContent = S.tilt.toFixed(1) + '°'; $('rD').textContent = (d * 1000).toFixed(0) + ' mm'; $('rTurns').textContent = (d / (Math.PI * P.DRUM_D)).toFixed(2);
  $('rMotor').textContent = S.motorDir > 0 ? 'running: tilting up' : S.motorDir < 0 ? 'running: tilting down' : 'stopped, held by worm gear and brake';
  const e = SCEN[S.sc].sun, inc = Math.sin((S.tilt + e) * D2R); $('rInc').textContent = e > 0 ? Math.max(0, inc * 100).toFixed(0) + ' %' : 'no sun';
  $('rWind').textContent = SCEN[S.sc].wind.toFixed(0) + ' m/s';
  drawArm(); projectLabels();
}
let last = performance.now();
function frame(now) { const dt = Math.min(0.05, (now - last) / 1000); last = now; step(dt); renderer.render(scene, camera); requestAnimationFrame(frame); }

/* ---------------- start ---------------- */
bind(); resize(); applyTilt(S.tilt); setScenario(Q.get('sc') && SCEN[Q.get('sc')] ? Q.get('sc') : 'noon', false);
S.tilt = S.target = SCEN[S.sc].tilt; applyTilt(S.tilt); $('tilt').value = S.tilt;
if (Q.get('tilt')) { S.tilt = S.target = +Q.get('tilt'); applyTilt(S.tilt); $('tilt').value = S.tilt; }
goView(VIEWS[Q.get('view')] ? Q.get('view') : 'overview', true);
if (Q.get('step')) { selectStep(+Q.get('step')); goView(Q.get('view') || STEPS[+Q.get('step')].view, true); } else { halo.visible = false; STEPS[0].li.classList.add('on'); }
if (Q.get('xray') === '1') { $('tXray').checked = true; S.xray = true; setXray(true); }
if (Q.get('ui') === '0') { document.body.classList.add('clean'); resize(); }
if (Q.get('lab') === '0') { S.labels = false; $('tLab').checked = false; }
if (Q.get('play') === '1') $('play').click();
amb.exp = ambT.exp; amb.sun = ambT.sun; amb.hemi = ambT.hemi; amb.top.set(ambT.top); amb.bot.set(ambT.bot); amb.fog.set(ambT.fog);
window.__srmc = { S, CAM, setScenario, goView, selectStep, step, applyTilt, render: () => renderer.render(scene, camera), renderer, scene, camera };
/* ---- optional offline video recording: ?record=1&port=8767 posts JPEG frames to a local helper (make_mechanism_video.py) ---- */
async function record() {
  const W = 1280, H = 720, FPS = 24, port = Q.get('port') || 8767; renderer.setPixelRatio(1); renderer.setSize(W, H, false); camera.aspect = W / H; camera.updateProjectionMatrix();
  const out = document.createElement('canvas'); out.width = W; out.height = H; const g = out.getContext('2d');
  const KEY = [
    { t: 0,  view: 'overview', sc: 'noon', tilt: 18, cap: 'The whole canopy: four rows of panels hang from stainless carrier ropes between columns. One motor tilts all of them.' },
    { t: 5,  view: 'winch', sc: 'morning', tilt: 45, cap: 'Step 1: the controller sends a target angle. The motor and self-locking worm gearbox turn the drum.' },
    { t: 11, view: 'winch', sc: 'noon', tilt: 18, cap: 'Step 2: the drum winds one end of the wire in and pays the other out. The wire is a closed loop, so it pulls both ways.' },
    { t: 16, view: 'tips', sc: 'morning', tilt: 45, cap: 'Step 3: one 6 mm wire runs over sheaves and is clamped to the tip of a lever arm on every row.' },
    { t: 22, view: 'arm', sc: 'hot', tilt: 60, cap: 'Step 4: the wire pulls the arm tip sideways, the arm turns the tube. d = 0.44 m x [sin 45 + sin(angle - 45)].' },
    { t: 28, view: 'arm', sc: 'noon', tilt: 18, cap: 'Reverse: the drum turns back, the wire pulls the tip the other way and the panels tilt down.' },
    { t: 33, view: 'side', sc: 'morning', tilt: 45, cap: 'Side section: all rows tilt together by the same angle; the lowest edge stays above 4.5 m.' },
    { t: 38, view: 'bearing', sc: 'hot', tilt: 55, cap: 'The tube turns inside bearing rings clamped on the carrier rope. Panels are bolted on rails along the tube.' },
    { t: 44, view: 'overview', sc: 'rain', tilt: 3, cap: 'Rain sensor wet: panels go flat (3 deg), the roof seals and the water runs to the gutter and cistern.' },
    { t: 50, view: 'tips', sc: 'storm', tilt: 90, cap: 'Anemometer reads 15 m/s or more: panels stow edge-on at 90 deg so the wind passes through.' },
    { t: 57, view: 'overview', sc: 'noon', tilt: 18, cap: 'Wind drops below 12 m/s: back to normal tracking. Design model, not a built system.' }
  ], TOTAL = 63; S.speed = 14;
  const FROM = +Q.get('from') || 0; let ki = -1; const N = (+Q.get('secs') || TOTAL) * FPS;
  for (let f = 0; f < N; f++) {
    const t = f / FPS; while (ki + 1 < KEY.length && KEY[ki + 1].t <= t) { ki++; const k = KEY[ki]; setScenario(k.sc, false); S.target = k.tilt; goView(k.view); }
    step(1 / FPS); if (!camAnim) CAM.az += 0.0016; if (f < FROM) continue; applyCam(); renderer.render(scene, camera);
    g.drawImage(cv, 0, 0, W, H);
    g.fillStyle = 'rgba(8,14,22,.78)'; g.fillRect(0, H - 86, W, 86); g.fillStyle = '#ffb020'; g.font = '600 18px system-ui,Segoe UI,sans-serif'; g.fillText('Agrovoltaic Canopy for Protection and Sustainable Farming: tilt mechanism', 24, H - 58);
    g.fillStyle = '#fff'; g.font = '20px system-ui,Segoe UI,sans-serif'; const cap = KEY[Math.max(0, ki)].cap; const words = cap.split(' '); let line = '', y = H - 30; words.forEach(w => { const test = line + w + ' '; if (g.measureText(test).width > W - 60 && line) { g.fillText(line, 24, y); line = w + ' '; y += 24; } else line = test; }); g.fillText(line, 24, y);
    const d = travelFlat(S.tilt); g.fillStyle = 'rgba(8,14,22,.78)'; g.fillRect(W - 300, 16, 284, 112); g.fillStyle = '#9fb0c4'; g.font = '14px system-ui,sans-serif'; g.fillText('PANEL TILT', W - 286, 40); g.fillStyle = '#ffb020'; g.font = '600 34px system-ui,sans-serif'; g.fillText(S.tilt.toFixed(1) + '°', W - 286, 76);
    g.fillStyle = '#e8eef5'; g.font = '15px system-ui,sans-serif'; g.fillText('wire moved ' + (d * 1000).toFixed(0) + ' mm   drum ' + (d / (Math.PI * P.DRUM_D)).toFixed(2) + ' turns', W - 286, 100); g.fillText(S.motorDir ? 'motor running' : 'motor stopped, gear holds', W - 286, 120);
    const blob = await new Promise(r => out.toBlob(r, 'image/jpeg', 0.9)); await fetch('http://localhost:' + port + '/f/' + f, { method: 'POST', body: blob });
  }
  await fetch('http://localhost:' + port + '/done', { method: 'POST', body: 'x' }); document.title = 'RECORD DONE';
}
if (Q.get('record')) { record(); } else requestAnimationFrame(frame);
})();
