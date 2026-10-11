# waterfall

**Goal:** three-tier open-front waterfall for Tyler's ball python enclosure,
8.25 in cube, pump in the back column; prints in one piece with its own
breakaway rib supports (slicer supports OFF).
**Status:** final (printed). Parametric in `src/waterfall.py`.

Repo-wide printer settings and print rules are in the root `CLAUDE.md`.
Run commands from this folder; outputs land in `<repo>/out/waterfall/`.

## Commands

```bash
pip install -r requirements.txt     # needs cadquery
python build.py                     # stl sheets water spill audit (~50 s)
python build.py stl                 # just stl/waterfall.stl (+ STEP, sections) (~7 s)
python build.py concept|overhang|coverage|testprint   # studies + support coupon
```

With `OUT_DIR` set and no steps (the configurator's `presets.py`), only the
printable `waterfall.stl` is written, straight into `OUT_DIR`.

## Fixed dimensions

| What | Value | Source |
|------|------:|--------|
| Footprint | 8.25 in square (209.6 mm) | `SIZE` |
| Height | 202 mm (7.95 in) | back wall top |
| Back wall holes | 0.78 in dia at z 3.25 / 6.25 in | `BACK_HOLE_*` |
| Layer height the ribs are snapped to | 0.2 mm | `SUPPORT_LAYER_H` |
| Rib Z-gap | 0.10 mm (coupon-confirmed) | `SUPPORT_GAP` |

## Where things are

- `src/waterfall.py` - the CadQuery model (only place to edit the design).
- `tools/solids.py` - exports; the printable STL goes through `pk.export()`
  (welds the 4 zero-length corner edges OCCT leaves, proves watertight).
- `tools/` - sheets, hydraulics (`hydro`, `audit` -> report.txt), water /
  spill diagrams, overhang + coverage studies, `support_test` coupon.
- `README.md` - full design notes (drip guides, channels, supports, open items).
- `docs/DESIGN_LOG.md` - **add a round there for each design change.**

## Project rules

- Re-set `SUPPORT_LAYER_H` if the print layer height changes; the rib gap
  only works at the layer height it was snapped to.
- OCCT `fillet()` can return a broken solid without raising - every fillet
  goes through `_valid()`; rim fillets must stay under half the wall (4.5 mm).
