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
