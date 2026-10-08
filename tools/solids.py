"""Build every solid from the Python sources and export meshes.

Nothing else in the project calls CadQuery directly; everything downstream
reads the STLs this module writes.
"""
import cadquery as cq
import trimesh

from . import paths

TOL = dict(tolerance=0.05, angularTolerance=0.1)
TOL_FAST = dict(tolerance=0.12, angularTolerance=0.35)

BIG = 400.0


def waterfall_solid():
    import waterfall as W
    return W.build()


def section(solid, axis="x", keep="neg", at=None):
    """Cut a solid with a half-space so interiors can be seen.

    axis: 'x' | 'y' | 'z'      keep: which side of the plane survives
    at:   plane position in mm (defaults to the model centre for x/y)
    """
    bb = solid.val().BoundingBox()
    centre_z = (bb.zmin + bb.zmax) / 2
    if at is None:
        at = 0.0 if axis in "xy" else centre_z

    if axis == "x":
        cutter = cq.Workplane("XY").box(BIG, BIG, BIG, centered=(False, True, True))
        cutter = cutter.translate((at, 0, centre_z))
        if keep == "pos":
            cutter = cq.Workplane("XY").box(BIG, BIG, BIG, centered=(False, True, True)) \
                .translate((at - BIG, 0, centre_z))
    elif axis == "y":
        cutter = cq.Workplane("XY").box(BIG, BIG, BIG, centered=(True, False, True))
        cutter = cutter.translate((0, at, centre_z))
        if keep == "pos":
            cutter = cq.Workplane("XY").box(BIG, BIG, BIG, centered=(True, False, True)) \
                .translate((0, at - BIG, centre_z))
    else:
        cutter = cq.Workplane("XY").box(BIG, BIG, BIG, centered=(True, True, False))
        cutter = cutter.translate((0, 0, at))
        if keep == "pos":
            cutter = cq.Workplane("XY").box(BIG, BIG, BIG, centered=(True, True, False)) \
                .translate((0, 0, at - BIG))
    return solid.cut(cutter)


def mesh_health(path, label=""):
    """Report open edges on an exported mesh and where they are.

    A fillet that comes back malformed shows up here as a cluster of open
    edges, which is exactly how the back-right basin corner was found.
    """
    import numpy as np
    m = trimesh.load(str(path))
    m.merge_vertices()
    groups = trimesh.grouping.group_rows(m.edges_sorted, require_count=1)
    n = len(groups)
    if n <= 8:
        print(f"    mesh ok ({n} stray edges, tessellation noise)")
        return n
    pts = m.vertices[m.edges[groups]].reshape(-1, 3)
    lo, hi = pts.min(0), pts.max(0)
    print(f"    ! {label or path}: {n} OPEN EDGES - hole near "
          f"x[{lo[0]:.0f},{hi[0]:.0f}] y[{lo[1]:.0f},{hi[1]:.0f}] "
          f"z[{lo[2]:.0f},{hi[2]:.0f}]")
    return n


def build_waterfall(fast=False):
    tol = TOL_FAST if fast else TOL
    solid = waterfall_solid()

    out = {}
    p = paths.STL / "waterfall.stl"
    cq.exporters.export(solid, str(p), **tol)
    cq.exporters.export(solid, str(paths.STL / "waterfall.step"))
    out["waterfall"] = p

    import waterfall as W
    p = paths.STL / "waterfall_section_x.stl"
    cq.exporters.export(section(solid, "x", "neg"), str(p), **tol)
    out["section_x"] = p

    bb = solid.val().BoundingBox()
    p = paths.STL / "waterfall_section_y.stl"
    cq.exporters.export(section(solid, "y", "neg", at=bb.ymin + bb.ylen * 0.55),
                        str(p), **tol)
    out["section_y"] = p

    bb = solid.val().BoundingBox()
    print(f"  waterfall  {bb.xlen:.1f} x {bb.ylen:.1f} x {bb.zlen:.1f} mm  "
          f"{solid.val().Volume()/1000:.0f} cm3  "
          f"solid_valid={solid.val().isValid()}")
    mesh_health(out["waterfall"], "waterfall.stl")
    return out


def build_fittings(seg=None):
    """seg: optional (cyl, torus_major, torus_minor) override for preview meshes."""
    import fittings as F
    if seg:
        F.SEG_CYL, F.SEG_TORUS_MAJOR, F.SEG_TORUS_MINOR = seg

    out = {}
    for name, factory in F.FITTINGS.items():
        mesh = factory()
        mesh.apply_translation((0, 0, -mesh.bounds[0][2]))   # sit on the bed
        p = paths.STL / f"{name}.stl"
        mesh.export(str(p))
        out[name] = p
        e = mesh.extents
        print(f"  {name:<12} {e[0]:5.1f} x {e[1]:5.1f} x {e[2]:5.1f} mm  "
              f"{mesh.volume/1000:5.1f} cm3  watertight={mesh.is_watertight}")
    return out


def run(fast=False):
    print("waterfall:")
    build_waterfall(fast=fast)
    print("fittings:")
    build_fittings()
    print(f"-> {paths.rel(paths.STL)}")


def load(name):
    return trimesh.load(str(paths.STL / f"{name}.stl"))
