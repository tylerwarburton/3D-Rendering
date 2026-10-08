# Working on this repo

Tyler's 3D-printed parts for a ball python enclosure: the **tube fittings**
(`src/fittings.py`, active) and the **waterfall** (`src/waterfall.py`, printed,
finished). He prints on a Bambu, 0.4 mm nozzle, 0.2 mm layers, PLA/PETG,
**no slicer supports** - every part must print flat-side down without them.

## Setup and commands

```bash
pip install --break-system-packages trimesh manifold3d shapely numpy scipy rtree mapbox_earcut pillow pytest
pytest -q                          # geometry checks, ~20 s - run after every change
python build.py fittings           # STLs + out/fittings_viewer.html + out/site/ (~5 min)
python tests/browser_viewer.py     # headless check of the built viewer (needs playwright)
```

Waterfall tooling (`python build.py`, default steps) also needs `cadquery`.

## Where things are

- `src/fittings.py` - every fitting. Socket/bore set once at the top; ports
  use the J-slot twist latch. `assemble(outer, inner, ports, genders)` adds a
  female socket or male end per port. Gate flange = `flange_set(g, gate=True)`
  -> outer plate, one-piece gate body (`gn_body`), blade (`gn_blade(beta)`).
- `tools/fittings_viewer.py` + `tools/viewer_template.html` - the viewer.
  One build writes the single-file `out/fittings_viewer.html` (must stay
  < ~31 MB) and `out/site/` (index.html + `data/chunk_N.json`, each <= 9 MB).
- `tools/latch_check.py` - latch simulation, male-port check, print audit.
- `docs/DESIGN_LOG.md` - every design round, why it changed, what was checked.
  **Add a round there for each design change.**
- `src/archive_rooms_iris.py` - removed room pods + iris gate, kept for later.

## Hosted viewer

The viewer is published as a claude.ai artifact:
https://claude.ai/artifact/4rmFJKwMERt3m1cZXwumJz - republish with
`file_path = out/site/index.html` and `files = {data/chunk_0..N.json}`; it
needs the `downloads` capability (carried forward automatically).

## Rules learned the hard way

- Export through `fittings.export_ready()` (welds + proves watertight on a real
  STL round trip). Validate every mesh after every boolean.
- Never butt faces flush in a boolean - overlap 0.3 mm. Never section exactly on
  a vertex plane.
- Overhangs: 45 deg is the limit; rounded corners on a 45 deg taper come out
  flatter - use sharp (mitre) offsets. Bridges are fine up to ~70 mm on his
  printer if the moving part under them has sag room.
- Print-in-place mechanisms fuse on his printer - make them assemblies.
- Each `ProximityQuery` costs ~0.7 GB; build, use, free.
- `pkill -f <pattern>` from the same shell kills the shell - use pids.
- Run the viewer build detached (`setsid nohup python3 -u -m tools.fittings_viewer &`).

## How Tyler works

Short messages, often typed fast. He judges by looking at the viewer, so
render or screenshot changes before calling them done. He dislikes extra
hardware (screws, clips) and visual clutter; keeps things simple and
uniform. Ask before big redesigns when there are real trade-offs.
