# python-enclosure - ball python enclosure hardware

Parametric source for Tyler's 3D-printed enclosure parts, plus the tooling to
view and check them before committing to a print.

- **Tube fittings** (active) - a modular, twist-latching "hamster tube" system
  for 2.5 in clear acrylic pipe (63.1 mm OD / 59.5 mm ID): elbows at any angle,
  couplers, tees, wyes, U-bends, vent tubes, caps (male/female), an in-line
  slide gate, and a tank-wall flange with an optional knife gate.
- The **waterfall** is its own project now: `projects/waterfall/`.

**Interactive viewer:** https://claude.ai/artifact/4rmFJKwMERt3m1cZXwumJz
(pick any fitting, change ports/angle/vents, download STLs).

## Quick start

```bash
pip install -r requirements.txt
pytest -q                           # fittings geometry checks, ~20 s
python build.py fittings            # fitting STLs + out/fittings_viewer.html
```

### View locally

```bash
python ../../serve.py               # http://localhost:8000 (opens the browser)
```

The **Configurator** has every combination (port F/M, elbow angles, vent
styles, flange with/without gate). The STL browser shows the default exports.

Everything generated lands in `<repo>/out/python-enclosure/` (git-ignored). `src/` is the only place
to edit; the tooling reads the design parameters at runtime.

## Layout

```
build.py                 one entrypoint for every build step
src/
  fittings.py            the fitting family (trimesh + manifold3d)
  archive_rooms_iris.py  removed room pods + iris gate, kept for later
tools/
  fittings_viewer.py     packs every fitting variant into the viewer
  viewer_template.html   Three.js viewer UI
  latch_check.py         latch simulation, male-port check, print audit
  (render.py moved to <repo>/shared/)
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
- **Flanges**: 94 x 94 plates, same 4 bolt holes (+-40.5) plain or gated.
- **Gate flange**: outer plate + one-piece gate body + blade. 4 M6 bolts,
  heads outside the tank; washer + nut on the gate body's flat back plate,
  visible under the skirt (length = 16 mm + wall; 3 mm wall -> M6x20).
  The blade crosses the neck 25 mm inside the tank and clicks open/closed.
- Everything prints without supports on a 0.4 mm nozzle (checked by the tests).
