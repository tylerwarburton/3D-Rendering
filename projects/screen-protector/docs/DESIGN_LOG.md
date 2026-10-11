# screen-protector - design log

One round per design change, newest first: what Tyler asked, what changed,
why, and how it was checked (tests, numbers, screenshot, test print result).

### Round 2 - bolt-together Base + Lid (2026-10-10)
Tyler: build from Base + Lid; M3 bolts + trapped nuts; the old one flexed /
twisted, the lid lifted, and the screws didn't fit.
- Cause of "screws didn't fit": lid holes were 2.8 mm (M3 is 3.0).
- `case_bottom` = source base + 13 M3 holes through the walls + hex nut
  pockets in the floor underside (nut flush, flats along the wall). Bolts: the
  6 original spots + 3 more per long wall + 1 mid far end.
- `case_lid` = source lid, old holes/counterbores filled, 3.4 holes + 90 deg
  countersinks (flush M3x16 CSK), + a 1.8 x 4 mm skirt wrapping the tray's
  outside (0.3 clearance; open at the cable opening): stops lifting/gaps and
  closes the box so it can't twist. Inside untouched.
- Checked: both watertight, lid/tray 0 mm3 overlap, fits bed (245.8 x 122.7),
  overhang only source chamfers + nut-pocket roof bridges; viewed in browser.

### Round 1 - project started (2026-10-09)
- Goal: Case that closes over a ~7 in screen + its cables; make it structurally sound and bolt-together

## Round: configurator options (2026-10-10)

- Bolt count is now `MID_BOLTS` (extra bolts per long wall, default 3 = same 13 bolts); `bolts()` builds the list.
- Configurator options: MID_BOLTS, BOLT_D, SKIRT_H, SKIRT_T (`configurator.json`).
- Checked: defaults give the same parts; MID_BOLTS=0 generates clean in the configurator.
