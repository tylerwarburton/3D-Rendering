#!/usr/bin/env python3
"""Single entrypoint for the intake adapter.

    python build.py part      - model, validate, export STL + STEP
    python build.py coupon    - short fit-test coupon (one connector)
    python build.py verify    - analytic checks on the exported mesh
    python build.py render    - orthographic view sheet + section
    python build.py all       - everything, in order
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [os.path.join(HERE, "src"), os.path.join(HERE, "tools")]
OUT = os.environ.get("OUT_DIR") or os.path.join(
    HERE, "..", "..", "out", "miata-intake")                  # <repo>/out/miata-intake
os.makedirs(OUT, exist_ok=True)

import numpy as np                                            # noqa: E402
import cadquery as cq                                         # noqa: E402
import trimesh                                                # noqa: E402

import params as P                                            # noqa: E402


def _export(solid, stem):
    stl = os.path.join(OUT, stem + ".stl")
    stp = os.path.join(OUT, stem + ".step")
    wp = cq.Workplane("XY").add(solid)
    cq.exporters.export(wp, stl, tolerance=P.STL_TOLERANCE,
                        angularTolerance=P.STL_ANG_TOL)
    cq.exporters.export(wp, stp)
    print(f"  -> {os.path.relpath(stl, HERE)}  ({os.path.getsize(stl)/1e6:.1f} MB)")
    print(f"  -> {os.path.relpath(stp, HERE)}  ({os.path.getsize(stp)/1e6:.1f} MB)")
    return stl


def cmd_part():
    t0 = time.time()
    solid = _body()
    _export(solid, "intake_adapter")
    print(f"  built in {time.time() - t0:.1f}s")


_CACHE = {}


def _body():
    if "body" not in _CACHE:
        import adapter
        _CACHE["body"] = adapter.build()
    return _CACHE["body"]


def cmd_coupon():
    """Print-first test pieces, sliced out of the exported part."""
    import coupons
    m = trimesh.load(os.path.join(OUT, "intake_adapter.stl"))
    for name, cm in coupons.make(m).items():
        path = os.path.join(OUT, name + ".stl")
        cm.export(path)
        print(f"  -> {os.path.relpath(path, HERE)}")


def cmd_verify():
    import verify
    m = trimesh.load(os.path.join(OUT, "intake_adapter.stl"))
    ok, lines = verify.report(m)
    print("\n".join("  " + ln for ln in lines))
    print("  ALL CHECKS PASS" if ok else "  >>> ISSUES FOUND")
    return 0 if ok else 1


def cmd_layout():
    import layout
    out = layout.draw(os.path.join(OUT, "connector_map.png"))
    print(f"  -> {os.path.relpath(out, HERE)}")


def cmd_render():
    import render
    # Render from the exported STL. Re-tessellating finer looks marginally
    # better and costs a full rebuild (~17 min) - never worth it inline.
    # Set RENDER_FINE=1 to spend that time deliberately.
    fine = os.path.join(OUT, "_render.stl")
    if os.environ.get("RENDER_FINE") and not os.path.exists(fine):
        cq.exporters.export(cq.Workplane("XY").add(_body()), fine,
                            tolerance=0.012, angularTolerance=0.05)
    src = fine if os.path.exists(fine) else os.path.join(
        OUT, "intake_adapter.stl")
    m = trimesh.load(src)
    m.apply_translation(-m.bounds.mean(axis=0))
    ref = float(np.linalg.norm(m.extents[:3]) * 0.62)
    S = 520
    views = [
        ((1.1, -0.85, 0.55), "iso - outlet side"),
        ((-0.9, 0.95, -0.55), "iso - mouth side"),
        ((0, 0, -1), "mouth (this face slides onto the frame)"),
        ((0, 0, 1), "outlet - 2.5 in tube"),
        ((0, -1, 0), "long face - two connectors"),
        ((1, 0, 0), "short end - one connector"),
    ]
    panels = []
    for eye, label in views:
        up = (0, 0, 1) if abs(eye[2]) < 0.9 else (0, 1, 0)
        panels.append((render.render_view(m, S, eye, up, scale_ref=ref), label))
    out = os.path.join(OUT, "views.png")
    render.contact_sheet(panels, 3, S,
                         "Miata NA turn-signal duct -> 2.5 in adapter", out)
    print(f"  -> {os.path.relpath(out, HERE)}")

    # longitudinal section, cut on the Y=0 plane
    half = trimesh.intersections.slice_mesh_plane(
        m, plane_normal=[0, 1, 0], plane_origin=[0, 0, 0], cap=True)
    # the cut face is the one lying ON the plane - a normal test also catches
    # interior walls that happen to face the same way
    ys = half.vertices[half.faces][:, :, 1]
    cut = np.where(np.abs(ys).max(axis=1) < 1e-4)[0]
    sec = [(render.render_view(half, S, (0.35, -1.0, 0.12), (0, 0, 1),
                               cut_faces=cut, scale_ref=ref),
            "section on the centreline - wall, stop ledge, tie bridge"),
           (render.render_view(half, S, (1.0, -0.55, 0.42), (0, 0, 1),
                               cut_faces=cut, scale_ref=ref),
            "section, three-quarter")]
    out2 = os.path.join(OUT, "section.png")
    render.contact_sheet(sec, 2, S, "Cutaway", out2)
    print(f"  -> {os.path.relpath(out2, HERE)}")

    # the attachment-point coupon, rendered on its own
    cp = os.path.join(OUT, "coupon_connector.stl")
    if os.path.exists(cp):
        cm = trimesh.load(cp)
        cm.apply_translation(-cm.bounds.mean(axis=0))
        cref = float(np.linalg.norm(cm.extents) * 0.60)
        cuts = trimesh.intersections.slice_mesh_plane(
            cm, plane_normal=[0, 1, 0], plane_origin=[0, 0, 0], cap=True)
        cys = cuts.vertices[cuts.faces][:, :, 1]
        cidx = np.where(np.abs(cys).max(axis=1) < 1e-4)[0]
        panels = [
            (render.render_view(cm, S, (1.0, -0.75, 0.5), (0, 0, 1),
                                scale_ref=cref), "outside - the two tie ports"),
            (render.render_view(cm, S, (-1.0, -0.7, 0.45), (0, 0, 1),
                                scale_ref=cref), "inside - the pocket is the only opening"),
            (render.render_view(cuts, S, (0.2, -1.0, 0.15), (0, 0, 1),
                                cut_faces=cidx, scale_ref=cref),
             "section - ports slant in and stop in the pocket"),
        ]
        ring = os.path.join(OUT, "coupon_mouth_ring.stl")
        if os.path.exists(ring):
            rm = trimesh.load(ring)
            rm.apply_translation(-rm.bounds.mean(axis=0))
            rref = float(np.linalg.norm(rm.extents) * 0.56)
            panels.append((render.render_view(rm, S, (0.1, 1.0, 0.45),
                                              (0, 0, 1), scale_ref=rref),
                           "mouth ring - flex slit through side B"))
        out3 = os.path.join(OUT, "coupon.png")
        render.contact_sheet(panels, 2, S,
                             "Test coupons - print these first", out3)
        print(f"  -> {os.path.relpath(out3, HERE)}")


def cmd_mock():
    import mock
    d, n = mock.make(OUT)
    print(f"  -> {os.path.relpath(d, HERE)} ({n} mock parts) + scene.json")


TARGETS = {"layout": cmd_layout, "part": cmd_part, "coupon": cmd_coupon,
           "verify": cmd_verify, "render": cmd_render, "mock": cmd_mock}


def main(argv):
    # --set NAME=VALUE (VALUE is JSON) overrides a params constant before
    # anything imports adapter; everything else is a target
    import json
    args, sets, it = [], {}, iter(argv[1:])
    for a in it:
        if a == "--set":
            name, _, val = next(it).partition("=")
            if not hasattr(P, name):
                print(f"unknown param {name!r}")
                return 2
            sets[name] = json.loads(val)
        else:
            args.append(a)
    for name, val in sets.items():
        setattr(P, name, val)
        print(f"  set {name} = {val!r}")
    if sets:
        P.derive()
        P._check_layout()
    args = args or ["all"]
    if args == ["all"]:
        args = ["layout", "part", "verify", "coupon", "render"]
    rc = 0
    for a in args:
        if a not in TARGETS:
            print(f"unknown target {a!r}; pick from {', '.join(TARGETS)}")
            return 2
        print(f"[{a}]")
        rc = TARGETS[a]() or rc
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv))
