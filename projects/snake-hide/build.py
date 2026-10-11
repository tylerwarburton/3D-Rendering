#!/usr/bin/env python3
"""Build the snake hide: python build.py [snake_hide.py options...]
-> <repo>/out/snake-hide/stl/snake_hide.stl (+ .obj), or $OUT_DIR when the
configurator runs it. Options pass straight through, e.g.
`python build.py --substrate 4 --hatch-torii`."""
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = Path(os.environ.get("OUT_DIR") or HERE.parents[1] / "out" / "snake-hide" / "stl")

if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    sys.exit(subprocess.call([sys.executable, "-u", str(HERE / "snake_hide.py"),
                              "--out", str(OUT / "snake_hide"), "--no-viewer",
                              "--scene", str(OUT / "scene.json"), *sys.argv[1:]]))
