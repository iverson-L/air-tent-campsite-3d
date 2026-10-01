# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Single-file three.js sandboxes for each tent (`block10_mock.html`, `block09_mock.html`, `block05.html`, `sofa_mock.html`), generated combination pages, and the full campsite scene `index.html`. `block10_mock.html` started as a mock split off from `index.html`. The on-screen hint says it plainly: edits here do not affect `index.html`. Several helpers and `buildTent()` are marked "copied verbatim from index.html". A change you want to keep has to be ported back to that file by hand.

`image3.png` is the reference photo of the real tent. Code comments cite it ("per image3") as the source of truth for colours, mesh transparency and interior darkness. Comments also mention `block10.png` and `ss3.png`, which are not in this directory.

## Running

There is no build, package manager, linter or test suite. three.js r160 loads from jsDelivr through an import map, so opening the page needs network access.

- Open `block10_mock.html` directly in a browser, or serve the folder: `python3 -m http.server 8000`, then open `http://localhost:8000/block10_mock.html`.
- Debug handles for console or browser-automation checks: `window.__scene`, `window.__camera`, `window.__controls` and `window.__renderer`.

## Structure of the script

Everything is in one inline `<script type="module">`, in this order:

1. **Scene and lights.** A `HemisphereLight` fill plus a moderate directional sun. An earlier, flatter rig made everything read as one flat value, which looked fake.
   - There is still no visible ground. An invisible `ShadowMaterial` plane catches the sun's shadow.
   - A blurred canvas "contact shadow" under the footprint grounds the tent.
2. **Official dimensions**, in metres: `W` (gable span, x), `D` (length, z, the ridge axis), `WALL_H` and `RIDGE_H`. All geometry is derived from these. The same block holds the shared constants:
   - **Side-wall lean:** `LEAN_DEG` is 11°. Per the user, only the long side walls (the 360 cm width) lean inward; the 280 cm gable ends stay vertical. The value is the perspective-corrected lean measured from the YAMATO10 reference photo. `LEAN` is its tangent, and `EAVE_X` is the eave half-width (about 2.94 m across at the eave, against the 3.6 m base). `ROOF_PITCH` and `EAVE_HALF_TURN` are derived from these. Everything that touches a side wall places it at `hwP − y·LEAN`.
   - Silhouette rounding: `R_EAVE`, `R_RIDGE`. These are bezier tangent lengths, measured along each (leaning) edge and used by `archPts`. `R_RIDGE` and `R_EAVE` are derived by `bezTangent` from true radii: `RIDGE_RADIUS` is 0.08 m (the spec is a 16 cm diameter ridge) and `EAVE_RADIUS` is 0.12 m. Change the radii, not the tangent lengths. The user wanted a crisp, less round roof.
   - Rake: `RAKE_R` (0.12 m, per the user) is the true radius of the rounded edge where the roof and side walls meet each gable wall. It covers the rake and the vertical gable corners.
   - `DOOR_SILL`: the height of the fabric sill under the front door opening.
3. **Procedural textures** drawn on a canvas:
   - `makeCottonTexture` makes a near-white base that the material colour tints.
   - `makeScreenTexture` makes an alpha map that uses only the **green channel**. Its `gapG`/`threadG` arguments set how opaque the insect mesh is.
   - `matScreenShadow` is a checkerboard-discard depth material, set as `customDepthMaterial` on the screens. The soft-shadow filter averages the checkerboard to about a 50% shadow. Without it, sun passes straight through the screens and lights the inside of the back wall. The user reported that as "light passing through the back".
4. **Materials.** The fabric is **dark grey**. The warm cast in `image3.png` is the evening light, not the fabric colour. The `fabric()` factory reuses the cotton texture as both `map` and `bumpMap`. The main materials:
   - `matCanvas`: the ONE exterior fabric material, shared by the roof, walls, gable panels, flaps and skirt. The user wants every panel the same colour. `matRoof` is just an alias for it; don't give it its own colour again.
   - `matTrim`: a darker material for zip tapes and flap straps, so they stay visible against the fabric.
5. **Shape helpers**: `roundedRectShape`, `archPts`, `makeTube`, `footprintLoop` and `loftLoops`.
   - `archPts(b, yFoot, seg, minR, bSide)` is the key helper: an exact perpendicular offset of the leaning silhouette, returned as an open arch. The roof lines are inset by `b` and the walls by `bSide`. Everything at the gable is built on it: the rounded body sections, both gable panels, the door opening (`doorPts()`, closed along `DOOR_SILL`) and the door flaps. The flaps pass `minR` (about 1.2 × the tube radius), so a tube never bends tighter than itself at the sharp ridge.
   - The roof slopes are flat planes. The old `puffRoof` mid-slope bulge was removed because the user said the roof looked puffed; don't add it back.
   - `makeTube` sweeps a tube along a polyline. Its `gather` argument ripples the radius so rolled fabric looks bunched, and `taper` closes the ends off so they don't show as open pipes.
   - `footprintLoop` samples the plan footprint at uniform arc length, pushed out by a per-point offset and height, and `loftLoops` stitches such loops into the draped snow skirt.
6. **`buildTent(cx, side)`** does five things:
   - It builds the body shell with `roundedBodyTube`. The shell is lofted through z-stations whose cross-sections are `archPts(inset)`. Over the last `RAKE_R` at each end, the inset follows a quarter circle, which gives the rounded rake and gable corners. The shell is open at both ends and at the bottom. Smooth normals are computed on the indexed grid before `toNonIndexed()`.
   - It removes the flat side-wall quads from that shell (`stripFlatWalls` tests points against the leaning plane) and rebuilds each side as a flat fabric panel with a window hole (`addWindowWalls`). Panels are built in (z, y) shape coordinates, then `onWall` places each vertex on the leaning plane. The panel runs from the ground to the eave and ends where the rounded corner takes over. It overlaps the curved body by `SEAM_OVERLAP` (1 cm), both into the corner and up into the eave. Butting the panel edge against the body left T-junction cracks, which showed as a hairline flickering down the pillar that the user spotted.
     - Each window has a see-through screen and a rolled storm flap above it. The flap is a gathered roll half-sunk into the wall, overlapping the screen's top edge; its ends taper shut, and two webbing straps with short tails hold it up. The user rejected an earlier floating, open-ended pipe version.
     - The tent is deliberately single-walled; you see straight through it from side to side. The old inner liner shell (5 cm inside the walls, with window sleeves and an inner back wall) was removed. It hid the bathtub wall and made the side walls look about 6 cm thick, which the user objected to.
   - It adds the chimney (stove-jack) cover: a flat square flap, `CHIMNEY_SIZE` (0.34 m, reduced from 0.40 at the user's request) per side, on the +x roof slope, the one above the side window in image3.png. Per the user it must be square and in the right position. `CHIMNEY_Z` is -0.50, about two-thirds of the way back. `CHIMNEY_UP` is the centre's distance up the slope from the eave vertex. It's set so the lower edge stays 12 cm up, just above the eave curve. Its edges run along the eave and down the slope, and a snap button sits near the top edge. It's built in a local basis (along the length, up the slope, roof normal) and uses the shared `matCanvas`.
   - It adds the bathtub floor, 500D PVC (`matTentFloor`: light grey with a satin clearcoat). It's one continuous sheet over the whole footprint that turns up in a soft bend into a 10 cm (`BAT_H`) tub wall. The tub wall sits flush against the inside of the tent walls, leaning with the side walls and rounding the corners with `RAKE_R`, with a hem bead on top. It's built from `footprintLoop`s: the `skin()` inset is 4 mm at the side walls and 1.6 cm at the gable panels. Per the user there must be no gap between the tent and the floor.
   - It adds an inflatable air bed, 200 × 180 × 38 cm, modelled on the Naturehike Horizon air mattress. Its length runs along z, with the head 3.5 cm off the closed back gable, and it's centred across the width, leaving about 75 cm of floor inside the door.
     - Sides: glossy taupe PVC in three stacked bands, lofted with `footprintLoop`.
     - Top: a cream flocked rolled rim around a quilted field of tufted dimples on a 20 cm pitch.
     - A pump panel and valve sit on the foot end.
     - Two domed pillows are at the head.
     - The rim doesn't cast shadows, because it produced shadow acne when it did.
   - It adds the interior air frame: light-grey (`matPole`) Ø14 cm beams, all joined together.
     - An arch at each end runs up the corner pillars from the floor, following the lean, and meets under the ridge. Its centreline is `archPts(FRAME_B)`, where `FRAME_B` is 9 cm.
     - A ridge beam runs between the two arch crowns, at `crownY`.
     - Two side-wall beams run at the eaves, centred on the arch's eave knee.
     - Fabric sleeves (`matCanvas`, slightly looser than the tube and softly rumpled) cover the frame's runs: the pillars, the roof-slope rafters and the side eave beams. Bare light-grey tube shows only in these places:
       - the whole ridge beam
       - the bottom `SLEEVE_Y0` (45 cm; the user shortened the sleeves by 15 cm) of each pillar
       - every junction, left bare for `JOINT_BARE` (25 cm, per the user: "at least 25 cm") along each member from the junction centre. The eave elbow's centre is the arch's eave knee, where the side beam plugs in: pillar, rafter and side beam are all bare there. The crown's centre is the arch apex, where the ridge beam plugs in: both rafters are bare there.

       The sleeve cut points are found by arc length along `frameArch` (`subPath`). An earlier version sleeved over the junctions, and the user rejected it.
     - All the beams end inside the arches. The front arch is hidden from outside behind the front panel's border.
   - At each gable end, the flat gable panels sit at the rim plane inside the rounded edge, so their outline is `archPts(RAKE_R)`. The earlier air-beam tube was removed: it would poke through the rounded edge, and the user didn't want a puffy arch showing.
     - **Back (`s = -1`) is closed:** one flat fabric panel filling the rounded rim, flush with it. It has no frame, recess or flap, because the tent is closed at the back. It keeps a zip line down the middle; the user wants it kept, because it represents the zip.
     - **Front (`s = 1`) is the entrance:** ONE flat fabric panel (`FACING_D` thick) fills the rounded rim, flush with it, with the door opening cut out by `doorPts()`. The screen sits at mid-thickness of that panel. There's deliberately no recess and no separate frame band; the user wanted the mesh and pillars flat with no gaps. The opening's border, per the user, is 22 cm across the top (`FRAME_W`) and 25 cm down the sides (`FRAME_SIDE`). The side border is the 12 cm rounded corner plus 13 cm of flat panel.
     - A zip seam runs down the middle of the front door. Both ends carry this middle line; don't remove it.
     - Rolled door flaps run along the top of the opening. It's a double door, so per the user there are two separate rolls, one for each door half. They meet at the zip under the ridge with a small gap (`ZIP_GAP`), and each tapers shut at both ends.
       - The rolls are slim: `rollR` is 0.04, and the user asked for slimmer.
       - They sit half-sunk into the panel face just above the opening and turn down just past the eaves. Per image3.png, don't let them hang down the door sides.
       - Four tie ropes hang from them, two per door-half roll, with 5 cm tails. Each is a thin loop around the roll plus a short hanging rope with a knot, in `matTrim`.
   - It adds the snow skirt: a short band (seam 5 cm up, reaching about 4.5 cm out; the user shortened it twice) that drapes onto the ground. It's lofted from four `footprintLoop`s:
     - a seam exactly ON the wall surface (offset 0; on the leaning sides `lean(y, nx)` pulls every loop in by `y·LEAN`)
     - a tangential peel-off just below it
     - a belly
     - the hem

     With the same material and a tangential start, there's no visible join; the user asked for it to be seamless. Don't reintroduce a ledge or an outward step at the seam. One shared `fold` signal drives the loops, so the folds run from seam to hem. The footprint corner radius is `RAKE_R`, so the skirt follows the rounded gable corners. The user rejected an earlier rigid, plinth-like skirt.

## Gotchas

- **Transparent screens:** these use `depthWrite: false` plus an explicit `renderOrder`, with the outermost screen drawn last. three.js sorts transparent objects by object-centre distance by default, which produced artefacts at grazing angles. Keep the explicit ordering when you add transparent layers.
- **Tiny offsets:** the front panel, screen (`hd - FACING_D / 2`) and zip seam use millimetre offsets within the panel's 1.2 cm thickness to avoid z-fighting. Changing one usually means rechecking the others.
- **Rounded ends:** everything at the gable rim is sized from `RAKE_R`: the front and back panel outlines, `FRAME_SIDE`, the side-panel length, the skirt corners, and the bathtub floor's corners. Change `RAKE_R` rather than those individually. The gable panel outlines are `archPts(RAKE_R - PANEL_TUCK)`, which reach 4 mm past the rounded edge so the panel's side face buries itself in the curve. Stopping at or short of the edge left a hairline gap at the pillar/panel joint, which the user spotted.
- **Rolls on zero-thickness walls:** rolled flaps must rest fully OUTSIDE the wall surface, at an offset of `rollR + 3 mm`. Their strap rings get a gap (`STRAP_GAP`) where they touch the wall. A half-sunk roll pokes through into the interior, which happened in both files and was fixed.
- **Ties:** each flap has at most 2 ties (strap or rope), with short tails: 4 cm webbing, 5 cm rope. The user asked for this.
- **Sun shadow range:** both files set `sun.shadow.camera.near/far` to 8/24. Three.js's default 0.5–500 m range made the normalised depth bias about 20 cm in world units. Occluders near the ground stopped casting, so light leaked onto the ground at the wall bases, which the user reported. Keep the range tight if you move the sun.
- **Interior light = the lantern (both files):** each tent has exactly ONE interior light, a downward `SpotLight` (81° half-angle, soft edge) at the lantern's glow tube; there's no free-floating light.
  - Block 10's lantern hangs mid-ridge-beam, with its window facing the door, at 1.1. Block 05's hangs on its front top beam, at 0.45.
  - It's a spot, not a point light, because a point light 7 cm below the bare beam blew the beam out to white.
  - Don't turn on its shadows. The page's `ShadowMaterial` ground catches every light's shadows, and the whole ground went grey.
  - These lights exist only in the mocks so the interior shows through the screens; they aren't part of `index.html`.

## block05.html (single-slope tent)

A second standalone sandbox, rebuilt from `05.jpg` (photo) and `block05.png` (dimensioned drawing) in Block 10's style.

- **Shared code:** the texture, material and helper code (`makeCottonTexture`, `fabric()`, `matCanvas`, `matTrim`, `matTentFloor`, `matGableMesh`, `matScreenShadow`, `roundedRectShape`, `makeTube`, `loftLoops`) was copied verbatim from `block10_mock.html`, so colours match. If you change a shared material in one file, change it in the other too.
- **Dimensions:** 190 cm deep (`DEPTH`, along x) × 240 cm wide (`WIDTH`, along z). The front door wall is 140 cm tall (`H_FRONT`) and the back wall 80 cm (`H_BACK`). x runs from back (−) to front (+).
- **Back wall lean:** `BACK_LEAN_DEG` is 10.5°, top leaning in toward the door. Per the user the real tent's big-window wall slopes. The angle was measured from block05.png using its own dimension lines (the back edge rises 82 cm over a 15.2 cm horizontal shift). The foot stays on the 190 cm footprint (`XB`), and the eave vertex is at `XE0`, about 15 cm inside it.
  - `profPts` intersects the offset leaning wall line (`WN`) with the offset roof line (`RN`), so every piece built on it follows the lean.
  - The back panel is built in (z, distance up the wall) coordinates with a `WD`/`WN` basis. Use `backX(y)` and `onBack(y, out)` to place parts on the wall.
  - The tub wall, skirt and bed clearance all subtract `y * BACK_LEAN` on the back side.
- **Shell:** the back wall, roof and a 25 cm porch canopy (`VISOR`) past the door wall form one shell, lofted along z like Block 10's `roundedBodyTube`. The shell's cross-section comes from `profPts(b)`, an exact offset of the side profile. Its ends curl in with `RAKE_R` (`curlInset(z)`).
- **Side walls:** flat panels (`profPts(RAKE_R - PANEL_TUCK)`) with a leaning front edge running from the front foot up to the canopy tip. Each has a 2×2-pane mesh window (50 × 40 cm) with a zipped U-shaped surround and a rolled flap with straps. Per the user it sits up and toward the entrance: centred at `WIN_X` 0.03, which is 47% of the way from the leaning back edge to the wing's front edge, as drawn in block05.png. The mesh is 43–83 cm up, with the roll just under the roof edge.
- **Front door wall:** a flat panel at `XF`, with its top following the roof underside including the curl. The top is measured at the wall's INNER face (`roofY(XF - FACING_D)`); measuring at the outer face poked the wall 3 mm up through the sloped roof. It has a big open doorway (`DOOR_SIDE`, `DOOR_SILL`, `DOOR_TOP`), with the door rolled up along the top and two tie ropes.
- **Porch:** per the user there are no porch poles, guy ropes or pegs. The canopy is carried by the side walls' leaning front edges.
- **Floor and skirt:** the bathtub floor and snow skirt are the same as Block 10's, built on `footLoop`, which has rounded back corners and near-square front corners. Keep the interior light dim. A free-floating light washed the PVC floor out to a white tray at 1.6, and at 0.7 it threw a bright patch under the roof; the user asked for it dimmer both times.
- **Interior air frame:** built like Block 10's, with light-grey Ø14 cm beams all joined together.
  - Each side end (z = ±`FRAME_Z`) has one continuous tube following the profile offset in by `FRAME_B`: the back pillar (leaning with the wall), the back eave elbow, the roof rafter, the front elbow and the front pillar (vertical, just inside the door wall). The back part comes from `profPts(FRAME_B, …, minR)`.
  - Two beams run along z: the front top beam at the front elbows, and the back eave beam at the back elbows.
  - Sleeves follow Block 10's rules. The front top beam is the highest member and is left bare, like Block 10's ridge. Pillar bottoms are bare up to 45 cm, except the short back pillars, which are bare up to 15 cm so they still get a sleeve (the user asked for this). Every junction has 10 cm bare on each side (`JOINT_BARE`), per the user, who settled on it after trying 25 cm and 5 cm. Block 10 keeps 25 cm.
- **Lantern:** a Blackdog-style camping lantern hangs on a ring and S-hook from the bare front top beam, at mid-width. It has a black cap with a lens and power button, an M-shaped bail, a champagne-metal body whose window faces the door, an emissive glow tube and a ribbed base. The tent's interior light (warm, 0.45) sits at its glow tube; the old free-floating `innerLight` is gone. Note that three.js cylinder angles start from +z, so `π/2` faces +x.
- **Bed:** a 150 × 180 × 38 cm air bed, using Block 10's bed code (and `footprintLoop`) copied in. It sits against the back wall with its 180 cm length along z, head toward the +z side as in 05.jpg, and the pump facing the door.
- **Back window:** a large mesh window on the back wall, opposite the entrance, per the YAMATO 9+10+5 photo. It's 160 × 40 cm (`BW_SIDE` 0.40), measured from the photo as about 66% of the wall's width. The user found the first 208 × 47 cm version oversize. Per the user it sits high, close under the roof (`BW_Y0` 0.28 to `BW_Y1` 0.68), with its roll topping out at the start of the eave curve. The shell skips its flat back-wall strip, and a separate back panel (overlapping the curl by 1 cm) holds the window hole, the screen, a zipped U-shaped surround and a rolled flap with two straps.
- **Edges:** `EAVE_RADIUS` and `RAKE_R` are 7 cm here, not 12 cm like Block 10. The user found the 12 cm version too puffy on this smaller tent. Rolls and hems are slimmer too.
- **Entrance corners:** the canopy-edge hem tapers shut at its ends, and the porch poles stop just under the canopy corner, hugging the wing's leaning edge. The user reported an artefact at the entrance's top corner, caused by an open-ended hem and a pole spike poking past the roof corner.

## sofa_mock.html (inflatable sofa)

A standalone sandbox modelled on `sofa_1.png` (dimensioned) and `sofa_2.png` (photo), a "Spark Air" style inflatable sofa. It uses the same scene setup as the tent mocks, including the tight sun shadow range.

- **Dimensions:** 200 cm wide (`W`), on a 40 cm base (`BASE_H`). The seat is 150 × 80 cm, with arms 30 cm and the backrest 50 cm above it. The depth `D` (1.10 m) is estimated from the photo.
- **`inflatedBox`:** builds a `RoundedBoxGeometry` whose faces bow outward with a `pillow(u, v)` bulge.
- **`faceDecal`:** builds the printed graphics ("SPARK AIR", "01 AIR", the tagline) as canvas textures on a plane curved with that same bulge, so the print sits exactly on the puffy surface.
- **Details:**
  - a thin seat pad with a seam
  - zipped pockets with velcro patches on each arm's front and outer side. The pocket binding and velcro are draped onto the pouch's real curved surface by raycasting (`surfZ`/`drape` in `pocket()`). Straight tubes floated off the bulge, which the user reported.
  - a black pump box on the left arm
  - a carry strap on the base
- **Colour:** sage grey `0x9aa7a2`, a brushed `MeshPhysicalMaterial` with sheen. The print is near-black charcoal.

## block09_mock.html (gable tent, 360 × 250)

A copy of `block10_mock.html`, adapted from `block09_dimension.webp`, `block09_entrance.webp` and `block09_back.webp`. Everything not listed below is identical to Block 10, so most fixes need making in both files.

- **Size:** the cross-section matches Block 10 exactly (360 cm wide, 170 cm walls, 245 cm ridge, 11° wall lean). Only `D` differs: 2.5 m instead of 2.8 m.
- **Side windows:** narrower (`WIN_HZ` 0.65, so 130 cm) with a higher sill (`WIN_Y0` 0.45). Each has a 3×3 pane grid of dark bars on the outer face.
- **Back gable:** open, not closed. A single mesh door sits right of centre and a 2×2 mesh window to its left, as seen from outside, with a 10 cm gap between them and their tops aligned at 180 cm (`BACK_TOP`), both per the user. The window is 80 cm tall. The side windows and the back window have rounder bottom corners than top ones (`roundedRectShape2`; side windows 16 cm vs 6 cm, back window 12 cm vs 4 cm). Each has a rolled flap with 2 short ties. They're defined as `BD` and `BW` in outside-view coordinates; `toWorld` maps them, because the panel is rotated by π.
- **Skylight:** a transparent TPU roof window, centred on the +x slope (middle of both the length and the slope). Per the user, it's flush, with no frame and no visible layer or edge from outside.
  - Its rectangle (`SKY`) is snapped to the roof's own roughly 10 cm loft grid. The roof triangles inside it are moved into a separate mesh with the clear TPU material, which doesn't cast shadows, so light comes in.
  - Its fabric cover is rolled up INSIDE the tent along the ridge-side edge, with 2 short ties.
  - The stove-jack cover sits low on the same slope, toward the back corner.
- **Bed:** Block 10's 200 × 180 × 38 cm air bed. Its head is against the back gable, shifted toward +x (x −0.28 to 1.52) to clear the back corner pillar while leaving about 50 cm of the back doorway clear.
- **No logo:** per the user, the "09 BLOCK" print in the reference images is ignored.

## Shared conventions (all tents)

- **Corner radii:** every window has rounder bottom corners than top ones (`roundedRectShape2(w, h, rTop, rBot)`), with a 16 cm bottom radius (`WIN_RB`). Block 09's back window uses 12 cm. Exception: Block 05's small side windows have plain 1 cm corners all round (`WIN_R`, per the user). Every entrance also gets 16 cm bottom corners. The arch-shaped gable entrances use `filletFeet(archPts(...), 0.16)`, and the rectangular doors (Block 05's front door, Block 09's back door) use `roundedRectShape2`. All of this is per the user.
- **`onWall` mirroring:** `onWall` (Blocks 10 and 09) mirrors the shape on the +x wall so the panel faces OUTWARD. Before this, the +x wall faced inward. Shading looked fine, but the shadow `normalBias` pushed lookups into the tent, so the sunny wall self-shadowed and read darker than its rounded corners, which the user spotted. Never pre-flip shapes before calling `onWall`. If you add a panel by other means, check its winding faces outward.

## Combined pages: block10_05.html, block10_09_05.html (GENERATED)

Both are generated by `python3 build_combos.py`; don't edit them by hand. The script copies each model's code (dimensions → helpers → builder) verbatim from its own file into a separate closure, so their identically named constants and helpers don't clash. It then lays them out under one scene setup: 4096 shadow map, ±7 m shadow area, tight near/far. Re-run the script after editing any source model. The edits it makes to the copied code are anchored on exact source text, and the script fails loudly if an anchor disappears.

- **Layout** (per block10+05.png and the YAMATO 9+10+5 photo):
  - **Block 10:** at the origin.
  - **Block 05:** turned 180° on Block 10's +x side, centred along its length. `VISOR` is 0.30 (it was raised so the canopy met the wall back when Block 05 docked flush).
    - **Everywhere (both combo pages and `index.html`):** Block 05 stands off the wall and an EXPANDABLE connection cloth (`makeDockCloth`, per block10+05.png and the user) bridges the gap. A slider sets the gap (10–60 cm, default 15 cm per the user), moving Block 05 and rebuilding the cloth.
      - The cloth is a fabric tunnel in `matCanvas`. Its top is VELCROED onto Block 10's wall (per user, not zipped) just under the eave, and it slopes down over Block 05's canopy tip. Its sides drop to the ground over Block 05's leaning wing edges.
      - At Block 05 the cloth passes just over the tip hem, then LAPS 5 cm (`LAP`) onto the roof and wing faces. The corners follow the roof's `RAKE_R` curl. Ending it at the tip left a few-mm slit under the cloth that showed the sky, which the user spotted.
      - It's taut and smooth, a straight slope with no wrinkles or sag; the user rejected the earlier wrinkled version, so don't add folds back. There are NO trim or zip lines along its edges (the user removed them: it's velcro); it has ground hems and a PVC ground sheet joining the two floors. Its faces point outward, for the shadow normalBias.
      - Block 10 is built with `dockOpen`: the +x window mesh is opened, and the mesh and storm flap are rolled together into one thick roll with 2 straps just under the eave. The roll sits on top of the cloth's velcro line.
  - **Block 09** (three-tent page only): end to end behind Block 10, with its entrance gable 2 mm from Block 10's back gable and the ridges in line.
- **Changes to the copied code:**
  - Only Block 10 (`docked_x=True`) drops its +x side-window storm flap, because that side is docked to Block 05. Block 09 keeps its flap.
  - Snow skirts are removed wherever tents meet, by `cutTris` on the skirt mesh (`skirt_cuts`): along Block 10's docked +x side, along Block 05's door wall, and across the 10↔09 gable joint. Otherwise they show inside through the meshes and doorways, which the user reported. Outside the joints the skirt is kept.
  - Block 10's bed is replaced by the sofa (from `sofa_mock.html`).
    - In `block10_05.html`, the sofa is backed against Block 10's back gable, facing the entrance.
    - In `block10_09_05.html`, the sofa is against Block 10's −x side wall, facing Block 05; the back is now a walkway. Its position clears the 11° leaning wall and the corner pillars.
  - Three-tent page only: the 10↔09 joint is WIDE OPEN, per the user.
    - Block 10's back gable is generated as a rim panel with the same `doorPts()` opening as its entrance (`open_back`), with no mesh, zip or rolls. Both doorways keep their 16 cm fabric sill at floor level: the user tried opening them to the floor and preferred the sill as more natural.
    - Block 09's entrance keeps only its frame panel (`open_front`); the mesh, zip and door rolls are removed. Those rolls used to stick out into Block 10's back gable.
    - Both tents share the same profile, so the two openings line up exactly.
  - Three-tent page only: a connection cloth covers the outside of the 10↔09 joint (`LAYOUT_JOINT_CLOTH`), per the user.
    - It's a 30 cm fabric band that follows the full outer silhouette from floor to floor over the ridge, using Block 10's own `archPts`, offset 2 mm out. It covers both tents' 12 cm rounded edges plus 3 cm onto each shell.
    - Its centre sits slightly proud and its edges tuck down, with dark binding along both edges.
    - The gable builders expose `archPts`, `makeTube`, `matCanvas` and `matTrim` on the tent group's `userData` so the layout can use them.
  - Block 09 and Block 05 keep their beds.

## Builders and index.html (campsite scene)

`build_combos.py` turns each model into a builder closure with runtime options. One code copy serves every variant:
- `makeBlock10(o)` / `makeBlock09(o)`:
  - `o.docked`: Block 05 docks on the +x side, so there's no storm flap or skirt there.
  - `o.bed === false`: no bed.
  - `o.openBack` / `o.openFront`: an open passage to the neighbouring tent, with the skirt cut across the joint.
- `makeBlock05(o)`: `o.docked` means no skirt along the door wall.
- `makeSofa()`.
- `makeJointCloth(block10)`: the connection band over a 10↔09 joint, returned as a group.
- `o.dockOpen` (Block 10/09): the +x side window is opened into a connection cloth, and `userData.dock` records where the cloth velcros on. Block 05 exposes `userData.dock` (its porch geometry). `makeDockCloth(block10, block05)` builds the tunnel from both tents' current placement. Both combo pages and `index.html` use it. In `index.html` the gap is a fixed 15 cm (`B05_DOCK` = 0.15 + 0.95). The right tent's cloth lives in world space and is rebuilt in `layoutTents()` when the gap slider moves the tents. `unit3`'s cloth is built before the unit is transformed, so it sits in the unit's own space. The cloth measures ground level from the tents (`y0`), so it works at `TENT_Y`.
- Each tent group's `userData` exposes `lantern`, `lanternGlow` and `matGableMesh`; night mode uses them.

`index.html` is hand-written except the region between `// <<GENERATED TENT MODELS` and `// GENERATED TENT MODELS>>`, which `build_combos.py` overwrites. Re-run the script after editing any model. The region is injected inline, not imported as a module, so `index.html` still opens from `file://`.

- **Layout:**
  - The left Block 10 has the bed. The right Block 10 has Block 05 joined by the 15 cm connection cloth, and the sofa (as `block10_05.html`). Both sit either side of the flysheet gap.
  - The campfire is at (0, 4.05).
  - Across the fire stands a Block 10 + 09 + 05 unit (`unit3`, as `block10_09_05.html`), turned 180° so its entrance faces the fire.
  - A free-standing Block 05 (`solo05`) on the front right has its doorway rotated toward the fire.
  - The gravel `AREA` covers everything. `areaShape()` takes real world z: the shape is laid flat with `rotation.x = −π/2`, which flips z. Trees are kept off the site and out of the default camera's line of sight.
- **Tent height:** all tent groups sit at `TENT_Y = 0.006`, so the gravel patch at 0.005 can't z-fight through the tent floors.
- **Sun:** placed 62 m out along (8, 12, 6) with shadow near/far 15/100, so the shadow camera is outside the ±42 m frustum and the bias stays about 2 cm. The sun sprite sits on the same direction.
- **Loading:** a static `#loader` overlay shows immediately. The module's build is split by `await stage(label, pct)` calls, so the bar repaints; then `renderer.compile` runs, and the overlay fades after the first frame. A classic script reports load errors in the overlay.
- **UI:** a refined light panel using CSS variables, toggle switches styled from the same checkbox ids, and collapsible sections. Under 520 px it becomes a bottom sheet. A walk-mode hint bar appears at the bottom. `#app` is its own stacking context so CSS2D labels stay under the panel.

