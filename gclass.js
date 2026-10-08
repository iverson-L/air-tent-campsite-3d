// ===== parked G-Class (per user: rebuilt from a photo of the new W465 G-Class in green) at the site edge. Local +z is
//       the front. A HOLLOW shell so you can sit in it (E, see `car` below): side panels with real wheel arches (front
//       fender / door / rear pieces, so the driver's door can swing), hood, floor, roof on A–D pillars, see-through
//       glass, and a cabin (dash with widescreen, wheel, seats, trims). Black arch flares, sills, rub strips, bumpers
//       with mesh inserts, slatted grille, round LED headlights in black pods, amber indicator "bullets" on the wings,
//       mirrors, ladder roof rack, 5-spoke wheels on chunky tyres, spare wheel on the side-hinged rear door.
//       Right-hand drive (driver on local −x). No badges. =====
// Builder: adds the G-Class to `scene` at world (x, z) = at, heading rotY, and returns its rig for `car` in main.js.
import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import { addBeams, shadowAll } from './common.js?v=3';

const V = (x, y, z) => new THREE.Vector3(x, y, z);

export function buildGClass(scene, at, rotY = 0) {
  let carRig = null;
  {
    const g = new THREE.Group();
    const paint = new THREE.MeshStandardMaterial({ color: 0x6b8a2c, roughness: 0.38, metalness: 0.3, side: THREE.DoubleSide });
    const black = new THREE.MeshStandardMaterial({ color: 0x1a1b1d, roughness: 0.75 }), satin = new THREE.MeshStandardMaterial({ color: 0x232427, roughness: 0.45, metalness: 0.4 });
    const trim = new THREE.MeshStandardMaterial({ color: 0x2b2c2f, roughness: 0.85 }), seat = new THREE.MeshStandardMaterial({ color: 0x1f1d1c, roughness: 0.7 });
    const glass = new THREE.MeshPhysicalMaterial({ color: 0x3f5058, roughness: 0.05, metalness: 0.1, transparent: true, opacity: 0.45, side: THREE.DoubleSide, depthWrite: false });   // lighter tint (per user)
    const silver = new THREE.MeshStandardMaterial({ color: 0xd9dcdf, roughness: 0.25, metalness: 0.7 }), rimDark = new THREE.MeshStandardMaterial({ color: 0x8d9196, roughness: 0.35, metalness: 0.7 }), rubber = new THREE.MeshStandardMaterial({ color: 0x161617, roughness: 0.92 });
    const lensMat = new THREE.MeshStandardMaterial({ color: 0xdfe6ea, roughness: 0.15, metalness: 0.2, emissive: 0xfff4dd, emissiveIntensity: 0 });
    const tailMat = new THREE.MeshStandardMaterial({ color: 0x8e1414, roughness: 0.35, emissive: 0xff2010, emissiveIntensity: 0 });
    const amber = new THREE.MeshStandardMaterial({ color: 0xf08a12, roughness: 0.3, emissive: 0x6a3000, emissiveIntensity: 0.25 });
    const screenMat = new THREE.MeshStandardMaterial({ color: 0x0c1218, roughness: 0.2, emissive: 0x16324a, emissiveIntensity: 0.25 });
    const wellMat = new THREE.MeshStandardMaterial({ color: 0x141416, roughness: 0.95, side: THREE.DoubleSide });
    const HW = 0.93, ZF = 2.25, ZR = -2.25, BELT = 1.24, BOT = 0.5, ROOF = 1.95, TR = 0.39;
    const AX = [1.42, -1.47], AR = 0.47;                                 // axles (z) and arch radius
    const box = (w, h, d, mat, x, y, z, parent = g, r = 0.012) => { const m = new THREE.Mesh(new RoundedBoxGeometry(w, h, d, 2, Math.min(r, w / 2, h / 2, d / 2)), mat); m.position.set(x, y, z); parent.add(m); return m; };
    // side panel piece between z0..z1: bottom follows the wheel arches, top = beltline (cabin) / hood line (front)
    const bottomY = z => { for (const a of AX) if (Math.abs(z - a) < AR) return TR + Math.sqrt(AR * AR - (z - a) ** 2); return BOT; };
    const topY = z => z > 0.62 ? 1.22 - 0.02 * (z - 0.62) / (ZF - 0.62) : BELT;
    const sidePiece = (z0, z1, sx, mat = paint) => {
      const pts = [];
      for (let i = 0; i <= 48; i++) { const z = z0 + (z1 - z0) * i / 48; pts.push(new THREE.Vector2(z, bottomY(z))); }
      for (let i = 0; i <= 6; i++) { const z = z1 + (z0 - z1) * i / 6; pts.push(new THREE.Vector2(z, topY(z))); }
      const geo = new THREE.ExtrudeGeometry(new THREE.Shape(pts), { depth: 0.045, bevelEnabled: true, bevelThickness: 0.008, bevelSize: 0.008, bevelSegments: 2, curveSegments: 4 });
      geo.rotateY(-Math.PI / 2);                                         // shape x → world z, extrusion → −x
      geo.translate(sx > 0 ? HW : -HW + 0.045, 0, 0);
      return new THREE.Mesh(geo, mat);
    };
    const DOOR = [-0.52, 0.6];                                           // front door span (z)
    const doorGlassGeo = (() => { const sh = new THREE.Shape([[DOOR[0] - 0.03, 1.235], [0.64, 1.235], [0.44, 1.92], [DOOR[0] - 0.03, 1.92]].map(([z, y]) => new THREE.Vector2(z, y)));   // edges tuck under the A/B pillars, belt and roof
      const geo = new THREE.ShapeGeometry(sh); geo.rotateY(-Math.PI / 2); return geo; })();   // shape x → world z (plane at x = 0)
    for (const sx of [-1, 1]) {
      g.add(sidePiece(DOOR[1] + 0.012, ZF, sx));                         // front wing
      g.add(sidePiece(ZR, DOOR[0] - 0.012, sx));                         // rear doors + quarter
      if (sx > 0) g.add(sidePiece(DOOR[0], DOOR[1], sx));                // passenger front door (fixed)
    }
    // driver's door (local −x side): its own panel + window frame + glass, hinged at its front edge
    const doorPivot = new THREE.Group(); doorPivot.position.set(-HW, 0, DOOR[1]); doorPivot.userData.dynamic = true; g.add(doorPivot);
    { const d = sidePiece(DOOR[0], DOOR[1], -1); d.position.set(HW, 0, -DOOR[1]); doorPivot.add(d);
      const inner = box(0.03, 0.62, 1.06, trim, HW - 0.06, 0.88, -0.06 - DOOR[1] + 0.06, doorPivot); inner.position.set(0.05, 0.88, (DOOR[0] + DOOR[1]) / 2 - DOOR[1]);
      const fr = (w, h, d, x, y, z) => box(w, h, d, paint, x, y, z, doorPivot, 0.006);
      fr(0.04, 0.05, 1.0, 0.02, 1.885, (DOOR[0] + 0.02 + 0.42) / 2 - DOOR[1]);                         // frame top
      fr(0.04, 0.66, 0.05, 0.02, 1.57, DOOR[0] + 0.03 - DOOR[1]);                                     // frame rear
      const gl = new THREE.Mesh(doorGlassGeo, glass); gl.position.set(0.025, 0, -DOOR[1]); doorPivot.add(gl);
      box(0.03, 0.025, 0.14, black, -0.012, 1.12, DOOR[0] + 0.12 - DOOR[1], doorPivot);                // handle
      box(0.012, 0.035, 1.0, black, -0.004, 1.0, (DOOR[0] + DOOR[1]) / 2 - DOOR[1], doorPivot);        // rub strip
    }
    // hood, grille panel, floor, rear panel, wheel wells
    box(2 * HW - 0.09, 0.2, ZF - 0.62, paint, 0, 1.115, (ZF + 0.62) / 2, g, 0.03);
    box(2 * HW - 0.1, 0.42, 0.04, black, 0, 0.83, ZF - 0.02);
    for (let i = 0; i < 4; i++) box(0.98, 0.028, 0.03, satin, 0, 0.78 + i * 0.085, ZF + 0.012);         // grille slats
    box(2 * HW - 0.08, 0.05, ZF - ZR - 0.1, trim, 0, BOT + 0.02, 0);                                    // floor
    // rear door (side-hinged on local −x, as on the G-Class): lower panel, window and the spare wheel swing together
    const rearPivot = new THREE.Group(); rearPivot.position.set(-HW + 0.03, 0, ZR); rearPivot.userData.dynamic = true; g.add(rearPivot);
    const RX = HW - 0.03;                                                                               // pivot-local x of the car's centreline
    box(2 * HW - 0.06, BELT - BOT - 0.04, 0.045, paint, RX, (BELT + BOT) / 2, 0.022, rearPivot);       // rear door (lower)
    box(0.05, ROOF - BELT - 0.08, 0.05, paint, RX + HW - 0.07, (ROOF + BELT) / 2 - 0.03, 0.03, rearPivot, 0.008);   // its window frame (latch side)
    box(2 * HW - 0.12, 0.05, 0.05, paint, RX, ROOF - 0.09, 0.03, rearPivot, 0.008);                                 // frame top
    for (const a of AX) for (const sx of [-1, 1]) {                                                    // wheel wells (hide the cabin through the arches)
      const w = new THREE.Mesh(new THREE.CylinderGeometry(AR - 0.01, AR - 0.01, 0.34, 18, 1, true, 0, Math.PI), wellMat);   // upper half
      w.rotation.z = Math.PI / 2; w.position.set(sx * 0.77, TR, a); g.add(w);
      const cap = new THREE.Mesh(new THREE.CircleGeometry(AR - 0.01, 18, 0, Math.PI), wellMat); cap.rotation.y = sx * Math.PI / 2; cap.position.set(sx * 0.6, TR, a); g.add(cap);
    }
    // greenhouse: roof, pillars (A raked, B, C, D), windscreen, side + rear glass
    box(2 * HW - 0.04, 0.07, 2.66, paint, 0, ROOF - 0.035, -0.91, g, 0.03);   // wide enough to cap the glass tops
    const pillar = (sx, z, w) => box(0.05, ROOF - BELT, w, paint, sx * (HW - 0.045), (ROOF + BELT) / 2, z, g, 0.008);
    for (const sx of [-1, 1]) {
      pillar(sx, -0.56, 0.08); pillar(sx, -1.56, 0.09); pillar(sx, ZR + 0.06, 0.12);                   // B, C, D
      const a = box(0.06, 0.72, 0.07, paint, sx * (HW - 0.05), (BELT + ROOF) / 2, 0.52, g, 0.008); a.rotation.x = -0.29;   // A, raked
      for (const [z0, z1] of [[-0.6, -1.52], [-1.61, ZR + 0.12]]) {                                   // rear door + quarter glass
        const gl = new THREE.Mesh(new THREE.PlaneGeometry(Math.abs(z1 - z0) + 0.06, 0.69), glass); gl.rotation.y = Math.PI / 2; gl.position.set(sx * (HW - 0.03), 1.578, (z0 + z1) / 2); g.add(gl);
      }
    }
    { const gl = new THREE.Mesh(doorGlassGeo, glass); gl.position.x = HW - 0.025; g.add(gl); }        // passenger door glass
    { const ws = new THREE.Mesh(new THREE.PlaneGeometry(2 * HW - 0.08, 0.78), glass); ws.position.set(0, (BELT + ROOF) / 2, 0.525); ws.rotation.x = -0.29; g.add(ws); }  // windscreen, edges under the A pillars / header / cowl
    box(2 * HW - 0.1, 0.06, 0.08, paint, 0, ROOF - 0.04, 0.43, g, 0.01);                               // header
    { const rg = new THREE.Mesh(new THREE.PlaneGeometry(2 * HW - 0.08, 0.69), glass); rg.position.set(RX, 1.58, 0.02); rearPivot.add(rg); }   // rear window (on the door)
    // cabin
    box(2 * HW - 0.12, 0.26, 0.42, trim, 0, 1.1, 0.42, g, 0.04);                                         // dashboard
    { const scr = box(0.78, 0.1, 0.025, screenMat, -0.2, 1.255, 0.25, g, 0.01); scr.rotation.x = -0.3; } // widescreen, low on the dash
    const wheelG = new THREE.Group(); wheelG.position.set(-0.42, 1.2, 0.16); wheelG.rotation.x = 0.43;   // face tilted up toward the driver g.add(wheelG);
    wheelG.add(Object.assign(new THREE.Mesh(new THREE.TorusGeometry(0.18, 0.018, 8, 28), black), {}));
    { const hub = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.07, 0.05, 16), black); hub.rotation.x = Math.PI / 2; wheelG.add(hub);
      for (const a of [0, 2.1, 4.2]) { const sp = new THREE.Mesh(new THREE.BoxGeometry(0.15, 0.022, 0.012), black); sp.position.set(Math.cos(a) * 0.09, Math.sin(a) * 0.09, 0); sp.rotation.z = a; wheelG.add(sp); } }
    box(0.22, 0.24, 0.75, trim, 0, 0.74, -0.08, g, 0.04);                                                  // centre console
    for (const sx of [-1, 1]) {
      box(0.52, 0.13, 0.52, seat, sx * 0.42, 0.86, -0.28, g, 0.05);                                       // front cushions
      const back = box(0.52, 0.7, 0.13, seat, sx * 0.42, 1.25, -0.6, g, 0.05); back.rotation.x = -0.18;
      box(0.26, 0.17, 0.1, seat, sx * 0.42, 1.69, -0.7, g, 0.04);                                          // headrests
      { const z0 = ZR + 0.13, z1 = sx < 0 ? DOOR[0] - 0.02 : 0.55;                                        // inner trims (driver's door has its own)
        box(0.03, 0.62, z1 - z0, trim, sx * (HW - 0.065), 0.88, (z0 + z1) / 2); }
    }
    box(1.56, 0.13, 0.5, seat, 0, 0.86, -1.36, g, 0.05);                                                    // rear bench
    { const b = box(1.56, 0.62, 0.13, seat, 0, 1.22, -1.68, g, 0.05); b.rotation.x = -0.14; }
    // black bits: flares, sills, rub strips, bumpers, handles, mirrors
    for (const sx of [-1, 1]) {
      for (const a of AX) {
        const s = new THREE.Shape(); s.absarc(0, 0, AR + 0.07, 0.12, Math.PI - 0.12, false); s.absarc(0, 0, AR + 0.005, Math.PI - 0.12, 0.12, true);
        const fg = new THREE.ExtrudeGeometry(s, { depth: 0.075, bevelEnabled: true, bevelThickness: 0.012, bevelSize: 0.01, bevelSegments: 2, curveSegments: 20 });
        fg.rotateY(sx > 0 ? Math.PI / 2 : -Math.PI / 2); const f = new THREE.Mesh(fg, black); f.position.set(sx * (HW - 0.02), TR, a); g.add(f);
      }
      box(0.09, 0.07, 1.92, black, sx * (HW + 0.02), BOT + 0.02, -0.03);                                  // sill / step
      box(0.012, 0.035, 0.95, black, sx * (HW + 0.006), 1.0, -1.02);                                      // rub strip, rear door
      if (sx > 0) box(0.012, 0.035, 1.0, black, HW + 0.006, 1.0, 0.04);                                   // rub strip, passenger door
      box(0.012, 0.03, 1.2, black, sx * (HW + 0.006), 1.15, 1.45);                                        // wing strip
      for (const z of (sx > 0 ? [-0.4, -1.42] : [-1.42])) box(0.03, 0.025, 0.14, black, sx * (HW + 0.012), 1.12, z);   // handles
      // mirror (per user: check all mirrors): the head was a slab running fore-aft along the side — a mirror is wide
      // outward, tall and thin fore-aft, with its glass facing back; a short arm from the door's front corner holds it
      box(0.1, 0.035, 0.05, black, sx * (HW + 0.05), 1.36, 0.52);                                         // arm
      box(0.2, 0.15, 0.08, black, sx * (HW + 0.18), 1.42, 0.5, g, 0.025);                                // head
      { const mg = new THREE.Mesh(new THREE.PlaneGeometry(0.17, 0.12), new THREE.MeshStandardMaterial({ color: 0x1a2228, roughness: 0.05, metalness: 0.8 }));
        mg.position.set(sx * (HW + 0.18), 1.42, 0.459); mg.rotation.y = Math.PI; g.add(mg); }                // glass, facing back
      const ind = new THREE.Mesh(new THREE.CapsuleGeometry(0.025, 0.06, 4, 8), amber); ind.rotation.x = Math.PI / 2; ind.position.set(sx * 0.8, 1.235, ZF - 0.18); g.add(ind);   // indicator bullet
    }
    box(2 * HW + 0.08, 0.3, 0.28, black, 0, 0.64, ZF + 0.07, g, 0.04);                                     // front bumper
    for (const sx of [-1, 1]) box(0.36, 0.14, 0.03, satin, sx * 0.56, 0.65, ZF + 0.215);                   // mesh inserts
    box(2 * HW + 0.06, 0.26, 0.2, black, 0, 0.62, ZR - 0.06, g, 0.04);                                     // rear bumper
    // headlights: black pods, round lenses with an LED ring; tail lights
    for (const sx of [-1, 1]) {
      box(0.34, 0.33, 0.06, black, sx * 0.68, 0.98, ZF + 0.005, g, 0.04);
      const lens = new THREE.Mesh(new THREE.CylinderGeometry(0.115, 0.115, 0.03, 28), lensMat); lens.rotation.x = Math.PI / 2; lens.position.set(sx * 0.68, 0.98, ZF + 0.035); g.add(lens);
      const ring = new THREE.Mesh(new THREE.TorusGeometry(0.115, 0.009, 6, 28), lensMat); ring.position.set(sx * 0.68, 0.98, ZF + 0.05); g.add(ring);
      box(0.12, 0.32, 0.03, tailMat, sx * 0.83, 1.0, ZR - 0.012, g, 0.01);
    }
    // roof rack (black ladder)
    for (const sx of [-1, 1]) { box(0.04, 0.04, 2.3, black, sx * 0.8, ROOF + 0.09, -0.86); for (const z of [0.2, -0.6, -1.3, -1.95]) box(0.03, 0.08, 0.03, black, sx * 0.8, ROOF + 0.04, z); }
    for (let i = 0; i < 9; i++) box(1.6, 0.025, 0.03, black, 0, ROOF + 0.09, 0.27 - i * 0.28);
    // wheels: lathed tyre with rounded shoulders + 5-spoke silver rim; spare on the rear door
    const tyreGeo = new THREE.LatheGeometry([[0.25, -0.13], [0.34, -0.135], [0.38, -0.12], [TR, -0.08], [TR, 0.08], [0.38, 0.12], [0.34, 0.135], [0.25, 0.13]].map(([r, y]) => new THREE.Vector2(r, y)), 28);
    const wheels = [];
    const wheel = (parent, x, y, z, rotY) => {
      const w = new THREE.Group(); w.position.set(x, y, z); w.rotation.set(0, rotY, 0, 'YXZ'); parent.add(w);
      const t = new THREE.Mesh(tyreGeo, rubber); t.rotation.z = Math.PI / 2; w.add(t);
      const barrel = new THREE.Mesh(new THREE.CylinderGeometry(0.25, 0.25, 0.24, 24, 1, true), satin); barrel.rotation.z = Math.PI / 2; w.add(barrel);
      const face = new THREE.Mesh(new THREE.CylinderGeometry(0.24, 0.24, 0.02, 24), rimDark); face.rotation.z = Math.PI / 2; face.position.x = 0.06; w.add(face);
      for (let k = 0; k < 5; k++) { const a = k / 5 * Math.PI * 2, sp = new THREE.Mesh(new THREE.BoxGeometry(0.03, 0.2, 0.065), silver);
        sp.position.set(0.085, Math.cos(a) * 0.12, Math.sin(a) * 0.12); sp.rotation.x = a; w.add(sp); }
      const rimR = new THREE.Mesh(new THREE.TorusGeometry(0.235, 0.02, 6, 28), silver); rimR.rotation.y = Math.PI / 2; rimR.position.x = 0.085; w.add(rimR);
      const cap = new THREE.Mesh(new THREE.CylinderGeometry(0.045, 0.05, 0.04, 16), silver); cap.rotation.z = Math.PI / 2; cap.position.x = 0.1; w.add(cap);
      return w;
    };
    for (const a of AX) for (const sx of [-1, 1]) { const w = wheel(g, sx * 0.8, TR, a, sx > 0 ? 0 : Math.PI); w.userData.dynamic = true; wheels.push({ w, front: a > 0, sx, base: w.rotation.y }); }
    { const sp = new THREE.Group(); sp.position.set(RX + 0.05, 1.16, -0.2); sp.rotation.y = -Math.PI / 2; rearPivot.add(sp);   // spare: tyre + black cover
      const t = new THREE.Mesh(tyreGeo, rubber); t.rotation.z = Math.PI / 2; sp.add(t);
      const cov = new THREE.Mesh(new THREE.CylinderGeometry(0.3, 0.3, 0.2, 28), black); cov.rotation.z = Math.PI / 2; cov.position.x = 0.02; sp.add(cov);
      box(0.14, 0.12, 0.1, black, RX + 0.05, 1.16, -0.08, rearPivot); }
    const { beams, beamGroup, beamMat, flareMat } = addBeams(g, [-0.68, 0.68].map(x => [x, 0.98, ZF + 0.06]));
    g.position.set(at[0], 0, at[1]); g.rotation.y = rotY;
    scene.add(shadowAll(g));
    g.traverse(o => { if (o.isMesh && o.material === glass) o.castShadow = false; });                    // glass lets the sun in
    beamGroup.traverse(o => { o.castShadow = o.receiveShadow = false; });
    carRig = { g, doorPivot, rearPivot, beams, lensMat, tailMat, wheels, TR, seatEye: V(-0.42, 1.5, -0.3), beamGroup, beamMat, flareMat,
      WB: 2.89, MAXF: 12.5, ACC: 4.2, BRK: 9, R: 1.0, circles: [-1.45, 0, 1.45], doorLocal: [-1.55, 0, 0.1], camDist: 6.4, ev: false, name: 'G-Class' };
  }
  return carRig;
}
