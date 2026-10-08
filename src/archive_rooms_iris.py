"""ARCHIVE - not part of the build. Parked 2026-10-08 at Tyler's request.

Removed from src/fittings.py to keep the viewer lean:
  * ROOMS: turnaround pod, junction room, XL junction room, mesh lids.
  * IRIS GATE v2 (assembled, 6 leaves on two levels) + its fit coupons.
    (v1, print-in-place, fused solid when printed - see PROJECT.md Round 9.)
Plus their checks from tools/latch_check.py (run_room, run_iris).

To bring one back: paste its section into src/fittings.py above REGISTRY, add
its PORT_NAMES / PORT_GENDER / FITTINGS entries and the viewer variants again.
The code below expects to run inside fittings.py's namespace.
"""
from fittings import *          # noqa: F401,F403  (helpers, constants)
import numpy as np
import trimesh
import trimesh.transformations as tf

IRIS_LAYER = 0.2
IRIS_ZGAP = 0.2

# ===========================================================================
#                   ROOMS  (turnaround pod, junction room, mesh lid)
# ===========================================================================
# A room is a short round chamber she can coil and turn around in. Ports sit
# at floor level: the bore axis is at ROOM_PORT_Z so a mated fitting's skirt
# clears the surface the room stands on, and the room FLOOR is flush with the
# bottom of the bore, so she slides straight in - no step, no ramp. (The
# thick floor prints as normal infill.) Each port stub starts far enough
# inside that it meets the curved wall all the way round - a stub that starts
# at the wall line leaves gaps at its sides, where the wall curves away.
# The mesh lid twist-locks onto a latch collar around the top of the wall -
# same bayonet, scaled to the room's radius.
ROOM_ID        = 160.0       # inside diameter (about 6.3 in)
ROOM_WALL      = 3.5
ROOM_FLOOR_T   = 3.0
ROOM_STUB      = SOCKET_DEPTH + 4.0      # port stub, wall -> mouth
ROOM_PORT_Z    = SKIRT_RO + 1.5          # bore axis height: mated skirts clear
ROOM_HEADROOM  = 12.0        # above the top of the port bore
ROOM_LATCH_N   = 4           # lugs on the lid
ROOM_STUB_M    = 6.0         # stub for a MALE room port: the male end sticks out
                             # on its own, so the stub only has to clear the wall
ROOM_PORTS = {               # port angles, degrees around the room
    'room_pod':      [0.0],                  # dead end: turn around and leave
    'room_junction': [0.0, 90.0, 180.0],     # tee-shaped rest stop
    'room_junction_xl': [0.0, 90.0, 180.0],  # bigger room, male ports
}
# Per room type: inside diameter and DEFAULT port genders - every room port
# toggles F/M like any fitting (make_room(kind, genders=...)). The XL junction
# is sized so that with MALE ports it has the same width as the standard
# junction with a shim on every port (302 mm); with its default female ports
# (lower profile, no grip ribs) it is 291 mm across.
ROOM_KINDS = {
    'room_pod':         dict(id=ROOM_ID, genders='F'),
    'room_junction':    dict(id=ROOM_ID, genders='FFF'),
    'room_junction_xl': dict(id=ROOM_ID + 2 * (ROOM_STUB - ROOM_STUB_M), genders='FFF'),
}
LID_T          = 3.0
LID_HOLE       = 10.0        # hex holes, across flats
LID_BEAM       = 2.4         # solid between holes
LID_RIM        = 5.0         # solid band inside the wall line


def _room_dims(kind='room_pod'):
    ri = ROOM_KINDS[kind]['id'] / 2
    ro = ri + ROOM_WALL
    rc = ro + COLLAR_T                      # lid latch collar
    # Tall enough that the lid's latch collar and skirt (which hang
    # COLLAR_L + COLLAR_T below the rim) clear the tops of the port stubs.
    h = max(ROOM_PORT_Z + BORE_R + ROOM_HEADROOM,
            ROOM_PORT_Z + OUTER_R + COLLAR_L + COLLAR_T + 2.0)
    return ri, ro, rc, h


def room_top_frame(kind='room_pod'):
    """Port frame of the lid opening: mouth on the wall top, room below."""
    ri, ro, rc, h = _room_dims(kind)
    return port_frame((0, 0, h), (0, 0, -1))


def room_ports(kind, genders=None):
    """[(mouth, axis into the room)] for a room type."""
    ri, ro, rc, h = _room_dims(kind)
    g = genders or ROOM_KINDS[kind]['genders']
    out = []
    for a, gi in zip(ROOM_PORTS[kind], g):
        u = np.array([np.cos(np.radians(a)), np.sin(np.radians(a)), 0.0])
        stub = ROOM_STUB if gi == 'F' else ROOM_STUB_M
        out.append((u * (ro + stub) + np.array([0, 0, ROOM_PORT_Z]), -u))
    return out


def make_room(kind='room_pod', labels=False, genders=None):
    """Round room with ports at floor level and a latch collar for the lid."""
    ri, ro, rc, h = _room_dims(kind)
    gend = (genders or ROOM_KINDS[kind]['genders']).upper()
    angs = [np.radians(a) for a in ROOM_PORTS[kind]]
    floor_top = ROOM_PORT_Z - BORE_R            # flush with the bore floor
    outer = [cylinder_between((0, 0, 0), (0, 0, h), ro)]
    inner = [cylinder_between((0, 0, floor_top), (0, 0, h + 1), ri)]
    # stub root: where the inner wall is, at the stub's widest point
    r_root = np.sqrt(ri**2 - OUTER_R**2) - 1.0
    ports = room_ports(kind, gend)
    for (mouth, d_in) in ports:
        u = -d_in
        root = u * r_root + np.array([0, 0, ROOM_PORT_Z])
        outer.append(cylinder_between(root, mouth, OUTER_R))
        # bore runs well past the curved wall: ending it at the wall line along
        # the axis left a lip of wall across both sides of every entrance
        inner.append(cylinder_between(mouth + u * 1.0, u * (r_root - 6.0) + np.array([0, 0, ROOM_PORT_Z]), BORE_R))
    # lid latch collar at the top of the wall (built in the lid's port frame)
    T = room_top_frame(kind)
    col = _revolve([(ro - 1.0, 0.0), (rc, 0.0), (rc, COLLAR_L),
                    (ro - 0.3, COLLAR_L + COLLAR_T + 0.3), (ro - 1.0, COLLAR_L + COLLAR_T + 0.3)],
                   sections=180)
    col.apply_transform(T); outer.append(col)
    sl = slot_cutter_local(rc, ROOM_LATCH_N); sl.apply_transform(T)
    body = assemble(outer, inner + [sl], ports, gend)
    if labels:
        return body, port_labels(ports, gend, [f"P{i+1}" for i in range(len(ports))])
    return body


def make_room_pod(genders=None, labels=False):
    """Turnaround pod: a dead-end room to coil and come back out."""
    return make_room('room_pod', labels, genders)


def make_room_junction(genders=None, labels=False):
    """Junction room: three ports, a rest stop where routes meet."""
    return make_room('room_junction', labels, genders)


def make_room_junction_xl(genders=None, labels=False):
    """XL junction room: 216 mm inside; female ports by default (toggle any
    port to male - with all three male it matches the standard junction +
    shims, 302 mm across)."""
    return make_room('room_junction_xl', labels, genders)


def make_room_lid(kind='room_pod'):
    """Hex-mesh lid for any room: twist-locks on like a cap (4 lugs).
    Print plate-down, no supports. Built in the room's top port frame
    (plate at z < 0, skirt and lugs toward +z)."""
    import shapely.geometry as sg
    from shapely.ops import unary_union
    from trimesh.creation import extrude_polygon
    ri, ro, rc, h = _room_dims(kind)
    s_ri = rc + SKIRT_CL; s_ro = s_ri + SKIRT_T
    r_mesh = ri - LID_RIM
    pitch = LID_HOLE + LID_BEAM
    hr = LID_HOLE / np.sqrt(3)                   # hex circumradius from flats
    hexes = []
    n = int(r_mesh // pitch) + 2
    for i in range(-n, n + 1):
        for j in range(-n, n + 1):
            x = pitch * (i + 0.5 * (j % 2)); y = pitch * 0.866 * j
            if np.hypot(x, y) + hr <= r_mesh:
                hexes.append(sg.Polygon([(x + hr * np.cos(np.pi / 6 + k * np.pi / 3),
                                          y + hr * np.sin(np.pi / 6 + k * np.pi / 3))
                                         for k in range(6)]))
    plate2d = sg.Point(0, 0).buffer(s_ro, 256).difference(unary_union(hexes))
    plate = extrude_polygon(plate2d, height=LID_T)
    plate.apply_translation((0, 0, -LID_T))
    skirt = _revolve([(s_ri, -0.5), (s_ro, -0.5), (s_ro, SKIRT_L),
                      (s_ri + 0.4, SKIRT_L), (s_ri, SKIRT_L - 0.4)], sections=180)
    parts = [plate, skirt, lugs_local(rc, ROOM_LATCH_N)]
    for k in range(48):
        a = 2 * np.pi * (k + 0.5) / 48
        parts.append(_sector(s_ro - 0.3, s_ro + 1.0, a - _arc(0.8, s_ro), a + _arc(0.8, s_ro),
                             -LID_T + 0.6, SKIRT_L - 1.0))
    return drop_slivers(union(parts))



# ===========================================================================
#                    IRIS GATE  (assembled, 2 levels of leaves)
# ===========================================================================
# v1 was print-in-place and fused solid (0.2 mm gaps over big sliding faces).
# v2 is ASSEMBLED from separate parts with real clearances; every part prints
# flat with no supports.
#
# Six identical flat leaves, each turning about a fixed pivot pin. While they
# move, neighbouring leaves overlap - but ONLY neighbours ever do (the 2D
# sweep in latch_check.run_iris proves it). So the leaves alternate between
# two levels: even leaves LOW, odd leaves HIGH, and two leaves on the same
# level never come closer than IRIS_SAME_GAP.
#
# Each leaf is one level thick (IRIS_T) wherever a neighbour ever passes over
# or under it, and FULL height (both levels) everywhere else - a "pad". The
# pad bears on the floor below and the ring/cover above, so every leaf is held
# at its own level in any orientation (a gate in a vertical tube can't let the
# top leaves sag into the bottom ones).
#
# Nothing sticks out of a leaf: it has a pivot HOLE and a drive SLOT. The
# pivot pins stand on the base (low leaves) and hang from the cover (high
# leaves); the drive pins stand on the lower ring (low leaves) and hang from
# the upper ring (high leaves). Every pin is shorter than one leaf level, so
# no pin ever reaches the other level. The two rings key together through the
# cup wall around the leaves and turn as one by the lever.
#
# The slot holds the leaf still for IRIS_DWELL degrees of ring travel at each
# end, so pushing on the leaves - open or closed - cannot turn the ring.
#
# Parts: base (port A), cover (port B, 3x M3x16), lower ring + lever, upper
# ring, 3x leaf_low, 3x leaf_high (mirror images - print 3 of each).

IRIS_N        = 6
IRIS_PHI      = 60.0          # leaf span (deg) in the open position
IRIS_R1       = BORE_R + 0.75 # leaf inner edge, open (clear of the bore)
IRIS_R2       = 56.0          # leaf outer edge
IRIS_PIV_R    = 35.0          # pivot radius ...
IRIS_PIV_A    = 2.5           # ... and angle (deg) in the leaf's open frame
IRIS_SWING    = 55.0          # leaf rotation, open -> closed (deg)
IRIS_K        = 0.25          # ring degrees per leaf degree
IRIS_RPIN     = (42.5, 3.0)   # drive pin on the ring, leaf 0, ring at 0 (open)
IRIS_EAR      = 4.8           # leaf material around the pivot
IRIS_T        = 2.2           # one leaf level
IRIS_PIN_D    = 4.0           # pivot and drive pins
IRIS_RING_T   = 4.0
IRIS_G        = 0.3           # axial clearance at every sliding face
IRIS_CLR      = 0.25          # radial clearance: pin/hole, ring/step
IRIS_SLOT_CLR = 0.30          # per side, pin in slot
IRIS_DWELL    = 5.0           # deg of ring travel at each end with no leaf motion
IRIS_PAD_M    = 0.8           # pad edge kept this far from any neighbour's sweep
IRIS_STEP_W   = 1.2           # step material around a pivot pin
IRIS_CUP_W    = 2.4           # cup wall (joins the two rings)
IRIS_WALL     = 3.0           # housing wall
IRIS_LEVER    = 14.0
IRIS_SCREW_PILOT = 2.6        # M3 self-tapping into the base flange
IRIS_SCREW_CLR   = 3.4
IRIS_SAME_GAP = 1.5           # minimum allowed gap, two leaves on one level


def _rot2(p, deg, about=(0.0, 0.0)):
    t = np.radians(deg); c, s = np.cos(t), np.sin(t)
    q = np.asarray(p, float) - about
    return np.array([c * q[0] - s * q[1], s * q[0] + c * q[1]]) + about


def _iris_pivot():
    a = np.radians(IRIS_PIV_A)
    return np.array([IRIS_PIV_R * np.cos(a), IRIS_PIV_R * np.sin(a)])


_IRIS_CACHE = {}


def _iris_leaf_poly():
    """Leaf outline in its OPEN position, leaf 0 (spans 0..IRIS_PHI deg)."""
    if 'poly' not in _IRIS_CACHE:
        import shapely.geometry as sg
        a = np.radians(np.linspace(0, IRIS_PHI, 121))
        S = sg.Polygon([(IRIS_R2 * np.cos(t), IRIS_R2 * np.sin(t)) for t in a] +
                       [(IRIS_R1 * np.cos(t), IRIS_R1 * np.sin(t)) for t in a[::-1]])
        P = _iris_pivot()
        E = sg.Point(P).buffer(IRIS_EAR, 48)
        bridge = S.intersection(sg.Point(P).buffer(IRIS_EAR + 8, 48)).union(E).convex_hull
        L = S.union(bridge)
        _IRIS_CACHE['poly'] = L.buffer(-0.8, join_style=1).buffer(0.8, join_style=1)
    return _IRIS_CACHE['poly']


def iris_rot():
    """Total lever / ring travel, open -> closed (deg)."""
    return IRIS_K * IRIS_SWING + 2 * IRIS_DWELL


def iris_leaf_angle(beta):
    """Leaf rotation (deg) for ring angle beta (0 = open)."""
    return float(np.clip((beta - IRIS_DWELL) / IRIS_K, 0.0, IRIS_SWING))


def _iris_outline(k, beta):
    import shapely.affinity as sa
    L = sa.rotate(_iris_leaf_poly(), iris_leaf_angle(beta), origin=tuple(_iris_pivot()))
    return sa.rotate(L, 360.0 * k / IRIS_N, origin=(0, 0))


def _iris_pad_poly():
    """Leaf-0 region (open frame) that no neighbour ever passes over or under:
    the leaf is full height there."""
    if 'pad' not in _IRIS_CACHE:
        import shapely.affinity as sa
        from shapely.ops import unary_union
        P = tuple(_iris_pivot()); L = _iris_leaf_poly(); ov = []
        for b in np.linspace(0, iris_rot(), 90):
            a = iris_leaf_angle(b)
            L0 = _iris_outline(0, b)
            for j in (1, -1):
                o = L0.intersection(_iris_outline(j, b))
                if not o.is_empty:
                    ov.append(sa.rotate(o, -a, origin=P))
        pad = L.difference(unary_union(ov).buffer(IRIS_PAD_M, 32))
        pad = pad.buffer(-0.6, join_style=1).buffer(0.6, join_style=1)
        # inset from the leaf outline: a pad wall exactly on the plate wall
        # unions into sliver faces that break the STL
        pad = pad.intersection(L.buffer(-0.3, join_style=1)).simplify(0.03)
        if pad.geom_type == 'MultiPolygon':                 # keep the real pad, drop crumbs
            pad = max(pad.geoms, key=lambda g: g.area)
        _IRIS_CACHE['pad'] = pad
    return _IRIS_CACHE['pad']


def _iris_slot_path():
    """Drive pin path in the leaf-0 open frame, ring open -> closed."""
    P = _iris_pivot(); pts = []
    for b in np.linspace(0, iris_rot(), 120):
        w = _rot2(IRIS_RPIN, b)                             # pin, world
        pts.append(tuple(_rot2(w, -iris_leaf_angle(b), P)))  # seen from the leaf
    return pts


def iris_dims():
    if 'dims' in _IRIS_CACHE:
        return dict(_IRIS_CACHE['dims'])
    d = {}
    d['step_r'] = IRIS_PIV_R + IRIS_PIN_D / 2 + IRIS_STEP_W
    d['ring_ri'] = d['step_r'] + IRIS_CLR + 0.15
    r = 0.0
    for b in np.linspace(0, iris_rot(), 31):
        q = _iris_outline(0, b)
        r = max(r, np.hypot(*np.asarray(q.exterior.coords).T).max())
    d['maxR'] = r
    d['cup_ri'] = d['maxR'] + 0.8
    d['cup_ro'] = d['cup_ri'] + IRIS_CUP_W
    d['Rc'] = d['cup_ro'] + 0.5
    d['Rh'] = d['Rc'] + IRIS_WALL
    g = IRIS_G
    d['zc0'] = COLLAR_L + COLLAR_T + 2.0                  # 45 deg cone starts
    d['zf0'] = d['zc0'] + (d['Rh'] - OUTER_R)             # cone at full width
    d['zF'] = d['zf0'] + 1.0                              # chamber floor
    d['zR0'] = d['zF'] + g;  d['zR1'] = d['zR0'] + IRIS_RING_T     # lower ring
    d['zL0'] = d['zR1'] + g; d['zL1'] = d['zL0'] + IRIS_T          # low level
    d['zH0'] = d['zL1'] + g; d['zH1'] = d['zH0'] + IRIS_T          # high level
    d['zU0'] = d['zH1'] + g; d['zU1'] = d['zU0'] + IRIS_RING_T     # upper ring
    d['zTop'] = d['zU1'] + g                              # base rim top = cover face
    d['Rf'] = min(d['Rh'] + 11.0, OUTER_R + (d['zTop'] - d['zc0']))
    d['Rs'] = d['Rh'] + 5.0                               # screw circle
    assert d['Rf'] >= d['Rs'] + 4.5, "flange too narrow for the screws"
    d['cover_t'] = 4.0
    d['zcv'] = d['zTop'] + d['cover_t']
    d['zcv1'] = d['zcv'] + (d['Rf'] - OUTER_R)
    d['H'] = d['zcv1'] + d['zc0']                         # port B mouth (mirror of A)
    d['lever_a'] = np.radians(-90.0)                      # lever points -y (front)
    _IRIS_CACHE['dims'] = d
    return dict(d)


def _iris_leaf_frame(k, beta):
    """4x4: leaf-0 open frame -> leaf k at ring angle beta."""
    a = iris_leaf_angle(beta)
    P = _iris_pivot()
    T1 = tf.translation_matrix((-P[0], -P[1], 0))
    R1 = tf.rotation_matrix(np.radians(a), (0, 0, 1))
    T2 = tf.translation_matrix((P[0], P[1], 0))
    Rk = tf.rotation_matrix(2 * np.pi * k / IRIS_N, (0, 0, 1))
    return Rk @ T2 @ R1 @ T1


def iris_leaf_local(level):
    """Leaf 0 in its open position, in place. 'low': plate on the low level,
    pad rising to the top of the high level. 'high': the mirror."""
    import shapely.geometry as sg
    from trimesh.creation import extrude_polygon
    d = iris_dims()
    plate = extrude_polygon(_iris_leaf_poly(), height=IRIS_T)
    pad = extrude_polygon(_iris_pad_poly(), height=IRIS_T + IRIS_G + 0.3)
    if level == 'low':
        plate.apply_translation((0, 0, d['zL0']))
        pad.apply_translation((0, 0, d['zL1'] - 0.3))
    else:
        plate.apply_translation((0, 0, d['zH0']))
        pad.apply_translation((0, 0, d['zL0']))
    body = union([plate, pad])
    P = _iris_pivot()
    hole = cylinder_between((P[0], P[1], d['zL0'] - 1), (P[0], P[1], d['zH1'] + 1),
                            IRIS_PIN_D / 2 + IRIS_CLR, sections=48)
    slot2d = sg.LineString(_iris_slot_path()).simplify(0.02).buffer(IRIS_PIN_D / 2 + IRIS_SLOT_CLR, 12)
    slot = extrude_polygon(slot2d, height=d['zH1'] - d['zL0'] + 2)
    slot.apply_translation((0, 0, d['zL0'] - 1))
    return difference(body, union([hole, slot]))


def iris_leaf(k, beta=0.0):
    # weld BEFORE rotating: the plate/pad union leaves vertices ~1e-6 mm apart,
    # and after a 60 or 240 deg turn float32 rounding merges them (broken STL)
    lv = 'low' if k % 2 == 0 else 'high'
    if ('leaf', lv) not in _IRIS_CACHE:
        _IRIS_CACHE[('leaf', lv)] = export_ready(iris_leaf_local(lv))
    m = _IRIS_CACHE[('leaf', lv)].copy()
    m.apply_transform(_iris_leaf_frame(k, beta))
    return m


def _iris_keys():
    """Angles of the 3 keys joining the upper ring to the cup wall."""
    return [np.radians(30.0 + 120.0 * i) for i in range(3)]


def _iris_pin(x, y, z_root, z_tip, c=0.5):
    """Pin with a lead-in chamfer at the tip (tip up or down)."""
    r = IRIS_PIN_D / 2
    h = abs(z_tip - z_root)
    m = _revolve([(0, 0), (r, 0), (r, h - c), (r - c, h), (0, h)], sections=48)
    if z_tip < z_root:
        m.apply_transform(tf.rotation_matrix(np.pi, (1, 0, 0)))
    m.apply_translation((x, y, z_root))
    return m


def _iris_ring_pins(ks, z_root, z_tip):
    out = []
    for k in ks:
        q = _rot2(IRIS_RPIN, 360.0 * k / IRIS_N)
        out.append(_iris_pin(q[0], q[1], z_root, z_tip))
    return out


def iris_ring_lower(beta=0.0):
    """Lower ring + cup wall + lever (one part). Its pins drive the LOW leaves."""
    import shapely.geometry as sg
    import shapely.affinity as sa
    from trimesh.creation import extrude_polygon
    d = iris_dims()
    ring = sg.Point(0, 0).buffer(d['cup_ro'], 256).difference(sg.Point(0, 0).buffer(d['ring_ri'], 256))
    la = d['lever_a']; tw = 10.0
    tab = sg.box(d['cup_ro'] - 1.0, -tw / 2, d['Rf'] + 2.0, tw / 2)
    tab = sa.rotate(tab, la, origin=(0, 0), use_radians=True)
    base = extrude_polygon(ring.union(tab), height=IRIS_RING_T)
    base.apply_translation((0, 0, d['zR0']))
    wall = _revolve([(d['cup_ri'], d['zR1'] - 0.3), (d['cup_ro'], d['zR1'] - 0.3),
                     (d['cup_ro'], d['zU0']), (d['cup_ri'], d['zU0'])], sections=256)
    parts = [base, wall] + _iris_ring_pins([0, 2, 4], d['zR1'] - 0.3, d['zL1'] - 0.15)
    # lever rises 45 deg up and out from the tab (exactly 45: prints unsupported)
    u = np.array([np.cos(la), np.sin(la), 0]); v = np.array([-u[1], u[0], 0])
    r0 = d['Rf'] + 0.6; rise = IRIS_LEVER
    pts = []
    for (r, z) in [(d['Rf'] + 0.6, d['zR0']), (d['Rf'] + 0.6, d['zR1']),
                   (r0 + rise, d['zR0'] + rise), (r0 + rise, d['zR1'] + rise)]:
        for s_ in (-tw / 2, tw / 2):
            pts.append(u * r + v * s_ + np.array([0, 0, z]))
    parts.append(trimesh.convex.convex_hull(np.array(pts)))
    m = union(parts)
    cut = [_sector(d['cup_ri'] - 0.5, d['cup_ro'] + 0.5, a - _arc(3.3, d['cup_ro']),
                   a + _arc(3.3, d['cup_ro']), d['zU0'] - 2.0, d['zU0'] + 1.0) for a in _iris_keys()]
    m = difference(m, union(cut))
    m.apply_transform(tf.rotation_matrix(np.radians(beta), (0, 0, 1)))
    return m


def iris_ring_upper(beta=0.0):
    """Upper ring: its pins drive the HIGH leaves; keys drop into the cup wall."""
    import shapely.geometry as sg
    from trimesh.creation import extrude_polygon
    d = iris_dims()
    ring = sg.Point(0, 0).buffer(d['cup_ro'], 256).difference(sg.Point(0, 0).buffer(d['ring_ri'], 256))
    m = extrude_polygon(ring, height=IRIS_RING_T)
    m.apply_translation((0, 0, d['zU0']))
    keys = [_sector(d['cup_ri'] + 0.25, d['cup_ro'] - 0.25, a - _arc(3.0, d['cup_ro']),
                    a + _arc(3.0, d['cup_ro']), d['zU0'] - 1.7, d['zU0'] + 0.3) for a in _iris_keys()]
    m = union([m] + keys + _iris_ring_pins([1, 3, 5], d['zU0'] + 0.3, d['zH0'] + 0.15))
    m.apply_transform(tf.rotation_matrix(np.radians(beta), (0, 0, 1)))
    return m


def iris_ports():
    d = iris_dims()
    return [((0, 0, 0), (0, 0, 1)), ((0, 0, d['H']), (0, 0, -1))]


def _iris_screw_angles():
    """3 screws, spaced away from the lever window."""
    la = np.degrees(iris_dims()['lever_a'])
    return [np.radians(la + x) for x in (110.0, 230.0, 350.0)]


def _iris_screw(a, z0, z1, rad):
    d = iris_dims()
    p = np.array([d['Rs'] * np.cos(a), d['Rs'] * np.sin(a)])
    return cylinder_between((p[0], p[1], z0), (p[0], p[1], z1), rad, sections=32)


IRIS_TONGUE = (2.0, 1.5)      # centring tongue on the base rim: width, height


def _iris_pivot_pins(ks, z_root, z_tip):
    out = []
    for k in ks:
        P = _rot2(_iris_pivot(), 360.0 * k / IRIS_N)
        out.append(_iris_pin(P[0], P[1], z_root, z_tip))
    return out


def iris_base(genders=None):
    """Port A, 45 deg cone/flange, chamber floor with the low leaves' pivot
    pins, lever window, centring tongue, 3 screw pilots. Prints standing on
    port A, no supports."""
    g = (genders or PORT_GENDER.get('iris_gate', 'FF'))[0]
    d = iris_dims()
    tw, th = IRIS_TONGUE
    t0 = d['Rh'] + 0.5
    outer = [cylinder_between((0, 0, 0), (0, 0, d['zc0'] + 0.5), OUTER_R),
             _revolve([(BORE_R + 0.5, d['zc0']), (OUTER_R, d['zc0']),
                       (d['Rf'], d['zc0'] + d['Rf'] - OUTER_R), (d['Rf'], d['zTop']),
                       (t0 + tw, d['zTop']), (t0 + tw, d['zTop'] + th),
                       (t0, d['zTop'] + th), (t0, d['zTop']),
                       (BORE_R + 0.5, d['zTop'])], sections=256)]
    inner = [cylinder_between((0, 0, -1), (0, 0, d['zTop'] + 1), BORE_R, sections=SEG_CYL),
             _revolve([(d['step_r'], d['zR1']), (d['step_r'], d['zF']), (d['Rc'], d['zF']),
                       (d['Rc'], d['zTop'] + 1), (BORE_R - 1, d['zTop'] + 1),
                       (BORE_R - 1, d['zR1'])], sections=256)]
    # lever window: full travel of the 10 mm tab at lower-ring height. Its top
    # is a ~45 mm bridge: 0.8 mm headroom so a little sag can't rub the lever
    la = d['lever_a']; half = np.arcsin(5.0 / d['Rh']) + np.radians(2.5)
    a0, a1 = la - half, la + np.radians(iris_rot()) + half
    inner.append(_sector(d['Rc'] - 1.0, d['Rf'] + 1.0, a0, a1, d['zR0'] - IRIS_G, d['zR1'] + 0.8))
    inner += [_iris_screw(a, d['zTop'] - 11.0, d['zTop'] + 3, IRIS_SCREW_PILOT / 2)
              for a in _iris_screw_angles()]
    body = assemble(outer, inner, [iris_ports()[0]], g)
    return union([body] + _iris_pivot_pins([0, 2, 4], d['zR1'] - 0.3, d['zL1'] - 0.15))


def iris_cover(genders=None):
    """Cover: step + the high leaves' pivot pins, centring groove, 3 screw
    holes with counterbores, 45 deg cone, port B. Prints standing on port B
    (upside down), no supports."""
    g = (genders or PORT_GENDER.get('iris_gate', 'FF'))[1]
    d = iris_dims()
    zt = d['zTop']
    outer = [_revolve([(BORE_R + 0.5, d['zU0']), (d['step_r'], d['zU0']), (d['step_r'], zt),
                       (d['Rf'], zt), (d['Rf'], d['zcv']),
                       (OUTER_R, d['zcv1']), (BORE_R + 0.5, d['zcv1'])], sections=256),
             cylinder_between((0, 0, d['zcv1'] - 0.5), (0, 0, d['H']), OUTER_R)]
    inner = [cylinder_between((0, 0, d['zU0'] - 1), (0, 0, d['H'] + 1), BORE_R, sections=SEG_CYL)]
    tw, th = IRIS_TONGUE
    t0 = d['Rh'] + 0.5
    inner.append(_revolve([(t0 - IRIS_CLR, zt - 1), (t0 + tw + IRIS_CLR, zt - 1),
                           (t0 + tw + IRIS_CLR, zt + th + 0.3), (t0 - IRIS_CLR, zt + th + 0.3)],
                          sections=256))
    for a in _iris_screw_angles():
        inner.append(_iris_screw(a, zt - 1, zt + 40, IRIS_SCREW_CLR / 2))
        inner.append(_iris_screw(a, zt + 6.0, zt + 60, 3.3))          # head counterbore
    body = assemble(outer, inner, [iris_ports()[1]], g)
    return union([body] + _iris_pivot_pins([1, 3, 5], d['zU0'] + 0.3, d['zH0'] + 0.15))


def iris_parts(genders=None, beta=0.0):
    """[base, cover, lower ring, upper ring, leaf0..5] assembled at ring
    angle beta (0 = open, iris_rot() = closed)."""
    return ([iris_base(genders), iris_cover(genders), iris_ring_lower(beta),
             iris_ring_upper(beta)] + [iris_leaf(k, beta) for k in range(IRIS_N)])


IRIS_PART_NAMES = ['base', 'cover', 'ring_lower', 'ring_upper'] + \
                  [f'leaf{k}_{"low" if k % 2 == 0 else "high"}' for k in range(IRIS_N)]


def iris_print_kit(genders=None):
    """{file stem: mesh} - every part in its print orientation, on z = 0.
    High leaves print flipped (flat face down), so their STL is the mirror of
    the low leaf - 3 of each, not interchangeable."""
    def bed(m, flip=False):
        m = m.copy()
        if flip:
            m.apply_transform(tf.rotation_matrix(np.pi, (1, 0, 0)))
        m.apply_translation((0, 0, -m.bounds[0][2]))
        return m
    return {'iris_base': bed(iris_base(genders)),
            'iris_cover': bed(iris_cover(genders), flip=True),
            'iris_ring_lower': bed(iris_ring_lower()),
            'iris_ring_upper': bed(iris_ring_upper(), flip=True),
            'iris_leaf_low_x3': bed(iris_leaf_local('low')),
            'iris_leaf_high_x3': bed(iris_leaf_local('high'), flip=True)}


def make_iris_fit_coupons():
    """[plate, key] - a 10-minute test of the iris clearances before the big
    print. The plate has the real pivot pin and a second fixed pin; the key is
    a short piece of leaf (real thickness) with the real pivot hole and an arc
    slot with the real slot clearance. Drop the key over the pins: it must
    swing end to end without binding and without rattling loose."""
    import shapely.geometry as sg
    from trimesh.creation import extrude_polygon
    R = 12.0                                  # pivot -> drive pin
    sweep = np.radians(25.0)
    th = 3.0
    plate = trimesh.creation.box(extents=(30.0, 30.0, th)); plate.apply_translation((6.0, 0, th / 2))
    pin_h = IRIS_G + IRIS_T - 0.15
    pins = [cylinder_between((0, 0, th - 0.3), (0, 0, th + pin_h), IRIS_PIN_D / 2, sections=48),
            cylinder_between((R, 0, th - 0.3), (R, 0, th + pin_h), IRIS_PIN_D / 2, sections=32)]
    plate = union([plate] + pins)
    a = np.linspace(-sweep, sweep, 40)
    key2d = sg.Point(0, 0).buffer(IRIS_EAR, 48).union(
        sg.LineString([(R * np.cos(t), R * np.sin(t)) for t in a]).buffer(IRIS_PIN_D / 2 + IRIS_SLOT_CLR + 1.6, 32)
    ).convex_hull
    key = extrude_polygon(key2d, height=IRIS_T)
    hole = cylinder_between((0, 0, -1), (0, 0, IRIS_T + 1), IRIS_PIN_D / 2 + IRIS_CLR, sections=48)
    slot2d = sg.LineString([(R * np.cos(t), R * np.sin(t)) for t in a]).buffer(IRIS_PIN_D / 2 + IRIS_SLOT_CLR, 32)
    slot = extrude_polygon(slot2d, height=IRIS_T + 2); slot.apply_translation((0, 0, -1))
    key = difference(key, union([hole, slot]))
    key.apply_translation((0, 24.0, 0))
    return [plate, key]


def export_ready_multi(parts, digits=4):
    """Several separate bodies -> one mesh, each proven watertight first."""
    return trimesh.util.concatenate([export_ready(m, digits) for m in parts])


def make_iris_gate(genders=None, labels=False):
    """Iris gate, assembled (open). Preview of all parts in place - print the
    parts from iris_print_kit()."""
    g = genders or PORT_GENDER.get('iris_gate', 'FF')
    parts = iris_parts(g, 0.0)
    m = trimesh.util.concatenate(parts)
    return (m, port_labels(iris_ports(), g, ['A', 'B'])) if labels else m



# ---- checks (were in tools/latch_check.py) ----
def run_room(F=None, kind='room_junction', genders=None):
    """Room checks: (1) the lid locks on (no overlap), holds when pushed up
    from inside, lifts free at entry; (2) a coupler latched on every port
    (directly on a male port, or through a shim on a female one) clears the
    room, and for male ports is held when pulled and free at entry; (3)
    nothing - room or attached fittings - goes below the surface it sits on."""
    if F is None:
        import fittings as F
    g = (genders or F.ROOM_KINDS[kind]['genders']).upper()
    room, labels = F.make_room(kind, labels=True, genders=g)
    lid = F.make_room_lid(kind)
    T = F.room_top_frame(kind)
    rot = F.LATCH_ROT_DEG

    def lid_at(deg, pull):
        m = lid.copy()
        m.apply_transform(tf.rotation_matrix(np.radians(deg), (0, 0, 1)))
        m.apply_translation((0, 0, -pull))
        m.apply_transform(T)
        return m
    r = {"lid locked": _overlap(room, lid_at(rot, 0)),
         "lid locked, lifted 1 mm": _overlap(room, lid_at(rot, 1.0)),
         "lid at entry, lifted 1 mm": _overlap(room, lid_at(0, 1.0))}
    cp = F.make_coupler()
    worst, lowest, held_min, free_max = 0.0, room.bounds[0][2], 1e9, 0.0
    for (mouth, d_in), gi in zip(F.room_ports(kind, g), g):
        W = F.port_frame(mouth, d_in) @ F.shim_side_frame()

        def mate(deg, pull):
            c = cp.copy()
            c.apply_transform(tf.rotation_matrix(np.radians(-deg), (0, 0, 1)))
            c.apply_translation((0, 0, pull))
            c.apply_transform(W)
            return c
        c = mate(rot, 0)
        worst = max(worst, _overlap(room, c))
        lowest = min(lowest, c.bounds[0][2])
        if gi == 'M':
            held_min = min(held_min, _overlap(room, mate(rot, 1.0)))
            free_max = max(free_max, _overlap(room, mate(0, 1.0)))
        else:
            cap = F.make_cap(); cap.apply_transform(F.port_frame(mouth, d_in))
            lowest = min(lowest, cap.bounds[0][2])
    r["coupler on each port"] = worst
    if held_min < 1e9:
        r["male port: locked, pulled 1 mm"] = held_min
        r["male port: entry, pulled 1 mm"] = free_max
    for k, v in r.items():
        print(f"  {k:32s} {v:8.2f} mm3")
    print(f"  lowest point, room + anything latched on: z = {lowest:.2f} mm (surface is z = 0)")
    ok = (r["lid locked"] < 0.5 and r["lid locked, lifted 1 mm"] > 5
          and r["lid at entry, lifted 1 mm"] < 0.5 and worst < 0.5 and lowest >= -1e-6
          and (held_min > 5 if held_min < 1e9 else True) and free_max < 0.5)
    print(f"  ROOM {kind} {g}:", "OK" if ok else "FAILED")
    return ok



def run_iris(F=None, steps=24, genders='FF'):
    """Assembled iris (v2). At every ring angle open -> closed: no part may
    overlap any other (base, cover, both rings, six leaves on two levels, all
    pins). Plus: open = bore completely clear; closed = only a small centre
    hole; same-level leaves never closer than IRIS_SAME_GAP; every leaf's
    full-height pad stays over the floor/ring (so no leaf can drift into the
    other level in any orientation); pins engage deeper than the leaf can
    lift; every sliding face has real clearance."""
    if F is None:
        import fittings as F
    import itertools
    import shapely.geometry as sg
    import shapely.affinity as sa
    from shapely.ops import unary_union
    d = F.iris_dims(); rot = F.iris_rot()
    base, cover = F.iris_base(genders), F.iris_cover(genders)
    worst, where = 0.0, None
    for b in np.linspace(0, rot, steps + 1):
        parts = [base, cover, F.iris_ring_lower(b), F.iris_ring_upper(b)] + \
                [F.iris_leaf(k, b) for k in range(F.IRIS_N)]
        for i, j in itertools.combinations(range(len(parts)), 2):
            v = _overlap(parts[i], parts[j])
            if v > worst:
                worst, where = v, (round(float(b), 1), F.IRIS_PART_NAMES[i], F.IRIS_PART_NAMES[j])
    out = F._iris_outline
    open_r = min(np.hypot(*np.asarray(out(k, 0).exterior.coords).T).min() for k in range(F.IRIS_N))
    disk = sg.Point(0, 0).buffer(F.BORE_R, 256)
    hole = disk.difference(unary_union([out(k, rot) for k in range(F.IRIS_N)]))
    far = 0.0 if hole.is_empty else max(sg.Point(0, 0).hausdorff_distance(g)
                                        for g in getattr(hole, 'geoms', [hole]))
    same = min(out(0, b).distance(out(2, b)) for b in np.linspace(0, rot, 60))
    # pad support: the part of the pad that is over the floor step / rings
    P = tuple(F._iris_pivot()); pad = F._iris_pad_poly()
    support = sg.Point(0, 0).buffer(d['cup_ro'], 256).difference(sg.Point(0, 0).buffer(F.BORE_R + 0.5, 256))
    pad_min = min(sa.rotate(pad, F.iris_leaf_angle(b), origin=P).intersection(support).area
                  for b in np.linspace(0, rot, 40))
    lift = F.IRIS_G                                   # pad top/bottom is one gap from the ring/cover
    eng = (d['zL1'] - 0.15) - d['zL0']                # pivot and drive pins into the leaf
    from trimesh.proximity import ProximityQuery
    parts0 = [base, cover, F.iris_ring_lower(0), F.iris_ring_upper(0)] + [F.iris_leaf(k, 0) for k in range(F.IRIS_N)]
    gap = np.inf
    joined = {(0, 1), (1, 0), (2, 3), (3, 2)}        # base+cover screwed, rings keyed: meant to touch
    import gc
    samples = {i: parts0[i].sample(4000) for i in range(2, len(parts0))}
    for j in range(len(parts0)):                     # one spatial index per mesh, then free it
        q = parts0[j].copy()                         # (each index is ~0.7 GB: never keep ten)
        pq = ProximityQuery(q)
        for i, pts in samples.items():
            if i != j and (i, j) not in joined:
                gap = min(gap, np.abs(pq.signed_distance(pts)).min())
        del pq, q; gc.collect()
    print(f"  worst overlap over {steps+1} ring angles (0..{rot:.1f} deg): {worst:.3f} mm3  {where or ''}")
    print(f"  open:   leaves start at r = {open_r:.2f} mm (bore radius {F.BORE_R:.2f}) -> bore fully clear")
    print(f"  closed: everything outside r = {far:.1f} mm is covered (centre hole <= {2*far:.1f} mm across)")
    print(f"  same-level leaves: closest {same:.2f} mm apart (min {F.IRIS_SAME_GAP})")
    print(f"  pads: >= {pad_min:.0f} mm2 of each leaf's full-height pad always over floor/ring")
    print(f"  pins: {eng:.2f} mm into the leaf, leaf can lift {lift:.2f} mm")
    print(f"  resting clearance between parts ~{gap:.2f} mm")
    ok = (worst < 0.05 and open_r >= F.BORE_R and far <= 4.0 and same >= F.IRIS_SAME_GAP
          and pad_min > 60 and eng > lift + 1.2 and gap > 0.15)
    print("  IRIS", "OK" if ok else "FAILED")
    return ok


