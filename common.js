// Shared by main.js (the campsite) and cybertruck_mock.html: the computed sun-disc texture (the sky's sun sprite and
// the headlight flares), shadowAll, and addBeams (vehicle headlights). Imported everywhere as './common.js?v=2'
// (one specifier, so it loads once).
import * as THREE from 'three';

// sun (per user: pixelated artefacts): the 256 px canvas radial gradient banded into rings (8-bit alpha) and its fully
// transparent edge lost its colour, so filtering drew a dark fringe. Now computed per pixel like the clouds: a bright
// disc with a soft rim inside a warm glow, ±½-step dithered, colour defined everywhere, mipmapped.
export function makeSunTexture(N = 512) {
  const data = new Uint8Array(N * N * 4), sm = THREE.MathUtils.smoothstep;
  for (let y = 0; y < N; y++) for (let x = 0; x < N; x++) {
    const r = Math.hypot(x + 0.5 - N / 2, y + 0.5 - N / 2) / (N / 2);           // 0 centre … 1 edge
    const core = 1 - sm(r, 0.13, 0.19);                                         // the disc, soft-rimmed
    const glow = 0.85 * Math.exp(-((r / 0.33) ** 2)) * (1 - sm(r, 0.8, 1));     // halo, exactly 0 at the border
    const a = core + glow * (1 - core), k = (y * N + x) * 4;
    data[k] = 255; data[k + 1] = Math.round(240 + 12 * core); data[k + 2] = Math.round(200 + 34 * core);  // warm glow → near-white disc
    data[k + 3] = Math.max(0, Math.min(255, Math.round(a * 255 + Math.random() - 0.5)));
  }
  const t = new THREE.DataTexture(data, N, N, THREE.RGBAFormat);
  t.colorSpace = THREE.SRGBColorSpace; t.generateMipmaps = true; t.minFilter = THREE.LinearMipmapLinearFilter; t.magFilter = THREE.LinearFilter;
  t.needsUpdate = true;
  return t;
}

export const shadowAll = g => { g.traverse(o => { if (o.isMesh) o.castShadow = o.receiveShadow = true; }); return g; };

// vehicle headlights (shared by the G-Class and the Cybertruck): a SpotLight per lamp (off until L) and the visible
// beams (per user: "headlights beam visible at night") — a soft additive cone from each lamp, bright at the lens and
// fading out over 9 m, faint at its silhouette edges so it reads as light in the air, plus a glow flare on each lens.
// Strength follows night / rain (car.update sets uI). lamps: [[x, y, z], …] in the vehicle's frame, facing +z.
export function addBeams(g, lamps, col = {}) {          // col: { light, beam, flare } colours (default: warm halogen)
  const beams = lamps.map(([x, y, z]) => {
    const l = new THREE.SpotLight(col.light ?? 0xfff2dc, 0, 40, 0.62, 0.6, 2); l.position.set(x, y, z + 0.04);
    l.target.position.set(x * 1.3, 0, z + 14); g.add(l, l.target); l.visible = false; return l;
  });
  const beamGroup = new THREE.Group(); beamGroup.userData.dynamic = true; beamGroup.visible = false; g.add(beamGroup);
  const BL = 9, coneGeo = new THREE.ConeGeometry(1.9, BL, 28, 8, true);
  coneGeo.translate(0, -BL / 2, 0);                                     // apex at the lamp
  { const pp = coneGeo.attributes.position, tA = new Float32Array(pp.count); for (let i = 0; i < pp.count; i++) tA[i] = -pp.getY(i) / BL;
    coneGeo.setAttribute('aT', new THREE.BufferAttribute(tA, 1)); }
  coneGeo.scale(col.wide ?? 1.7, 1, 1);                                  // per user: a wider beam side to side (an oval cone, not round)
  coneGeo.rotateX(-Math.PI / 2 + 0.08);                                 // pointing ahead (+z), dipped toward the road (−π/2 − x tilted it UP, per user)
  const beamMat = new THREE.ShaderMaterial({
    uniforms: { uI: { value: 0 }, uC: { value: new THREE.Color(col.beam ?? 0xfff1d6) } },
    vertexShader: `attribute float aT; varying float vT; varying vec3 vN; varying vec3 vV;
      void main() { vT = aT; vec4 mv = modelViewMatrix * vec4(position, 1.0); vN = normalize(normalMatrix * normal); vV = normalize(-mv.xyz); gl_Position = projectionMatrix * mv; }`,
    fragmentShader: `uniform float uI; uniform vec3 uC; varying float vT; varying vec3 vN; varying vec3 vV;
      void main() { float facing = pow(abs(dot(normalize(vN), normalize(vV))), 1.4);
        float a = uI * pow(1.0 - vT, 1.7) * smoothstep(0.0, 0.04, vT) * (0.15 + 0.85 * facing);
        gl_FragColor = vec4(uC, a); }`,                  // additive blending multiplies by alpha itself
    transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, side: THREE.DoubleSide,
  });
  const flareMat = new THREE.SpriteMaterial({ map: makeSunTexture(128), color: col.flare ?? 0xfff4e0, blending: THREE.AdditiveBlending, transparent: true, depthWrite: false, opacity: 0 });
  for (const [x, y, z] of lamps) {
    const cone = new THREE.Mesh(coneGeo, beamMat); cone.position.set(x, y, z); cone.renderOrder = 5; cone.frustumCulled = false; beamGroup.add(cone);
    const fl = new THREE.Sprite(flareMat); fl.scale.setScalar(col.flareSize ?? 0.9); fl.position.set(x, y, z + 0.02); beamGroup.add(fl);
  }
  return { beams, beamGroup, beamMat, flareMat };
}
