# __NAME__

**Goal:** __GOAL__
**Status:** designing   <!-- idea | designing | test print | printed | done -->
**Started:** __DATE__

Repo-wide printer settings and print rules are in the root `CLAUDE.md`. This
file holds what is specific to THIS project - keep it current: when Tyler
gives a measurement, a fit result from a print, or a decision, write it here
(and the why in `docs/DESIGN_LOG.md`).

## What it's for / where it goes

<!-- the real-world use, what it attaches to, what it must survive -->

## Fixed dimensions (real world - never change without a new measurement)

| What | Value (mm) | Source / date |
|------|-----------:|---------------|
|      |            |               |

## Design rules for this project

<!-- tolerances, clearances, fits learned from test prints, style choices -->
- Clearance for parts that slide/fit together: 0.3 mm per side (default).

## Parts

`__SLUG__.py` - every part is a function in `PARTS` (print orientation,
flat side down, mm). Any STL dropped in `source/` shows up as a part
automatically; edit it by writing a function that loads and changes it.

| Part | Prints | Notes |
|------|--------|-------|

## Source STLs (`source/`)

<!-- where each came from (link, author, license) and what was changed -->

## Commands (from the repo root)

```bash
python build.py __NAME__            # every part -> out/__NAME__/stl/
python build.py __NAME__ <part>     # one part
pytest projects/__NAME__ -q         # watertight, fits bed, no overhang > 45 deg
python serve.py                     # look at it: http://localhost:8000
```
