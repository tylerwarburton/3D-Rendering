# miata-toggle-panel

**Goal:** Two standard toggle switches in each of the three driver-side Mazda Miata dashboard switch openings
**Status:** test print   <!-- idea | designing | test print | printed | done -->
**Started:** 2026-10-22

Repo-wide printer settings and print rules are in the root `CLAUDE.md`. This
file holds what is specific to THIS project - keep it current: when Tyler
gives a measurement, a fit result from a print, or a decision, write it here
(and the why in `docs/DESIGN_LOG.md`).

## What it's for / where it goes

The three switch positions to the left of the driver in a Mazda Miata. One
printed shim holds two panel-mount toggle switches; print three shims for six
switches total.

## Fixed dimensions (real world - never change without a new measurement)

| What | Value (mm) | Source / date |
|------|-----------:|---------------|
| Bezel exterior | 53.75 x 31.30 x 20.50 | downloaded STL, 2026-10-22 |
| Front opening | 41.50 x 24.50 | downloaded STL, 2026-10-22 |
| Front-face location | z = 2.00 | downloaded STL, 2026-10-22 |
| Rear switch-body width | 14 | Tyler correction, 2026-10-23 |
| Rear body width at centred protrusion | about 15 | Tyler correction, 2026-10-23 |
| Depth before clip expansion | 3 | Tyler, 2026-10-23 |
| Rear body reported height | about 29 | Tyler, 2026-10-23; still provisional |
| Rear body depth | 20 | Tyler, 2026-10-23 |
| Terminals beyond body | 8 | Tyler, 2026-10-23 |
| Terminal arrangement | top centre, bottom centre, left-middle | Tyler, 2026-10-23; rear view |
| Centred side protrusion length | 21 | Tyler, 2026-10-23 |

## Design rules for this project

<!-- tolerances, clearances, fits learned from test prints, style choices -->
- Clearance for parts that slide/fit together: 0.3 mm per side (default).
- Preserve the downloaded outside and retention geometry.
- Print with the visible front face on the bed.
- Hardware is a lever-style ON-OFF-ON toggle: round washer/nut and metal lever
  on the visible front, rectangular body and side clips behind the panel.
- Hardware must be rendered as scene-only reference geometry, like the
  miata-intake car mockup. It must never appear in the printable parts list.
- Each switch must appear independently in the browser scene's sidebar so
  Tyler can toggle its visibility.
- In the car, the bezel's 53.75 mm long side runs vertically, so the two
  switches are stacked top-to-bottom.
- Each switch is three-position: upper ON, centre neutral/OFF, lower ON. Its
  lever throw runs parallel to the bezel's long vertical axis.
- Treat the 15/17/29/20 mm dimensions as a provisional rear-body envelope,
  never as a visible rectangular rocker face.
- Current browser trial rotates both complete switches 90 degrees around their
  mounting axes and shows both simultaneously. This makes the 29 mm rear-body
  dimension horizontal but also changes lever throw from vertical to
  left/right; that tradeoff remains in the deep-cage fit-test revision.
- Tyler approved exploring a structural fit around the rotated bodies: preserve
  the visible outer lip, cut away the interfering original rear walls, extend
  the plug deeper, and add printed guides/clips for stability.
- First structural trial extends the original rear profile from 18.5 to 23 mm,
  clears 17.8 x 29.8 mm channels, and adds a shared centre guide plus flexible
  outer arms with 0.10 mm snap interference. Washer/nut remain primary retention.
- Tyler found the open guide frame did not visibly or mechanically cradle the
  switch bodies. The conforming revision uses 0.15 mm running clearance on all
  four sides, 0.8 mm flexible walls along the 29 mm faces, mid-depth friction
  ribs with 0.10 mm interference, and the existing rear snap nubs.
- Tyler then clarified that the added walls appeared separated from the
  original shell and still did not look like true flex clips. The next revision
  splits each long cradle wall into two fixed strips plus a 6 mm cantilever
  between 1 mm relief slots. Fixed strips overlap the retained original walls;
  the finger has a rear lead-in and bows 0.25 mm inward for 0.10 mm interference.
- Tyler moved the intended clips off the stretched 29 mm walls: those walls are
  rigid bearing surfaces. Flex clips now occupy the two shorter, thicker outer
  walls and both sides of a split centre column. Four independent cantilevers
  bow 0.25 mm toward the 17 mm body faces.
- Hardware orientation: flip the lower switch to -90 degrees and keep the upper
  at +90 degrees so each odd side-middle terminal points away from the centre.
  Printed outer clips are therefore at the bottom/top, with two independent
  centre-column clips between the switches.
- Clip construction clarified: every clip must be a tongue inside a visible
  U-shaped channel cut from an otherwise solid wall. The tongue stays anchored
  at the front, is free at the rear, and carries a two-way wedge hook that
  forces it aside during both insertion and removal. Four total: bottom, top,
  and two separate tongues in the centre column.
- Fitment correction: remove the long walls along both 29 mm switch faces so
  the broad body edges remain uncovered. Keep bottom/top clip walls and widen
  the centre column to 2.65 mm, leaving roughly 0.05 mm fixed-face clearance
  outside its two tongue channels.
- Added walls must never extend beyond the downloaded plug's 0..27.3 mm side
  wall edges. Bottom/top walls now use that exact width and sit 0.05 mm from
  the provisional body envelope; the centre wall fills the full 2.75 mm body
  gap and is flush outside its two tongue channels.
- The 21 mm centred protrusion leaves confirmed 4 mm plain-base zones at each
  end. Fixed walls stay flush to the 17 mm protrusion envelope; 2.6 mm-wide
  tabs are offset into the end zones and step inward to the 15 mm base. Outer
  tabs are 1.6 mm thick, centre tabs 1.2 mm, with 0.50 mm hook interference
  and a longer 3 mm release ramp.
- Final requested count is four corner tongues per toggle: low/high tabs on its
  outer wall and low/high tabs on its centre-column side. Eight total, all
  inside the confirmed 4 mm plain-base zones.
- Latest body correction reduces the rear base from 15 to 14 mm and the centred
  protrusion envelope from 17 to 15 mm. Keep the 12.2 mm mounting hole. Hook
  interference increases from 0.50 to 1.00 mm and its peak moves from the body
  entrance to z=-14 mm, closer to the printed face, with release by z=-10 mm.
- Every U-channel now includes 1.5 mm of asymmetric clearance behind its tongue
  (away from the switch) plus 0.2 mm ahead, so the 1.0 mm hook deflection cannot
  bottom out against the surrounding wall.

## Parts

`miata_toggle_panel.py` - every part is a function in `PARTS` (print orientation,
flat side down, mm). Any STL dropped in `source/` shows up as a part
automatically; edit it by writing a function that loads and changes it.

| Part | Prints | Notes |
|------|--------|-------|
| `two_toggle_panel` | 1 test | Deep-cage rotated-body fit trial; do not print 3 yet |

## Source STLs (`source/`)

`miata_starter_switch_blank (1).stl` was Tyler's newest matching Downloads
file on 2026-10-22. Its duplicate without `(1)` has the same SHA-256. The
source had one missing triangle; the generator repairs it, fills the front
opening, and drills two toggle holes. Origin/author/license are not yet known.

## Commands (from the repo root)

```bash
python build.py miata-toggle-panel            # every part -> out/miata-toggle-panel/stl/
python build.py miata-toggle-panel <part>     # one part
pytest projects/miata-toggle-panel -q         # watertight, fits bed, no overhang > 45 deg
python serve.py                     # look at it: http://localhost:8000
```
