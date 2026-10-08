"""Every path in the project resolves from here, so scripts work from any cwd."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
TOOLS = ROOT / "tools"
OUT = ROOT / "out"
STL = OUT / "stl"
IMG = OUT / "img"

for d in (OUT, STL, IMG):
    d.mkdir(parents=True, exist_ok=True)

# design sources live in src/ and are imported as plain modules
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def rel(p):
    """Path relative to the project root, for tidy log lines."""
    try:
        return str(Path(p).resolve().relative_to(ROOT))
    except ValueError:
        return str(p)
