# snake-hide - design log

### Round 1 - own project (2026-10-10)
- Moved out of `projects/python-enclosure/src/` (history there: chat
  "L-shaped snake hide generator script", 2026-09; FINAL). Unchanged; build
  writes to `<repo>/out/snake-hide/stl/`.

### Round 2 - fits the bed, dirt hill view, snake animation (2026-10-10)
- Tyler: "shrink it a bit" (256.0 mm long = flagged too big for the bed) ->
  long leg 8 -> 7 in (one torii fewer); 230.6 x 141.7 x 131.3 mm.
- Whole roof showed red: the mirrored STL was inside-out (negative volume).
  Winding now reversed with the mirror; volume +291.5 cm3, overhang 30,773 ->
  13,650 mm2 (what is left is the bore ceiling = bridges, fine).
- Configurator presets cut to the hill toggle only (lantern on, torii off,
  open to the glass are fixed).
- `--scene`: dirt hill + glass + snake path for the configurator. Path checked
  against the mesh: centre line >= radius - 0.6 mm from every surface, and it
  only goes below the dirt inside the hide.
