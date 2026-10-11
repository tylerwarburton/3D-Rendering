# python-enclosure

**Goal:** hardware for Tyler's ball python enclosure - a modular tube system
the snake travels through and a tank-wall flange (optional knife gate).
(The waterfall and the underground hide are their own projects:
`projects/waterfall/`, `projects/snake-hide/`.)
**Status:** tube fittings + flange ACTIVE.

Repo-wide printer settings and print rules are in the root `CLAUDE.md`.
Run commands from this folder; outputs land in `<repo>/out/python-enclosure/`.

## Fixed dimensions (real world)

| What | Value (mm) | Source |
|------|-----------:|--------|
| Acrylic tube OD / ID | 63.1 / 59.5 | 2.5 in clear pipe |
| Flange plates (all) | 94 x 94 | Tyler, test print 2026-10-09 |
| Flange bolt holes | +-40.5 square, M6 | Tyler 2026-10-09 (near the edge, visible) |
| Tank wall (viewer gap only) | 3 | any wall works, bolts get longer |

## Setup and commands

```bash
pip install --break-system-packages trimesh manifold3d shapely numpy scipy rtree mapbox_earcut pillow pytest
pytest -q                          # geometry checks, ~20 s - run after every change
python build.py fittings           # STLs + fittings_viewer.html + site/ in out/python-enclosure/ (~5 min)
python build.py cover              # cover.stl - the home-page card picture (tee fitting)
python tests/browser_viewer.py     # headless check of the built viewer (needs playwright)
python ../../serve.py              # local viewers at http://localhost:8000 (configurator + STL browser)
```

## Where things are

- `src/fittings.py` - every fitting. Socket/bore set once at the top; ports
  use the J-slot twist latch. `assemble(outer, inner, ports, genders)` adds a
  female socket or male end per port. Gate flange = `flange_set(g, gate=True)`
  -> outer plate, one-piece gate body (`gn_body`), blade (`gn_blade(beta)`).
- `tools/fittings_viewer.py` + `tools/viewer_template.html` - the viewer.
  One build writes the single-file `fittings_viewer.html` (must stay
  < ~31 MB) and `site/` (index.html + `data/chunk_N.json`, each <= 9 MB).
- Shared (repo root): `serve.py` (`/p/python-enclosure` opens `site/`), `shared/render.py`.
- `tools/latch_check.py` - latch simulation, male-port check, print audit.
- `docs/DESIGN_LOG.md` - every design round, why it changed, what was checked.
  **Add a round there for each design change.**
- `src/archive_rooms_iris.py` - removed room pods + iris gate, kept for later.

## Hosted viewer

The viewer is published as a claude.ai artifact:
https://claude.ai/artifact/4rmFJKwMERt3m1cZXwumJz - republish with
`file_path = out/python-enclosure/site/index.html` (repo root) and `files = {data/chunk_0..N.json}`; it
needs the `downloads` capability (carried forward automatically).

## Project rules

- Latch: 9 entry slots per socket, 3 lugs per male end, 20 deg twist ->
  joints go together at 9 angles, 40 deg apart (Tyler 2026-10-11).
- Export through `fittings.export_ready()`; the viewer packs exact geometry.
- Gate flange: bolt heads outside the tank, washer + nut on the flat back
  plate under the skirt (no recesses). Skirt must stay clear of a 12 mm washer.
- Each `ProximityQuery` costs ~0.7 GB; build, use, free.
- Viewer build takes ~3-5 min; run it in the background.
