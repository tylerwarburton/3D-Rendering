# miata-intake

**Goal:** adapter that slides over the OEM turn-signal air duct frame on
Tyler's 1990 NA Miata and converts it to a 2.5 in OD intake tube.
**Status:** designing - part + coupons verified; test-fit coupons first.
**Started:** before 2026-10 (imported from a Claude project 2026-10-10)

Repo-wide printer settings and print rules are in the root `CLAUDE.md`. This
file holds what is specific to THIS project - keep it current.

## Commands (from this folder; needs `cadquery`)

```bash
python build.py            # layout, part, verify, coupon, render -> <repo>/out/miata-intake/
python build.py part       # just the part (~6 min) - run long builds in the background
python build.py render     # PNG sheets from the exported STL (~1 min)
```

`src/params.py` = every dimension; `src/adapter.py` = the CadQuery part;
`tools/` = verify, coupons, render, layout (connector map).
Configurator: no options (Tyler: the specs are fixed). **Car** button = rough
mockup (`tools/mock.py`, `build.py mock` -> `mock/*.stl` + `scene.json`)
with Explode, Lights / Wink (pop-ups on rear hinges), a spec table and Air (intake + exhaust particles coloured by
temperature, spinning turbo wheels) at a chosen mph. Tyler's plumbing:
false turn signal -> adapter (its socket slides over the housing's duct end -
that rim is ~136 x 45, the frame this part was measured from - centred on it,
rim against the stop ledge, pointing straight back along the duct, upright
so end A (20 deg) is outboard where the vent's duct flares). In real life the vent rim has the
six hollow tabs and a mesh screen sits between vent and adapter, all held by
zip ties through the ports - the mockup shows tabs, screen and ties
(`mock.hardware()`, built from the adapter's own connector sites). -> short hose
-> turbo cold side (its only inlet) -> down, forward -> intercooler in front
of the radiator -> up the passenger side -> throttle body. Exhaust: 4 runners
straight out sideways, merging into the turbine (hot side), which is centred
on the engine's length -> downpipe, dumps under the car. Only the adapter and
`source/false_turn_signal.stl` are real; the car, bay and turbo are mock
shapes. Never change the adapter to suit the mockup (Tyler: it fits). build.py still takes `--set NAME=VALUE` on params; `derive()` recomputes the derived sizes.

Parametric CadQuery part that slides over the OEM turn-signal air duct frame
on Tyler's 1990 NA Miata and converts it to a 2.5 in OD tube.

## False turn signal (source/false_turn_signal.stl)

Tyler's printed false turn signal (smaller blinker + an air slot), both sides
in one file (2026-10-11). Each side is 3 touching pieces, ~300 x 118 x 57 mm;
bezel faces -y, length along x, duct runs +y. On the car it sits upside down
(as printed) with the blinker OUTBOARD - side B (y > 0) is the driver side,
side A the passenger side (Tyler 2026-10-11, after trying all of them).
On the car: centred under the pop-up headlight, its face 1 in ahead of the
pop-up's front edge and its top 1 in below it (Tyler); the pop-ups sit well
back of the nose. The vent's duct is skewed ~14 deg to its bezel: on the car
the duct runs straight back and the bezel faces forward and OUT, wrapping
the nose corner (Tyler: angled out, not in). The snub nose is round (not
pointed, not flat) and rides the bezel's curve out to the fender. Its duct
measures ~45 mm tall outside.

## Side naming (embossed on the part)

A = -X short end (20° flare) · B = +Y long face (B1, B2) ·
C = +X short end (7.5° flare) · D = -Y long face (D1, D2). Numbering runs
1, 2 from the A end. Letters embossed 0.8 mm proud on the socket wall below
each connector. Use these names in all discussion.

## It is a clamshell

Side B is split from the mouth to z=37, just under the top of the collar, so
the socket springs open over the frame. The blend and tube above stay closed.

- split 1.2 mm wide, ending in a 1.6 mm round — a square end there is where
  a flexing part cracks
- two clamp ears flank it, 10 mm wide, 8 mm proud, with one tie hole
  (5.6 × 2.4) through both and across the split. A tie there closes the
  split after fitting so it stops flexing.
- ear undersides sit at 45° (tip shifted up relative to base) so they print
  without support
- `COUPON_SLIT` is off — the ring coupon inherits the real split

## How the attachment works

**The OEM connector is hollow.** The tie enters the upper port, threads down
through the connector, and leaves by the lower port.

- Pocket 16 × 7 × 4.8 deep, tab top flush with the frame's outer rim
- Two **slanted ports** per connector: 9 × 5.2 on the outside, ±7.6 mm from
  tab centre, slanting in to land inside the pocket at ±1.3, starting 0.5 mm
  off the bore surface
- **The six pockets are the only breaks in the inner wall.** `verify` probes
  the wall behind every port to prove it.

## Measured off the car

- Frame 136 × 44 mm at the outer rim, corner radius ~6 mm
- Long faces flat and parallel; short ends flare outward away from the
  outlet: **A 20°** (was 15, read too shallow), C 7.5°
- Connector footprint 14 × 6 mm, flush at the top of the frame, hollow
- B1/D1 centre 38 mm from the A end face, B2/D2 centre 109 mm (71 apart).
  History: 37/112 → 37/105 → 33/109 → 38/109, each step eyeballed against a
  render or print.
- Socket clearance 0.75 mm (0.40 printed too snug)

## Current state (verified)

160 × 67.5 × 138 mm, 144 cm³, watertight single body, all checks pass.

## Still assumed

- `TAB_PROUD` 3.0, `SOCKET_DEPTH` 28.0, side D matching side B

## Hard-won notes (OCCT / trimesh / process)

- `Shape.Volume()` (GProp) is **unreliable on spline surfaces** — read
  146 cm³ for a prism that is actually 201. Validate on a tessellation.
- Build every section from one wire generator so lofts share exact
  interfaces; mixing an exact prism with a spline loft leaves slivers.
- A single non-ruled loft through straight-blend-straight pinches the
  straight runs ~7%. Separate lofts sharing interface wires do not.
- `Workplane.revolve()` resolves its axis in workplane-local coords. A loft
  of circles is a filled disc stack, not a ring.
- **Anything ending exactly tangent to a lofted surface tears the mesh.**
  Ribs bury 0.6 mm; tie ports start 0.5 mm off the bore; the mouth lead-in
  is a section of the bore loft, not a separate cut (381 broken faces as a
  cut).
- `clean()` throws on some overlapping-cutter results — `safe_clean` falls
  back to the uncleaned shape. **Do not pre-fuse cutters**: 6-7 min → 17.
- `slice_mesh_plane(cap=True)` fails where the plane lands on mesh vertices;
  `coupons._slice_clean()` searches for a clean height.
- **Verification probes must be derived from params, never hard-coded.** Bit
  five times now; the latest sent the bore ray straight down the new split
  and it found nothing. `_clear_spot()` takes a `blocks` list so any new
  feature can be excluded.
- **`str.replace` silently no-ops when the target is absent.** Several
  patches "succeeded" while changing nothing, one leaving a slow code path
  in place for multiple builds. Always assert the target exists and re-read
  the file after writing.
- **Timing:** `build.py part` ~6 min. `build.py render` reads the exported
  STL (~1 min); `RENDER_FINE=1` opts into a full rebuild — never casually.
  Bash calls cap at 10 min, so long builds go
  `setsid nohup python3 -u ... &` with polling (`-u` matters).

## Test coupons

Sliced out of the exported part at mesh level so they cannot drift.

- `coupon_connector` — the C end, ~9 cm³. Pocket fit, port alignment with
  the connector's hollow, the 7.5° flare. Print first.
- `coupon_mouth_ring` — socket + collar, ~59 cm³, carrying the split and
  both clamp ears.

## Tooling

`build.py all` → layout / part / verify / coupon / render.
Orthographic z-buffer renderer, ray-cast and point-containment verification,
single-file Three.js viewer with a section plane, PIL-drawn connector map.
