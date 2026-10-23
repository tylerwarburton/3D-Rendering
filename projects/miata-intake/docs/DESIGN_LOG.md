# miata-intake - design log

One round per design change, newest first: what Tyler asked, what changed,
why, and how it was checked.

### Round 1 - imported into the 3D-Rendering repo (2026-10-10)
- Source, notes and outputs moved over from the Claude project
  (`intake_adapter_source.zip`, `intake-adapter.md`). Only change: build
  output goes to `<repo>/out/miata-intake/`. Earlier history is summarised in
  CLAUDE.md ("Measured off the car" - connector positions 37/112 -> 38/109,
  A flare 15 -> 20 deg, socket clearance 0.40 -> 0.75).

## Round: builds on CadQuery 2.7 + configurator (2026-10-10)

- Build failed on CadQuery 2.7 ("6 pockets + 12 tie ports: invalid solid"). Cause: the D2 upper tie-port wire, splined from 140 points, came out mis-oriented where it crosses the flat boss tip, so the port stayed filled. Fix: `npts=141` for both tie-port wires (outline unchanged to microns).
- params.py derived sizes moved into `derive()`; build.py takes `--set NAME=VALUE` + `OUT_DIR` for the configurator.
- Single-file part viewer removed (configurator replaces it).
- Checked: default build 86 s, valid solid, 144.18 cm3, 159.5 x 67.5 x 138 mm, verify ALL CHECKS PASS; WALL=3.5 + no ribs also valid.

## Car mockup (2026-10-11)
- Tyler asked for a rough car + bay mockup showing the air path into the turbo,
  explodable and playable at speed. Added `tools/mock.py` (`build.py mock`,
  part of the configurator preset) and Car / Explode / Air in the configurator.
- Uses Tyler's false turn signal file (`source/false_turn_signal.stl`) as the
  real housing; everything else is mock shapes. The adapter is unchanged.
- Spec numbers are honest: ram pressure is 0.02 / 0.06 / 0.14 psi at
  30 / 60 / 90 mph - the win is cool outside air to the compressor, not boost.
- Round 2 (Tyler): the housing was upside down -> flipped (side A is the
  driver side); dropped the made-up OEM frame - the adapter slides straight
  onto the housing's duct; NA-shaped body (lofted shell, pop-ups, oval mouth,
  windshield, open cockpit); real plumbing - 4 runners into the turbine,
  downpipe under the car, compressor -> down/forward -> intercooler -> up the
  passenger side -> throttle body. Air shows cool / hot / intercooled colours.
- Round 3 (Tyler): blinker goes inboard, next to the radiator -> side B;
  adapter points straight back; turbo moved back so the turbine is centred on
  the engine, runners straight out sideways; hood / fender crowns raised so the
  wheel arches and engine stay under the body; see-through pipes with the air
  drawn on top so the flow shows. Pop-up Lights / Wink buttons.
- Round 4 (Tyler): blinker outboard after all -> back to side A; housing turned
  to follow the nose (fitted yaw, bezel within 4 mm of the surface); adapter
  flipped upside down and centred on the duct's back opening (it sat too far
  to the driver side).
- Vent centred under the pop-up headlight (Tyler); headlight cover and its
  dark outline no longer overlap (they flickered).
- Adapter seated on the vent: the housing's duct end is the ~136 x 45 rim, so
  the socket now goes over it centred on the rim outline (was ~50 mm outboard,
  centred on the slanted end's bounding box) and the full 28 mm deep, rim on
  the stop ledge. Checked with plan + rear sections of both meshes.
- Air splits four ways at the plenum into the runners; the blinker lens now
  sits in the bezel's light hole (found by ray-casting through the end piece,
  ~17 mm).
- Round 5 (Tyler): vents were left/right swapped -> driver side is file side
  B as printed (blinker outboard), passenger vent added as its mirror; adapter
  upright so its 20 deg end A sits on the duct's flared (outboard) end. Added
  the real-life hardware: the vent's six hollow tabs, the mesh screen
  sandwiched between vent and adapter (screen at the rim + sleeve in the
  0.75 mm clearance with windows at the tabs) and six zip ties (upper port ->
  through the tab -> lower port -> head on the boss). Explode separates them.
- Round 6 (Tyler): snub nose. The vent goes on square (its bezel already has
  the car's curve) and the nose plan is drawn through it: flat across the
  middle, along the bezel, round to the fender. Pop-ups' front edge 1 in
  behind the vent face, vent top 1 in below them; pop-up boxes made shallow
  so they clear the vent and adapter.
- Round 7 (Tyler): pop-ups (and so the vent) sit further back - vent face
  120 mm behind the nose tip. Snub means round, not flat: the nose is a round
  curve from the tip easing onto the bezel's middle, then along the bezel.
  Adapter fit: the vent's duct runs back and ~14 deg outboard and its rim is
  cut square to it, so the adapter now sits along the duct axis, centred on
  the rim (measured from the file) - the duct sits inside the socket all
  round. Radiator 55 mm and intercooler 75 mm thick with a ~75 mm gap.
- Round 8 (Tyler): the vent was angled in; it should angle out with the
  car. The file's duct is skewed ~14 deg to its bezel, so the vent now goes
  on with its duct straight back (the adapter straight back again) and the
  bezel faces forward and out, wrapping the nose corner. Nose was pointed:
  now a broad parabola from the tip meeting the bezel with the bezel's own
  slope (>= 60 mm deep), then riding the bezel to the fender; the bezel's
  inner end sits ~12 mm recessed.
- Round 9 (Tyler, mockup only): pop-ups 2 in further back (`HL_BACK`);
  side view an equilateral triangle, lid curved to the hood (ray-cast off
  the body), lamp on the front face; they roll up 30 deg about a pivot under
  the lid (back sinks into the car) so the lamp face ends vertical. Vents
  dropped 2 in (`VENT_DROP`, Tyler's guess - not measured); closed, the deep
  pop-up still overlaps the adapter in the mock. Charge pipes: smooth
  splines, slid onto stubs (compressor outlet, intercooler necks, throttle
  body) under blue couplers, rerouted clear of the radiator. Engine sim in
  the configurator: Throttle slider -> rpm, turbo spool/lag, manifold
  vacuum/boost, AFR (rich on boost, lean on decel), blow-off on a snap
  shut; air colour/speed/density follow it, throttle plate turns. Cockpit:
  steering wheel faces the driver, dash cluster (speedo, tach) and centre
  tombstone (boost, AFR) as live gauges; Dash button = driver's view.
- Round 10 (Tyler, mockup only): hood raised ~25 mm and crowned in the
  middle (front fender crowns removed); vent height kept off the old hood
  line (`TOP0`). Pop-ups smaller (210 x 200) and pop up again: pivot 20 mm
  behind / 150 mm under the lid's back, 30 deg, front rises ~115 mm, lamp
  face ends vertical. Boost: the engine can make 20+ psi, controlled to 16
  (`BOOST_PSI`, small spike then the wastegate settles it); later spool,
  boost gauge to +25. Turbo housings 1.2x (`TURBO_SCALE`). Tombstone: small
  boost (left) + AFR (right) on top, radio, then a screen of spec dials
  (coolant, oil temp/pressure, IAT, EGT, volts - driven by load).
- Round 11 (Tyler, mockup only): cockpit cut down to the floor pan (it
  stopped at seat-back height, so the cabin read as filled in); carpet, door
  cards, rear bulkhead, reclined seats with headrests, longer tunnel.
  Pop-ups 190 x 190 (square face) with a round lens filling it; they turn
  30 deg about the triangle's centroid (Tyler: axis in the middle, front up
  and forward, back down and back) until the lens face is vertical.
- Round 12 (Tyler picked "real NA flip" from side-view sketches): pop-ups
  are a 190 x 190 x 100 box under a hood-curved lid, round lens on the
  underside facing down when closed; they flip 90 deg on a hinge along the
  lid's back edge and stand up, lens vertical facing forward, lid at the back.
  Replaces the triangle / middle-axis versions.
- Round 13 (Tyler, mockup only): Isolate button - only the vent, blinker,
  tabs, mesh screen, zip ties and the adapter, camera framed on them.
  Bay air toggle - our intake out (vents, adapter, hose, clamps hidden),
  stock amber turn signals in both corners, a cone filter on the turbo inlet
  breathing engine-bay air: particles wander in slow and stop-start from
  behind the radiator and the exhaust, coloured hot (~150 F, a typical
  guess, not measured), hotter still after the compressor and intercooler;
  readout and IAT dial run hotter.
- Round 14 (Tyler, mockup only): the hood is its own panel (cowl to just
  behind the nose, between the pop-ups); Hood button takes it off, the
  pop-ups stay. Risk button: "chance it blows up" meter - a rough knock
  score from boost, IAT (lags like heat soak), lean AFR under boost and low
  rpm under boost, for stock B6 internals on pump gas. Calibrated so idle
  ~0%, 5 psi ~3%, 16 psi outside air ~50%, 16 psi bay air ~97%. Relative
  only - not a real knock model.
- Round 15 (Tyler, mockup only): hood / bay opening no longer a narrow
  rectangle - between the pop-ups up front, then out to the fender tops
  (+-640) from behind the pop-ups' swing back to the cowl, over the front
  wheels. mph slider removed: the sim is parked, out of gear (it only set a
  ram-pressure readout; ram numbers stay in the spec table).
