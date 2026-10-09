# Working on this repo

Tyler's repo for all his 3D-printed creations. One folder per project under
`projects/`; shared tooling at the root. Each project holds its own context.

**Before touching a project, read its `CLAUDE.md`** (goal, real-world
dimensions, project rules, parts). When Tyler gives a measurement, a test
print result, or a decision, write it into that project's `CLAUDE.md`, and
add a round to its `docs/DESIGN_LOG.md` for every design change.

## Projects

- `projects/python-enclosure/` - ball python enclosure: tube fittings
  (active), waterfall (printed), snake hide.

## Commands (repo root)

```bash
python new_project.py <name> "<goal>" [--from file.stl ...]   # start a project (from scratch or from STLs)
python build.py <project> [parts/steps]                         # build -> out/<project>/
python serve.py                                                 # http://localhost:8000 - every project + STL browser
pytest -q                                                       # every project's tests
```

## Starting / editing

- New idea -> `python new_project.py`. Fill in its `CLAUDE.md` goal + the
  dimension table from Tyler's measurements before designing.
- Editing an existing STL -> start a project `--from` it (or drop it in a
  project's `source/`). Every source STL is a part as-is; write a function in
  the project's parts module that `pk.load()`s it and changes it.
- `shared/printkit.py` (`from shared import printkit as pk`): load, box,
  cylinder, move/rotate/scale, union/difference/intersection (manifold3d),
  on_bed, export (proves watertight), overhang_area, report.
- `templates/project/` is what new projects are copied from.

## Printer + print rules (all projects unless a project says otherwise)

- Bambu, 256 mm bed, 0.4 mm nozzle, 0.2 mm layers, PLA/PETG.
- **No slicer supports**: every part prints flat side down. Overhangs 45 deg
  max. Bridges are fine up to ~70 mm (leave sag room under moving parts).
- Fit clearance 0.3 mm per side for parts that slide or fit together.
- Print-in-place mechanisms fuse on his printer - make them assemblies.
- He dislikes extra hardware (screws, clips) and visual clutter.

## Geometry rules learned the hard way

- Export through `pk.export()` (or a project's own `export_ready()`): weld,
  then prove watertight on a real STL round trip. Validate every mesh after
  every boolean - booleans fail silently.
- Never butt faces flush in a boolean - overlap 0.3 mm. Never section
  exactly on a vertex plane.
- Rounded corners on a 45 deg taper come out flatter than 45 - build tapers
  from exact solids (offsets / Minkowski mixes), not hulls of mismatched shapes.
- Verification numbers derive from parameters, never hard-coded.
- `pkill -f <pattern>` from the same shell kills the shell - use pids.

## Shared tooling

- `serve.py` - serves `out/`; home lists every `out/<project>/` (its
  `site/` configurator, viewers, STLs) + the STL browser.
- `shared/stl_browser.html` - any STL (listed or dropped): size, bed fit,
  volume, grams, >45 deg overhangs.
- `shared/render.py` - numpy z-buffer renderer for PNG review sheets.
- Outputs (`out/`) and STLs are git-ignored, except `projects/*/source/*.stl`.

## How Tyler works

Short messages, often typed fast. He judges by looking, so render or
screenshot changes (serve.py + Chrome) before calling them done. Keeps
things simple and uniform. Ask before big redesigns when there are real
trade-offs.
