# 3D-Rendering - all my 3D printing projects

One folder per project, each with its own goal, measurements, rules and
design history; shared tools to build, check and view any STL locally.

## Quick start

```bash
pip install -r requirements.txt
python new_project.py desk-hook "Hook that clips under my desk"     # new from scratch
python new_project.py vase-fix "Fix a downloaded vase" --from vase.stl   # edit an existing STL
python build.py desk-hook          # -> out/desk-hook/stl/
python serve.py                    # http://localhost:8000
pytest -q                          # every project: watertight, fits bed, no supports
```

`serve.py` opens every project in a **configurator**: on/off presets
(`configurator.json`, pre-built by `python presets.py <project>`), 3D view
(bed fit, ~grams PLA, >45 deg overhangs in red, section, ruler) and STL/OBJ
download. Sizes are changed by asking the project chat. The repo
holds generators only - no STLs except a project's `source/` inputs.

## Layout

```
new_project.py        start a project from templates/project/
build.py              runs projects/<name>/build.py
serve.py              local server for out/
shared/
  printkit.py         load / edit / export STLs, print checks
  configurator.html   the per-project configurator page
  render.py           numpy renderer for PNG sheets
templates/project/    CLAUDE.md (goal, dimensions, rules), design log, parts, tests
projects/
  python-enclosure/   ball python enclosure: tube fittings, tank flange
  waterfall/          three-tier enclosure waterfall (printed)
  snake-hide/         underground snake hide
  miata-intake/       Miata duct -> 2.5 in intake adapter
  screen-protector/   bolt-together case for a 7 in screen
out/<project>/        generated (git-ignored)
```

## A project

```
projects/<name>/
  CLAUDE.md           goal, status, real-world dimensions, project rules
  docs/DESIGN_LOG.md  every design change: why, and how it was checked
  <name>.py           PARTS = {name: function -> mesh in print orientation}
  source/             STLs it starts from (tracked in git; each is a part)
  build.py            python build.py <name> [part ...] [--set NAME=VALUE]
  configurator.json   the on/off presets the configurator shows
  tests/              watertight, fits bed, overhang <= 45 deg
```
