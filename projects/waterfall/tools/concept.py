"""Side-by-side of the two drip-guide modes now living in src/waterfall.py.

    DRIP_MODE = "stub"    8 mm nub, water detaches and free-falls
    DRIP_MODE = "column"  runs straight down and lands on the floor below

Renders both from identical viewpoints so the difference is the geometry,
not the camera.
"""
import numpy as np
import cadquery as cq
import trimesh

from . import paths, solids
from shared import render as R
import waterfall as W

AQUA = (70, 190, 178)
EXPORT = dict(tolerance=0.06, angularTolerance=0.15)

SEC_VIEW = (-1.0, 0.03, -0.03)
LOW_VIEW = (0.9, 0.45, 0.30)
SECROP = np.array([[-5, -25, 118], [5, 105, 200]])
LOWCROP = np.array([[-110, -60, 55], [10, 105, 205]])
BASECROP = np.array([[-5, -5, 116], [5, 45, 152]])


def build_mode(mode):
    """Build the model under a given DRIP_MODE, restoring the setting after."""
    prev = W.DRIP_MODE
    W.DRIP_MODE = mode
    try:
        return W.build()
    finally:
        W.DRIP_MODE = prev


def column_lengths():
    out = []
    for tier, ((iw, idp), rim) in enumerate(zip(W.POOL_INNER, W.POOL_RIM_Z)):
        shelf = rim - W.POOL_DEPTH_Z - W.POOL_FLOOR_T
        land = (W.POOL_RIM_Z[tier + 1] - W.POOL_DEPTH_Z
                if tier + 1 < len(W.POOL_RIM_Z) else W.FLOOR)
        out.append((["top", "mid", "bottom"][tier], shelf - land, land))
    return out


def run():
    print("concept:")
    for name, length, land in column_lengths():
        print(f"    {name:<7} column {length:5.1f} mm, lands at z={land:.1f} mm")

    for mode in ("stub", "column"):
        solid = build_mode(mode)
        cq.exporters.export(solid, str(paths.STL / f"waterfall_{mode}.stl"), **EXPORT)
        cq.exporters.export(solids.section(solid, "x", "neg"),
                            str(paths.STL / f"waterfall_{mode}_section.stl"), **EXPORT)
        print(f"    {mode:<7} {solid.val().Volume()/1000:6.0f} cm3")

    a_full = solids.load("waterfall_stub")
    b_full = solids.load("waterfall_column")
    a_sec = solids.load("waterfall_stub_section")
    b_sec = solids.load("waterfall_column_section")

    from .water_diagram import _water_slabs
    water = trimesh.util.concatenate(_water_slabs(half=True))

    def wet(sec):
        comb = trimesh.util.concatenate([sec, water])
        return comb, np.arange(len(sec.faces), len(comb.faces))

    ca, aa = wet(a_sec)
    cb, ab = wet(b_sec)

    imgs = [
        R.render(ca, view_dir=SEC_VIEW, size=(640, 640), bounds=SECROP, ss=2,
                 accent_faces=aa, accent=AQUA, pad=0.10),
        R.render(cb, view_dir=SEC_VIEW, size=(640, 640), bounds=SECROP, ss=2,
                 accent_faces=ab, accent=AQUA, pad=0.10),
        R.render(a_full, view_dir=LOW_VIEW, size=(640, 640), bounds=LOWCROP, ss=2),
        R.render(b_full, view_dir=LOW_VIEW, size=(640, 640), bounds=LOWCROP, ss=2),
        R.render(cb, view_dir=SEC_VIEW, size=(640, 640), bounds=BASECROP, ss=2,
                 accent_faces=ab, accent=AQUA, pad=0.14),
        R.render(b_full, view_dir=(0.85, 1.0, -0.5), size=(640, 640),
                 bounds=b_full.vertices, ss=2),
    ]
    labs = [
        'DRIP_MODE = "stub"  -  tip ends 7 mm above the water',
        'DRIP_MODE = "column"  -  runs down and meets the floor',
        '"stub"  -  underside, shelves hang unsupported',
        '"column"  -  underside, every shelf is propped',
        '"column"  -  flat foot, splayed joint at the floor',
        '"column"  -  whole part',
    ]
    R.grid(imgs, labs, 2, str(paths.IMG / "concept_columns.png"))
    print(f"  concept_columns -> {paths.rel(paths.IMG / 'concept_columns.png')}")
