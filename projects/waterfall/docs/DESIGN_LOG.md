# waterfall - design log

Newest round first. Full design notes (drip guides, flow channels, breakaway
supports, fillet limits, support coupon) are in `README.md`.

### Round 1 - own project (2026-10-10)
- Moved out of `projects/python-enclosure/` (src/waterfall.py + its tools).
  Design unchanged: 209.6 x 209.6 x 202.0 mm, 1480 cm3, 38 ribs.
- Dropped the old single-file `part_viewer` (tools/viewer.py) and the
  fittings parts of solids/sheets/audit (the enclosure's fittings_viewer
  covers those).
- Printable STL now exported through `pk.export()`: the raw OCCT mesh had 4
  zero-length open edges at the base corners; welded at 1e-4 mm it is
  watertight (volume unchanged, 1480.1 cm3).
- `OUT_DIR` (configurator presets) gets just `waterfall.stl`.
- Checked `C:\Users\tyler\Downloads\waterfall.py` (2026-10-10): identical to
  this source except the `__main__` export path.

### Before the split (from the python-enclosure log)
Three-tier open-front waterfall, 8.25 in cube, pump in the back column.
`DRIP_MODE="column"`, U flow channels (`CHANNEL_FRAC` 0.75), back holes
3.25 / 6.25 in, wall-rib breakaway supports 0.10 mm Z-gap snapped to 0.2 mm
layers, `RIM_EDGE_STYLE="none"`. ~1480 cm3, 38 ribs, 3049 mm line contact.
Verified byte-identical to Tyler's file (2026-09-26).
History: chat "Ball python enclosure water system design" (2026-08).
