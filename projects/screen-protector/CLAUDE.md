# screen-protector

**Goal:** Case that closes over a ~7 in screen + its cables; make it structurally sound and bolt-together
**Status:** designing   <!-- idea | designing | test print | printed | done -->
**Started:** 2026-10-09

Repo-wide printer settings and print rules are in the root `CLAUDE.md`. This
file holds what is specific to THIS project - keep it current: when Tyler
gives a measurement, a fit result from a print, or a decision, write it here
(and the why in `docs/DESIGN_LOG.md`).

## What it's for / where it goes

A case that closes over a ~7 in screen and its cables, which then plug into
devices. Tyler has two existing versions (below) and wants a stronger one
that bolts together.

## Fixed dimensions (real world - never change without a new measurement)

| What | Value (mm) | Source / date |
|------|-----------:|---------------|
| Screen window (both versions) | 155 x 89, centre (89, 53.8) | measured from source STLs 2026-10-09 |
| Round port (cable/connector) | 22 dia through floor, 30 x 30 boss, centre (-29, 22) | source STLs |
| Screen bay inside tray | x 0..179.7, y 0.5..106.1, 10.4 deep | source base.stl |
| Cable opening, -x end wall | y 66.0..92.4, full height | source base.stl |
| Screen module itself (W x H x thick) | ? | ask Tyler - not needed yet (inside untouched) |

## Design rules for this project

<!-- tolerances, clearances, fits learned from test prints, style choices -->
- Clearance for parts that slide/fit together: 0.3 mm per side (default).
- Build from Tyler's Base + Lid (the newer pair). Never change the inside
  (screen bay, electronics bay, port, cable opening) - it already fits.
- Bolt-together = M3 countersunk bolts (M3x16) through lid + wall + floor into
  M3 hex nuts pressed into the floor underside (flush). 3.4 clearance holes -
  the source lid's 2.8 holes are why the screws didn't fit.
- Problems with the original: flexed/twisted, lid lifted/gapped, screws didn't fit.

## Parts

`screen_protector.py` - every part is a function in `PARTS` (print orientation,
flat side down, mm). Any STL dropped in `source/` shows up as a part
automatically; edit it by writing a function that loads and changes it.

| Part | Prints | Notes |
|------|--------|-------|
| `case_bottom` | floor down | source base + 13 bolt holes + nut pockets underneath |
| `case_lid` | top face down | source lid + skirt round the tray, 13 countersunk holes |

## Source STLs (`source/`)

From `Downloads/screen` (2026-10-09). Inputs only - not exported (Tyler
wants only the new parts). The older Rear/Front Case pair was removed.

| File | Size (mm) | What |
|------|-----------|------|
| `base.stl` + `lid.stl` | 241.6 x 118.5, tray 12.9 + lid 3.5 | 6 screws (2.8 pilots in the tray walls, 6.0 counterbores in the lid: 4 corners + 2 at y 38.5); 22 mm port in tray AND lid |

Tray floor 2.5 mm; walls ~4 mm (rear) / ~6 mm (base); cable notch in the -x
end wall. Self-tapping M3 into 2.8 mm pilots in printed walls - the weak
point for a bolt-together build.

## Commands (from the repo root)

```bash
python build.py screen-protector            # every part -> out/screen-protector/stl/
python build.py screen-protector <part>     # one part
pytest projects/screen-protector -q         # watertight, fits bed, no overhang > 45 deg
python serve.py                     # look at it: http://localhost:8000
```
