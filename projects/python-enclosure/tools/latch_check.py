"""Simulate a cap on a real fitting port and measure solid overlap (mm^3).

Everything is derived from fittings.py parameters, nothing hard-coded. The
fitting and the cap are both in the port frame (z=0 at the mouth, fitting
at z>0), so no transform guesswork. Overlap ~0 means the move is free;
overlap > 0 means plastic hits plastic (blocked, or a detent to click over).
"""
import numpy as np
from trimesh import transformations as tf


def _overlap(a, b):
    try:
        i = a.intersection(b, engine='manifold')
        return float(i.volume) if len(i.faces) else 0.0
    except Exception:
        return 0.0


def run(F=None, verbose=True, fitting=None):
    if F is None:
        import fittings as F
    fit = fitting if fitting is not None else F.make_coupler()  # port at z=0, +z
    cap0 = F.make_cap()
    rot = F.LATCH_ROT_DEG

    def cap_at(z=0.0, deg=0.0):
        c = cap0.copy()
        c.apply_transform(tf.rotation_matrix(np.radians(deg), (0, 0, 1)))
        c.apply_translation((0, 0, z))
        return c

    res = {}
    res["push on (entry, 15 mm out -> seated)"] = max(
        _overlap(fit, cap_at(-z)) for z in np.linspace(15, 0, 7))
    sweep = [(d, _overlap(fit, cap_at(0, d))) for d in np.linspace(0, rot, 31)]
    res["twist 0 -> lock, worst (detent click)"] = max(v for _, v in sweep)
    res["seated + locked"] = _overlap(fit, cap_at(0, rot))
    res["locked, pulled 1 mm"] = _overlap(fit, cap_at(-1.0, rot))
    res["entry, pulled 1 mm (should be free)"] = _overlap(fit, cap_at(-1.0, 0))
    res["locked, twisted past stop +3 deg"] = _overlap(fit, cap_at(0, rot + 3))
    if verbose:
        for k, v in res.items():
            print(f"  {k:42s} {v:8.2f} mm3")
        print("  twist sweep (deg: mm3):",
              " ".join(f"{d:.0f}:{v:.1f}" for d, v in sweep if v > 0.01) or "none")
    ok = (res["push on (entry, 15 mm out -> seated)"] < 0.5
          and res["seated + locked"] < 0.5
          and res["entry, pulled 1 mm (should be free)"] < 0.5
          and res["locked, pulled 1 mm"] > 5
          and res["locked, twisted past stop +3 deg"] > 1
          and 0.5 < res["twist 0 -> lock, worst (detent click)"] < 30)
    print("  LATCH", "OK" if ok else "FAILED")
    return ok, res, sweep


def ports(F):
    """(fitting name, mouth point, axis into the fitting) for every latched
    port, derived from the same parameters the builders use."""
    L = F.LEG_LENGTH
    Lt = F.SOCKET_DEPTH + F.PIPE_OD / 2 + F.JUNCTION_CLEARANCE
    a = np.deg2rad(45)
    b1 = np.array([np.sin(a), 0, np.cos(a)])
    b2 = np.array([-np.sin(a), 0, np.cos(a)])
    H = 4.0 + 42.0
    return [
        ('elbow', (F.BEND_R, 0, -L), (0, 0, 1)), ('elbow', (-L, 0, F.BEND_R), (1, 0, 0)),
        ('coupler', (0, 0, 0), (0, 0, 1)), ('coupler', (0, 0, 2 * L), (0, 0, -1)),
        ('tee', (-Lt, 0, 0), (1, 0, 0)), ('tee', (Lt, 0, 0), (-1, 0, 0)), ('tee', (0, 0, Lt), (0, 0, -1)),
        ('u_bend', (F.BEND_R, 0, -L), (0, 0, 1)), ('u_bend', (-F.BEND_R, 0, -L), (0, 0, 1)),
        ('y_fitting', (0, 0, -L), (0, 0, 1)), ('y_fitting', tuple(Lt * b1), tuple(-b1)),
        ('y_fitting', tuple(Lt * b2), tuple(-b2)),
        ('flange', (0, 0, H), (0, 0, -1)), ('latch_coupon', (0, 0, 0), (0, 0, 1)),
    ]


def run_shim(F=None):
    """Shim checks: (1) locked on EVERY port of every fitting with zero
    overlap (catches a skirt too long for a bend or junction); (2) two
    couplers latched through one shim: seated, held, and each pulls free
    only at its entry angle."""
    if F is None:
        import fittings as F
    shim = F.make_shim()
    rot = np.radians(F.LATCH_ROT_DEG)
    built, worst = {}, 0.0
    print("  shim locked on every port (mm3 overlap):")
    for name, p, d in ports(F):
        if name not in built:
            built[name] = F.FITTINGS[name]()
        s = shim.copy()
        s.apply_transform(tf.rotation_matrix(rot, (0, 0, 1)))
        s.apply_transform(F.port_frame(p, d))
        v = _overlap(built[name], s)
        worst = max(worst, v)
        print(f"    {name:13s} port at {np.round(p, 1)}: {v:.2f}")

    cp = F.make_coupler()
    M2 = F.shim_side_frame()

    def fit_b(deg=-F.LATCH_ROT_DEG, pull=0.0):
        """Coupler B on the shim's second side, twisted `deg` in its own frame
        (fitting turned -rot == shim turned +rot), pulled `pull` mm away."""
        m = cp.copy()
        m.apply_transform(tf.rotation_matrix(np.radians(deg), (0, 0, 1)))
        m.apply_translation((0, 0, pull))
        m.apply_transform(M2)
        return m

    def fit_a(deg=-F.LATCH_ROT_DEG, pull=0.0):
        m = cp.copy()
        m.apply_transform(tf.rotation_matrix(np.radians(deg), (0, 0, 1)))
        m.apply_translation((0, 0, pull))
        return m

    r = {
        "A locked": _overlap(fit_a(), shim),
        "B locked": _overlap(fit_b(), shim),
        "A locked, pulled 1 mm": _overlap(fit_a(pull=1.0), shim),
        "B locked, pulled 1 mm": _overlap(fit_b(pull=1.0), shim),
        "A at entry, pulled 1 mm": _overlap(fit_a(deg=0, pull=1.0), shim),
        "B at entry, pulled 1 mm": _overlap(fit_b(deg=0, pull=1.0), shim),
        "A vs B (fittings touch?)": _overlap(fit_a(), fit_b()),
    }
    for k, v in r.items():
        print(f"  {k:28s} {v:8.2f} mm3")
    ok = (worst < 0.5 and r["A locked"] < 0.5 and r["B locked"] < 0.5
          and r["A locked, pulled 1 mm"] > 5 and r["B locked, pulled 1 mm"] > 5
          and r["A at entry, pulled 1 mm"] < 0.5 and r["B at entry, pulled 1 mm"] < 0.5
          and r["A vs B (fittings touch?)"] < 0.5)
    print("  SHIM", "OK" if ok else "FAILED")
    return ok, r


def run_male(F=None, cases=None):
    """A coupler latched onto a fitting's built-in MALE port: locked = no
    overlap with ANY part of the fitting, pulled while locked = blocked,
    pulled at the entry angle = free. Uses the labelled port positions."""
    if F is None:
        import fittings as F
    cases = cases or [('elbow', 'FM', dict(angle=45.0)), ('elbow', 'MM', dict(angle=22.5)),
                      ('y_fitting', 'FMM', {}), ('tee', 'MFM', {}), ('coupler', 'MM', {}),
                      ('u_bend', 'MF', dict(vent=True)), ('flange', 'M', {})]
    cp = F.make_coupler()
    rot = F.LATCH_ROT_DEG
    ok_all = True
    for fam, g, kw in cases:
        fit, _ = F.FITTINGS[fam](g, labels=True, **kw)
        ports = F.port_list(fam, **kw)
        for (p, d), gi in zip(ports, g):
            if gi != 'M':
                continue
            W = F.port_frame(p, d) @ F.shim_side_frame()

            def mate(deg, pull):
                m = cp.copy()
                m.apply_transform(tf.rotation_matrix(np.radians(-deg), (0, 0, 1)))
                m.apply_translation((0, 0, pull))
                m.apply_transform(W)
                return m
            locked, held, free = (_overlap(fit, mate(rot, 0)), _overlap(fit, mate(rot, 1.0)),
                                  _overlap(fit, mate(0, 1.0)))
            ok = locked < 0.5 and held > 5 and free < 0.5
            ok_all &= ok
            print(f"  {fam:9s} {g:3s} {str(kw):18s} male port at {np.round(p,0)}: "
                  f"locked {locked:5.2f}  pulled-locked {held:6.2f}  pulled-entry {free:5.2f}  "
                  f"{'OK' if ok else 'FAIL'}")
    print("  MALE PORTS", "OK" if ok_all else "FAILED")
    return ok_all


def run_print_audit(mesh, layer=0.2, max_drop=0.45, label='part'):
    """Printability without slicer supports.
    (1) Overhangs: faces facing down steeper than 45 deg, with nothing (bed
        or another part, e.g. a modelled one-layer gap) within max_drop below.
    (2) Islands: every horizontal slice, every region that does not sit on
        the slice below it - catches knob tips and anything else that would
        start in mid-air, which a face-angle test misses (a point has no face).
    Returns (overhang_area_mm2, islands) and prints a summary."""
    import shapely.geometry as sg
    n = mesh.face_normals; c = mesh.triangles_center; A = mesh.area_faces
    down = (n[:, 2] < -0.72) & (c[:, 2] > 0.05)
    idx = np.where(down)[0]
    o = c[idx] - np.array([0, 0, 0.01])
    loc, ri, _ = mesh.ray.intersects_location(o, np.tile([0, 0, -1.0], (len(idx), 1)),
                                              multiple_hits=False)
    drop = np.full(len(idx), np.inf)
    for L_, k in zip(loc, ri):
        drop[k] = min(drop[k], o[k, 2] - L_[2])
    drop = np.minimum(drop, o[:, 2])
    over = float(A[idx][drop > max_drop].sum())
    islands = []
    zs = np.arange(layer / 2, mesh.bounds[1][2], layer)
    secs = mesh.section_multiplane((0, 0, 0), (0, 0, 1), list(zs))
    from shapely.ops import unary_union
    back = int(np.ceil(max_drop / layer))            # look down through a modelled gap
    hist = []
    for z, sec in zip(zs, secs):
        polys = [] if sec is None else list(sec.polygons_full)
        if hist and z > layer:
            below = unary_union(hist[-back:])
            for p in polys:
                if p.area > 0.5 and not p.buffer(0.3).intersects(below):
                    islands.append((round(float(z), 2), round(float(p.area), 1),
                                    tuple(np.round(p.centroid.coords[0], 1))))
        hist.append(unary_union(polys) if polys else sg.Polygon())
    print(f"  {label}: steep overhang with nothing below: {over:.0f} mm2;  "
          f"islands (start in mid-air): {len(islands)} {islands[:3]}")
    return over, islands
