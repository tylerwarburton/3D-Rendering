# snake-hide

**Goal:** L-shaped underground hide for a small snake, sitting in a tank
corner so the glass forms two walls - you look straight into the "tomb":
Japanese torii-gate corridor, covered stone stairway entrance (SW), escape
shaft with a stepped rim (NE), coffered corner chamber.
**Status:** final (printed design); parametric for variants.

Repo-wide printer settings and print rules are in the root `CLAUDE.md`.

## Commands (from this folder)

```bash
python build.py                            # -> <repo>/out/snake-hide/stl/snake_hide.stl/.obj (~20 s)
python build.py --substrate 4 --hatch-torii  # any snake_hide.py option passes through
python snake_hide.py --help                # every option (legs, tunnel, walls, substrate, torii, ...)
```

## Fixed dimensions

| What | Value | Source |
|------|------:|--------|
| Long leg (tomb, along front glass) | 7 in (+2 in stair to 9 in, 231 mm) | Tyler 2026-10-10: shrink to fit the 256 bed (8 in was 256.0 mm) |
| Short leg (along right glass) | 5.5 in | snake_hide.py defaults |
| Origin | inside corner where the two panes meet; +X west, +Y north, +Z up | docstring |

## How it's built / rules

- Ordered list of rounded boxes added/subtracted into a signed distance field,
  polygonised with naive surface nets; nothing is left sharp (`--round`,
  `--blend`). Self-checks watertight + sealed interior on every run.
- Faces touching glass are left open; `--closed` prints all four walls.
- `--mirror` (the default) flips x and reverses the winding (it used to leave
  the STL inside-out - the configurator showed the whole roof as overhang).
- Configurator: one preset, the hill on/off. Each build also writes
  `scene.json` (`--scene`): the dirt hill + glass drawn around the hide and the
  path of the "Snake" animation (stairs -> tomb -> hatch -> onto the hill).
  The path must stay >= the snake radius clear of the hide mesh.
