"""Packs preview meshes into the single-file interactive viewer.

Geometry is stored as non-indexed uint16 positions (about 18 bytes per
triangle) so the whole thing stays under a megabyte and still shades flat.
"""
import base64
import json

import numpy as np
import trimesh
import cadquery as cq

from . import paths, solids, hydro
import waterfall as W

PREVIEW_TOL = dict(tolerance=0.12, angularTolerance=0.35)
PREVIEW_SEG = (36, 40, 22)          # cyl, torus major, torus minor

NOTES = {
    "coupler": "Straight inline joiner, socket at each end.",
    "elbow_90": "90 degree turn. 70 mm centreline radius.",
    "u_bend": "180 degree return. Two parallel sockets 140 mm apart.",
    "tee": "Three-way junction, branch at 90 degrees.",
    "y_fitting": "Wye - trunk plus two branches at +-45 degrees.",
    "cap": "Plug-in end cap with a rim so it cannot be pushed through.",
    "flange": "Square mounting plate with an integral socket - bulkhead through a wall.",
    "back_plate": "Companion plate for the flange, clamps the wall from the other side.",
    "pipe_hook": "Wall-mounted cradle that supports a pipe run.",
}
META = {
    "coupler": {"Sockets": "2 x 30 mm deep", "Bore": "59.5 mm"},
    "elbow_90": {"Bend radius": "70 mm centreline", "Bore": "59.5 mm"},
    "u_bend": {"Bend radius": "70 mm centreline", "Leg spacing": "140 mm"},
    "tee": {"Legs": "71.55 mm each", "Pipe tip stop": "41.5 mm from centre"},
    "y_fitting": {"Branch angle": "+-45 deg", "Branch length": "71.55 mm"},
    "cap": {"Plug": "63.1 mm dia x 25 mm", "Rim": "71.8 mm dia x 4 mm"},
    "flange": {"Plate": "3.5 in sq x 4 mm", "Holes": "4 x 6.5 mm", "Stub": "42 mm"},
    "back_plate": {"Plate": "3.5 in sq x 4 mm", "Centre hole": "73.0 mm"},
    "pipe_hook": {"Cradle ID": "63.1 mm", "Wrap": "200 deg", "Width": "40 mm"},
}


def _pack(mesh, group, note, meta):
    """Exact geometry: float32 vertices + uint32 faces (the same precision as
    a binary STL), so downloads from the viewer are identical to the exported
    files. Do NOT quantise: these meshes have distinct vertices < 1e-6 mm
    apart, and rounding merges them and breaks watertightness."""
    v = np.ascontiguousarray(mesh.vertices, dtype='<f4')
    f = np.ascontiguousarray(mesh.faces, dtype='<u4')
    return dict(group=group, note=note, meta=meta, fmt='f32i',
                nv=int(len(v)), nf=int(len(f)),
                dims=[round(float(x), 1) for x in mesh.extents],
                tris=int(len(f)), vol=round(float(mesh.volume) / 1000, 1),
                b64=base64.b64encode(v.tobytes() + f.tobytes()).decode('ascii'))


def _waterfall_meta():
    ps, bs = hydro.pools(), hydro.basin()
    return {
        "Outer size": f"{W.SIZE/25.4:.2f} x {W.SIZE/25.4:.2f} x {W.BACK_WALL_TOP/25.4:.2f} in",
        "Basin": f"{bs['usable_depth']:.0f} mm deep, {bs['gross_l']:.2f} L gross",
        "Pools": f"3 tiers, {ps[0]['depth']:.0f} mm of water each "
                 f"({sum(p['volume_ml'] for p in ps):.0f} mL total)",
        "Weir slits": f"9 total, {W.SLIT_W:.1f} x {hydro.slit_h():.1f} mm",
        "Weir capacity": f"{hydro.weir_capacity_lph():.0f} L/h per pool",
        "Riser channel": f"{W.SPINE_UP_W - 2*W.SPINE_UP_WALL:.1f} x "
                         f"{W.SPINE_UP_INNER_D - W.SPINE_UP_WALL:.1f} mm",
        "Outlet": f"{W.SPINE_CAP_HOLE_D:.2f} mm through the cap",
    }


def run():
    parts = {}
    print("  waterfall preview:")
    solid = solids.waterfall_solid()
    tmp = paths.STL / "_preview_waterfall.stl"
    cq.exporters.export(solid, str(tmp), **PREVIEW_TOL)
    _pack(parts, "waterfall", trimesh.load(str(tmp)), "Waterfall",
          "Three-tier open-front waterfall. The back column houses the pump and riser.",
          _waterfall_meta())

    tmp2 = paths.STL / "_preview_waterfall_section.stl"
    cq.exporters.export(solids.section(solid, "x", "neg"), str(tmp2), **PREVIEW_TOL)
    _pack(parts, "waterfall_section", trimesh.load(str(tmp2)), "Waterfall",
          "Half the waterfall, cut on the centre plane - riser, pump box and pool floors.",
          {"Cut": "X = 0 centre plane"})

    print("  fittings preview:")
    import fittings as F
    F.SEG_CYL, F.SEG_TORUS_MAJOR, F.SEG_TORUS_MINOR = PREVIEW_SEG
    for name, factory in F.FITTINGS.items():
        m = factory()
        m.apply_translation((0, 0, -m.bounds[0][2]))
        _pack(parts, name, m, "Fittings", NOTES[name], META[name])

    ps, bs = hydro.pools(), hydro.basin()
    water = [dict(cx=0, cy=(p["f_in"] + p["back_y"]) / 2, z0=p["floor_in"],
                  z1=p["surf"], w=p["iw"], d=p["back_y"] - p["f_in"]) for p in ps]
    water.append(dict(cx=0, cy=0, z0=bs["floor_in"], z1=bs["floor_in"] + 45,
                      w=bs["iw"], d=bs["idp"]))

    data = "const PARTS = " + json.dumps(parts) + ";\n" \
           "const WATER = " + json.dumps(water) + ";\n"

    html = (paths.TOOLS / "viewer_template.html").read_text()
    assert "/*DATA*/" in html, "viewer_template.html lost its /*DATA*/ marker"
    html = html.replace("/*DATA*/", data)

    out = paths.OUT / "part_viewer.html"
    out.write_text(html)
    for t in (tmp, tmp2):
        t.unlink(missing_ok=True)
    print(f"  part_viewer -> {paths.rel(out)}  ({len(html)/1024/1024:.2f} MB)")
