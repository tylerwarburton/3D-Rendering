"""Shared helpers for every project: load / edit / export STLs + print checks.

    from shared import printkit as pk
    m = pk.load("source/thing.stl")              # any STL -> one trimesh
    m = pk.difference(m, pk.cylinder(3.25, 20))  # booleans (manifold3d)
    pk.export(pk.on_bed(m), pk.out_dir("my-project") / "thing.stl")
    print(pk.report(m))

Printer defaults (Bambu, 0.4 nozzle, 0.2 layers, no supports) live here;
a project overrides them in its own constants if it needs to.
"""
import io
from pathlib import Path

import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[1]
BED = (256.0, 256.0, 256.0)     # X1 / P1 / A1 build volume, mm
MAX_OVERHANG = 45.0             # deg from vertical, no supports
PLA = 1.24                      # g/cm3


def out_dir(project):
    """out/<project>/stl/, created. serve.py shows everything under out/."""
    d = ROOT / "out" / project / "stl"
    d.mkdir(parents=True, exist_ok=True)
    return d


# ---------------------------------------------------------------- load + edit
def load(path):
    """Any STL (or OBJ/3MF/...) -> a single welded trimesh, mm."""
    m = trimesh.load(str(path), force="mesh")
    m.merge_vertices()
    return m


def box(x, y, z):
    """Box with its bottom on z = 0, centred in x/y."""
    m = trimesh.creation.box(extents=(x, y, z))
    m.apply_translation((0, 0, z / 2))
    return m


def cylinder(r, h, z0=0.0, sections=96):
    """Vertical cylinder from z0 to z0 + h, on the z axis."""
    m = trimesh.creation.cylinder(radius=r, height=h, sections=sections)
    m.apply_translation((0, 0, z0 + h / 2))
    return m


def move(m, x=0.0, y=0.0, z=0.0):
    m = m.copy()
    m.apply_translation((x, y, z))
    return m


def rotate(m, deg, axis=(0, 0, 1)):
    m = m.copy()
    m.apply_transform(trimesh.transformations.rotation_matrix(np.radians(deg), axis))
    return m


def scale(m, s):
    """Uniform (number) or per-axis (x, y, z) scale."""
    m = m.copy()
    m.apply_scale(s)
    return m


def union(*meshes):
    return _check(trimesh.boolean.union(list(meshes), engine="manifold"))


def difference(m, *cutters):
    return _check(trimesh.boolean.difference([m, *cutters], engine="manifold"))


def intersection(*meshes):
    return _check(trimesh.boolean.intersection(list(meshes), engine="manifold"))


def _check(m):
    if not m.is_watertight or m.volume <= 0:
        raise RuntimeError("boolean result is not a watertight solid")
    return m


def on_bed(m):
    """Drop onto z = 0, centred in x/y (print position)."""
    m = m.copy()
    lo, hi = m.bounds
    m.apply_translation((-(lo[0] + hi[0]) / 2, -(lo[1] + hi[1]) / 2, -lo[2]))
    return m


# ---------------------------------------------------------------- export + checks
def export(m, path, digits=4):
    """Weld, then PROVE the file is watertight by reading the STL back.
    STL is float32: boolean slivers < 1e-6 mm apart can merge on save and
    leave broken edges - this raises instead of writing a bad file."""
    m = m.copy()
    m.merge_vertices(digits_vertex=digits)
    m.update_faces(m.nondegenerate_faces())
    m.update_faces(m.unique_faces())
    m.remove_unreferenced_vertices()
    buf = io.BytesIO()
    m.export(buf, file_type="stl")
    buf.seek(0)
    back = trimesh.load(buf, file_type="stl")
    if not back.is_watertight:
        raise RuntimeError(f"{path}: not watertight after STL round trip")
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    m.export(str(path))
    return m


def overhang_area(m, limit=MAX_OVERHANG):
    """mm2 of downward faces steeper than `limit` (from vertical), ignoring
    faces on the bed. Exactly 45 deg passes."""
    n, c, a = m.face_normals, m.triangles_center, m.area_faces
    bad = (n[:, 2] < -np.cos(np.radians(limit)) - 1e-3) & (c[:, 2] > m.bounds[0][2] + 0.2)
    return float(a[bad].sum())


def report(m, bed=BED):
    """Numbers to judge a part by before slicing."""
    ext = m.extents
    return dict(
        size=tuple(round(float(x), 1) for x in ext),
        fits_bed=bool(all(e <= b for e, b in zip(ext, bed))),
        volume_cm3=round(float(m.volume) / 1000, 1),
        grams_pla=round(float(m.volume) / 1000 * PLA),
        overhang_mm2=round(overhang_area(m), 1),
        watertight=bool(m.is_watertight),
    )
