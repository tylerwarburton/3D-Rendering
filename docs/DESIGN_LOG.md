# Design log — Tyler's printed parts

Design history and decisions, newest round first. The code is in this repo;
`CLAUDE.md` has the working rules and `README.md` the overview.
The `src/archive_rooms_iris.py` file keeps the removed room pods + iris gate.

```
build.py                    waterfall pipeline (stl sheets water spill audit viewer
                            + concept overhang coverage testprint)
src/
  fittings.py               2.5 in acrylic "hamster tube" fittings, trimesh+manifold
  waterfall.py              3-tier waterfall, CadQuery (FINAL, as printed)
  snake_hide.py             L-shaped underground snake hide, SDF + surface nets
tools/
  render.py                 orthographic z-buffer renderer (numpy) + cutaway()
  viewer_template.html      Three.js part viewer (orbit, section plane, water);
                            /*DATA*/ gets replaced with packed meshes
  fittings_viewer.py        python -m tools.fittings_viewer -> STLs + out/fittings_viewer.html
  latch_check.py            simulates cap push-on / twist / lock / pull-off
  paths.py, solids.py, sheets.py, viewer.py, hydro.py, water_diagram.py,
  spill_map.py, audit.py, concept.py, overhang.py, coverage.py,
  support_test.py           waterfall tooling (needs cadquery)
```

## Parts

### Tube fittings — `src/fittings.py` (ACTIVE)
Modular snake tube system for 2.5 in clear acrylic (63.1 OD / 59.5 ID).
Socket 63.80 ID x 30 deep, bore 59.50 (stepless with an inserted tube),
wall 4.0, bend radius 70. Parts: elbow_90, coupler, tee, u_bend, y_fitting,
cap, flange, back_plate, pipe_hook, latch_coupon, shim, vent_tube,
room_pod, room_junction, room_lid, iris_gate (elbow = any angle). All build as one watertight
body (`drop_slivers` raises otherwise).

**Quarter-turn latch (2026-09-26).** Female on every socket, male on the cap.
- Female: raised collar at each port mouth (OD 76.2, `COLLAR_T` 2.2) with 3
  J-slots — axial entry, 30 deg circumferential run, hard stop, rounded
  detent bump (0.5 high) just behind the locked lug. Slots cut only the
  collar; tubes still slide into the socket as before.
- Male cap: plug ring into the socket (ID = bore, so a capped port is a
  smooth dead end) + skirt wrapping the collar with 3 lugs + grip ribs.
  32 cm3 (old solid cap 94). Print disk-down, no supports; the lug's flat
  bearing face is a 1.4 mm overhang.
- `tools/latch_check.py` result: push-on 0 mm3 overlap, detent 3 mm3 over
  16-29 deg (the click), locked 0, locked+pulled 1 mm 22 mm3 (held), entry
  pulled 0 (free), past stop 24 mm3 (blocked).
- back_plate hole now clears the collar (`PORT_OD` + 1.2).
- `LATCH_ENABLE = False` restores plain sockets.
- **Shim** (66.8 cm3): joins two fittings directly, no acrylic. Double-ended
  male latch — plug + lugged skirt on each side of a 4 mm band
  (`SHIM_BAND_T`), bore straight through at 59.5. Skirts are full plug
  length so it prints standing on either end without supports and resists
  bending. Side B is side A rotated 180 deg about x (`shim_side_frame()`),
  not mirrored, so the twist is the same from each fitting.
  `latch_check.run_shim()`: 0 overlap locked on all 13 ports of every
  fitting; two couplers through one shim both hold (22 mm3 when pulled)
  and release only at the entry angle.
- latch_coupon has a FULL-DEPTH socket (33 mm tall, 35.6 cm3). The first
  version (19 mm) was too shallow for the cap/shim plug — caught 2026-09-26.
- Print `latch_coupon` + `cap` first. Tunables if the fit is off:
  `DETENT_H` (click strength), `SKIRT_CL`, `LUG_RAD_CL`, `SLOT_AX_CL`.

Open items: empty-socket ledge 2.15 mm; pipe_hook cradle zero clearance;
70 mm bend radius tight for a ball python.

### Waterfall — `src/waterfall.py` (FINAL, printed)
Three-tier open-front waterfall, 8.25 in cube, pump in the back column.
`DRIP_MODE="column"`, U flow channels (`CHANNEL_FRAC` 0.75), back holes
3.25 / 6.25 in, wall-rib breakaway supports 0.10 mm Z-gap snapped to 0.2 mm
layers, `RIM_EDGE_STYLE="none"`. ~1480 cm3, 38 ribs, 3049 mm line contact.
Verified byte-identical to Tyler's file (2026-09-26).
History: chat "Ball python enclosure water system design" (2026-08).

### Snake hide — `src/snake_hide.py` (FINAL)
L-shaped underground hide for small snakes, glass forms two walls. SDF +
naive surface nets, self-verifies watertight + sealed interior. Ramen-shop
stair entrance, stone-lantern escape hatch, torii corridor, masonry detail.
`python3 snake_hide.py [--out PREFIX] [--res 0.028]` -> OBJ, STL, viewer HTML
(~25 s). Verified byte-identical to Tyler's file (2026-09-26).
Known bug: default `--mirror` flips x without reversing winding, so the STL
is inside-out (signed volume -305 cm3); slicers usually repair it.
History: chat "L-shaped snake hide generator script" (2026-09).

### Miata intake adapter — see `claude/intake-adapter.md`
Design notes only; the CadQuery source is not stored here yet.

### Port system, angles, vents, rooms (2026-09-26, round 3)
- **Every port is F or M.** `PORT_NAMES` / `PORT_GENDER` at the top of the
  fittings section; builders take `genders='FMF'` etc. F = socket + collar;
  M = built-in shim end (`male_port()` returns solid + one coaxial bore
  cutter; adding a hollow ring after the cut left slivers on tilted axes).
  Port labels live only in the viewer (`labels=True` returns positions),
  never in the STL.
- **Elbow any angle**: `make_elbow(genders, angle, vent)`, `bend_arc()` cuts
  a torus with a wedge (partial revolves come out uncapped). Viewer offers
  `ELBOW_ANGLES` 22.5/30/45/60/90.
- **Vents**: `VENT` per family, 6 mm holes, 45 deg chamfer on the inside
  edge, staggered; the inside of bends stays solid (holes would crowd).
  `vent_tube` = 150 mm straight vented section. Vent option on elbow (90
  only), coupler, u_bend.
- **Rooms**: `room_pod` (1 port), `room_junction` (3 ports), `room_lid` (10 mm
  hex mesh, 2.4 mm beams, 4-lug bayonet at room radius). 160 ID; height is
  derived so the lid collar/skirt clear the port stubs (95 mm); port axis at
  `SKIRT_RO + 1.5` so mated skirts clear the table; 18 deg ramp from the
  bore floor to the room floor. Junction spans 235 mm - needs a 235+ bed.
  Room ports are horizontal sockets: slicer support inside them.
- `latch_check.run_male()`, `run_room()` added; all pass. 62 gender/angle/
  vent variants build as single watertight bodies through `export_ready`.
- Print notes: M ends print best pointing UP; a horizontal M end needs a
  little support under its skirt.

### Round 4 (2026-09-27): thinner walls, lattice vents, room fixes, iris
- `WALL` 4.0 -> 3.0 (port OD now 74.2). All latch checks re-pass.
- **Vents are a lattice now** (`vent_path`): styles `scale` (snake-scale
  diamonds, fully self-supporting upright) and `hex` (honeycomb; hole tops
  bridge). 8 mm holes on the INSIDE, 3 mm struts, flared 12 deg outward so
  every inside edge is obtuse (~102 deg) - the old round holes' inside
  chamfers overlapped into knife edges. One field along the centreline across
  legs and bends (no seam); holes shrink toward the inside of a bend with the
  strut kept full width, and drop out below `VENT_MIN`; solid band
  `VENT_MARGIN` before each collar.
- **Male-end bore cutter is BORE_R - 0.02**: two coincident cutters (same
  radius/axis/facets) unioned into random sliver edges (broke MM elbow).
- **Rooms**: port stubs start at sqrt(ri^2 - OUTER_R^2) - 1 so they meet the
  curved wall all round (starting at the wall line left gaps at the sides);
  entrance bores run past the curve (ending at the wall line left a lip over
  both sides of each entrance - found by Tyler, confirmed by a 144-ray test);
  floor is flush with the bore floor (no step/ramp; thick floor = infill);
  support feet removed - use slicer supports on build plate for the stubs.
- **Iris gate v1 - SUPERSEDED, it fused (see Round 9)** (`make_iris_gate`, print in place, 8 bodies in one STL): six
  pie-slice wedges on one layer slide radially (scroll-chuck style - a camera
  iris needs stacked blades, can't PIP); a ring with spiral slots drives
  their pins; lever out through a window, 45 deg travel; 6 deg dwell at each
  slot end = self-locking open and closed; flat tips leave an 8 mm blunt hex
  when closed. Gaps: 0.2 mm vertical (one layer, same as the proven support
  Z-gap; all interfaces snapped to 0.2), 0.35 mm sideways. OD 139, 97 tall.
  `latch_check.run_iris()`: zero overlap at 17 lever angles, open clears the
  bore, printed gap 0.20. Wedges must be pie slices with a curved back - a
  straight back's corners hit the chamber wall when open.
  Safety: closing on her pinches along the six seams - only close it when
  you can see the gate is clear.
- `export_ready_multi()` for print-in-place parts.

### Round 5 (2026-09-27): XL room, iris print fixes + animation, wrapped vents
- **XL junction room** (`room_junction_xl`, `room_lid_xl`): male ports, ID
  216 mm, sized so its width across the ports equals the standard junction
  with a shim on every port (302 mm): ID = ROOM_ID + 2*(ROOM_STUB -
  ROOM_STUB_M). 28 mm deeper front-to-back. Rooms are per-type now:
  `ROOM_KINDS` (id, genders), `room_ports(kind)`, `_room_dims(kind)`.
  Too big for a 256 bed - split into pieces if needed.
- **Iris printability** (`latch_check.run_print_audit`: steep overhangs with
  nothing within a modelled gap below, AND per-layer islands):
  lever now RISES up-out at 45 deg (a down-sloping lever started its knob as
  an island in mid-air); knob removed (can't sit on a 45 deg lever); two
  snap-off ribs hold the roof over the lever window (break out before use);
  fixed pads between the wedge lanes carry the ring (and act as bearing
  pads); ring-to-wedge gap is 2 layers (0.4) so a sagging bridge can't rub.
  0 islands; what remains is short bridging. Print with slicer supports
  OFF - they would fuse the mechanism.
- **Vents wrap onto the tube**: the lattice is laid out flat (u around, s
  along the centreline) and every hole corner is mapped through one wrap,
  so lattice lines stay continuous on the inside of bends (resizing holes
  individually kinked them). Compressed holes shrink about their centres.
- **Bends are one seamless swept tube** (`bend_path` + `tube_along`), not
  legs + torus: the legs' 0.3 mm overlap left near-coincident surfaces that
  vent holes across the seam turned into shards.
- **Tee and wye vents** (`near_leg` keeps a solid band round the seams).
- 110 gender/angle/vent variants build watertight; all checks pass.
- Viewer encoding 'q3' (`_encode`): vertices on a 0.1 um grid (the same grid
  `export_ready` welds on - 1 um merged points and broke vented parts once
  saved), sorted + delta-coded, triangles sorted, byte-shuffled, zlib.
  `quantize()` proves each part still one watertight body AFTER an STL
  round trip (merge by position, as a slicer reads it) or keeps exact
  float32. Exported STLs use the same geometry, so downloads == exports.
  Viewer 40 MB -> 23.5 MB.
- Viewer: iris packed as separate bodies (`_pack_multi`) with its kinematics;
  "Close iris / Open iris" animates it (4.5 s, eased) in full view and
  section; camera looks down the tube for the iris. Download = the same 8
  bodies. Viewer is ~40 MB (vent variants dominate).

### Round 6 (2026-09-27): strut widths, room port toggles
- **Vent hole size is solved from real strut widths** (`_hole_f`): largest
  hole scale keeping >= VENT_STRUT (3.0) inside and >= VENT_STRUT_OUT (1.5)
  outside, measured to the six neighbours on the lattice as it actually
  sits (squished/stretched by loc = 1 + k*cos*rho, widened by rho/r_in,
  flared). The old row-spacing rule never shrank nested-row patterns -
  scale struts went to ~2 mm on the inside of bends (Tyler spotted it).
- **`assemble_vented`**: tries tiny pattern rotations (`VENT_PHASES`, <0.5
  deg) until the part passes export_ready. 16 holes around divides the 96
  tube facets exactly, so hole corners can land a hair off facet edges.
- Male-end bore cutter is BORE_R - 0.06 (0.02 sat inside the swept tube's
  facet sag, 0.004 mm - broke male hex elbows).
- **Rooms toggle F/M per port** like fittings (`make_room(kind, genders=)`,
  PORT_NAMES P1..P3). XL defaults to FEMALE (lower profile, no grip ribs):
  291 mm across; all male = 302. All 18 room combos build.
- All 64 vented variants + every other variant build; all checks pass;
  viewer 24.9 MiB.

### Round 7 - male ends = cap (2026-09-28)
- Tyler: cap fits perfectly, male ends/shim were way too tight. Cause: the
  male ends had a long skirt sleeve (full-length grip area) - too much outer
  contact. Fix: every male end (shim, fitting male ports, room male ports)
  now uses the cap's exact geometry via `male_parts()`: short SKIRT_L 10.5
  skirt, ONE ring of 24 grip ribs, cap lead-ins (0.4 skirt / 0.8 plug),
  `MALE_FIT_EXTRA = 0.0`.
- Shim prints standing on a plug tip; the upper skirt overhang gets a thin
  pull-off revolve ring (`shim_print_ring`, 0.2 mm gap, layer-snapped).
  `make_shim_print()` -> [shim, ring]; STL is two bodies.
- `male_fit_coupons.stl`: three rings +0.00/+0.15/+0.30 (1/2/3 notches) if the
  male fit ever needs tuning - set MALE_FIT_EXTRA to the winner.
- All latch checks pass (shim, male ports, rooms MMM, base latch).

### Round 8 - vents fill more area (2026-09-28)
Tyler: hex pattern on the Y and others "isn't all the places it could be".
- Tee/wye seams: the old rule (`near_leg`) tested only the hole CENTRE with a
  5 mm band + fudge, so whole areas near a junction stayed solid (Y trunk kept
  2 of 32 holes). New `vent_path(avoid=[(origin, dir, t0, t1, bore_t0)])` +
  `_clear_of()`: tests the whole cutter (densified edges x depth) against the
  other legs, but only from this leg's OUTER surface outward - inside its own
  wall it only removes own wall (overlapping walls are the same solid) and
  inside its bore it cuts nothing. Points inside another leg's hollow bore
  are free. Band `VENT_SEAM` = 2 mm.
- Near a seam a hole that does not fit is shrunk in steps
  (`VENT_SEAM_SHRINK` 1.0 -> 0.45) instead of dropped, so the lattice fades
  into the seam.
- `vm(g)`: vent margin per port gender. F = past the latch collar
  (`VENT_MARGIN` now 2.0 -> 17.3 mm); M = `VENT_MALE_MARGIN` 4 mm (a male end
  adds nothing inside the body past z = 0.4).

### Round 10 - knife gate (blade lives inside); iris parked (2026-10-05)
Tyler: iris too complex for now - hide it, keep the code. Wants a simple gate:
a blade/wall that slides in to block the passage, and the gate must CONTAIN
its blade (first try had a loose push-in blade; he wanted a real knife gate).
- Iris hidden from the viewer (`SHOW_IRIS = False` in tools/fittings_viewer.py);
  all iris code, checks and the print kit remain in src/fittings.py.
- `make_slide_gate(genders)`: straight fitting (130 mouth to mouth) + a flat
  pocket ARM at GATE_TILT = 45 deg. Blade (`gate_blade(beta)`, beta 0 = open,
  1 = closed): D-shape, 3 mm, 0.25 clearance per side. Travel T = 88 mm (tip
  must clear the bore: BORE_R/cos45 + 1 + b). Open: blade parked entirely in
  the arm, 0 mm3 in the bore. Closed: tip seats in a groove in the far wall.
- 45 deg because the body prints standing on port A: the arm RISES (a falling
  arm starts as an island); every overhang is 45 deg; no supports. Arm reaches
  ~105 mm off the axis and above the top mouth - inherent to a knife gate
  (travel ~ 2.8 x bore radius). Checked: cap / male coupler on port B clear it.
- Knob on the blade's n- face (down-outward) through an open-ended slot in the
  arm underside; offset to -u so the slot doesn't cut the tube wall. (On the n+
  face it would hit the mating fitting's skirt.)
- Detent: in-plane spring finger on the blade's +u edge (2.2 x 18 mm, bump
  0.75 mm, ~3.6 N, 0.76% strain) into notches in the arm wall: CLOSED = V
  notch, OPEN = square back face -> captive. Release: 1.6 mm hole through the
  arm side into the OPEN notch (paperclip pushes the finger in).
- Assembly: blade into the open far end of the arm, knob through the slot,
  push until it clicks. 2 parts, no hardware, no print-in-place.
- Viewer: anim kind 'slide' (mover = blade, vec = travel); `dl=[0]` makes
  Download STL give the body only (blade is gate_blade.stl). Mid-travel the
  check shows ~1.6 mm3 overlap = the bump on the wall (intended interference).

### Round 19 - ONE-piece gate body, even 45 deg taper, no clips (2026-10-08)
Tyler didn't want the snap clips or the uneven collar + fins. Picked "one
piece" over glue or long bolts.
- `gn_body(g)` = back plate + square pyramid-frustum taper (exactly 45 deg on
  all four faces, sharp edges - rounded corners came out ~37 deg) + gate block
  with the blade slot THROUGH it (roof is a bridge, ~68 mm across beyond the
  bore) + tube + port. Slot height `GN_CH_T` = blade + 0.8 (sag room).
- `flange_set(gate=True)` -> outer, body, blade (3 prints). Registry key
  `gate_flange_body`. Viewer mover = 2.
- Hooks, rails, fins, `_gn_neck2d`, `gn_housing`, `gn_neck` removed
  (previous version in scratchpad `fittings_pre_onepiece.py`).
- Overhang audit: only the slot-roof bridge + the usual female collar.
  Body 127 cm3 (F). Blade clicks at both ends, 0 overlap at the ends.

### Round 18 - neck SNAPS on, short wall bolts, no block down to the wall (2026-10-08)
Tyler: the bolts didn't need to run through the whole gate, and the housing
didn't need to be a solid block down to the wall.
- Bolts moved to (+-48, +-32), outside the frame (socket-wrench room); they
  clamp only outer plate + wall + back plate: 4 + wall + 4 + nut
  (3 mm wall -> M6x20).
- `gn_housing` is now "back plate + gate": back plate, tube, a 45 deg flared
  collar (cone clipped to the frame), and the frame on top. Beyond the collar
  the frame is two rails (x 30..38.5) on 45 deg fins - no unsupported floor.
- Neck base is held by two printed snap hooks (`_gn_hook`, x sides, y -10..4,
  ~20 mm flex length, 1.1 mm barb, 45 deg lead-in); wings beside the hooks
  locate it in y. Pry the hooks out to take it off.
- `GN_DET_Y` -21 so the open notch (+44.5) stays inside the rails (end 52).
- Volume 280 -> 190 cm3. Overhangs: only the 1.1 mm barb lips + 45 deg faces.
Checked as in Round 17 (watertight F/M, no overlaps, blade clicks at both
ends, viewer row + zip in Chromium).

### Round 17 - NECK gate: no extra screws, blade 25 mm up the neck (2026-10-08)
Replaces Round 16's plate-face guillotine (it needed 2 extra M3 screws).
`flange_set(g, gate=True, beta)` -> outer, housing, neck, blade:
- **outer** plate outside the wall + 1.5 mm centring lip (`GN_LIP`) that sits
  in the wall hole. Nothing depends on wall thickness - Tyler: "thickness is
  irrelevant, I just use bigger screws". `FLANGE_WALL` (3) is only the gap
  drawn in the viewer. Wall hole >= 72 mm (lip OD = 2*OUTER_R).
- **housing** = the back plate: a block on the inside face, 26.75 tall, blade
  channel recessed in its TOP face (open at the far end), click notches.
- **neck**: flat base that closes the channel + tube + port (`gn_neck`, in
  the registry as `gate_flange_neck`).
- **blade** (`gn_blade`): spring fingers click into notches open + closed,
  pull tab with finger slot. Travel `GN_TRAVEL` 65.5; open clears the bore by
  2 mm, closed overlaps it 4 mm.
- The same 4 M6 bolts at (+-46, +-36) clamp all three. Bolt length =
  4 + wall + 26.75 + 4 + nut (3 mm wall -> M6x45).
Checked: all pieces watertight F/M; no overlaps between plate/housing/neck;
blade vs housing only the 4 mm3 finger bumps mid-travel, 0 at both ends;
print audit clean (outer, housing, blade 0 mm2; neck same as plain flange);
`run_male` flange M OK; viewer download row/zip tested in Chromium.

### Round 16 - gate flange (guillotine, square to the tube) + flange sets (2026-10-08)
- `flange_set(genders, gate, beta)` -> [(name, mesh)] assembled: flange,
  back plate (FLANGE_WALL_VIS = 6 mm gap for the wall), and with the gate
  spacer, cover, blade. Viewer: one 'flange' family, toggles port M/F and
  variant plain/with gate; a 'print' row downloads each piece laid flat
  (`dl_parts` entries [label, '.', [body indices]] -> dlPiece); Download STL
  on such an entry = zip of every piece; All-STLs zip adds each piece.
  back_plate is no longer a standalone sidebar entry.
- Gate flange: blade slides ALONG THE WALL across the opening (perpendicular
  to the tube). 3 flat layers, no bridges: flange plate (6 mm, 100 wide),
  SPACER (3.5, blade channel open at the top edge + V click notches) and
  COVER (2.5, bore opening). Standard bolts (+-34.45) sit in the blade's path,
  so the gate flange is 100 mm with bolts at +-41 and its own back plate.
  Plates extend to y = 72 to hold the open blade; 2 M3 screws (blind 2.6
  pilots in the flange plate) clamp the extension. Blade: 2*(BORE_R+4) wide,
  travel 65.5, pull tab with finger slot, spring finger on each edge (same
  GATE_FINGER), bumps click at closed (y -8) and open. Open: 0 mm3 in the
  bore; closed: bore disk fully covered (slits sit 0.4 mm outside the bore).
- BACK_HOLE_R = SKIRT_RO + 1.7 (41.5): the old back-plate hole (collar + 0.6)
  could not pass a MALE flange's skirt + grip ribs.
- Viewer anim may carry `el` (camera elevation): the gate flange is viewed
  from the gate side (-0.95).

### Round 15 - female cap (2026-10-08)
- `make_cap(genders)`: 'M' (default, the original cap, now `make_cap_male()`)
  closes a FEMALE port; 'F' closes a MALE port: `cap_female_local()` = a short
  socket (SOCKET_DEPTH) + standard latch collar + 3 mm floor + grip ribs on
  the barrel (ribs run down to the bed: stopping 1 mm short made them start
  in mid-air). Printed floor-down (flipped) so the floor never bridges.
- Latch check against male ends of a coupler, 45 deg elbow, tee and flange:
  locked 0 mm3, pulled-locked 22 mm3 (held), pulled at entry 0 (free).
- Viewer: cap is a family with an M/F toggle (cap_A-M / cap_A-F), not a single.

### Round 14 - rooms + iris removed; ONE single-file viewer again (2026-10-08)
Tyler: remove all rooms and the old iris code so the viewer fits in one file.
- Rooms (pod, junction, XL, lids) and iris v2 (+ its fit coupons, run_room,
  run_iris) moved to `src/archive_rooms_iris.py` (not built, not imported;
  header says how to bring one back). fittings.py 2140 -> 1575 lines.
  IRIS_LAYER / IRIS_ZGAP stay in fittings.py (the shim print ring uses them).
- Rooms were only 1.7 MB and the iris 0 (already hidden), so that alone left
  ~40 MB. Two more savings make everything fit:
  * TWINS (`_twin`): MF = FM turned around for elbow (180 deg about the bend
    bisector), coupler/vent tube (180 deg about x at mid-length), u-bend
    (180 deg about z); tee A<->B and wye L<->R (180 deg about z). All proper
    rotations (det +1: latch handedness kept), each lands every port exactly
    on its twin's (error ~1e-14). The twin entry has `src` + `xf` (3x4) and
    no geometry; the page draws/exports src through xf. Saves ~10 MB.
  * quantize(): weld at 1 um, then snap to a 1 um grid (UNITS = 1 um, then
    0.1 um, then exact float); `u` in each q3 pack tells the page the grid.
- Vents at EVERY elbow angle are back in the main viewer. One build writes
  out/fittings_viewer.html (single file) AND out/site/ (hosted copy).

### Round 13 - ONE viewer, hosted (2026-10-07)
Tyler didn't want a second viewer file. Everything (incl. vents at every elbow
angle, 176 entries, ~42 MB of geometry) can't fit one sendable file (~31 MB),
so the viewer is now a hosted Artifact: https://claude.ai/artifact/4rmFJKwMERt3m1cZXwumJz
- `python -m tools.fittings_viewer` (default mode 'site') -> out/site/index.html
  (0.14 MB: page + part index) + out/site/data/chunk_N.json (geometry, <= 9 MB
  each, grouped by family; parts carry `ck` + `key`). The page fetches a chunk
  the first time a part in it is shown (`loadChunk`).
- Publish: Artifact file_path=out/site/index.html, files = the chunks,
  capabilities {downloads: true}. Republish to the same URL after rebuilding.
- Host rules: host supplies doctype/head/body + metas (`_site_page` strips
  ours); downloads only via claude.use('downloads') (confirm prompt) and .stl
  is not an allowed type -> a single STL arrives inside a .zip (saveStl); a
  local file falls back to a plain link. One deliberate dark theme. Phone:
  rail on top, view row minmax(0,1fr) (canvas used to push the page taller
  than the screen), toolbar wraps, options pinned at the bottom.
- `python -m tools.fittings_viewer page` re-wraps the page without rebuilding
  geometry. Modes 'main' / 'elbows' still build the old single-file viewers.
- Tested over HTTP in Chromium: lazy chunk loads, vented 45/22.5 deg elbows,
  gate animation + both gate downloads, phone width 400 with no sideways
  scroll. The claude.ai save prompt can only be exercised in the app.

### Round 12 - hex + scale vents at every elbow angle (2026-10-07)
- All 4 extra angles (22.5/30/45/60) x 4 port combos x 2 styles build clean
  (struts fine at the tight angles - `_hole_f` handles it).
- SIZE: each vented elbow is ~0.4-0.6 MB packed (holes x tube facets: 256
  holes x ~270 tris on the 90 deg); 32 more would push the single-file viewer
  to ~41 MB, past the ~31 MB send limit. Coarser vertex grids (1 or 10 um)
  break the vented meshes (q3 falls back to f32); 64/48-facet tubes only save
  ~15%. So: SECOND viewer file.
- `python -m tools.fittings_viewer elbows` -> out/elbows_viewer.html (18 MB,
  60 entries: every angle x off/hex/scale x FF/FM/MF/MM). `variants(F, mode)`;
  `run(mode)`; `_write()`. The main viewer keeps vents on 90 deg only; its
  disabled vent chips say "open elbows_viewer.html".

### Round 11 - gate: 2 downloads, firmer click, human knob (2026-10-06)
- Viewer: slide gate panel has a "print" row with one download per piece
  (`dl_parts` on the entry: [label, part id | '.' = this entry]): Gate body,
  Slide (blade). `dlPart(n)` in the template is shared with Download STL.
- Click: a spring finger on BOTH blade edges (2.6 x 18 mm, bump 1.15 mm with
  45 deg flanks and a rounded tip) into 1.3 mm notches with 45 deg flanks, so
  the bump snaps fully home. ~7 N per finger (1.1% strain - fine for PLA/PETG).
  OPEN notch: +u square back (captive), -u V - one paperclip in the +u side
  hole releases it. Mid-travel overlap ~4.7 mm3 = the two bumps on the walls.
- Knob: centred stem (12 x 14) through the arm-underside slot, 45 deg flare
  (1.35x so even the rounded corners stay under 45 deg - the first try had
  74 mm2 of overhang at the corners), cap 26 x 22 x 9 with 4 mm rounded edges
  and 4 round-bottomed grip grooves across the push direction. 0.4 mm clear of
  the arm at every position. Knob moved to the centre so it can't sit over a
  finger; that pushed GATE_TOP to 70 and the arm end to w = 160 (~113 mm off
  the axis).

### Round 9 - iris gate v2, ASSEMBLED (2026-10-05)
Tyler printed the v1 print-in-place iris: fused solid, unusable. Cause: 0.2 mm
gaps over large flat sliding faces - one layer is enough to bond wherever the
plastic squishes or droops. **Rule: no print-in-place for sliding mechanisms
with big contact areas. Assemble from separate parts, 0.25-0.3 mm clearances.**
v1 code is gone; v2 is a camera-style iris (Bambu 0.4, PLA/PETG clearances).
- 6 identical flat leaves (60 deg, r 30.5..56) turning 55 deg about fixed
  pivots at r 35. 2D sweeps (scratch search -> `run_iris`) proved only
  NEIGHBOURS ever overlap, so leaves alternate levels: even LOW, odd HIGH;
  same-level leaves stay >= 3.0 mm apart.
- Where no neighbour ever passes, each leaf is full height (a PAD, ~28% of
  the leaf, inset 0.3 from the outline - a pad wall flush with the plate wall
  unions into slivers that broke the STL after a 60 deg rotation). Pads bear
  on floor/rings below and above, so no leaf can drift into the other level
  in any orientation (a vertical tube was the failure case found in review).
- Nothing sticks out of a leaf: pivot HOLE + drive SLOT. Pivot pins on the
  base (low) / cover (high); drive pins on the lower ring (low) / upper ring
  (high); every pin is shorter than one level (2.05 mm engagement, lift is
  only the 0.3 gap). Low leaves print flat-down as-is; high leaves are the
  mirror (print flipped). Pins have 0.5 mm lead-in chamfers.
- Pivots must sit at the leaf's trailing corner for full closure; a
  neighbour always sweeps over that corner, which is why pivots can't be on
  the pads (searched exhaustively, no solution) and leaves carry holes, not
  bosses.
- Ring turns 0.25 deg per leaf deg (`IRIS_K`) + 5 deg dwell each end
  (self-locking: pushing the leaves can't turn the ring); lever travel 23.75
  deg. The two rings key together through a cup wall (3 keys, 120 deg
  symmetric so any orientation is correct) and turn as one.
- Housing: base (port A) + cover (port B), each a 45 deg flared flange
  (Rf 73.7) so both print standing on their port with no supports;
  centring tongue/groove; 3x M3x16 screws (2.6 pilots in the base). Lever
  window top is a ~45 mm bridge -> 0.8 mm headroom over the lever.
- Size: 147 mm across, 120 mm port to port.
- Assembly order + the one blind step: top leaves are aligned by nudging each
  CLOCKWISE (looking down) until it stops (measured: 1 deg of free play that
  way = 0.15 mm at the hole) before the cover goes on.
- `make_iris_fit_coupons()` = plate with the real pivot+drive pins, key with
  the real hole + slot: print first (10 min).
- `run_iris()` checks: 0 overlap at 25 ring angles (all 10 parts), bore clear
  open (leaves from r 30.26), closed hole <= 6.8 mm, same-level gap 3.04,
  pads >= 225 mm2 always supported, 0.25 clearance everywhere that moves.
  Its proximity pass builds one ~0.7 GB index per mesh -> build, use, free
  (keeping them OOM-killed the run).
- Viewer: anim kind 'pivot' = table of (ring angle, leaf angle) + movers
  (part index, pivot x/y, ring|leaf); every moving part turns about its own
  vertical axis. 'Iris parts' group = the print kit (base/cover also male).
- Gotcha: `pkill -f <pattern>` in the same shell command kills the shell
  itself (the pattern is in its own command line) - use a pid file.

### Viewer (fittings_viewer.html)
One sidebar entry per family; port chips toggle F/M, angle chips, vent
toggle; on-screen port labels (Labels button). 70+ variants packed exactly
(float32 + uint32) and zlib-compressed, inflated in the browser on demand
(DecompressionStream) - 13 MB. "All STLs .zip" = the CURRENT choice of each
family. File names encode the config, e.g. `tee_A-M_B-F_C-M.stl`.

### Viewer downloads (2026-09-26)
`tools/viewer_template.html` has **Download STL** (current part) and **All
STLs .zip** (every printable part; assemblies excluded). Parts are packed as
exact float32 vertices + uint32 faces (`fmt: 'f32i'`), so a download is
identical to the exported STL. Verified in headless Chromium: both buttons
download, zip CRC OK, all 11 STLs watertight and identical to `out/stl/`.

## Rules learned the hard way
- STL is float32. Boolean output can hold vertices < 1e-6 mm apart that
  merge on export (tee and wye did — non-manifold). Always export through
  `fittings.export_ready()`: weld at 1e-4 mm, then prove watertight on a
  real STL round trip.
- Never quantise geometry you might print (the viewer's old uint16 packing
  broke watertightness on download).
- Validate every mesh after every boolean. OCCT and manifold both return
  bad results silently (broken fillet; zero-volume sliver shells).
- Never butt faces exactly flush in a boolean — overlap 0.3 mm.
- Never section exactly on a vertex plane; offset ~0.37 mm.
- `str.replace` patches no-op silently: assert the target count, re-read.
- Verification probes derive from parameters, never hard-coded numbers.
- Coupon first, full part second. Tyler's "something looks wrong" has been
  right every time — check it before defending the model.
