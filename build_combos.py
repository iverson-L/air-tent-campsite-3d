#!/usr/bin/env python3
"""Generate the combined tent pages from the single-model sandboxes.

    python3 build_combos.py

Writes block10_05.html (Block 10 + Block 05, sofa in Block 10) and block10_09_05.html (Block 10 + 09 + 05).
Each model's code (dimensions → helpers → builder) is copied verbatim from its own file into its own closure,
so the files' identically named constants/helpers don't clash. Re-run after editing any source model.

Layout (per block10+05.png and the YAMATO 9+10+5 photo):
  Block 10  at the origin, gable entrance facing +z.
  Block 05  on Block 10's +x side, turned to face it, centred along Block 10's length, standing 15 cm off the wall
            (slider) and joined by the expandable, velcroed connection cloth (makeDockCloth) over Block 10's
            opened side window. index.html uses the same 15 cm cloth (fixed, no slider).
  Block 09  end-to-end behind Block 10 (−z): same 360 × 245 profile, ridges in line, its entrance gable against
            Block 10's back gable.
"""
import re
from pathlib import Path

HERE = Path(__file__).parent


def section(path, start, end):
    s = (HERE / path).read_text()
    i = s.index(start)
    j = s.index(end, i)
    return s[i:j]


def edit(code, old, new, label):
    assert code.count(old) == 1, f"{label}: anchor not found exactly once: {old[:60]!r}"
    return code.replace(old, new)


OPEN_BACK_GABLE = """    if (s === -1 && OPTS.openBack) {
      // GENERATED (OPTS.openBack): back gable WIDE OPEN into Block 09 (per user) — the flat panel keeps its rim
      // but has the same door opening as the front entrance (doorPts), with no mesh, zip or door rolls; keeps the
      // 16 cm fabric sill at floor level (per user — looks more natural than opening it to the floor)
      const shape = new THREE.Shape(archPts(RAKE_R - PANEL_TUCK));
      shape.holes.push(new THREE.Path(doorPts()));
      const cap = new THREE.Mesh(new THREE.ExtrudeGeometry(shape, { depth: FACING_D, bevelEnabled: false }), matCanvas);
      cap.rotation.y = Math.PI;
      cap.position.z = -(hd - FACING_D); // outer face exactly on the rim plane
      cap.castShadow = cap.receiveShadow = true;
      g.add(cap);
      continue;
    }
"""


DOCK_OPEN_SIDE = """    if (s === 1 && OPTS.dockOpen) {
      // GENERATED (OPTS.dockOpen): the +x side opens into Block 05's connection cloth (per block10+05.png) — the
      // mesh and storm flap are unzipped and rolled up TOGETHER into one thick roll just under the eave (2 straps,
      // per user max 2 ties). The cloth's top edge is velcroed onto the wall right beneath the roll (userData.dock).
      const rollR = 0.055, rollY = WALL_Y1 - 0.01, rollX = hw - rollY * LEAN + rollR + 0.003, zr = WIN_HZ + 0.08;
      const roll = new THREE.Mesh(makeTube([new THREE.Vector3(rollX, rollY, -zr), new THREE.Vector3(rollX, rollY, zr)],
        rollR, 0.16, 24, 0.12), matCanvas);
      roll.castShadow = roll.receiveShadow = true;
      g.add(roll);
      for (const zs of [-1, 1]) {
        const STRAP_GAP = 1.6; // ring open where the roll rests on the zero-thickness wall
        const strap = new THREE.Mesh(new THREE.TorusGeometry(rollR * 1.14, 0.005, 6, 28, Math.PI * 2 - STRAP_GAP), matTrim);
        strap.rotation.z = Math.PI + LEAN_RAD + STRAP_GAP / 2;
        strap.position.set(rollX, rollY, zs * zr * 0.6);
        g.add(strap);
      }
      g.userData.dock = { hw, LEAN, y: rollY - rollR - 0.012, zr };
      continue;
    }
"""


# helper injected into every model: drop the triangles of a mesh whose centroid satisfies drop(cx, cz)
CUT_HELPER = """// GENERATED: remove a mesh's triangles whose centroid (x, z) satisfies drop(cx, cz) — used to take the snow skirt
// away where two tents meet, so it doesn't show inside through the joint / mesh / doorway
function cutTris(mesh, drop) {
  const g0 = mesh.geometry, p = g0.attributes.position;
  const idx = g0.index ? Array.from(g0.index.array) : [...Array(p.count).keys()];
  const keep = [];
  for (let i = 0; i < idx.length; i += 3) {
    let cx = 0, cz = 0;
    for (let k = 0; k < 3; k++) { cx += p.getX(idx[i + k]) / 3; cz += p.getZ(idx[i + k]) / 3; }
    if (!drop(cx, cz)) keep.push(idx[i], idx[i + 1], idx[i + 2]);
  }
  g0.setIndex(keep);
}

"""


def add_cut_helper(code, label):
    anchor = "// ---------- tent builder" if "// ---------- tent builder" in code else "// ---------- Block 05 builder"
    return edit(code, anchor, CUT_HELPER + "let OPTS = {}; // GENERATED: per-instance build options (set by the returned builder)\n" + anchor, label)


def expose_lantern(code, label):
    # night mode hooks: the lantern light + its glow material on the tent group
    return edit(code, "      lamp.add(light, light.target);\n",
                "      lamp.add(light, light.target);\n      g.userData.lantern = light; g.userData.lanternGlow = matGlow; // GENERATED\n", label)


def gable_tent(path):
    """Block 10 / Block 09 code → a builder `o => group` with runtime options:
      o.docked    — Block 05 docks on the +x side wall: no storm flap / snow skirt there
      o.bed       — false removes the air bed (that Block 10 gets the sofa)
      o.openBack  — back gable is an open doorway frame (no mesh/zip/rolls), skirt cut across the joint
      o.openFront — entrance keeps only its frame panel (faces another tent), skirt cut across the joint
      o.dockOpen  — the +x side window is opened into a connection cloth: mesh + storm flap rolled up together
                    under the eave; exposes userData.dock (where the cloth velcros on) for makeDockCloth"""
    code = section(path, "// ---------- Block", "// (interior light now lives")
    code = add_cut_helper(code, path)
    code = expose_lantern(code, path)
    code = edit(code, "    // rolled storm flap (refined,",
                "    if (s === 1 && OPTS.docked) continue; // GENERATED: +x side docked to Block 05 — no storm flap\n"
                "    // rolled storm flap (refined,", path)
    code = edit(code, "    g.add(skirt);\n",
                "    cutTris(skirt, (cx, cz) => // GENERATED: no snow skirt where tents meet\n"
                "      (OPTS.docked && cx > hw - 0.12 && Math.abs(cz) < 1.22) ||      // Block 05's 240 cm docking face\n"
                "      (OPTS.openBack && cz < -(hd - 0.12) && Math.abs(cx) < 1.62) ||  // gable joint behind\n"
                "      (OPTS.openFront && cz > hd - 0.12 && Math.abs(cx) < 1.62));     // gable joint in front\n"
                "    g.add(skirt);\n", path)
    code = edit(code, "    // fine see-through screen (same as the gable door): overlaps the hole edge by 1 cm and sits\n",
                DOCK_OPEN_SIDE + "    // fine see-through screen (same as the gable door): overlaps the hole edge by 1 cm and sits\n", path)
    code = edit(code, "    if (s === -1) {\n", OPEN_BACK_GABLE + "    if (s === -1) {\n", path)
    code = edit(code, "    g.add(panel);\n",
                "    g.add(panel);\n"
                "    if (OPTS.openFront) continue; // GENERATED: entrance wide open into another tent — no mesh / zip / rolls\n", path)
    i = code.index("  // Inflatable air bed")
    j = code.index("  // Gable ends: the body")
    code = code[:i] + "  if (OPTS.bed !== false) { // GENERATED: o.bed === false → no bed (that Block 10 has the sofa)\n" + code[i:j] + "  }\n\n" + code[j:]
    # builder; the shared helpers are exposed so layouts can build joint pieces with the tent's own profile/fabric
    return code + ("\nreturn (o = {}) => {\n  OPTS = o;\n  const tent = buildTent(0, -1);\n"
                   "  Object.assign(tent.userData, { archPts, makeTube, matCanvas, matTrim, matGableMesh, matTentFloor });\n  return tent;\n};\n")


def block05():
    code = section("block05.html", "// ---------- Block 05 dimensions", "// (interior light now lives")
    code = add_cut_helper(code, "block05")
    code = expose_lantern(code, "block05")
    code = edit(code, "    g.add(skirt);\n",
                "    if (OPTS.docked) cutTris(skirt, (cx, cz) => cx > XF - 0.12 && Math.abs(cz) < hd - 0.03); // GENERATED: docked door wall — no skirt\n"
                "    g.add(skirt);\n", "block05")
    # canopy 5 cm deeper so the porch wing edge reaches Block 10's leaning wall at the top (no light slit)
    code = edit(code, "const VISOR = 0.25;", "const VISOR = 0.30; // docked: reaches Block 10's leaning wall (no slit at the joint)", "block05")
    # builder: o.docked — docked on a Block 10 side wall (no snow skirt along its door wall)
    # (userData.dock: its porch geometry, for makeDockCloth)
    return code + ("\nreturn (o = {}) => { OPTS = o; const b = buildBlock05(); b.userData.matGableMesh = matGableMesh;\n"
                   "  b.userData.dock = { XF, XT, hd, RAKE_R, roofY }; return b; };\n")


def sofa():
    code = section("sofa_mock.html", "// ---------- dimensions (per sofa_1.png)", "// ---------- grounding")
    return code + "\nreturn buildSofa;\n"


def closure(name, code):
    body = "\n".join("  " + line if line else line for line in code.splitlines())
    return f"const {name} = (() => {{\n{body}\n}})();\n"


HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>{title}</title>
<style>
  html, body {{ margin: 0; height: 100%; overflow: hidden; background: #e8eaed; font-family: system-ui, sans-serif; }}
  #app {{ width: 100%; height: 100%; }}
  #hint {{ position: absolute; top: 12px; left: 12px; z-index: 10; background: rgba(255,255,255,.85);
    border-radius: 8px; padding: 8px 12px; font-size: 12px; color: #444; box-shadow: 0 2px 10px rgba(0,0,0,.15); }}
  #gapUI {{ position: absolute; top: 52px; left: 12px; z-index: 10; display: flex; align-items: center; gap: 8px;
    background: rgba(255,255,255,.85); border-radius: 8px; padding: 6px 12px; font-size: 12px; color: #444;
    box-shadow: 0 2px 10px rgba(0,0,0,.15); }}
  #gapUI b {{ min-width: 3.2em; }}
</style>
<script type="importmap">
{{
  "imports": {{
    "three": "https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js",
    "three/addons/": "https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/"
  }}
}}
</script>
</head>
<body>
<div id="hint">{hint} GENERATED by build_combos.py — edit the single-model files, then re-run it.</div>
<div id="app"></div>

<script type="module">
// GENERATED by build_combos.py from {sources}. Do not edit by hand — edit the source model and re-run.
import * as THREE from 'three';
import {{ OrbitControls }} from 'three/addons/controls/OrbitControls.js';
import {{ RoundedBoxGeometry }} from 'three/addons/geometries/RoundedBoxGeometry.js';

// ---------- scene rig (same as the single-model mocks) ----------
const renderer = new THREE.WebGLRenderer({{ antialias: true }});
renderer.setSize(innerWidth, innerHeight);
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
document.getElementById('app').appendChild(renderer.domElement);

const scene = new THREE.Scene();
scene.background = new THREE.Color(0xe8eaed);

const camera = new THREE.PerspectiveCamera(45, innerWidth / innerHeight, 0.1, 200);
camera.position.set({cam});
const controls = new OrbitControls(camera, renderer.domElement);
controls.target.set({target});
controls.update();

scene.add(new THREE.HemisphereLight(0xdfe8f2, 0x8f928a, 1.45));
const sun = new THREE.DirectionalLight(0xfff4e0, 1.25);
sun.position.set(8, 12, 6);
sun.castShadow = true;
sun.shadow.mapSize.set(4096, 4096);                 // bigger area than a single tent → more texels
sun.shadow.camera.left = -7; sun.shadow.camera.right = 7;
sun.shadow.camera.top = 7; sun.shadow.camera.bottom = -7;
// tight depth range (the default 0.5–500 m makes the bias ~20 cm and light leaks under the wall bases)
sun.shadow.camera.near = 8; sun.shadow.camera.far = 24;
sun.shadow.bias = -0.0002; sun.shadow.normalBias = 0.01;
scene.add(sun);

"""

TAIL = """
// ---------- grounding (no visible ground surface, like the single mocks) ----------
const shadowCatcher = new THREE.Mesh(new THREE.PlaneGeometry(40, 40), new THREE.ShadowMaterial({ opacity: 0.18 }));
shadowCatcher.rotation.x = -Math.PI / 2;
shadowCatcher.receiveShadow = true;
scene.add(shadowCatcher);
// soft contact shadow under each footprint
const blobTex = (() => {
  const c = document.createElement('canvas');
  c.width = c.height = 256;
  const ctx = c.getContext('2d');
  ctx.fillStyle = '#000'; ctx.fillRect(0, 0, 256, 256); // alphaMap reads GREEN: black = clear
  ctx.filter = 'blur(18px)';
  ctx.fillStyle = 'rgb(140,140,140)';
  ctx.fillRect(40, 40, 176, 176);
  return new THREE.CanvasTexture(c);
})();
function contactShadow(cx, cz, w, d) {
  const m = new THREE.Mesh(new THREE.PlaneGeometry(w * 1.45, d * 1.55),
    new THREE.MeshBasicMaterial({ color: 0x000000, alphaMap: blobTex, transparent: true, depthWrite: false }));
  m.rotation.x = -Math.PI / 2;
  m.position.set(cx, 0.001, cz);
  scene.add(m);
  return m;
}

{layout}

// debug handles (for MCP / console testing)
window.__scene = scene;
window.__camera = camera;
window.__controls = controls;
window.__renderer = renderer;

addEventListener('resize', () => {
  camera.aspect = innerWidth / innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(innerWidth, innerHeight);
});

renderer.setAnimationLoop(() => {
  controls.update();
  renderer.render(scene, camera);
});
</script>
</body>
</html>
"""

LAYOUT_10 = """
// Block 10 at the origin (entrance +z)
scene.add(block10);
contactShadow(0, 0, 3.6, 2.8);
"""
LAYOUT_SOFA = """
// sofa (sofa_mock.html) in Block 10, back against the closed back gable, facing the entrance
sofa.position.set(0, 0.003, -1.40 + 0.05 + 0.55);
scene.add(sofa);
"""
# 3-tent page: Block 10's back is a walkway into Block 09, so the sofa goes against Block 10's −x side wall, facing
# +x (Block 05's doorway). Its backrest top (0.9 m, 51.5 cm behind the sofa centre) clears the 11° leaning wall
# (x = −1.80 + 0.9·tan11° = −1.625) by 2 cm; centred along the length, clear of the corner pillars (|z| > 1.08).
LAYOUT_SOFA_SIDE = """
// sofa (sofa_mock.html) against Block 10's −x side wall, facing Block 05 (+x)
sofa.rotation.y = Math.PI / 2;
sofa.position.set(-1.07, 0.003, 0);
scene.add(sofa);
"""
# Connection cloth over the 10↔09 joint (per user): the two tents' rounded rake edges leave an open V-groove all
# round the outside of the joint. A fabric band follows the full silhouette floor → over the ridge → floor,
# 30 cm wide (covers both 12 cm rake curls + 3 cm onto each shell), 6 mm proud at the centre line and tucked to
# 2 mm at its edges, with a dark binding strip along both edges.
JOINT_CLOTH_FN = """
// connection cloth over the Block 10 ↔ Block 09 gable joint, in Block 10's local space (joint plane z = −1.401)
function makeJointCloth(block10) {
  const grp = new THREE.Group();
  const { archPts, makeTube, matCanvas, matTrim } = block10.userData;
  const ZJ = -1.401, HALF = 0.15, NZ = 9;                         // joint plane z, band half-width, stations across
  const path = archPts(-0.002, 0, 16);                            // outer silhouette (2 mm out), foot → ridge → foot
  const pts = [path[0]];
  for (let i = 1; i < path.length; i++) {                          // resample ≤ 5 cm so the band bends smoothly
    const a = path[i - 1], b = path[i], n = Math.max(1, Math.ceil(a.distanceTo(b) / 0.05));
    for (let k = 1; k <= n; k++) pts.push(a.clone().lerp(b, k / n));
  }
  const nrm = pts.map((p, i) => {                                  // outward normal of the path (right foot → left foot)
    const a = pts[Math.max(0, i - 1)], b = pts[Math.min(pts.length - 1, i + 1)];
    const t = b.clone().sub(a).normalize();
    return new THREE.Vector2(t.y, -t.x);
  });
  const pos = [], uv = [], idx = [];
  let u = 0;
  pts.forEach((p, i) => {
    if (i > 0) u += p.distanceTo(pts[i - 1]);
    for (let k = 0; k < NZ; k++) {
      const f = k / (NZ - 1) * 2 - 1, off = 0.002 + 0.004 * (1 - f * f); // tucked edges, slightly proud centre
      pos.push(p.x + nrm[i].x * off, p.y + nrm[i].y * off, ZJ + f * HALF);
      uv.push(u, f * HALF);
    }
  });
  for (let i = 0; i < pts.length - 1; i++) for (let k = 0; k < NZ - 1; k++) {
    const a = i * NZ + k, b = a + NZ;
    idx.push(a, b, a + 1, a + 1, b, b + 1);
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  geo.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
  geo.setIndex(idx);
  geo.computeVertexNormals();
  const cloth = new THREE.Mesh(geo, matCanvas);
  cloth.castShadow = cloth.receiveShadow = true;
  grp.add(cloth);
  for (const f of [-1, 1]) {                                       // binding along both edges
    const edge = pts.map((p, i) => new THREE.Vector3(p.x + nrm[i].x * 0.003, p.y + nrm[i].y * 0.003, ZJ + f * (HALF - 0.004)));
    const bind = new THREE.Mesh(makeTube(edge, 0.004, 0, 8), matTrim);
    grp.add(bind);
  }
  return grp;
}
"""
LAYOUT_JOINT_CLOTH = JOINT_CLOTH_FN + """
scene.add(makeJointCloth(block10));
"""
LAYOUT_09 = """
// Block 09 end-to-end behind Block 10: its entrance gable (+z) 2 mm from Block 10's back gable (a 1 cm gap let a
// line of light through the joint), ridges in line
block09.position.set(0, 0, -1.40 - 0.002 - 1.25);
scene.add(block09);
contactShadow(0, -2.66, 3.6, 2.5);
"""

DOCK_CLOTH_FN = """
// EXPANDABLE connection cloth between Block 10's opened +x side and a docked Block 05 (per block10+05.png): a slack
// fabric tunnel. Its top is velcroed onto Block 10's wall right under the rolled-up side (block10.userData.dock) and slopes
// down onto Block 05's canopy tip; its sides drop to the ground along Block 05's leaning porch-wing edges. Built
// from both tents' CURRENT placement, so it stretches to whatever gap Block 05 stands at. Taut and smooth — a straight
// slope with no wrinkles or sag (per user). A PVC ground sheet joins the two floors.
function makeDockCloth(block10, block05) {
  const grp = new THREE.Group();
  const { makeTube, matCanvas, matTentFloor } = block10.userData;
  const A = block10.userData.dock, B = block05.userData.dock;
  block10.updateMatrixWorld(true); block05.updateMatrixWorld(true);
  const zAxis = g => new THREE.Vector3(0, 0, 1).transformDirection(g.matrixWorld);
  const zW = zAxis(block10), flip = zAxis(block05).dot(zW) < 0 ? -1 : 1; // Block 05 turned π → its z runs backwards
  // U-shaped section (−z foot → up → over the rounded top → down → +z foot) in 5 parts, with the SAME u breakpoints
  // at both ends so the corners loft into each other. sect() → [z, y, nz, ny] (n = the section's outward normal).
  const tipY = B.roofY(B.XT);
  // flat on Block 10's leaning wall; sides 6 cm past the roll ends so they cover the cut end of Block 10's snow skirt
  // (at +3 cm a small notch showed at the ground between the cloth and the skirt, per user)
  const secA = { Z: A.zr + 0.06, H: A.y, r: 0.12 };
  const parts = s => [s.H - s.r, Math.PI * s.r / 2, 2 * (s.Z - s.r), Math.PI * s.r / 2, s.H - s.r];
  const LA = parts(secA), TOT = LA.reduce((a, b) => a + b), BRK = [0];
  LA.forEach(l => BRK.push(BRK[BRK.length - 1] + l / TOT));
  const sect = (s, u) => {
    let i = 0;
    while (i < 4 && u > BRK[i + 1]) i++;
    const t = (u - BRK[i]) / (BRK[i + 1] - BRK[i]), cY = s.H - s.r, cZ = s.Z - s.r;
    if (i === 0) return [-s.Z, t * cY, -1, 0];
    if (i === 4) return [s.Z, (1 - t) * cY, 1, 0];
    if (i === 2) return [-cZ + 2 * cZ * t, s.H, 0, 1];
    const a = i === 1 ? Math.PI - t * Math.PI / 2 : Math.PI / 2 - t * Math.PI / 2;
    return [(i === 1 ? -cZ : cZ) + s.r * Math.cos(a), cY + s.r * Math.sin(a), Math.cos(a), Math.sin(a)];
  };
  const endA = (u, out = 0.004, grow = 0) => {
    const [z, y] = sect(grow ? { Z: secA.Z + grow, H: secA.H + grow, r: secA.r + grow } : secA, u);
    return block10.localToWorld(new THREE.Vector3(A.hw - y * A.LEAN + out, y, z)); };
  // Block 05 end, `back` m behind its porch edge (canopy tip / leaning wing edges), `off` m proud of its surface:
  // sides on the wing faces, top on the sloped roof, corners round the roof's RAKE_R curl
  const endB = (u, off, back) => {
    const sec = { Z: B.hd + off, H: B.roofY(B.XT - back) + off, r: B.RAKE_R + off };
    const [z, y] = sect(sec, u), k = Math.min(y / tipY, 1);
    return block05.localToWorld(new THREE.Vector3(B.XF + (B.XT - B.XF) * k - back, y, flip * z));
  };
  // rows: Block 10 velcro line → straight span → just over the canopy tip hem → LAPPED 5 cm onto Block 05's roof and wing
  // faces. (Ending at the tip left a few-mm slit between the cloth edge and the roof that showed the sky, per user.)
  // ...and at Block 10 the cloth LAPS 3.5 cm onto the wall, 1.5 mm off it (it used to stand 4 mm off the wall with
  // a raw edge: looking along the wall you could see through that slit — per user)
  const LAP = 0.05, LAP_A = 0.035, A_OFF = 0.0015, NU = 160, NV = 4, ROWS = NV + 3;
  const y0 = endA(0).y;                                       // ground level of the tents (index.html lifts them)
  const gap = endA(0.5).distanceTo(endB(0.5, 0.012, 0));
  const pos = [], uv = [], idx = [];
  for (let i = 0; i <= NU; i++) {
    const u = i / NU, a = endA(u, A_OFF), b = endB(u, 0.012, 0), arc = u * TOT;
    const row = [endA(u, A_OFF, LAP_A), ...Array.from({ length: NV + 1 }, (_, j) => a.clone().lerp(b, j / NV)), endB(u, 0.004, LAP)];
    row.forEach((p, j) => {
      pos.push(p.x, Math.max(p.y, y0), p.z);
      uv.push(arc, j === 0 ? -LAP_A : j <= NV + 1 ? (j - 1) / NV * gap : gap + LAP);
    });
  }
  for (let i = 0; i < NU; i++) for (let j = 0; j < ROWS - 1; j++) {
    const a = i * ROWS + j, b = a + ROWS;
    idx.push(a, b, a + 1, a + 1, b, b + 1);
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  geo.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
  geo.setIndex(idx);
  geo.computeVertexNormals();
  // faces must point OUTWARD (as onWall): an inward face self-shadows through the shadow normalBias
  const mid = (NU / 2) * ROWS + 1 + NV / 2;
  if (geo.attributes.normal.getY(mid) < 0) {
    for (let k = 0; k < idx.length; k += 3) [idx[k + 1], idx[k + 2]] = [idx[k + 2], idx[k + 1]];
    geo.setIndex(idx);
    geo.computeVertexNormals();
  }
  const cloth = new THREE.Mesh(geo, matCanvas);
  cloth.castShadow = cloth.receiveShadow = true;
  grp.add(cloth);

  // no zip lines (per user): the cloth is VELCROED onto Block 10, so its edges show no trim. Hems along the ground.
  const line = (f, n = 90) => Array.from({ length: n + 1 }, (_, i) => f(i / n));
  for (const i of [0, NU]) {
    const hem = line(v => { const k = (i * ROWS + 1 + Math.round(v * NV)) * 3; return new THREE.Vector3(pos[k], y0 + 0.008, pos[k + 2]); }, NV);
    const t = new THREE.Mesh(makeTube(hem, 0.008, 0, 10, 0.02), matCanvas);
    t.castShadow = true;
    grp.add(t);
  }
  // ground sheet joining the two bathtub floors
  const fl = [endA(0), endA(1), endB(1, 0, 0), endB(0, 0, 0)].map(p => new THREE.Vector3(p.x, y0 + 0.003, p.z));
  const fg = new THREE.BufferGeometry().setFromPoints([fl[0], fl[2], fl[1], fl[0], fl[3], fl[2]]);
  fg.computeVertexNormals();
  const floor = new THREE.Mesh(fg, matTentFloor);
  floor.receiveShadow = true;
  grp.add(floor);
  return grp;
}
"""
# block10_05.html + block10_09_05.html: Block 05 stands off Block 10's opened side and the connection cloth spans the gap; the slider
# stretches it (Block 05 slides out, the cloth is rebuilt to fit)
LAYOUT_05_CLOTH = DOCK_CLOTH_FN + """
// Block 05 on Block 10's +x side, facing it, centred along its length, joined by the expandable connection cloth
block05.rotation.y = Math.PI;
scene.add(block05);
const shadow05 = contactShadow(0, 0, 2.15, 2.4);
let dockCloth = null;
function setDockGap(gap) {                                   // Block 10 wall base → Block 05 door-wall foot
  block05.position.set(1.80 + gap + 0.95, 0, 0);
  shadow05.position.x = 1.80 + gap + 0.95;
  if (dockCloth) { scene.remove(dockCloth); dockCloth.traverse(o => o.geometry && o.geometry.dispose()); }
  dockCloth = makeDockCloth(block10, block05);
  scene.add(dockCloth);
}
const gapUI = document.createElement('label');
gapUI.id = 'gapUI';
gapUI.innerHTML = 'Connection cloth <input type="range" min="10" max="60" step="1" value="15"><b>15 cm</b>';
document.body.appendChild(gapUI);
gapUI.querySelector('input').addEventListener('input', e => {
  setDockGap(e.target.value / 100);
  gapUI.querySelector('b').textContent = e.target.value + ' cm';
});
setDockGap(0.15); // 15 cm connection cloth (per user)
"""


def write(name, title, hint, sources, parts, layout, cam, target):
    html = HEAD.format(title=title, hint=hint, sources=", ".join(sources), cam=cam, target=target)
    html += "\n".join(closure(n, c) for n, c in parts)
    html += TAIL.replace("{layout}", layout)
    (HERE / name).write_text(html)
    print("wrote", name, len(html.splitlines()), "lines")


write("block10_05.html", "Block 10 + 05 Mock",
      "Block 10 + Block 05, joined by the expandable connection cloth (drag the slider). Sofa in Block 10.",
      ["block10_mock.html", "block05.html", "sofa_mock.html"],
      [("makeBlock10", gable_tent("block10_mock.html")), ("makeBlock05", block05()), ("makeSofa", sofa())],
      "const block10 = makeBlock10({ docked: true, dockOpen: true, bed: false }), block05 = makeBlock05({ docked: true }),\n"
      "  sofa = makeSofa();\n"
      + LAYOUT_10 + LAYOUT_05_CLOTH + LAYOUT_SOFA, "-3.4, 2.6, 6.6", "0.9, 0.9, 0")

write("block10_09_05.html", "Block 10 + 09 + 05 Mock",
      "Block 10 (front) + Block 09 (behind, end-to-end) + Block 05, joined by the expandable connection cloth (drag the slider). Sofa in Block 10.",
      ["block10_mock.html", "block09_mock.html", "block05.html", "sofa_mock.html"],
      [("makeBlock10", gable_tent("block10_mock.html")), ("makeBlock09", gable_tent("block09_mock.html")),
       ("makeBlock05", block05()), ("makeSofa", sofa())],
      "const block10 = makeBlock10({ docked: true, dockOpen: true, bed: false, openBack: true }),\n"
      "  block09 = makeBlock09({ openFront: true }), block05 = makeBlock05({ docked: true }), sofa = makeSofa();\n"
      + LAYOUT_10 + LAYOUT_09 + LAYOUT_JOINT_CLOTH + LAYOUT_05_CLOTH + LAYOUT_SOFA_SIDE, "-4.2, 3.4, 7.2", "0.8, 0.9, -1.2")


# ---- index.html: inject the model builders between markers (the rest of index.html is hand-written) ----
MARK_A, MARK_B = "// <<GENERATED TENT MODELS", "// GENERATED TENT MODELS>>"
idx_path = HERE / "index.html"
idx = idx_path.read_text()
assert idx.count(MARK_A) == 1 and idx.count(MARK_B) == 1, "index.html: generation markers missing"
gen = (MARK_A + " — written by build_combos.py from block10_mock.html, block09_mock.html, block05.html, sofa_mock.html; do not edit\n"
       + "\n".join(closure(n, c) for n, c in [("makeBlock10", gable_tent("block10_mock.html")),
                                               ("makeBlock09", gable_tent("block09_mock.html")),
                                               ("makeBlock05", block05()), ("makeSofa", sofa())])
       + JOINT_CLOTH_FN + DOCK_CLOTH_FN)
a = idx.index(MARK_A); b = idx.index(MARK_B)
idx_path.write_text(idx[:a] + gen + idx[b:])
print("updated index.html model block", gen.count("\n"), "lines")
