# flag-badge - design log

One round per design change, newest first: what Tyler asked, what changed,
why, and how it was checked (tests, numbers, screenshot, test print result).

### Round 12 - walls flipped, clean logo fill (2026-10-17)
- Tyler: on-its-side orientation is right, but the walls are upside down -
  connector is U'd at the bottom / rounded on top, walls had U up. Walls now
  flipped end over end about the middle rod hole (WALL_FLIP_X 232.19); holes
  still line up (<0.08 mm) and the wall's rounded edge now matches the
  connector's curve exactly. Flag widened to END_X 213.5..250.5 (hoist 37).
- Tyler: the logo cover rectangle bled into air and showed. Replaced with
  thin strips on a 0.25 grid - only cells fully on the face (depth < 0.4) and
  touching the logo floor - sunk 0.02 below the face (flush strips left
  float32 slivers). Checked: no logo left, nothing changed outside the logo
  and flag, 27 tests pass.

### Round 11 - real-use orientation (2026-10-17)
- Tyler: walls look wrong - their top is rounded, bottom U'd. Assembly (hole
  match) is right; in use the whole thing lies on its side, walls' rounded
  edge (+x) up, rods horizontal. So in use the end flags fly normally
  (stripes horizontal, canton top; +y end canton top-left, -y end mirrored).
- assembly_preview now shown in that orientation. Print parts unchanged.

### Round 10 - clear the side hole (2026-10-17)
- Tyler: the flag covers one of the holes slightly - move it more onto the walls.
- The hole: +y end of the connector, x 244-250, z 179-184.5. FLAG_MIN_Z 185.5;
  flag start picked so the seam falls midway between two star rows (bot 186.55,
  stars clear the seam by 0.13 > SEAM_GAP). Canton now split at the seam like
  the stripes. Checked: hole open (ray goes through), 27 tests pass, rendered.

### Round 9 - ends mirror each other (2026-10-17)
- Tyler: one end right, the other flipped - they should mirror each other.
  Kept the logo (+y, left wall) end; the -y end now has its canton on the same
  high-x side, so it reads mirrored. Awaiting Tyler's check of which end is right.

### Round 8 - canton to the bottom (2026-10-17)
- Tyler: wrong flip - undo it and flip the other axis. Canton back on the
  viewer's left, now at the BOTTOM of the banner, all on the connector
  (ends 0.5 below the seam); stripes run up across the seam onto the wall.

### Round 7 - flag mirrored (2026-10-17)
- Tyler: flag is backwards (not upside down). Canton moved to the viewer's
  right on both ends. 27 tests pass.

### Round 6 - flags on the real pieces (2026-10-17)
- Tyler dropped connecter/left/right STLs; wants the logo gone and a flag on
  the connector + walls side, each piece downloadable separately.
- Assembled by matching rod holes (walls +244.54 x, +18.73 z). End face shared
  by connector + wall is only ~29 x 178 flat -> Tyler chose an upright banner,
  both ends, raised blue + indented stars; then "less raised" and "use the
  curved part" -> END_RAISE 0.6, pieces follow the surface depth profile
  (ray-cast) across the rounded edges: hoist 36.2 (x 214.2..250.4), fly 68.8.
- Canton sits fully on the wall (0.5 above the seam); stripes split at the
  seam, stopping 0.1 short each side (0.005 left float32 slivers on export).
- Logo filled with a box flush to the end face. Walls print upright as the
  source did (flat = 2017 mm2 rod-hole overhang).
- Checked: 27 tests pass, all pieces watertight single bodies; looked at it in
  the configurator.

### Round 5 - both star versions (2026-10-15)
- Tyler: likes the stars indented with the blue sticking out too - have both
  ready, he'll print both.
- Added `flag_test_plate_canton`: raised canton (CANTON_H back), star holes
  STAR_D + 2*GAP, stars = posts with STAR_DOME 0.4 tops peaking at RAISE.
- Checked: 6 tests pass; canton version = 14 flat paint faces + backing.

### Round 4 - no canton, stars flush with stripes (2026-10-15)
- Tyler: stars stick out the same as the stripes; the backing will be blue,
  so the stars don't need a raised blue base.
- Removed the raised canton; stars = spherical-cap nubs on the backing,
  1.2 mm tall (= RAISE). Dropped STAR_RAISE / CANTON_H.
- Checked: tests pass, 13 separate stripe faces + 1 backing face, star peaks
  level with stripe tops.

### Round 3 - raise doubled (2026-10-15)
- Tyler: looks good, make everything stick out more.
- RAISE 0.6 -> 1.2, STAR_RAISE 0.6 -> 1.2 (nubs now ~hemispheres).
- Checked: tests pass, still 14 separate stripe/canton faces + 1 backing face.

### Round 2 - flag test plate (2026-10-15)
- Tyler: full flag, stars as rounded nubs, stripes as rectangles, 0.01 mm
  slits so each piece is its own face to paint; flying orientation; test on
  a rectangle first before the real STL.
- Built `flag_test_plate`: 13 stripes + canton (+0.6 mm), 50 spherical-cap
  nubs (+0.6 mm), all 0.01 mm apart, on a 4 mm backing with 6 mm border.
- Checked: watertight, tests pass, 14 separate flat top faces + 1 backing face.
  Overhang = the 0.6 mm stripe ledges + nub undersides (allowed in OVERHANG_OK).

### Round 1 - project started (2026-10-15)
- Goal: Remove a side logo from an STL and add a raised, paintable US flag (test plate first)

## Round 13 - logo patch truly flush (2026-10-17)

Tyler could still see the logo outline. The filler stopped 0.02 mm short of
the face (LOGO_SINK), so the logo's edge still showed. The filler's outer face
now uses the end face's exact float32 y from the mesh, so it is coplanar and
the export stays watertight. Ray check: no logo depth is left. The only
recessed strip left (x 213.2-213.45) is the part's original rounded edge, so
the rest of the part keeps its dimensions.

## Round 14 - flags only on the walls (2026-10-17)

Tyler wanted the flag entirely on the walls. Each end flag (37 x 70 mm)
now sits only on its wall's front face, starting 2 mm past the seam (FLAG_GAP),
with the canton next to the connector. The wall face is flat along its whole
131 mm, so the flag doesn't need to cross the seam anymore. That made
FLAG_MIN_Z (side-hole clearance) and SEAM_GAP unnecessary. The connector now
only has the logo filled.
