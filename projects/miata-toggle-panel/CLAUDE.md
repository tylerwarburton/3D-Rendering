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
| Front shoulder | 16 wide x 3 deep | Tyler, 2026-10-23 |

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
- Tyler rejected the long triangular friction wedges. Each tongue is now a
  straight bar with a short rectangular clip only at its free rear/top end.
  The seated body has 0.2 mm axial clearance and no side interference; a 1.5 mm
  lip snaps behind it. Back-flex clearance increases from 1.5 to 2.5 mm.
- Clip-tip relief is larger than the bar channel: 4.0 mm behind the end lip and
  1.8 mm on each side, extending forward to z=-19.5. The bar keeps its 2.5 mm
  pocket and front anchor unchanged.
- Browser surface naming is enabled for this project. `Name surface` reports
  stable labels for the front, lip, toggle mounts, centre column, flex bars,
  and all eight individual clip ends, plus file coordinates and face direction.
- Correction: extra tip relief belongs only behind the clip, not beside it.
  Side relief returns to the normal 1.0 mm slot; the flex-direction pocket is
  5.0 mm and extends forward to z=-16 mm.
- Final clarification: "behind" means the complete long face opposite the
  toggle body. The combined channel is replaced by a 5 mm pocket behind the
  entire free bar length plus two independent 1 mm edge slots. No separate
  widened tip pocket remains.
- The first 3 mm behind the visible face is a 16 mm-wide shoulder. Rear channel
  clearance now uses that larger envelope, and all added walls/tongue anchors
  begin at z=-3.6, just behind it. Retaining lips stay at the body rear edge.
- After using surface naming, Tyler clarified that `upper_outer_clip_A` itself
  stays; the unwanted feature was the material behind its bar. All solid walls
  now move 1 mm farther from the switch. Flex bars are half thickness (outer
  0.8 mm, centre 0.6 mm), remain at their verified clip position, and connect
  to walls only through short front anchors. The full backside gap stays open.
- Named face `lower_outer_wall - flat bottom` established the next correction:
  move all wall fronts 0.5 mm farther behind the front shoulder, keep primary
  wall faces flat, add only 0.8 mm local pockets directly behind clip ends, and
  double bar thicknesses back to 1.6 mm outer / 1.2 mm centre.
- `centre_column - flat right` identified the exact unwanted material behind a
  flex bar. Every wall now has an opening equal to the bar's 2.6 mm width and
  free length, cut completely through behind each of the eight tabs. Front
  anchors remain; no extra side cuts, tip pockets, or replacement walls.
- Final mechanism clarification supersedes the bar-window attempt: tabs remain
  separate from solid walls (not U-cut). Each outside bar has a 1.6 mm backside
  gap; each centre bar has a 1.2 mm backside gap. Bars start 3 mm farther back
  at z=-7.1, shortening their free length while preserving front anchors and
  all eight retaining clips.
- Retaining lip projection reduced from 1.5 to 1.0 mm at Tyler's request; bar
  thickness, bar length, lip height, and flex pocket remain unchanged.
- The fixed-wall setback from Round 29 created unwanted axial cutouts between
  the wall-bottom faces and the original rear-shell top faces. Extend all three
  fixed walls forward to overlap the rear-shell ledge. Do not change the later,
  shorter flex bars or their thickness-matched backside gaps.
- The source/new-wall transition also left a repeated 0.125 mm inset face on
  both outer walls (identified as F9 beside F10). Fill only the solid front
  section to the existing shell plane, stopping where the flex bars begin.
- Shorten every flex bar another 3 mm to a 12.4 mm free length. Keep all eight
  clips, bar thicknesses, and thickness-matched backside gaps.
- F11 and F12 identify the two faces of the intended narrow centre core. Remove
  the source bezel's wider centre rib completely behind the mounting plate;
  retain only that narrow core plus its four flex tabs, anchors, and clips. The
  narrow core itself must overlap the rear of the face plate so it prints as
  one body; do not restore wider material to make that connection.
- F13 and F14 exposed that the added fixed walls extended 2.15 mm past the
  original straight rear-shell wall at both ends. Limit all three fixed wall
  inserts to the source shell's 23 mm span; retain the separate corner tabs.
- F20/F21 exposed old shell material still blocking part of the flex cavity.
  Cut a straight tab-width relief behind every flex bar from its anchored root
  to z=-23, 0.5 mm past the free end. These are clearance channels in the old
  shell, not U-shaped tongues cut from the new fixed walls.
- F24 and its three matching outer-tab end faces showed excessive projection
  past the 23 mm fixed walls. Halve that outside projection from 1.875 to
  0.9375 mm on the four outer-wall tabs only, keeping their body-side edges.
  Extend each outer relief into its bar to make the flex separation real.
- F26 showed the first 0.2 mm bite stopped 0.05 mm short of the old channel
  face. Deepen all four outer-tab bites to 0.4 mm: 0.15 mm through that face,
  leaving 1.2 mm of the original 1.6 mm bar thickness.
- Thicken the internal/centre column to 1.6 mm, matching both outside walls.
  Preserve the 1.2 mm backside flex gap by recessing only the four local centre
  tab zones; the column base and uninterrupted middle stay the full thickness.
- Make the uninterrupted 21 mm middle span of the centre and both outside walls
  as wide as safely possible. Behind the shoulder all three become 3.95 mm
  thick, stopping 0.4 mm from the 15 mm body envelope. In the front shoulder
  zone use the maximum 16 mm-envelope clearance instead. Do not fill the tab
  end zones or their flex pockets.
- Final simplification: remove the entire printed flex-retention system—eight
  bars, anchors, end clips, relief channels, and tab bites. Keep only three
  continuous support walls with their maximum-width middle reinforcements.
  Retention is handled by the switch hardware and a separate holder; do not add
  that holder to this model.
- After removing the flex system, restore wall material through every former
  tab/cutout zone. The original STL's rear plug envelope spans y=0..27.3 mm, so
  all three continuous walls use that full span rather than the prior 23 mm
  flex-era trim.
- F31 identified the unwanted end face of a 21 mm-wide local reinforcement
  pillar. Remove all four matching pillar transitions by extending the thick
  rear sections across the complete 27.3 mm wall span. Bring the rear outer
  walls and both sides of the centre wall flush to the former F33 body-clearance
  planes; retain only the short front step required by the 16 mm shoulder.
- Final geometry audit supersedes every added-wall experiment above. Build from
  the repaired original STL and keep only: the 23 mm rear extension, filled
  front plate, two 12.2 mm holes, two 16.8 x 29.8 mm rectangular body channels,
  and one straight 2.95 x 27.3 mm centre divider. Do not add outside walls,
  filler strips, reinforcement steps, pillars, flex parts, or local wall cuts.
- Explicit post-audit exception: fill the source STL's two symmetric 23 x 10.5
  mm outer-wall recesses until they are flush with the rectangular channel
  planes at x=6.6 and x=43.15 mm. These simple fillers preserve the 0.4 mm
  shoulder clearance and replace the selected F35 indent with the F36 plane.
- F37/F38 revealed that limiting those fillers to the original indent bounds
  left cap and sloped transition surfaces. Extend both fillers across the entire
  27.3 x 22.55 mm channel-side footprints, z=-23..-0.45, so each outer inner
  wall is one flush plane with no intermediate width or depth transitions.
- F41/F42 identified a final 0.05 mm axial step: channel cutters ended at
  z=-0.45 while the mounting-panel back is z=-0.4. End all three rear cutters
  and both flush fillers at PANEL_BACK_Z so those +Z surfaces are coplanar.
- F43 and three matching end faces showed the rectangular fillers projecting
  past the original rounded rear-shell outline. Clip both fillers against an
  extrusion of the source STL's rear-band convex outline so all four corners
  follow the original curve while retaining the flush channel-side planes.

## Parts

`miata_toggle_panel.py` - every part is a function in `PARTS` (print orientation,
flat side down, mm). Any STL dropped in `source/` shows up as a part
automatically; edit it by writing a function that loads and changes it.

| Part | Prints | Notes |
|------|--------|-------|
| `two_toggle_panel` | 1 test | Minimal two-toggle fit trial; do not print 3 yet |

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
