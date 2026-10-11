"""Every path in the project resolves from here, so scripts work from any cwd.
ROOT = this project folder; outputs go to <repo>/out/<project name>/."""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]                 # repo root (shared/ lives there)
SRC = ROOT / "src"
TOOLS = ROOT / "tools"
OUT = REPO / "out" / ROOT.name
STL = OUT / "stl"
IMG = OUT / "img"
PRINT = Path(os.environ.get("OUT_DIR") or STL)   # printable STLs only (configurator sets OUT_DIR)

for d in (OUT, STL, IMG, PRINT):
    d.mkdir(parents=True, exist_ok=True)

# design sources live in src/ and are imported as plain modules
for _p in (SRC, REPO):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))


def rel(p):
    """Path relative to the repo root, for tidy log lines."""
    try:
        return str(Path(p).resolve().relative_to(REPO))
    except ValueError:
        return str(p)
