# Working on this repo

Tyler's repo for all his 3D-printed creations. One folder per project under
`projects/`; shared tooling at the root. Each project holds its own context.

**Before touching a project, read its `CLAUDE.md`** (goal, real-world
dimensions, project rules, parts). When Tyler gives a measurement, a test
print result, or a decision, write it into that project's `CLAUDE.md`, and
add a round to its `docs/DESIGN_LOG.md` for every design change.

## Projects

- `projects/python-enclosure/` - ball python enclosure: tube fittings + tank flange (active).
- `projects/waterfall/` - three-tier enclosure waterfall (CadQuery), printed (final).
- `projects/snake-hide/` - L-shaped underground snake hide (torii corridor), final.
- `projects/miata-intake/` - 1990 NA Miata turn-signal duct -> 2.5 in intake adapter (CadQuery).
- `projects/screen-protector/` - Case that closes over a ~7 in screen + its cables; make it structurally sound and bolt-together

## Commands (repo root)

```bash
python new_project.py <name> "<goal>" [--from file.stl ...]   # start a project (from scratch or from STLs)
python build.py <project> [parts/steps]                         # build -> out/<project>/
python presets.py <project>                                     # pre-build every configurator preset
python serve.py                                                 # http://localhost:8000 - a configurator per project
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
- **No STLs in the repo** - only generators (the one exception: a project's
  `source/` STL it modifies). Outputs go to git-ignored `out/`.
- Every project's UI is its **configurator**: on/off presets in
  `configurator.json` (`{"id", "label", "default", "on": [build.py args],
  "off": [args]}`), every combination pre-built by `python presets.py
  <project>` into `out/<project>/presets/` - the page only switches, never
  builds. Presets are features like the enclosure's female/male or the
  hide's hill - never dimension sliders (a build may also write `scene.json` -
  dirt/glass/an animated snake drawn around the part, see snake-hide): Tyler changes sizes by asking in the
  chat, and measured specs stay fixed. **Re-run `presets.py` after any
  generator change.**

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

- `serve.py` - home = a card per project (picture: `out/<p>/cover.stl` if the
  build writes one, else the biggest part of the default preset; optional
  `"cover_view": [x, y, z]` look direction in configurator.json); `/p/<project>` = its configurator.
- `shared/configurator.html` - options -> Generate -> 3D view (size, bed fit,
  grams, >45 deg overhangs, views, section, ruler) + STL/OBJ download.
- `shared/render.py` - numpy z-buffer renderer for PNG review sheets.
- Outputs (`out/`) and STLs are git-ignored, except `projects/*/source/*.stl`.

## How Tyler works

Short messages, often typed fast. He judges by looking, so render or
screenshot changes (serve.py + Chrome) before calling them done. Keeps
things simple and uniform. Ask before big redesigns when there are real
trade-offs.
