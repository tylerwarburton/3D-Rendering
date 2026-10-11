"""Turn-signal duct -> 2.5 in tube adapter, built with CadQuery.

Everything is driven from params.py. The build validates the solid after
every boolean because OCCT can return a broken shape without raising.

Geometry notes
--------------
The OEM frame is not a prism. Its long faces are flat and parallel, but the
two short ends flare outward away from the outlet, at different angles. So
the socket is a tapered, asymmetric loft, the short-end faces are tilted,
and every feature that sits on one of them (boss, pocket, tie slots, crush
ribs, side label) is built in that face's own frame rather than in world Z.
"""
import math

import numpy as np
import cadquery as cq
import trimesh

import params as P

V = cq.Vector
SECTION_N = 400          # points per lofted cross-section spline

SIDE_NAME = {"-X": "A", "+Y": "B", "+X": "C", "-Y": "D"}
DRAFT = {
    "+X": math.tan(math.radians(P.FRAME_DRAFT_PX)),
    "-X": math.tan(math.radians(P.FRAME_DRAFT_NX)),
    "+Y": 0.0,
    "-Y": 0.0,
}


# ---------------------------------------------------------------- validation
class GeomError(RuntimeError):
    pass


def mesh_of(shape, tol=0.03, ang=0.12):
    """Tessellate an OCCT shape into a trimesh for honest measurement."""
    s = shape.val() if isinstance(shape, cq.Workplane) else shape
    verts, faces = s.tessellate(tol, ang)
    return trimesh.Trimesh(
        vertices=np.array([[p.x, p.y, p.z] for p in verts], dtype=float),
        faces=np.array(faces, dtype=np.int64), process=True)


def safe_clean(shape):
    """clean() merges coplanar faces, but the face unifier throws outright on
    some results of overlapping cutters. The uncleaned shape is still valid,
    so fall back to it rather than losing the operation."""
    try:
        return shape.clean()
    except Exception:
        return shape


def check(shape, label, deep=True):
    """Validate an intermediate result.

    OCCT's GProp volume is unreliable on spline surfaces, so anything that
    matters is measured off a tessellation instead.
    """
    s = shape.val() if isinstance(shape, cq.Workplane) else shape
    if s is None:
        raise GeomError(f"{label}: produced nothing")
    if not s.isValid():
        raise GeomError(f"{label}: OCCT reports an invalid solid")
    note = ""
    if deep:
        m = mesh_of(s)
        if not m.is_watertight:
            raise GeomError(f"{label}: tessellation is not watertight "
                            f"({len(trimesh.repair.broken_faces(m))} broken faces)")
        if m.volume <= 0 or not math.isfinite(m.volume):
            raise GeomError(f"{label}: non-physical volume {m.volume}")
        note = f"vol={m.volume / 1000.0:8.2f} cm^3   tris={len(m.faces):6d}"
    print(f"  ok  {label:<32} {note}")
    return shape


# ------------------------------------------------- rounded rect <-> circle
def _rrect_sdf(px, py, hw, hh, r):
    qx = np.abs(px) - (hw - r)
    qy = np.abs(py) - (hh - r)
    return (np.hypot(np.maximum(qx, 0.0), np.maximum(qy, 0.0))
            + np.minimum(np.maximum(qx, qy), 0.0) - r)


def rrect_radius(theta, hw, hh, r, cx=0.0):
    """Distance from the ORIGIN to a rounded rect whose centre is at cx."""
    c, s = np.cos(theta), np.sin(theta)
    lo = np.zeros_like(theta)
    hi = np.full_like(theta, 3.0 * max(hw, hh) + abs(cx))
    for _ in range(64):
        mid = 0.5 * (lo + hi)
        inside = _rrect_sdf(mid * c - cx, mid * s, hw, hh, r) < 0.0
        lo = np.where(inside, mid, lo)
        hi = np.where(inside, hi, mid)
    return 0.5 * (lo + hi)


def smoothstep(t):
    return t * t * (3.0 - 2.0 * t)


def _spline_wire(pts3d):
    edge = cq.Edge.makeSpline([V(*p) for p in pts3d], periodic=True)
    return cq.Wire.assembleEdges([edge])


def _theta(n):
    return np.linspace(0.0, 2.0 * np.pi, n, endpoint=False)


def xy_wire(t, hw, hh, r, r_circle, z, n=SECTION_N):
    """Symmetric section, morphed t=0 rounded rect -> t=1 circle."""
    th = _theta(n)
    k = smoothstep(t)
    rad = (1.0 - k) * rrect_radius(th, hw, hh, r) + k * r_circle
    return _spline_wire(np.stack([rad * np.cos(th), rad * np.sin(th),
                                  np.full_like(th, z)], axis=1))


def half_x(kind, base_hw, z):
    """Half-extent of the drafted short end at height z.

    z = SOCKET_DEPTH is the outer rim, where the frame measures FRAME_W.
    Below that the end flares outward, so the mouth is the widest section.
    """
    return base_hw + DRAFT[kind] * max(P.SOCKET_DEPTH - z, 0.0)


def sock_wire(z, base_hw, base_hh, r, n=SECTION_N):
    """Socket section at height z, with the two short ends drafted apart."""
    hxp = half_x("+X", base_hw, z)
    hxn = half_x("-X", base_hw, z)
    cx = (hxp - hxn) / 2.0
    hw = (hxp + hxn) / 2.0
    th = _theta(n)
    rad = rrect_radius(th, hw, base_hh, r, cx)
    return _spline_wire(np.stack([rad * np.cos(th), rad * np.sin(th),
                                  np.full_like(th, z)], axis=1))


def duct_shell(base_hw, base_hh, r, r_circle, z_mouth, z_sock_end,
               z_t0, z_t1, z_end):
    """Drafted socket, straight collar, rect-to-round blend, straight tube.

    Separate lofts that SHARE their interface wires, so the joints are
    geometrically identical and the fuse leaves no slivers. Lofting the whole
    thing in one shot instead pinches the straight runs by ~7%.
    """
    w_sock = xy_wire(0.0, base_hw, base_hh, r, r_circle, z_sock_end)
    w_t0 = xy_wire(0.0, base_hw, base_hh, r, r_circle, z_t0)
    stack = []
    if z_mouth is not None and abs(z_sock_end - z_mouth) > 1e-6:
        stack.append(cq.Solid.makeLoft(
            [sock_wire(z_mouth, base_hw, base_hh, r), w_sock], True))
    if z_t0 - z_sock_end > 1e-6:
        stack.append(cq.Solid.makeLoft([w_sock, w_t0], True))

    lead = P.TRANS_LEAD
    plan = [(z_t0 + lead, 0.0)]
    inner = np.linspace(z_t0 + lead, z_t1 - lead, P.TRANS_SECTIONS)
    for i, z in enumerate(inner[1:-1], start=1):
        plan.append((float(z), i / (P.TRANS_SECTIONS - 1.0)))
    plan.append((z_t1 - lead, 1.0))
    mid = [w_t0] + [xy_wire(t, base_hw, base_hh, r, r_circle, z)
                    for z, t in plan]
    w_t1 = xy_wire(1.0, base_hw, base_hh, r, r_circle, z_t1)
    mid.append(w_t1)
    blend = cq.Solid.makeLoft(mid, False)

    w_end = xy_wire(1.0, base_hw, base_hh, r, r_circle, z_end)
    tube = cq.Solid.makeLoft([w_t1, w_end], True)

    parts = stack + [blend, tube]
    out = parts[0]
    if len(parts) > 1:
        out = out.fuse(*parts[1:])
    return out.clean()


# ------------------------------------------------------------- face frames
def face_axes(kind, drafted=True):
    """(lateral u, outward normal n, in-plane along-flow v) for a face."""
    t = DRAFT[kind] if drafted else 0.0
    if kind == "+X":
        u, n = V(0, 1, 0), V(1, 0, t)
    elif kind == "-X":
        u, n = V(0, -1, 0), V(-1, 0, t)
    elif kind == "+Y":
        u, n = V(-1, 0, 0), V(0, 1, 0)
    elif kind == "-Y":
        u, n = V(1, 0, 0), V(0, -1, 0)
    else:
        raise ValueError(kind)
    n = n.normalized()
    return u, n, n.cross(u)


def face_frame(kind, lat, zc, drafted=None):
    """Origin on the inner wall face, `lat` mm along the face, plus axes.

    `lat` is measured in the face's own lateral direction u, so the same
    number means the same thing on all four faces. Above the socket the
    walls are straight again, so the draft is dropped there.
    """
    if drafted is None:
        drafted = zc < P.SOCKET_DEPTH - 1e-9
    u, n, v = face_axes(kind, drafted)
    if kind in ("+X", "-X"):
        sgn = 1.0 if kind == "+X" else -1.0
        c = V(sgn * half_x(kind, P.SOCK_ID_HW, zc), 0, zc)
    else:
        c = V(0, P.SOCK_ID_HH if kind == "+Y" else -P.SOCK_ID_HH, zc)
    return c + u.multiply(lat), u, n, v


def wall_perp(kind, drafted=True):
    """True wall thickness measured perpendicular to a face."""
    t = DRAFT[kind] if drafted else 0.0
    return P.WALL / math.sqrt(1.0 + t ** 2)


def connector_sites():
    """The six connectors as (label, face, lateral, z).

    Labels match what is printed on the part: A and C are the short ends,
    B and D the long faces, numbered 1 and 2 from the A end.
    """
    zc = P.SOCKET_DEPTH - P.TAB_Z_FROM_RIM
    sites = [("A", "-X", -P.TAB_Y_FACE_NX, zc),
             ("C", "+X", P.TAB_Y_FACE_PX, zc)]
    for i, x in enumerate(sorted(P.TAB_X_FACE_PY)):
        sites.append((f"B{i + 1}", "+Y", -x, zc))
    for i, x in enumerate(sorted(P.TAB_X_FACE_NY)):
        sites.append((f"D{i + 1}", "-Y", x, zc))
    return sites


def site_frame_xy(kind, lat, zc=None):
    """Back out the frame-coordinate (x, y) of a site, for drawings."""
    if zc is None:
        zc = P.SOCKET_DEPTH - P.TAB_Z_FROM_RIM
    O, u, n, v = face_frame(kind, lat, zc)
    return O.x, O.y


def face_rr_wire(O, u, v, n, off, hlat, hax, r, lat_shift=0.0, ax_shift=0.0,
                 npts=140):
    th = _theta(npts)
    rad = rrect_radius(th, hlat, hax, r)
    pts = []
    for a, rr in zip(th, rad):
        p = (O + n.multiply(off)
             + u.multiply(rr * math.cos(a) + lat_shift)
             + v.multiply(rr * math.sin(a) + ax_shift))
        pts.append((p.x, p.y, p.z))
    return _spline_wire(pts)


def face_prism(frame, off0, off1, hlat, hax, r, taper=0.0,
               lat_shift=0.0, ax_shift=0.0):
    O, u, n, v = frame
    w0 = face_rr_wire(O, u, v, n, off0, hlat, hax, r, lat_shift, ax_shift)
    w1 = face_rr_wire(O, u, v, n, off1, max(hlat - taper, 1.0),
                      max(hax - taper, 1.0), max(r - taper, 0.8),
                      lat_shift, ax_shift)
    return cq.Solid.makeLoft([w0, w1], False)


# -------------------------------------------------- connector-site features
def boss_solid(kind, lat, zc):
    return face_prism(face_frame(kind, lat, zc), 0.0, P.WALL + P.BOSS_T,
                      P.BOSS_LAT / 2.0, P.BOSS_AX / 2.0, P.BOSS_R,
                      taper=P.BOSS_DRAFT)


def pocket_solid(kind, lat, zc):
    depth = P.TAB_PROUD + P.TAB_DEPTH_CLEAR
    return face_prism(face_frame(kind, lat, zc), -0.05, depth,
                      (P.TAB_L + 2 * P.TAB_CLEAR) / 2.0,
                      (P.TAB_W + 2 * P.TAB_CLEAR_AX) / 2.0, 1.0)


def tie_port_solids(kind, lat, zc):
    """The two zip-tie ports at one connector.

    Each is a slanted tunnel: it opens on the outside face clear of the
    pocket, and lands INSIDE the pocket near one end of the tab. It starts
    at TIE_PORT_START, above the bore surface, so the only thing breaking
    the inner wall is the pocket itself - the ports never open into the duct.

    The tie goes in the upper port, down through the hollow connector, and
    out the lower one.
    """
    O, u, n, v = face_frame(kind, lat, zc)
    out = []
    # 141, not the default 140, spline points: with 140 the D2 upper port's
    # cut through the flat boss tip came back with a mis-oriented hole wire
    # (BRepCheck_BadOrientationOfSubshape -> invalid solid, port left
    # filled). Same outline to within microns; only the parametrisation moves.
    npts = 141
    for sgn in (-1.0, 1.0):
        w_in = face_rr_wire(O, u, v, n, P.TIE_PORT_START,
                            P.TIE_SLOT_LAT / 2.0, P.TIE_PORT_IN_AX / 2.0,
                            min(P.TIE_SLOT_R, P.TIE_PORT_IN_AX / 2.0 - 0.3),
                            0.0, sgn * P.TIE_PORT_IN_OFF, npts=npts)
        w_out = face_rr_wire(O, u, v, n, P.WALL + P.BOSS_T + 3.0,
                             P.TIE_SLOT_LAT / 2.0, P.TIE_SLOT_AX / 2.0,
                             P.TIE_SLOT_R, 0.0, sgn * P.TIE_PORT_OUT_OFF,
                             npts=npts)
        out.append(cq.Solid.makeLoft([w_in, w_out], True))
    return out


# ---------------------------------------------------------------- crush ribs
def rib_solid(kind, lat):
    z0, z1 = P.RIB_START_Z, P.SOCKET_DEPTH - P.RIB_END_INSET
    zc = (z0 + z1) / 2.0
    O, u, n, v = face_frame(kind, lat, zc)
    # v is tilted on the drafted ends, so stretch along it to keep the rib
    # covering the same span in Z
    span = (z1 - z0) / max(v.z, 1e-6)
    ramp = P.RIB_RAMP / max(v.z, 1e-6)
    # the rib is buried RIB_EMBED into the wall rather than sitting exactly
    # on it - a coincident face against the lofted wall leaves slivers that
    # break the tessellation
    e = -P.RIB_EMBED
    prof = [(-span / 2.0, e), (-span / 2.0 + ramp, P.RIB_PROUD),
            (span / 2.0, P.RIB_PROUD), (span / 2.0, e)]
    half = P.RIB_WIDTH / 2.0
    ring = []
    for s, d in prof:
        p = O + v.multiply(s) + n.multiply(-d) + u.multiply(-half)
        ring.append(V(p.x, p.y, p.z))
    wire = cq.Wire.makePolygon(ring + [ring[0]])
    return cq.Solid.extrudeLinear(wire, [], u.multiply(P.RIB_WIDTH))


def rib_sites():
    if not P.RIB_ENABLE:
        return []
    out = []
    for x in P.RIB_X_LONG:
        out += [("+Y", -x), ("-Y", x)]
    for y in P.RIB_Y_SHORT:
        out += [("+X", y), ("-X", -y)]
    return out


# -------------------------------------------------------------- side labels
def label_sites():
    """Where A / B1 / B2 / C / D1 / D2 get embossed, on the collar.

    Each number lands directly above the connector it names, so there is
    never a question which one is being talked about.
    """
    z = P.LABEL_Z
    out = [("A", "-X", 0.0, z), ("C", "+X", 0.0, z)]  # noqa: E501
    for face, xs, sign in (("+Y", sorted(P.TAB_X_FACE_PY), -1.0),
                           ("-Y", sorted(P.TAB_X_FACE_NY), 1.0)):
        letter = SIDE_NAME[face]
        for i, x in enumerate(xs):
            out.append((f"{letter}{i + 1}", face, sign * x, z))
    return out


def label_solid(txt, kind, lat, zc):
    O, u, n, v = face_frame(kind, lat, zc)
    drafted = zc < P.SOCKET_DEPTH - 1e-9
    base = O + n.multiply(wall_perp(kind, drafted) - 0.3)
    plane = cq.Plane(origin=(base.x, base.y, base.z),
                     xDir=(u.x, u.y, u.z), normal=(n.x, n.y, n.z))
    return (cq.Workplane(plane)
            .text(txt, P.LABEL_SIZE, P.LABEL_PROUD + 0.3,
                  font=P.LABEL_FONT, combine=False).val())


# ------------------------------------------------------------ clamshell
def ear_sites():
    """The two clamp ears, as frame-X positions either side of the split."""
    half = P.EAR_LAT / 2.0
    return [P.SPLIT_X - (P.EAR_GAP + half), P.SPLIT_X + (P.EAR_GAP + half)]


def clamp_ear_solids():
    """Two lugs flanking the split. A tie through both pulls it shut.

    The tip is shifted up relative to the base so the underside sits at 45
    degrees and prints without support.
    """
    out = []
    for x in ear_sites():
        lat = -x if P.SPLIT_FACE == "+Y" else x
        O, u, n, v = face_frame(P.SPLIT_FACE, lat, P.EAR_Z)
        w0 = face_rr_wire(O, u, v, n, 0.0, P.EAR_LAT / 2.0,
                          P.EAR_AX / 2.0, P.EAR_R)
        w1 = face_rr_wire(O, u, v, n, P.WALL + P.EAR_PROUD,
                          P.EAR_LAT / 2.0, P.EAR_AX_TIP / 2.0,
                          min(P.EAR_R, P.EAR_AX_TIP / 2.0 - 0.5),
                          0.0, P.EAR_TIP_SHIFT)
        out.append(cq.Solid.makeLoft([w0, w1], True))
    return out


def ear_hole_cutter():
    """One tie hole straight through both ears, crossing the split."""
    span = 2.0 * (P.EAR_GAP + P.EAR_LAT) + 8.0
    y0 = P.SOCK_OD_HH + P.EAR_PROUD / 2.0 - P.EAR_HOLE_T / 2.0
    box = cq.Solid.makeBox(span, P.EAR_HOLE_T, P.EAR_HOLE_H,
                           V(P.SPLIT_X - span / 2.0, y0,
                             P.EAR_HOLE_Z - P.EAR_HOLE_H / 2.0))
    if P.SPLIT_FACE == "-Y":
        box = box.mirror("XZ")
    return box


def split_cutter():
    """The slit down one wall, with a round at the top.

    A square-ended slot is a stress riser, and this part is meant to flex.
    """
    sgn = 1.0 if P.SPLIT_FACE == "+Y" else -1.0
    y_in = P.SOCK_ID_HH - 6.0
    depth = (P.SOCK_OD_HH + P.EAR_PROUD + 6.0) - y_in
    slot = cq.Solid.makeBox(P.SPLIT_W, depth, P.SPLIT_TOP + 2.0,
                            V(P.SPLIT_X - P.SPLIT_W / 2.0, y_in, -2.0))
    relief = cq.Solid.makeCylinder(
        P.SPLIT_RELIEF_R, depth,
        V(P.SPLIT_X, y_in, P.SPLIT_TOP), V(0, 1, 0))
    cut = slot.fuse(relief)
    if sgn < 0:
        cut = cut.mirror("XZ")
    return cut


# ---------------------------------------------------------------- misc parts
def mouth_leadin_cutter():
    """Unused. Kept as a record: cutting the chamfer as a separate solid
    tears the mesh (381 broken faces) because the cutter ends tangent to the
    bore. The lead-in is a section of the bore loft instead."""
    c = P.MOUTH_LEADIN
    over = c * 0.5
    w0 = sock_wire(-1.0, P.SOCK_ID_HW + c + over, P.SOCK_ID_HH + c + over,
                   P.SOCK_ID_R + c + over)
    w1 = sock_wire(c, P.SOCK_ID_HW + 0.05, P.SOCK_ID_HH + 0.05,
                   P.SOCK_ID_R + 0.05)
    return cq.Solid.makeLoft([w0, w1], True)


def bead_solid():
    """Retention bead for the silicone coupler.

    Built as a stack of lofted circles rather than a revolve: revolve()
    resolves its axis in workplane-local coordinates, which silently put the
    ring around the wrong axis and left the part with no bead at all.
    """
    zc = P.Z_END - P.BEAD_FROM_END
    r0 = P.OUTLET_OD / 2.0 - 0.4
    r1 = P.OUTLET_OD / 2.0 + P.BEAD_HEIGHT
    h = P.BEAD_FLAT / 2.0
    levels = [(zc - h - P.BEAD_RAMP, r0), (zc - h, r1),
              (zc + h, r1), (zc + h + P.BEAD_RAMP, r0)]
    wires = [cq.Wire.makeCircle(r, V(0, 0, z), V(0, 0, 1)) for z, r in levels]
    ring = cq.Solid.makeLoft(wires, True)
    # a loft of circles is a filled disc stack - hollow it out or the bead
    # plugs the outlet
    r_in = P.OUTLET_OD / 2.0 - P.OUTLET_WALL
    plug = cq.Solid.makeCylinder(r_in, 60.0, V(0, 0, zc - 30.0))
    return ring.cut(plug)


# --------------------------------------------------------------------- build
def build():
    print("building adapter")
    r_out = P.OUTLET_OD / 2.0
    r_in = r_out - P.OUTLET_WALL

    outer = duct_shell(P.SOCK_OD_HW, P.SOCK_OD_HH, P.SOCK_OD_R, r_out,
                       0.0, P.SOCKET_DEPTH, P.Z_TRANS_0, P.Z_TRANS_1, P.Z_END)
    check(outer, "outer envelope")

    ledge = duct_shell(P.SOCK_ID_HW - P.STOP_LEDGE, P.SOCK_ID_HH - P.STOP_LEDGE,
                       max(P.SOCK_ID_R - P.STOP_LEDGE, 1.0), r_in,
                       None, P.SOCKET_DEPTH, P.Z_TRANS_0, P.Z_TRANS_1,
                       P.Z_END + 2.0)
    # the mouth lead-in is built INTO the bore as an extra section rather
    # than cut afterwards: a separate cutter ends tangent to the bore and
    # OCCT returned a torn solid from it
    c = P.MOUTH_LEADIN
    bore_socket = cq.Solid.makeLoft(
        [sock_wire(-2.0, P.SOCK_ID_HW + c + 2.0, P.SOCK_ID_HH + c + 2.0,
                   P.SOCK_ID_R + c + 2.0),
         sock_wire(c, P.SOCK_ID_HW, P.SOCK_ID_HH, P.SOCK_ID_R),
         xy_wire(0.0, P.SOCK_ID_HW, P.SOCK_ID_HH, P.SOCK_ID_R, r_in,
                 P.SOCKET_DEPTH)], True)
    bore = check(bore_socket.fuse(ledge).clean(), "bore + stop ledge")

    for name, kind, lat, zc in connector_sites():
        outer = outer.fuse(boss_solid(kind, lat, zc))
    outer = check(outer.clean(), "outer + 6 connector bosses")

    body = check(outer.cut(bore).clean(), "shelled body")

    # pocket plus its two slanted tie ports, per connector. They overlap on
    # purpose; pre-fusing them costs ten extra minutes and the single
    # multi-cut handles it as long as clean() is allowed to bail.
    cutters = []
    for name, kind, lat, zc in connector_sites():
        cutters.append(pocket_solid(kind, lat, zc))
        cutters.extend(tie_port_solids(kind, lat, zc))
    body = check(safe_clean(body.cut(*cutters)),
                 "6 pockets + 12 tie ports")

    if P.RIB_ENABLE:
        ribs = [rib_solid(kind, lat) for kind, lat in rib_sites()]
        body = check(body.fuse(*ribs).clean(), f"{len(ribs)} crush ribs")

    if P.LABEL_ENABLE:
        marks = [label_solid(t, k, l, z) for t, k, l, z in label_sites()]
        body = check(body.fuse(*marks).clean(),
                     f"{len(marks)} side labels ({', '.join(m[0] for m in label_sites())})")

    if P.BEAD_ENABLE:
        body = check(body.fuse(bead_solid()).clean(), "retention bead")

    if P.SPLIT_ENABLE and P.EAR_ENABLE:
        body = check(safe_clean(body.fuse(*clamp_ear_solids())),
                     "2 clamp ears")
        body = check(safe_clean(body.cut(ear_hole_cutter())), "clamp tie hole")

    if P.SPLIT_ENABLE:
        body = check(safe_clean(body.cut(split_cutter())),
                     f"clamshell split (side {SIDE_NAME[P.SPLIT_FACE]})")

    return body
