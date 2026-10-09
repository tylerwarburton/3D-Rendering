"""Static PNG review sheets: overall views, sections, details, cutaways."""
import numpy as np
import trimesh

from . import paths, solids
from shared import render as R

WF_VIEWS = [
    ("Front 3/4 (open face)", (0.85, 1.0, -0.55)),
    ("Front elevation", (0.0, 1.0, 0.0)),
    ("Right side", (-1.0, 0.0, 0.0)),
    ("Top", (0.0, 0.0, -1.0)),
    ("Back 3/4", (-0.85, -1.0, -0.5)),
    ("Front 3/4 low angle", (0.6, 1.0, -0.12)),
]

FITTING_VIEWS = {
    "coupler": (0.9, 1.0, -0.35),
    "elbow_90": (0.25, 1.0, -0.25),
    "u_bend": (0.25, 1.0, -0.25),
    "tee": (0.3, 1.0, -0.25),
    "y_fitting": (0.3, 1.0, -0.25),
    "cap": (0.8, 1.0, -0.5),
    "flange": (0.8, 1.0, -0.5),
    "back_plate": (0.7, 1.0, -0.6),
    "pipe_hook": (0.9, 0.75, -0.5),
}
FITTING_ORDER = ["coupler", "elbow_90", "u_bend", "tee", "y_fitting",
                 "cap", "flange", "back_plate", "pipe_hook"]


def waterfall_sheets(size=620):
    import waterfall as W
    full = solids.load("waterfall")
    secx = solids.load("waterfall_section_x")
    secy = solids.load("waterfall_section_y")
    B = full.vertices
    bb = full.bounds

    imgs = [R.render(full, view_dir=v, size=(size, size), bounds=B, ss=2)
            for _, v in WF_VIEWS]
    R.grid(imgs, [n for n, _ in WF_VIEWS], 3, str(paths.IMG / "waterfall_views.png"))

    si = [
        R.render(secx, view_dir=(-1.0, 0.15, -0.12), size=(size, size), bounds=B, ss=2),
        R.render(secx, view_dir=(-0.85, 0.75, -0.35), size=(size, size), bounds=B, ss=2),
        R.render(secy, view_dir=(0.35, 1.0, -0.35), size=(size, size), bounds=B, ss=2),
    ]
    R.grid(si, ["Section at centre (X=0) - spine cavity",
                "Section 3/4 - pools + spine",
                "Cut behind the front walls - pool interiors"],
           3, str(paths.IMG / "waterfall_sections.png"))

    top_rim = W.POOL_RIM_Z[0]
    zoom = np.array([[-70, bb[0][1], top_rim - 60], [70, bb[1][1], top_rim + 30]])
    mid = np.array([[-90, bb[0][1], W.POOL_RIM_Z[2] - 60],
                    [90, bb[1][1], W.POOL_RIM_Z[1] + 20]])
    di = [
        R.render(full, view_dir=(0.7, 1.0, -0.35), size=(size, size), bounds=zoom, ss=2),
        R.render(secx, view_dir=(-1.0, 0.2, -0.2), size=(size, size), bounds=zoom, ss=2),
        R.render(full, view_dir=(0.9, 1.0, -0.2), size=(size, size), bounds=mid, ss=2),
    ]
    R.grid(di, ["Top pool + spine cap (detail)",
                "Spine cap / cup section",
                "Mid + bottom pool, slits & stubs"],
           3, str(paths.IMG / "waterfall_detail.png"))
    print(f"  waterfall_views / _sections / _detail -> {paths.rel(paths.IMG)}")


def fitting_sheets(size=560):
    imgs, labs = [], []
    for name in FITTING_ORDER:
        m = solids.load(name)
        e = m.extents
        imgs.append(R.render(m, view_dir=FITTING_VIEWS[name], size=(size, size), ss=2))
        labs.append(f"{name}   {e[0]:.0f} x {e[1]:.0f} x {e[2]:.0f} mm")
    R.grid(imgs, labs, 3, str(paths.IMG / "fittings_views.png"))

    imgs, labs = [], []
    for name in ["coupler", "elbow_90", "u_bend", "tee", "y_fitting", "flange"]:
        m = solids.load(name)
        try:
            h = m.slice_plane(plane_origin=[0, 0, 0], plane_normal=[0, 1, 0], cap=True)
            if h is None or len(h.faces) == 0:
                raise ValueError("empty slice")
        except Exception as e:                       # fall back to a boolean cut
            print(f"    {name}: slice failed ({e}); using boolean")
            lo, hi = m.bounds
            box = trimesh.creation.box(extents=(hi - lo) + 400)
            box.apply_translation(((lo + hi) / 2) + [0, (max(hi - lo) + 400) / 2, 0])
            h = m.difference(box, engine="manifold")
        imgs.append(R.render(h, view_dir=(0.15, 1.0, -0.2), size=(size, size),
                             bounds=m.vertices, ss=2))
        labs.append(f"{name} - cutaway (socket + bore)")
    R.grid(imgs, labs, 3, str(paths.IMG / "fittings_cutaways.png"))
    print(f"  fittings_views / _cutaways -> {paths.rel(paths.IMG)}")


def run():
    print("sheets:")
    waterfall_sheets()
    fitting_sheets()
