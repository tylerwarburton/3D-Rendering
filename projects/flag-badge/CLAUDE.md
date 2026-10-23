# flag-badge

**Goal:** Remove a side logo from an STL and add a raised, paintable US flag (test plate first)
**Status:** designing   <!-- idea | designing | test print | printed | done -->
**Started:** 2026-10-15

Repo-wide printer settings and print rules are in the root `CLAUDE.md`. This
file holds what is specific to THIS project - keep it current: when Tyler
gives a measurement, a fit result from a print, or a decision, write it here
(and the why in `docs/DESIGN_LOG.md`).

## What it's for / where it goes

Tyler's STL has a logo on its side: grind it flat, put the biggest US flag
that fits there, raised, so he can colour it with Bambu Studio's face/fill
painter. First: a test plate (flag on a backing rectangle) to dial the flag in.

The real thing is 3 STLs (2026-10-17): a connector + a left wall + a right
wall; the connector joins the walls. Plan: remove the logo from the
connector's side, assemble all 3 as they fit together, put a flag across
each end (connector + that wall), then export each piece separately to print.
Decisions 2026-10-17: upright banner (stripes vertical, real 1.9:1
proportions, canton at the BOTTOM; the two ends mirror each other - canton on the high-x side of both), BOTH ends, raised blue + indented stars, raised LESS (0.6),
use the rounded edges to make it wider (~37 mm instead of ~29).
2026-10-17: flag ENTIRELY on the walls' front faces (none on the connector), starting 2 mm past the seam, canton next to the connector.

<!-- the real-world use, what it attaches to, what it must survive -->

## Fixed dimensions (real world - never change without a new measurement)

| What | Value (mm) | Source / date |
|------|-----------:|---------------|
| In use | on its side: +x (walls' rounded edge) up, rods horizontal | Tyler 2026-10-17 |
| Wall offset to assemble (x, z) | 244.54, 18.73, then flipped end over end about x 232.19 | rod holes = ear holes; walls stand on ear tops; rounded edge up like the connector (Tyler 2026-10-17) |
| Wall front / back | front = outer end face (flag), back = the face toward the other wall | Tyler 2026-10-17 |
| Seam (ear top = wall bottom) z | 208.21 | source STLs |
| Side hole, +y end of connector (keep clear) | x 244-250, z 179-184.5 | source STL |
| End faces y (+/-) | -187.93 / -273.91 | source STLs; logo engraved 0.25 deep on +y end of connector; filled exactly flush (no other dims change) |

## Design rules for this project

<!-- tolerances, clearances, fits learned from test prints, style choices -->
- Clearance for parts that slide/fit together: 0.3 mm per side (default).
- Flag = separate pieces 0.01 mm apart (GAP) so each stripe is its own flat
  face to fill-paint. Two test versions (Tyler prints both):
  - `flag_test_plate`: no raised canton, backing is blue, stars = nubs on it.
  - `flag_test_plate_canton`: raised blue canton, stars = posts in holes with
    a 0.4 mm domed top, peak level with the canton (reads as indented).
- Flag prints upright like it's flying: stripes horizontal, canton top-left.
- Backing around the flag stays one flat face (blue = the canton colour).

## Parts

`flag_badge.py` - every part is a function in `PARTS` (print orientation,
flat side down, mm). Any STL dropped in `source/` shows up as a part
automatically; edit it by writing a function that loads and changes it.

| Part | Prints | Notes |
|------|--------|-------|
| `flag_test_plate` | on its long edge | 95 x 50 flag on a 107 x 62 x 4 backing; stripes +1.2, star nubs +1.2 on the blue backing |
| `flag_test_plate_canton` | on its long edge | same, plus raised canton +1.2 with stars in 0.01 mm-clearance holes |
| `connector_flag` | as source (bottom down) | logo filled flush; no flag (name kept) |
| `left_wall_flag` / `right_wall_flag` | upright, as source | the whole flag on the front face; flat would make the rod holes overhang |
| `assembly_preview` | not printed | all three in place, turned the way it's used |

## Source STLs (`source/`)

- `connecter.stl`, `left.stl`, `right.stl` - Tyler's pieces (2026-10-17). Connector had a logo on its +y end.

<!-- where each came from (link, author, license) and what was changed -->

## Commands (from the repo root)

```bash
python build.py flag-badge            # every part -> out/flag-badge/stl/
python build.py flag-badge <part>     # one part
pytest projects/flag-badge -q         # watertight, fits bed, no overhang > 45 deg
python serve.py                     # look at it: http://localhost:8000
```
