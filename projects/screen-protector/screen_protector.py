"""screen-protector - every part as a function returning a trimesh in PRINT
orientation (flat side down, mm). Put dimensions in the constants block and
note where real-world numbers came from in CLAUDE.md.

case_bottom / case_lid = Tyler's Base + Lid (source/), made bolt-together:
every bolt runs lid -> wall -> floor into a hex nut pressed into the floor
from underneath; the lid gets a skirt that wraps the tray's outside edge.
The screen + electronics space inside is untouched."""
from pathlib import Path

import numpy as np
import shapely.geometry as sg
import trimesh

from shared import printkit as pk

HERE = Path(__file__).resolve().parent

# ---- dimensions --------------------------------------------------------------
CLEAR = 0.3            # per side, for anything that fits into something

# source geometry (measured from source/base.stl + lid.stl, see CLAUDE.md)
OUTER = (-56.0, -6.0, 185.6, 112.5)     # tray outline x0, y0, x1, y1
FLOOR_Z, TOP_Z, LID_Z = -2.5, 10.4, 13.9  # floor bottom, wall top, lid top
NOTCH_Y = (66.0, 92.4)                  # cable opening in the -x end wall (full height)
OLD_HOLES = [(-53.0, -3.0), (-53.0, 109.5), (-52.7, 38.5), (-3.3, 38.5),
             (181.7, -2.1), (181.7, 108.6)]

# M3 countersunk bolts (ISO 10642) into M3 hex nuts
BOLT_D = 3.4           # clearance
CSK_D = 6.4            # countersink top diameter (head 6.0), 90 deg
NUT_AF, NUT_H = 5.5 + CLEAR, 2.4 + 0.1
BOLT_LEN = 16          # M3x16: lid top to just past the nut, never out the bottom

MID_BOLTS = 3          # extra bolts along each long wall, between the corners


def bolts():
    """6 original screw spots + MID_BOLTS along each long wall + 1 mid far end wall."""
    mid = np.linspace(-53.0, 181.7, MID_BOLTS + 2)[1:-1]
    return OLD_HOLES + [(float(x), -3.0) for x in mid] + [(float(x), 109.5) for x in mid] + [(182.7, 53.25)]


SKIRT_T, SKIRT_H = 1.8, 4.0    # lid skirt around the tray's outside


# ---- helpers -----------------------------------------------------------------
def _prism(poly, z0, z1):
    m = trimesh.creation.extrude_polygon(poly, height=z1 - z0)
    m.apply_translation((0, 0, z0))
    return m


def _hex(x, y, z0, z1):
    """Hex nut pocket, flats facing +-y (fits inside the 6 mm long walls)."""
    r = NUT_AF / 2 / np.cos(np.pi / 6)
    pts = [(x + r * np.cos(a), y + r * np.sin(a)) for a in np.radians(np.arange(0, 360, 60))]
    return _prism(sg.Polygon(pts), z0, z1)


def _cyl(x, y, r, z0, z1):
    return pk.move(pk.cylinder(r, z1 - z0), x, y, z0)


# ---- parts -------------------------------------------------------------------
def case_bottom():
    """Base tray: through holes for every bolt + nut pockets in the floor
    underside (nut flush with the bottom). Prints floor down, as is."""
    m = pk.load(HERE / "source" / "base.stl")
    cut = []
    for x, y in bolts():
        cut.append(_cyl(x, y, BOLT_D / 2, FLOOR_Z - 1, TOP_Z + 1))
        cut.append(_hex(x, y, FLOOR_Z - 1, FLOOR_Z + NUT_H))
    return pk.difference(m, *cut)


def case_lid(assembled=False):
    """Lid: old 2.8 holes / 6.0 counterbores filled, M3 clearance +
    countersink at every bolt, skirt down around the tray (open at the cable
    opening). Prints top face down (skirt up, countersinks at exactly 45)."""
    m = pk.load(HERE / "source" / "lid.stl")
    x0, y0, x1, y1 = OUTER
    tray = sg.box(x0, y0, x1, y1)
    out = tray.buffer(CLEAR + SKIRT_T, join_style=1)
    ring = out.difference(tray.buffer(CLEAR, join_style=2))
    ring = ring.difference(sg.box(x0 - 5, NOTCH_Y[0] - 0.5, x0 + 2, NOTCH_Y[1] + 0.5))
    fill = [_cyl(x, y, 3.2, TOP_Z + 0.5, LID_Z - 0.01) for x, y in OLD_HOLES]
    m = pk.union(m, _prism(out.difference(tray.buffer(-1.0, join_style=2)), TOP_Z, LID_Z),
                 _prism(ring, TOP_Z - SKIRT_H, TOP_Z + 0.3), *fill)
    cut = []
    for x, y in bolts():
        cut.append(_cyl(x, y, BOLT_D / 2, TOP_Z - 1, LID_Z + 1))
        cone = trimesh.creation.cone(radius=CSK_D / 2 + 1.0, height=CSK_D / 2 + 1.0, sections=64)
        cone.apply_transform(trimesh.transformations.rotation_matrix(np.pi, (1, 0, 0)))
        cone.apply_translation((x, y, LID_Z + 1.0))               # tip down, 45 deg flank
        cut.append(cone)
    m = pk.difference(m, *cut)
    if assembled:
        return m
    return pk.on_bed(pk.rotate(m, 180, (1, 0, 0)))


PARTS = {
    "case_bottom": case_bottom,
    "case_lid": case_lid,
}

# source/base.stl + lid.stl are inputs only (Tyler: only the new parts).

# Overhang allowed per part (mm2 steeper than 45 deg), with the reason.
# Unlisted parts: 1 mm2.
OVERHANG_OK = dict(
    case_bottom=650,   # source's 0.5 mm bottom-edge chamfer + 13 nut-pocket roofs (6 mm bridges)
    case_lid=300,      # source's 0.4 mm chamfers, flipped onto the first layer
)
