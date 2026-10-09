"""__NAME__ - every part as a function returning a trimesh in PRINT
orientation (flat side down, mm). Put dimensions in the constants block and
note where real-world numbers came from in CLAUDE.md."""
from pathlib import Path

from shared import printkit as pk

HERE = Path(__file__).resolve().parent

# ---- dimensions --------------------------------------------------------------
CLEAR = 0.3            # per side, for anything that fits into something


# ---- parts -------------------------------------------------------------------
def example_plate():
    """Starter part - replace or delete. A plate with an M6 hole."""
    return pk.difference(pk.box(40, 20, 4), pk.cylinder(3.25, 10, z0=-1))


PARTS = {
    "example_plate": example_plate,
}

# Every STL in source/ is a part as-is ("<name>" -> out/.../<name>.stl). To
# change one, write a function that does pk.load(HERE / "source" / ...) and
# edits it, and register it under a new name above.
SOURCE = {p.stem: p for p in sorted((HERE / "source").glob("*.stl"))}
for _name, _path in SOURCE.items():
    PARTS.setdefault(_name, lambda p=_path: pk.on_bed(pk.load(p)))

# Overhang allowed per part (mm2 steeper than 45 deg). Bridges or source STLs
# that need supports go here, with the reason. Unlisted parts: 1 mm2.
OVERHANG_OK = {name: None for name in SOURCE}    # None = not checked (as downloaded)
