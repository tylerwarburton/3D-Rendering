# 3D-Rendering - ball python enclosure hardware

Parametric source for Tyler's 3D-printed enclosure parts, plus the tooling to
view and check them before committing to a print.

- **Tube fittings** (active) - a modular, twist-latching "hamster tube" system
  for 2.5 in clear acrylic pipe (63.1 mm OD / 59.5 mm ID): elbows at any angle,
  couplers, tees, wyes, U-bends, vent tubes, caps (male/female), an in-line
  slide gate, and a tank-wall flange with an optional knife gate.
- **Waterfall** (printed) - three-tier open-front water feature, 8.25 in cube.

**Interactive viewer:** https://claude.ai/artifact/4rmFJKwMERt3m1cZXwumJz
(pick any fitting, change ports/angle/vents, download STLs).

## Quick start

```bash
pip install -r requirements.txt     # cadquery only needed for the waterfall
pytest -q                           # fittings geometry checks, ~20 s
python build.py fittings            # fitting STLs + out/fittings_viewer.html
python build.py                     # waterfall: STL, sheets, audit, viewer
```

Everything generated lands in `out/` (git-ignored). `src/` is the only place
to edit; the tooling reads the design parameters at runtime.

## Layout

```
build.py                 one entrypoint for every build step
src/
  fittings.py            the fitting family (trimesh + manifold3d)
  waterfall.py           CadQuery model of the waterfall (as printed)
  snake_hide.py          L-shaped underground hide (SDF + surface nets)
  archive_rooms_iris.py  removed room pods + iris gate, kept for later
tools/
  fittings_viewer.py     packs every fitting variant into the viewer
  viewer_template.html   Three.js viewer UI
  latch_check.py         latch simulation, male-port check, print audit
  render.py              numpy z-buffer renderer + cutaways
  overhang.py, ...       waterfall tooling (needs cadquery)
tests/
  test_fittings.py       pytest: latches, watertight, gate collisions, printability
  browser_viewer.py      headless-browser check of the built viewer
docs/
  DESIGN_LOG.md          every design round: what changed, why, how it was checked
```

## Fittings in short

- Socket 63.80 ID x 30 deep, bore 59.50 (stepless with tube inserted), 4 mm
  walls, 70 mm bend radius. All dimensions set once at the top of `fittings.py`.
- Ports latch with a 30 deg J-slot twist and a detent click. Any port can be
  female (socket) or male (built-in plug), so fittings join directly.
- Optional hex vent pattern on elbows, couplers, tees, wyes, U-bends.
- **Gate flange**: outer plate + one-piece gate body + blade. 4 M6 bolts
  clamp the tank wall (length = 8 mm + wall + nut; 3 mm wall -> M6x20).
  The blade crosses the neck 25 mm inside the tank and clicks open/closed.
- Everything prints without supports on a 0.4 mm nozzle (checked by the tests).

## Waterfall - where the design stands

Verified against the printed `waterfall__24_.stl`: the rebuild from `src/` is
identical to within tessellation noise, so the Python is the source of truth.
All nine fittings generate watertight.

### Drip guides

`src/waterfall.py` now carries a `DRIP_MODE` switch:

| mode | behaviour |
|---|---|
| `"stub"` | original 8 mm nub. Water sheets down the outer wall, detaches at the rounded tip and free-falls 7 mm between tiers, 22 mm into the basin. |
| `"column"` | **default.** The guide runs straight down and lands on the wetted floor below: 32.1 mm on the top and mid tiers, 75.3 mm from the bottom pool to the basin floor. |

A column has no detachment point, so there is no free fall and nothing to
splash. The tip is deliberately left **flat, not rounded** - once it meets the
floor there is no drip edge to shape, and a rounded tip would only shrink the
contact patch and leave a crevice ring at the joint. `COLUMN_FOOT_FLARE` splays
the last 3 mm so the floor joint is a 45 degree transition rather than a sharp
internal corner, which is the hardest place in a pool to clean.

The flat foot also means each column carries load, so the cantilevered shelf
above it is propped rather than hanging. Columns cost about 33 cm3 of extra
material (1314 -> 1347 cm3).

### Flow channels

`CHANNEL_ENABLE` cuts a U-groove into the outer face below each slit, running
unbroken from the slit invert down to the bottom of the guide. Default is
`CHANNEL_FRAC = 0.75` of the slit width (9.5 mm) and `CHANNEL_DEPTH = 1.2` mm,
leaving 3.3 mm of the 4.5 mm wall. Costs about 5 cm3.

Continuity is the point: the groove has to cross the wall-to-guide transition
with no step, because a step is where the stream detaches.

The cutter is a cylinder whose axis sits `r - depth` IN FRONT of the face, and
it is intersected with a box so it can never exceed `CHANNEL_DEPTH`. Putting
the axis behind the face instead bores clean through the wall.

### Breakaway supports

`SUPPORT_ENABLE` prints sacrificial supports standing on the floor below each
shelf. Against the roughly 2060 cm3 of slicer support the shelves would
otherwise generate, **turn slicer supports off entirely** when printing these.

`SUPPORT_STYLE` picks the shape:

| style | count | contact | material |
|---|---|---|---|
| `"wall"` | 38 ribs | 3049 mm of line, 1372 mm2 bonded | 139 cm3 |
| `"tree"` | 14 trunks | 37 dots | 17 cm3 |
| `"pin"` | 37 spires | 37 dots | 42 cm3 |

`"wall"` is the default because thin ribs are what people actually hand-model.
Tree and pin shapes are what a *slicer* generates automatically - good for
organic models, but not the usual choice for modeled supports. A 1 mm rib is
two to three perimeters wide, prints stably without whipping, and peels out in
one piece along its length instead of leaving a scatter of dots to pick off.
It also gives continuous line contact rather than points, which is far better
under a flat ceiling like these shelves.

Each rib is profiled over its height rather than being a plain slab:

| height | width | why |
|---|---|---|
| tip | 0.45 mm | one extrusion width, minimum interface |
| taper (4 mm) | 0.45 -> 1.0 | narrows where the load is negligible |
| body | 1.0 mm | 2-3 perimeters, stable to print |
| neck (1.2 mm) | 0.6 mm | the only FUSED joint - deliberately the weakest point |

**The two ends are not equal.** The tip has a 0.2 mm Z-gap, so it is not
fused and lifts away. The foot cannot have a gap - a rib has to stand on
something - so it is welded to the pool floor below. That joint is the whole
removal problem, and it is worth understanding before printing:

| interface | area | fused? |
|---|---|---|
| tip -> shelf ceiling | 1372 mm2 | no, 0.2 mm gap |
| foot -> pool floor | 1829 mm2 | **yes** |

The foot is now 0.6 mm, narrower than the 1.0 mm body. That is deliberate: it
puts the weakest section exactly at the joint so a rib snaps at the floor
rather than tearing somewhere up its length, and it cut the fused area from
6098 mm2 to 1829 mm2. Raise `SUPPORT_WALL_FOOT_T` toward 1.0 if the 75 mm
bottom-tier ribs come loose mid-print.

**Which surface gets scarred is worth a thought.** The ceiling these ribs
protect is the UNDERSIDE of a pool floor - an exterior surface nobody touches.
The floor they are fused to is the INSIDE of the pool below, which holds water.
So the supports trade a cosmetic surface for a functional one. If you would
rather not sand 3 m of rib witness lines out of the pools, `SUPPORT_ENABLE =
False` and some droop on the undersides is a defensible choice - the floors are
6 mm thick and only the bottom layer or two would sag.

The taper halves the bonded interface: a rib meeting the ceiling at full
thickness bonds over 1.0 mm of width, and tapering to 0.45 mm cuts that to
374 mm2 over 832 mm of rib.

The foot is deliberately small. The usual "widen the foot" advice is about
BUILD PLATE adhesion, and no rib here touches the plate - they all stand on
already-printed pool floor, which bonds fine. A 3 x 3 mm foot running the full
length of every rib was 20% of the support material and fused a broad bar to a
surface that has to be cleaned afterwards.

`python build.py coverage` measures what is actually held up, rather than
trusting the nominal pitch. It builds masks from the same segment list the
geometry uses, then distance-transforms the unsupported region to find the
widest void on each ceiling:

| shelf | ceiling | worst void | beyond 15 mm |
|---|---|---|---|
| top | 83 cm2 | 19 mm | 2% |
| mid | 146 cm2 | 20 mm | 2% |
| bottom | 225 cm2 | 25 mm | 8% |

Three bugs were found this way, all of which silently gutted coverage:

1. **Ribs with no obstruction were dropped entirely.** The segment scan only
   closed a run when it hit a blocker, so a rib that was clear along its whole
   length never got emitted - deleting every rib in the outer half of each
   shelf. Worst void was 130 mm.
2. **Guide exclusions blocked the whole rib line.** A drip guide occupies a
   small patch, but the test blocked every y at that x. Now bounded in y.
3. **The pump box was treated as forbidden.** Its roof is solid and 22 mm
   below the bottom shelf - a perfectly good floor. Ribs there now land on it,
   which fixed the 58 mm void over the back half of the bottom shelf.

`SUPPORT_WALL_PITCH` is 12 mm, leaving an 11 mm unsupported span between ribs.
FDM bridges under about 10-15 mm cleanly, 10-30 mm with droop, and needs
support past 30 mm - so 12 mm pitch sits inside the clean band. 18 mm pitch
(17 mm span) is in the droop band and will show on the ceiling.

Ribs are automatically broken into segments wherever they would cross the
riser, the pump box or a drip guide, and segments shorter than
`SUPPORT_MIN_RUN` are dropped.

**The Z-gap is the whole trick.** `SUPPORT_GAP` defaults to `SUPPORT_LAYER_H`
(0.2 mm) - exactly one layer height, never zero. The first layer above droops
onto the support just enough to print, then releases cleanly. Zero welds the
support on; too much lets the overhang sag. **Re-set `SUPPORT_LAYER_H` if you
change layer height** - the gap has to match what you actually print at.

Because of that gap the supports are geometrically separate bodies inside the
same file, which is what slicers expect. Do not enable auto-supports on top.

Sources for the numbers: [Dreaming3D, "Stop Fighting Your Slicer: Design Your
Own Supports in CAD"](https://dreaming3d.net/blogs/news/stop-fighting-your-slicer-design-your-own-supports-in-cad)
(one-layer Z-gap, 0.8-1.2 mm ribs, 0.4-0.8 mm XY clearance, widened feet);
[UltiMaker community thread on custom support air
gaps](https://community.ultimaker.com/topic/11299-air-gap-requirement-for-custom-supports/)
(match the gap to layer height); [printpal supports
guide](https://printpal.io/wiki/supports-guide) (0.20-0.25 mm interface gap,
sacrificial geometry as an alternative to support material).

### Back wall penetrations

Moved 0.5 in apart: lower hole 3.25 in, upper 6.25 in, 3 in centre to centre,
56 mm of wall between the bores. The riser cavity is clear from z=61 mm (pump
box roof) to z=185 mm (cap underside), so with a 4 mm margin the lower hole
could drop to 2.95 in and the upper rise to 6.74 in if more spread is wanted.

The trade-off: a column that reaches the floor removes the visible cascade -
the water runs down a post instead of falling. Raise `COLUMN_LAND_GAP` above the
water line to get the cascade back, at the cost of the structural support.

Open items, in the order they matter:

1. **Weir capacity is 179 L/h per pool.** Above that the slits drown and water
   sheets over the rim. Most small pumps start at 200 L/h.
2. **Side slits have only 8.2 mm of catch margin** over the pool below - which
   is why the columns matter. In `"stub"` mode a stream leaving faster than
   0.09 m/s misses the pool entirely; in `"column"` mode the water never leaves
   the guide, so the margin stops mattering.
3. **The cap outlet is a 7.94 mm jet.** Past roughly 300 L/h it fountains out
   of the 6.3 mm cup instead of welling over the lip.
4. **The back-wall taper never cuts.** `BACK_TOP_W` and `TAPER_START_Z` are
   declared but the wedge cutters land in already-removed space, so the wall
   prints full width.
5. **Fittings:** an unoccupied socket leaves a 2.15 mm internal ledge; the hook
   cradle is exactly pipe OD with zero clearance.

Basin fill window is 38–68 mm (1.50–2.66 L). Below that the pump runs dry on
startup; above it the basin overflows when the pools drain back on shutdown.

## Fillet limits

Rounding is capped by the wall the fillet sits on: a rim fillet eats the radius
from both faces, so it must stay under half the wall thickness. `POOL_WALL` is
4.5 mm, and a 2.5 mm rim fillet does not fail cleanly — it hangs the geometry
kernel indefinitely. 2.0 mm is already close to the limit. Any "round
everything" pass needs radii keyed to local wall thickness, not one global
number.

## Mesh notes

The exported STL is not strictly manifold: the kernel's tessellation leaves a
handful of zero-volume slivers along coincident faces. This is pre-existing -
`waterfall_stub.stl` has exactly the same five components - and slicers handle
it. `out/stl/waterfall.step` is the clean solid if a slicer ever objects.

## Fillet validation (why a hole appeared)

`fillet()` in OCCT can return a **broken solid without raising an exception**.
The original code treated "no exception" as success, so when the 5 mm basin rim
fillet failed and the 4 mm fallback came back malformed, the loop accepted it
and a hole appeared where the basin rim runs out into the back wall on the
right-hand side.

Two changes guard against it now:

- `_valid()` checks every fillet and chamfer result, so a bad radius is
  rejected and reported rather than silently kept.
- `tools/solids.mesh_health()` reports open edges and their location after each
  export, so a defect like this is caught the moment it appears.

The basin rim edges are the fragile spot: they form a U that dead-ends into the
rising back wall, and that run-out is what the kernel cannot always build.
`RIM_EDGE_STYLE` defaults to `"none"` for a guaranteed-valid part. Set it to
`"fillet"` and watch the log - if your toolchain reports the full 5.0 mm you get
the rounded rim, and if it backs off you will be told.

## Support test coupon

`python build.py testprint` writes `out/stl/support_test.stl` - a 197 x 86 mm
plate, 88 cm3, that answers the three open questions before you commit to the
full 1480 cm3 print. Instructions land in `out/support_test_instructions.txt`.

| row | varies | labels |
|---|---|---|
| A | Z-gap | 10 / 15 / 20 / 25 / 30 (= 0.10-0.30 mm) |
| B | foot neck | 4 / 6 / 8 / 10 (= 0.4-1.0 mm) |
| C | bare bridging, no ribs | 12 / 16 / 20 / 25 (clear span, mm) |

Every rib is generated by `waterfall._rib_solid` with the module parameters
temporarily overridden, so the coupon is not a lookalike - what breaks here
breaks the same way on the real part.

Print it at the layer height and material you will use for the waterfall; the
Z-gap result is only valid for the layer height it was tested at.
