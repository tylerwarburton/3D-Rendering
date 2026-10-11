"""Mockup of the adapter in the car, for the configurator's Car view.

    python build.py mock      -> mock/*.stl + scene.json next to the part

Real geometry: the adapter and Tyler's false turn signal
(source/false_turn_signal.stl - the file holds both sides; side A, printed
upside down, is the driver side). Everything else is a mock at plausible
1990 NA Miata (US, LHD) sizes - not measured.

Plumbing (Tyler, 2026-10-11):
  intake   false turn signal (driver side) -> adapter -> short hose -> turbo
           compressor (its ONLY inlet) -> down, forward -> intercooler in
           front of the radiator -> up the passenger side -> throttle body
  exhaust  4 runners merge into the turbine (hot side) -> downpipe, dumps
           under the car

Car coordinates, mm: x forward, y to the driver side (left), z up from the
ground; x = 0 is the tip of the nose.
"""
import json
import math
import os

import numpy as np
import trimesh

import params as P

HERE = os.path.dirname(os.path.abspath(__file__))
SIGNAL_STL = os.path.join(HERE, "..", "source", "false_turn_signal.stl")
MPH = 0.44704
RHO = 1.204                                        # kg/m3, 20 C sea level

# ---------------------------------------------------------------- body shape
W_MAX = 837.0                                      # half of the 1675 mm width
TOP = [(40, 520), (0, 560), (-60, 585), (-300, 612), (-600, 650), (-1000, 700), (-1350, 750), (-1450, 790),
       (-2900, 800), (-3300, 840), (-3800, 830), (-3990, 720)]
# fender crowns standing above the hood / deck (front wings, rear haunches)
CROWN = [(0, 0), (-250, 30), (-500, 75), (-1150, 75), (-1450, 12), (-2800, 12), (-3050, 60), (-3600, 60), (-3850, 0)]
BOT = [(40, 270), (0, 240), (-200, 200), (-400, 175), (-3600, 165), (-3990, 280)]
AXLES = (-800.0, -3065.0)                          # 2265 mm wheelbase
WHEEL_R, WHEEL_Z, TRACK = 290.0, 290.0, 1405.0


def interp(tab, x):
    xs, vs = zip(*sorted(tab))
    return float(np.interp(x, xs, vs))


# ---------------------------------------------------------------- the false turn signal sets the nose
# The vent goes on first; the snub nose is then drawn through its bezel
# (Tyler: the nose follows the vents' curve), the pop-up's front edge sits
# 1 in behind the vent face and the vent's top 1 in below the pop-up.
SIGNAL_Y = 520.0                                   # centred under the pop-up headlight (Tyler)
INCH = 25.4
NOSE_TIP = 0.0


def duct_rim(v, zc):
    """Centre of the duct's back end (the 136 x 44 rim) and the duct's axis
    out of it (pointing back). The rim is cut square to the duct: in plan it
    runs from the inner wall's back corner to the outer wall's, at mid
    height. Works on the housing placed with its duct running roughly back."""
    a = v
    v = v[np.abs(v[:, 2] - zc) < 12]
    p_in = v[v[:, 0].argmin()]
    w = v[(v[:, 1] > p_in[1] + 0.6 * P.FRAME_W) & (v[:, 1] < p_in[1] + P.FRAME_W)]
    p_out = w[w[:, 0].argmin()]
    r = (p_out - p_in) * [1, 1, 0]
    r /= np.linalg.norm(r)
    axis = np.array([-r[1], r[0], 0.0])
    if axis[0] > 0:
        axis = -axis
    near = a[(a - p_in) @ axis > -8]                  # the last 8 mm of the duct
    near = near[np.abs((near - p_in) @ r - P.FRAME_W / 2) < P.FRAME_W * 0.6]
    u, z = (near - p_in) @ r, near[:, 2]
    end = p_in + r * (u.min() + u.max()) / 2
    end[2] = (z.min() + z.max()) / 2
    return end, axis


def _vent_plan():
    """Side B (the driver side, as printed, blinker outboard) in car x/y,
    z centred on 0, plus its bezel's front edge in plan. Its duct is skewed
    to its bezel; the duct runs straight back (as our adapter does) and the
    bezel then faces forward and out, wrapping round the nose corner
    (Tyler: angled out, not in)."""
    m = trimesh.load(SIGNAL_STL)
    bodies = [b for b in m.split(only_watertight=False) if b.centroid[1] > 0]
    h = trimesh.util.concatenate(bodies)
    lo, hi = h.bounds
    M = np.eye(4)
    M[:3, :3] = [[0, -1, 0], [1, 0, 0], [0, 0, 1]]    # file x -> car +y, -y -> +x (forward), z up
    M[:3, 3] = [lo[1], -(lo[0] + hi[0]) / 2, -(lo[2] + hi[2]) / 2]
    _, ax = duct_rim(trimesh.transform_points(h.vertices, M), 0.0)
    yaw = math.atan2(ax[1], -ax[0])                   # turn the duct straight back
    R = trimesh.transformations.rotation_matrix(yaw, [0, 0, 1])
    M = R @ M
    v = trimesh.transform_points(h.vertices, M)
    v = v[np.abs(v[:, 2]) < 20] + [0, SIGNAL_Y, 0]
    ys = np.linspace(v[:, 1].min() + 4, v[:, 1].max() - 4, 24)
    edge = np.array([v[np.abs(v[:, 1] - y) < 5, 0].max() for y in ys])   # bezel front edge, plan
    from scipy.ndimage import median_filter
    edge = median_filter(edge, 3, mode="nearest")     # a sparse spot in the mesh reads as a notch
    # slide it back so the round nose ahead of it has its tip at NOSE_TIP
    j = _nose_join(ys, edge)
    dx = NOSE_TIP - (edge[j] - 3 + _nose_round(ys, edge, j))
    M = trimesh.transformations.translation_matrix([dx, SIGNAL_Y, 0]) @ M
    return bodies, M, ys, edge + dx, yaw


NOSE_ROUND = 60.0                                  # the round nose stands at least this far ahead of where it meets the bezel


def _nose_round(ys, edge, j):
    """How far the tip stands ahead of the bezel at ys[j] for a parabola from
    the tip to meet the bezel there with the bezel's own slope."""
    a, b = max(j - 2, 0), min(j + 3, len(ys))
    slope = np.polyfit(ys[a:b], edge[a:b], 1)[0]      # dx/dy, negative: the bezel sweeps back
    return -slope * ys[j] / 2


def _nose_join(ys, edge):
    """Where the round nose meets the bezel: the first point along it where
    the nose is at least NOSE_ROUND deep - inboard of it the bezel's end sits
    a little recessed in the nose."""
    return next(j for j in range(len(ys)) if _nose_round(ys, edge, j) >= NOSE_ROUND)


_VB, _VM, _VY, _VX, _VYAW = _vent_plan()


def _nose_curve():
    """Plan of the nose, x(y) for y = 0 .. full width: a round snub nose
    (a parabola from the tip) meeting the vent bezel at its most forward
    point with the bezel's slope, then riding the bezel (3 mm behind its
    face) and round to the fender."""
    from scipy.interpolate import PchipInterpolator
    j = _nose_join(_VY, _VX)
    yj, xj = _VY[j], _VX[j] - 3
    u = np.linspace(0, 1, 14)[:-1]
    ys = list(u * yj) + list(_VY[j:]) + [W_MAX * 0.995]
    xs = list(xj + (NOSE_TIP - xj) * (1 - u ** 2)) + list(_VX[j:] - 3) + [_VX[-1] - 170]
    xs = np.minimum.accumulate(np.array(xs))           # never bulges forward again
    return PchipInterpolator(ys, xs)


_NOSE = _nose_curve()
_NY = np.linspace(0, W_MAX * 0.995, 400)
_NX = _NOSE(_NY)
X_TIP = float(_NX[0])


def nose_x(y):
    """x of the nose surface at half-width y."""
    return float(_NOSE(min(max(y, 0.0), W_MAX * 0.995)))


def half_width(x):
    """Plan view: the nose curve up front, rounded tail."""
    if x > _NX[-1]:
        return float(np.interp(x, _NX[::-1], _NY[::-1])) if x <= X_TIP else 0.0
    if x < -3750:
        t = min(1.0, (-3750 - x) / 240)
        return W_MAX * 0.98 * max(0.0, 1 - t ** 2.5) ** 0.5
    return W_MAX


HL_FRONT = nose_x(SIGNAL_Y) - INCH                 # pop-up headlights: front edge 1 in behind the vent face
HL_LEN = 250.0
WHEEL_C = np.array([-1850.0, 340.0, 700.0])        # steering wheel centre (driver: +y, LHD)
DASH_X = -1780.0                                   # dash's rear face (toward the driver)
HL_BACK = 2 * INCH                                 # Tyler: headlights 2 in further back than the vent rule put them
HL_PIVOT = (0.3, 60.0)                             # roll-up pivot: 0.3 of the way forward, 60 mm under the hood
VENT_DROP = 2 * INCH                               # Tyler: the vents sit lower than the 1 in rule put them (guess, 2026-10-11)
VENT_H = 57.3                                      # the vent's height
SIGNAL_Z = interp(TOP, HL_FRONT) - INCH - VENT_DROP - VENT_H / 2   # vent top 1 in (+ VENT_DROP) below the pop-up


def signal_housing():
    """Driver-side housing in car coordinates, the centre of its duct's back
    end and the blinker. File: bezel faces -y, length along x, z up as
    printed; the driver side is side B as printed, blinker outboard (Tyler
    2026-10-11 - side A is the passenger one)."""
    h = trimesh.util.concatenate(_VB)
    M = trimesh.transformations.translation_matrix([0, 0, SIGNAL_Z]) @ _VM
    h.apply_transform(M)
    R = trimesh.transformations.rotation_matrix(_VYAW, [0, 0, 1])[:3, :3]
    end, axis = duct_rim(h.vertices @ R, SIGNAL_Z)    # found with the yaw taken off, as in the file
    end, axis = R @ end, R @ axis
    return h, end, axis, blinker_hole([b for b in _VB if not b.is_watertight][0], M)


def blinker_hole(piece, M):
    """The round light hole in the bezel's end piece, found by shooting rays
    through the bezel front-to-back (file +y). Returns the blinker lens as
    (front point, back point, radius) in car coordinates."""
    from scipy import ndimage
    lo, hi = piece.bounds
    xs, zs = np.arange(lo[0], hi[0], 0.5), np.arange(lo[2], hi[2], 0.5)
    X, Z = np.meshgrid(xs, zs)
    o = np.stack([X.ravel(), np.full(X.size, lo[1] - 20), Z.ravel()], 1)
    d = np.tile([0, 1.0, 0], (len(o), 1))
    hit = piece.ray.intersects_any(o, d).reshape(X.shape)
    lab, n = ndimage.label(~hit)
    holes = []
    for k in range(1, n + 1):
        c = lab == k
        if c[0].any() or c[-1].any() or c[:, 0].any() or c[:, -1].any():
            continue                                   # open to the outside, not a hole
        zz, xx = np.nonzero(c)
        holes.append((c.sum(), xs[xx].mean(), zs[zz].mean()))
    area, hx, hz = max(holes)                          # the light hole is the biggest one
    r = math.sqrt(area * 0.25 / math.pi)               # 0.5 mm cells
    ring_pts = np.array([[hx + r * 1.3 * math.cos(t), lo[1] - 20, hz + r * 1.3 * math.sin(t)] for t in np.linspace(0, 6.28, 12)])
    loc, _, _ = piece.ray.intersects_location(ring_pts, np.tile([0, 1.0, 0], (12, 1)), multiple_hits=False)
    y_front = loc[:, 1].min()                          # bezel face round the hole
    pts = trimesh.transform_points([[hx, y_front + 1.0, hz], [hx, y_front + 8.0, hz]], M)
    return pts[0], pts[1], r - 0.4


HOUSING, DUCT_END, DUCT_AX, BLINK = signal_housing()        # BLINK = (front, back, radius) of the lens in its hole
HINGE = [0.0, 0.0, 0.0]                            # pop-up headlight hinge line (x, -, z), set by parts()
# the adapter's socket slides over the duct's end, centred on it, until the
# rim butts the stop ledge (SOCKET_DEPTH in); pointing back, upright,
# so its 20 deg end (A) is outboard where the vent's duct flares; square to
# the rim, so along the duct (back and a little outboard)
_Z = DUCT_AX
_Y = np.array([0, 0, 1.0])
_X = np.cross(_Y, _Z)
R_AD = np.stack([_X, _Y, _Z], 1)
T_AD = DUCT_END - P.SOCKET_DEPTH * _Z
OUTLET_Z = 138.0                                   # adapter outlet face, adapter z

# ---------------------------------------------------------------- engine bay layout
CYL_X = (-600.0, -720.0, -840.0, -960.0)           # inline four, longitudinal
TURBO_AX = np.array([0.0, 420.0, 420.0])           # turbo shaft runs along x at this y, z
TURBO_DX = -200.0                                  # turbo moved back: turbine centred on the engine (Tyler)
TURBO_IN = np.array([-400.0 + TURBO_DX, 420.0, 420.0])   # compressor inlet face (centre), faces forward
IC = dict(x0=-310.0, x1=-235.0, y=330.0, z0=250.0, z1=420.0)   # intercooler core, ~75 mm gap ahead of the radiator
THROTTLE = np.array([-560.0, -290.0, 510.0])       # throttle body (passenger side), faces forward


def to_car(a):
    return np.asarray(a, float) @ R_AD.T + T_AD


def tx(x):
    """A point on the turbo's shaft line; x is in the turbo's own layout (shifted by TURBO_DX)."""
    return np.array([x + TURBO_DX, TURBO_AX[1], TURBO_AX[2]])


def bx(x0, x1, y0, y1, z0, z1):
    m = trimesh.creation.box(extents=(abs(x1 - x0), abs(y1 - y0), abs(z1 - z0)))
    m.apply_translation(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
    return m


def cyl(p0, p1, r, n=48):
    return trimesh.creation.cylinder(radius=r, segment=[p0, p1], sections=n)


def ring(p0, p1, r_in, r_out, n=48):
    """Hollow tube p0 -> p1."""
    m = trimesh.creation.annulus(r_min=r_in, r_max=r_out, height=1.0, sections=n)
    d = np.subtract(p1, p0, dtype=float)
    L = np.linalg.norm(d)
    m.apply_scale((1, 1, L))
    m.apply_transform(trimesh.geometry.align_vectors([0, 0, 1], d / L))
    m.apply_translation((np.asarray(p0) + np.asarray(p1)) / 2)
    return m


def bezier(p0, p1, p2, p3, n):
    p0, p1, p2, p3 = (np.asarray(p, float) for p in (p0, p1, p2, p3))
    t = np.linspace(0, 1, n)[:, None]
    return (1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t ** 2 * p2 + t ** 3 * p3


def polyline(pts, step=10.0, round_r=60.0):
    """Polyline with rounded corners, resampled every `step` mm."""
    pts = [np.asarray(p, float) for p in pts]
    out = [pts[0]]
    for a, b, c in zip(pts, pts[1:], pts[2:]):
        r = min(round_r, np.linalg.norm(b - a) / 2.1, np.linalg.norm(c - b) / 2.1)
        p, q = b + (a - b) / np.linalg.norm(a - b) * r, b + (c - b) / np.linalg.norm(c - b) * r
        out += list(bezier(p, b, b, q, 8))
    out.append(pts[-1])
    return resample(np.array(out), step)


def resample(pts, step):
    seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    s = np.concatenate([[0], np.cumsum(seg)])
    S = np.arange(0, s[-1], step)
    S = np.append(S, s[-1])
    return np.stack([np.interp(S, s, pts[:, k]) for k in range(3)], 1)


def spline(pts, t0, t1, step=8.0):
    """Smooth path through pts (Catmull-Rom), leaving along t0 and arriving along t1."""
    P = [np.asarray(p, float) for p in pts]
    T = [np.asarray(t0, float)] + [(P[i + 1] - P[i - 1]) / 2 for i in range(1, len(P) - 1)] + [np.asarray(t1, float)]
    T[0] = T[0] / np.linalg.norm(T[0]) * np.linalg.norm(P[1] - P[0])
    T[-1] = T[-1] / np.linalg.norm(T[-1]) * np.linalg.norm(P[-1] - P[-2])
    out = []
    for i in range(len(P) - 1):
        u = np.linspace(0, 1, 40)[:-1, None]
        h = [2 * u ** 3 - 3 * u ** 2 + 1, u ** 3 - 2 * u ** 2 + u, -2 * u ** 3 + 3 * u ** 2, u ** 3 - u ** 2]
        out.append(h[0] * P[i] + h[1] * T[i] + h[2] * P[i + 1] + h[3] * T[i + 1])
    out.append(P[-1][None])
    return resample(np.concatenate(out), step)


def sweep(pts, r, n=32):
    """Closed tube of radius r (number or per-point list) along a polyline."""
    pts = np.asarray(pts, float)
    r = np.broadcast_to(np.asarray(r, float), (len(pts),))
    T = np.gradient(pts, axis=0)
    T /= np.linalg.norm(T, axis=1)[:, None]
    u = np.cross(T[0], [0, 0, 1.0])
    if np.linalg.norm(u) < 0.2:
        u = np.cross(T[0], [1.0, 0, 0])
    verts = []
    a = np.linspace(0, 2 * np.pi, n, endpoint=False)
    for i, t in enumerate(T):                       # parallel transport, no twist
        u = u - t * (u @ t)
        u /= np.linalg.norm(u)
        v = np.cross(t, u)
        verts.append(pts[i] + r[i] * (np.cos(a)[:, None] * u + np.sin(a)[:, None] * v))
    V = np.concatenate(verts + [pts[:1], pts[-1:]])
    F, m = [], len(pts)
    for i in range(m - 1):
        for j in range(n):
            a0, b0, c0, d0 = i * n + j, i * n + (j + 1) % n, (i + 1) * n + j, (i + 1) * n + (j + 1) % n
            F += [(a0, b0, d0), (a0, d0, c0)]
    c0, c1 = m * n, m * n + 1
    for j in range(n):
        F += [(c0, (j + 1) % n, j), (c1, (m - 1) * n + j, (m - 1) * n + (j + 1) % n)]
    return trimesh.Trimesh(V, np.array(F), process=False)


def slab(xs, ys, top, bot):
    """Closed solid between two height fields top/bot (shape nx x ny) on the grid xs x ys."""
    nx, ny = len(xs), len(ys)
    X, Y = np.meshgrid(xs, ys, indexing="ij")
    V = np.concatenate([np.stack([X, Y, top], -1).reshape(-1, 3), np.stack([X, Y, bot], -1).reshape(-1, 3)])
    T = lambda i, j: i * ny + j
    B = lambda i, j: nx * ny + i * ny + j
    F = []
    for i in range(nx - 1):
        for j in range(ny - 1):
            F += [(T(i, j), T(i + 1, j), T(i + 1, j + 1)), (T(i, j), T(i + 1, j + 1), T(i, j + 1)),
                  (B(i, j), B(i + 1, j + 1), B(i + 1, j)), (B(i, j), B(i, j + 1), B(i + 1, j + 1))]
    loop = ([(i, 0) for i in range(nx)] + [(nx - 1, j) for j in range(1, ny)]
            + [(i, ny - 1) for i in range(nx - 2, -1, -1)] + [(0, j) for j in range(ny - 2, 0, -1)])
    for p, q in zip(loop, loop[1:] + loop[:1]):
        F += [(T(*p), B(*p), B(*q)), (T(*p), B(*q), T(*q))]
    m = trimesh.Trimesh(V, np.array(F))
    if m.volume < 0:
        m.invert()
    return m


def hood_z(body_m, xs, ys):
    """Top of the body skin over the grid xs x ys (rays straight down)."""
    X, Y = np.meshgrid(xs, ys, indexing="ij")
    o = np.stack([X.ravel(), Y.ravel(), np.full(X.size, 2000.0)], 1)
    loc, idx, _ = body_m.ray.intersects_location(o, np.tile([0, 0, -1.0], (len(o), 1)))
    z = np.full(len(o), -np.inf)
    np.maximum.at(z, idx, loc[:, 2])
    return z.reshape(X.shape)


def sgnpow(v, e):
    return np.sign(v) * np.abs(v) ** e


def body():
    """NA-style shell: superellipse sections lofted nose to tail, wheel arches
    and the open cockpit cut out."""
    front = [X_TIP + 0.5]                             # snub nose: stations along the nose curve
    for y in np.linspace(40, W_MAX * 0.99, 30):
        x = nose_x(y)
        if x < front[-1] - 0.5:
            front.append(x)
    xs = np.concatenate([front, np.linspace(front[-1] - 40, -3740, 50), np.linspace(-3780, -3990, 8)])
    n, a = 64, np.linspace(0, 2 * np.pi, 64, endpoint=False)
    rings = []
    for x in xs:
        W, B, T = half_width(x), interp(BOT, x), interp(TOP, x)
        s = W / W_MAX
        zc, H = (B + T) / 2, (T - B) / 2
        if x < -3000:
            H *= max(0.35, s) ** 0.5                  # the tail tapers in height too
        y, z = max(W, 4.0) * sgnpow(np.cos(a), 2 / 4.5), zc + H * sgnpow(np.sin(a), 2 / 4.5)
        up = np.clip((z - zc) / max(H, 1), 0, 1)
        z = z + interp(CROWN, x) * np.exp(-((np.abs(y) / W_MAX - 0.8) / 0.15) ** 2) * up   # fender crowns
        rings.append(np.stack([np.full(n, x), y, z], 1))
    V = np.concatenate(rings + [rings[0].mean(0, keepdims=True), rings[-1].mean(0, keepdims=True)])
    F, m = [], len(rings)
    for i in range(m - 1):
        for j in range(n):
            a0, b0, c0, d0 = i * n + j, i * n + (j + 1) % n, (i + 1) * n + j, (i + 1) * n + (j + 1) % n
            F += [(a0, d0, b0), (a0, c0, d0)]
    c0, c1 = m * n, m * n + 1
    for j in range(n):
        F += [(c0, j, (j + 1) % n), (c1, (m - 1) * n + (j + 1) % n, (m - 1) * n + j)]
    shell = trimesh.Trimesh(V, np.array(F))
    if shell.volume < 0:
        shell.invert()
    cuts = []
    for ax in AXLES:
        for s in (1, -1):
            cuts.append(cyl((ax, s * 560, WHEEL_Z), (ax, s * 1000, WHEEL_Z), WHEEL_R + 30, 64))
    cuts.append(bx(-1520, -2780, -650, 650, 640, 1400))            # cockpit
    return trimesh.boolean.difference([shell, *cuts], engine="manifold")


def wheel(ax, s):
    yc = s * TRACK / 2
    tyre = ring((ax, yc - 92, WHEEL_Z), (ax, yc + 92, WHEEL_Z), 178, WHEEL_R, 64)
    rim = cyl((ax, yc - 70, WHEEL_Z), (ax, yc + 70, WHEEL_Z), 180, 64)
    return tyre, rim


def parts():
    """name -> (mesh, colour, opacity, explode vector, group)"""
    out = {}
    out["body"] = (body(), "#c8102e", .38, (0, 0, 900), "body")
    # pop-up headlights: side view an equilateral triangle - the lid on top,
    # curved to the hood, and two faces meeting below it at 60 deg. The lamp
    # is on the front face; the unit rolls up about a pivot under the lid
    # (its back sinks into the car) until that face stands vertical.
    body_m = out["body"][0]
    x1 = HL_FRONT - HL_BACK
    x0 = x1 - HL_LEN
    xs = np.linspace(x0, x1, 27)                                     # odd: the apex is a sample
    tan60 = math.tan(math.radians(60))
    gaps = []
    for s, nm in ((1, "headlight_left"), (-1, "headlight_right")):
        y0, y1 = sorted((s * 400, s * 640))
        ys = np.linspace(y0, y1, 13)
        top = hood_z(body_m, xs, ys) + 3
        bot = top - np.maximum(3.0, np.minimum(xs - x0, x1 - xs) * tan60)[:, None]
        out[nm] = (slab(xs, ys, top, bot), "#c8102e", 1, (0, 0, 900), "body")
        # lamp: centred on the front face
        n = np.array([math.sin(math.radians(60)), 0.0, -math.cos(math.radians(60))])   # front face's outward normal
        c = np.array([x1 - HL_LEN / 4, (y0 + y1) / 2, top[-1, len(ys) // 2] - HL_LEN / 4 * tan60])
        out[nm + "_lamp"] = (cyl(c - n * 1, c + n * 4, 80, 40), "#fff6d8", 1, (0, 0, 900), "body")
        gx = np.linspace(x0 - 5, x1 + 5, 26)
        gy = np.linspace(y0 - 5, y1 + 5, 13)
        g = hood_z(body_m, gx, gy)
        gaps.append(slab(gx, gy, g - 1, g - 7))                     # dark outline just under the hood skin
    out["headlight_gaps"] = (trimesh.util.concatenate(gaps), "#111111", 1, (0, 0, 900), "body")
    px = x0 + HL_PIVOT[0] * HL_LEN
    HINGE[:] = [px, 0.0, interp(TOP, px) - HL_PIVOT[1]]
    mouth = cyl((3, 0, 0), (-10, 0, 0), 1, 64)                     # the oval mouth in the nose
    mouth.apply_scale((1, 300, 55))
    mouth.apply_translation((nose_x(300), 0, 330))
    out["nose_mouth"] = (mouth, "#0c0c0c", 1, (0, 0, 900), "body")
    ws = []                                                          # windshield frame + glass
    for s in (1, -1):
        ws.append(cyl((-1430, s * 650, 790), (-1790, s * 610, 1215), 18, 16))
    ws.append(cyl((-1790, 610, 1215), (-1790, -610, 1215), 22, 16))
    out["windshield_frame"] = (trimesh.util.concatenate(ws), "#151515", 1, (0, 0, 900), "body")
    glass = trimesh.Trimesh([(-1430, 640, 795), (-1430, -640, 795), (-1785, -600, 1205), (-1785, 600, 1205)],
                            [(0, 1, 2), (0, 2, 3)])
    out["windshield_glass"] = (glass, "#9fd3e0", .25, (0, 0, 900), "body")
    seats = [b for s in (1, -1) for b in (bx(-2150, -2550, s * 120, s * 520, 300, 420),
                                          bx(-2480, -2600, s * 120, s * 520, 380, 950))]
    tunnel = bx(-1790, -2300, -95, 95, 300, 500)
    out["interior"] = (trimesh.util.concatenate([*seats, tunnel]), "#202020", 1, (0, 0, 900), "body")
    # steering wheel: faces the driver, its column running forward and down into the dash
    a = np.array([-math.cos(math.radians(25)), 0, math.sin(math.radians(25))])   # wheel axis, toward the driver
    e1, e2 = np.array([0, 1.0, 0]), np.cross(a, [0, 1.0, 0])
    sw = [ring(WHEEL_C - a * 12, WHEEL_C + a * 12, 165, 185, 48), cyl(WHEEL_C - a * 15, WHEEL_C + a * 18, 48, 32),
          cyl(WHEEL_C - a * 20, WHEEL_C - a * 360, 22, 24)]
    for d in (e1, -e1, -e2):                                         # three spokes: 9, 3 and 6 o'clock
        sw.append(cyl(WHEEL_C + d * 40, WHEEL_C + d * 170, 9, 16))
    out["steering_wheel"] = (trimesh.util.concatenate(sw), "#151515", 1, (0, 0, 900), "body")
    # dash: cluster under a hood behind the wheel, and the centre tombstone (boost + AFR)
    dash = [bx(-1500, DASH_X, -640, 640, 600, 820), bx(DASH_X - 20, DASH_X + 80, 215, 465, 820, 850),
            bx(DASH_X - 10, DASH_X + 90, -75, 75, 500, 820)]
    out["dashboard"] = (trimesh.util.concatenate(dash), "#2a2a2a", 1, (0, 0, 900), "body")
    out["tail_lights"] = (trimesh.util.concatenate([bx(-3978, -3950, s * 300, s * 740, 650, 730) for s in (1, -1)]
                                                   + [bx(-3975, -3955, -300, 300, 665, 715)]),
                          "#7a0010", 1, (0, 0, 900), "body")
    tyres, rims = [], []
    for ax in AXLES:
        for s in (1, -1):
            t, r = wheel(ax, s)
            tyres.append(t)
            rims.append(r)
    out["tyres"] = (trimesh.util.concatenate(tyres), "#1c1c1c", 1, (0, 0, 0), "body")
    out["wheels"] = (trimesh.util.concatenate(rims), "#b9bec4", 1, (0, 0, 0), "body")

    # ---- engine bay -------------------------------------------------------
    out["radiator"] = (bx(-440, -385, -330, 330, 240, 600), "#4d545b", 1, (0, 0, 0), "bay")
    eng = [bx(-1060, -520, -165, 165, 180, 470),                   # block
           bx(-1060, -520, -150, 150, 470, 540),                   # head
           bx(-1040, -540, -125, 125, 540, 590)]                   # cam cover
    for x in CYL_X:                                                # plug-lead tubes down the middle
        eng.append(cyl((x, 0, 590), (x, 0, 605), 14, 16))
    out["engine"] = (trimesh.util.concatenate(eng), "#3a3e44", 1, (0, 0, 0), "bay")
    # intake side (passenger, -y): plenum along the head, 4 runners, throttle body
    run = [cyl((-560, -290, 510), (-1000, -290, 510), 55)]         # plenum
    for x in CYL_X:
        run.append(sweep(bezier((x, -290, 490), (x, -250, 450), (x, -200, 450), (x, -150, 450), 16), 22))
    out["intake_manifold"] = (trimesh.util.concatenate(run), "#a7adb3", 1, (0, -250, 0), "bay")
    out["throttle_body"] = (ring(THROTTLE, THROTTLE + [40, 0, 0], 28, 32), "#a7adb3", .45, (0, -250, 0), "bay")
    out["throttle_plate"] = (cyl(THROTTLE + [19, 0, 0], THROTTLE + [21, 0, 0], 27.5, 32), "#c9a24a", 1, (0, -250, 0), "bay")

    # ---- exhaust: 4 runners -> turbine -> downpipe under the car ----------
    # runners leave the head straight sideways and merge into the turbine,
    # which sits centred on the engine's length
    tin = tx(-590) + [0, -80, 0]                                   # turbine inlet, on its engine side
    runners = [bezier((x, 155, 470), (x, 290, 470), tin + [0, -110, 20], tin, 30) for x in CYL_X]
    out["exhaust_manifold"] = (trimesh.util.concatenate([sweep(r, 22, 20) for r in runners]), "#7a5d48", .45, (0, 150, 0), "exhaust")
    dp = polyline([tx(-625), tx(-690), tx(-720) + [0, 0, -230], [-1050, 380, 140], [-1700, 280, 140], [-2600, 260, 150]],
                  10, 90)
    out["downpipe"] = (sweep(dp, 32, 24), "#8b8f94", .45, (0, 150, 0), "exhaust")

    # ---- intake: false turn signal -> adapter -> hose -> turbo -> IC -> throttle
    out["false_turn_signal"] = (HOUSING, "#262626", 1, (600, 0, 0), "intake")
    out["blinker"] = (cyl(BLINK[0], BLINK[1], BLINK[2], 32), "#ff9d1a", 1, (600, 0, 0), "intake")
    # the passenger-side vent (side A of the file) is the mirror image
    other = trimesh.util.concatenate([HOUSING, cyl(BLINK[0], BLINK[1], BLINK[2], 32)])
    other.apply_transform(np.diag([1, -1, 1, 1.0]))
    other.invert()
    out["false_turn_signal_right"] = (other, "#262626", 1, (600, 0, 0), "body")
    tabs, screen, ties = (m.apply_transform(_mat4()) or m for m in hardware())
    out["vent_tabs"] = (tabs, "#262626", 1, (600, 0, 0), "intake")
    out["mesh_screen"] = (screen, "#4a4f55", 1, (500, 0, 0), "intake")
    out["zip_ties"] = (ties, "#0d0d0d", 1, (450, 0, 160), "intake")
    o = to_car([0, 0, OUTLET_Z - 30])                              # hose slides 30 mm onto the outlet
    e = TURBO_IN + [-25, 0, 0]                                     # ... and 25 mm onto the inlet
    hose = bezier(o, o + _Z * 110, e + [110, 0, 0], e, 40)
    r_hose = P.OUTLET_OD / 2 + 4
    out["silicone_hose"] = (sweep(hose, r_hose), "#2366c9", .35, (0, 0, 220), "intake")
    clamps = trimesh.util.concatenate([ring(o + _Z * 6, o + _Z * 18, r_hose, r_hose + 2.5),
                                       ring(e + [18, 0, 0], e + [6, 0, 0], r_hose, r_hose + 2.5)])
    out["hose_clamps"] = (clamps, "#c8ccd0", 1, (0, 0, 220), "intake")
    # turbo: compressor (cold side, inlet forward), centre section, turbine (hot side)
    tb = (-180, 120, 0)
    out["compressor_housing"] = (trimesh.util.concatenate([
        ring(tx(-400), tx(-460), 32, 37), ring(tx(-460), tx(-515), 37, 82), cyl(tx(-505), tx(-518), 82)]),
        "#b9bec4", .4, tb, "turbo")
    out["turbine_housing"] = (trimesh.util.concatenate([cyl(tx(-518), tx(-555), 38), cyl(tx(-555), tx(-625), 76)]),
                              "#5a4a3e", .5, tb, "turbo")
    for nm, x0, x1, r, col, ex in (("compressor_wheel", -462, -420, 31, "#e2e5e8", (-60, 120, 0)),
                                   ("turbine_wheel", -615, -565, 34, "#9a8a7a", (-300, 120, 0))):
        bl = [cyl(tx(x0), tx(x1), 10, 24)]
        for k in range(10):
            b = bx(x0 + TURBO_DX, x1 + TURBO_DX, -1.2, 1.2, 10, r)
            b.apply_transform(trimesh.transformations.rotation_matrix(k * math.pi / 5, [1, 0, 0]))
            b.apply_translation((0, *TURBO_AX[1:]))
            bl.append(b)
        out[nm] = (trimesh.util.concatenate(bl), col, 1, ex, "turbo")
    # charge pipes: smooth mandrel-style bends, each end slid 25 mm onto a
    # stub (compressor outlet, intercooler necks, throttle body) under a
    # silicone coupler, so every joint visibly meets
    r_cp = 30.0
    co = tx(-488) + [0, 0, -60]                                     # compressor outlet stub, down out of the scroll
    co_end = co + [0, 0, -70]
    ic_in = np.array([(IC["x0"] + IC["x1"]) / 2, IC["y"] + 45, (IC["z0"] + IC["z1"]) / 2])   # tank outer face
    ic_out = ic_in * [1, -1, 1]
    neck_in, neck_out = ic_in + [0, 55, 0], ic_out - [0, 55, 0]
    tb_in = THROTTLE + [40, 0, 0]                                   # throttle body's front face
    stubs = [cyl(co - [0, 0, 5], co_end, r_cp - 2, 32), cyl(ic_in - [0, 5, 0], neck_in, r_cp - 2, 32),
             cyl(ic_out + [0, 5, 0], neck_out, r_cp - 2, 32), cyl(tb_in - [5, 0, 0], tb_in + [30, 0, 0], r_cp - 2, 32)]
    out["pipe_stubs"] = (trimesh.util.concatenate(stubs), "#9ea4aa", 1, (0, 0, 0), "charge")
    cp1 = spline([co_end + [0, 0, 25], [-690, 430, 200], [-520, 500, 190], [-300, 545, 220],
                  [-272, 540, 335], neck_in - [0, 25, 0]], [0, 0, -1], [0, -1, 0])
    cp2 = spline([neck_out + [0, 25, 0], [-272, -540, 335], [-300, -525, 470], [-420, -480, 530],
                  [-485, -405, 515], tb_in + [10, 0, 0]], [0, -1, 0], [-1, 0, 0])
    out["charge_pipe_hot"] = (sweep(cp1, r_cp, 40), "#d0d4d8", .35, (0, 160, -120), "charge")
    out["charge_pipe_cold"] = (sweep(cp2, r_cp, 40), "#d0d4d8", .35, (0, -160, 120), "charge")
    cpl = []
    for p, d, L in ((co_end, [0, 0, 1], 35), (neck_in, [0, -1, 0], 35), (neck_out, [0, 1, 0], 35),
                    (tb_in + [20, 0, 0], [-1, 0, 0], 20)):        # short at the throttle: the radiator is right ahead of it
        d = np.array(d, float)                                     # coupler centred on the joint
        cpl.append(ring(p - d * L, p + d * L, r_cp - 0.5, r_cp + 4, 40))
    out["couplers"] = (trimesh.util.concatenate(cpl), "#2366c9", .6, (0, 0, 0), "charge")
    core = bx(IC["x0"], IC["x1"], -IC["y"], IC["y"], IC["z0"], IC["z1"])
    tanks = [bx(IC["x0"] - 5, IC["x1"] + 5, s * IC["y"], s * (IC["y"] + 45), IC["z0"] - 10, IC["z1"] + 10) for s in (1, -1)]
    out["intercooler"] = (trimesh.util.concatenate([core, *tanks]), "#9ea4aa", .45, (420, 0, -80), "charge")
    return out, dict(hose=hose, runners=runners, dp=dp, cp1=cp1, cp2=cp2, ic_in=ic_in, ic_out=ic_out)


def hardware():
    """In adapter coordinates, from the adapter's own connector sites so they
    line up with its pockets and ports: the vent's six hollow tabs, the mesh
    screen sandwiched between the vent and the adapter (a screen at the rim +
    a thin sleeve with windows at the tabs), and a zip tie through each
    connector (in the upper port, through the tab, out the lower port, round
    the outside to its head)."""
    import adapter as A
    tabs, ties = [], []
    off_out = P.WALL + P.BOSS_T                       # boss surface, from the socket's inner face
    for label, kind, lat, zc in A.connector_sites():
        O, u, n, v = A.face_frame(kind, lat, zc)
        O, u, n, v = (np.array([q.x, q.y, q.z]) for q in (O, u, n, v))
        f0 = O - n * P.SOCKET_CLEAR                   # the vent's outer face
        c = [f0 + n * P.TAB_PROUD / 2]
        tab = trimesh.creation.box(extents=(P.TAB_L, P.TAB_PROUD, P.TAB_W))
        R = np.eye(4)
        R[:3, :3] = np.stack([u, n, v], 1)
        R[:3, 3] = c[0]
        tab.apply_transform(R)
        tabs.append(tab)
        loop = [(off_out + 3.5, 0), (off_out + 2.5, 5.5), (off_out + 1.0, P.TIE_PORT_OUT_OFF),
                (P.TIE_PORT_START, P.TIE_PORT_IN_OFF), (0.6, 1.0), (0.6, -1.0),
                (P.TIE_PORT_START, -P.TIE_PORT_IN_OFF), (off_out + 1.0, -P.TIE_PORT_OUT_OFF),
                (off_out + 2.5, -5.5), (off_out + 3.5, 0)]
        pts = np.array([O + n * a + v * b for a, b in loop])
        ties.append(sweep(resample(pts, 1.0), 1.1, 12))
        head = trimesh.creation.box(extents=(6.0, 4.5, 7.5))
        R[:3, 3] = O + n * (off_out + 5.5)
        head.apply_transform(R)
        ties.append(head)
    # mesh screen at the rim, inside the frame outline, + a sleeve in the socket clearance
    hw, hh, zr = P.FRAME_W / 2, P.FRAME_H / 2, P.SOCKET_DEPTH
    scr = [bx(-hw, hw, hh - 3, hh, zr - 0.6, zr + 0.6), bx(-hw, hw, -hh, -hh + 3, zr - 0.6, zr + 0.6),
           bx(hw - 3, hw, -hh, hh, zr - 0.6, zr + 0.6), bx(-hw, -hw + 3, -hh, hh, zr - 0.6, zr + 0.6)]
    scr += [bx(x - 0.4, x + 0.4, -hh, hh, zr - 0.4, zr + 0.4) for x in np.arange(-hw + 6, hw - 3, 6)]
    scr += [bx(-hw, hw, y - 0.4, y + 0.4, zr - 0.4, zr + 0.4) for y in np.arange(-hh + 6, hh - 3, 6)]
    t0, t1 = P.SOCKET_CLEAR * 0.2, P.SOCKET_CLEAR * 0.9  # inside the 0.75 mm clearance
    win = P.TAB_L / 2 + 1.5
    for sy in (1, -1):                                # long faces, windows at the two tabs
        xs = sorted([-hw, hw] + [x + d for x in P.TAB_X_FACE_PY for d in (-win, win)])
        for a, b in zip(xs[::2], xs[1::2]):
            scr.append(bx(a, b, sy * (hh + t0), sy * (hh + t1), zr - 9, zr))
    for sx in (1, -1):                                # short ends, a window at the middle tab
        for a, b in ((-hh, -win), (win, hh)):
            scr.append(bx(sx * (hw + t0), sx * (hw + t1), a, b, zr - 9, zr))
    return trimesh.util.concatenate(tabs), trimesh.util.concatenate(scr), trimesh.util.concatenate(ties)


def _mat4():
    M = np.eye(4)
    M[:3, :3], M[:3, 3] = R_AD, T_AD
    return M


EXH, EXH_OUT = "#ff5a2a", "#8a8a8a"


def flows(g):
    """Particle streams: centre line every 5 mm, the stream's radius at each
    sample, and colour changes [sample, colour]."""
    front = np.array([nose_x(SIGNAL_Y) + 320, DUCT_END[1], SIGNAL_Z])
    seg = [[front, front + [-300, 0, 0], DUCT_END, to_car([0, 0, 0]), to_car([0, 0, OUTLET_Z - 30])]]
    pts = np.concatenate([resample(np.array(seg[0]), 5), resample(g["hose"], 5)])
    k_wheel = len(pts)
    pts = np.concatenate([pts, resample(np.array([TURBO_IN, tx(-440), tx(-488)]), 5),
                          resample(g["cp1"], 5)])
    k_ic = len(pts)
    pts = np.concatenate([pts, resample(np.array([g["ic_in"], g["ic_out"]]), 5)])
    k_cool = len(pts)
    pts = np.concatenate([pts, resample(g["cp2"], 5), resample(np.array([THROTTLE, THROTTLE + [-30, 0, 0]]), 5)])
    entry = 300.0
    rad = np.full(len(pts), 20.0)
    rad[:int(entry / 5)] = 22 + 90 * (1 - np.arange(int(entry / 5)) / (entry / 5))
    rad[k_ic:k_cool] = 120.0                                       # spreads through the core
    intake = dict(path=np.round(pts, 1).tolist(), radius=np.round(rad, 1).tolist(), n=550, speed=1.0,
                  colors=[[0, "$amb"], [k_wheel + 12, "$hot"], [k_cool, "$ic"]], zone="pre")
    out = [intake]
    # the plenum splits it four ways: along the plenum, down each runner, into the port
    for x in CYL_X:
        p = np.concatenate([resample(np.array([THROTTLE + [-30, 0, 0], [x, THROTTLE[1], THROTTLE[2]]]), 5),
                            resample(bezier((x, -290, 490), (x, -250, 450), (x, -200, 450), (x, -140, 450), 16), 5)])
        out.append(dict(path=np.round(p, 1).tolist(), radius=[16.0] * len(p), n=60, speed=1.0, colors=[[0, "$man"]], zone="man"))
    for r in g["runners"]:
        p = np.concatenate([resample(r, 5), resample(np.array([r[-1], tx(-590), tx(-625)]), 5), resample(g["dp"], 5)])
        out.append(dict(path=np.round(p, 1).tolist(), radius=[14.0] * len(p), n=90, speed=1.6,
                        colors=[[0, EXH], [len(p) - 120, EXH_OUT]], zone="exh"))
    return out


def engine():
    """What the engine sim needs: boost target, rev range, the gauges' places
    (face centre, the way it faces, its up, radius) on the dash."""
    face, up = [-1.0, 0.0, 0.0], [0.0, 0.0, 1.0]
    g = lambda kind, y, z, r: dict(kind=kind, center=[DASH_X - 1.5, y, z], normal=face, up=up, r=r)
    return dict(boost_psi=8.0, redline=7200, idle=850, rpm_per_mph=55.0,
                gauges=[g("speedo", 283.0, 790.0, 52.0), g("tach", 397.0, 790.0, 52.0),
                        dict(g("boost", 0.0, 755.0, 42.0), center=[DASH_X - 11.5, 0.0, 755.0]),
                        dict(g("afr", 0.0, 650.0, 42.0), center=[DASH_X - 11.5, 0.0, 650.0])])


def spec(hose_len):
    out_id = P.OUTLET_OD - 2 * P.OUTLET_WALL
    a_out = math.pi * (out_id / 2) ** 2
    q = lambda mph: 0.5 * RHO * (mph * MPH) ** 2 / 6894.76
    flow = 1.6e-3 * 7000 / 2 / 60 * 0.9 * (14.7 + 8) / 14.7        # B6 at 7000 rpm, VE 0.9, 8 psi
    return [
        ["Car", "1990 Mazda MX-5 (NA), US / LHD, B6 1.6 L"],
        ["Intake", "false turn signal -> adapter -> hose -> turbo (cold side) -> down, forward -> "
                   "intercooler -> up the passenger side -> throttle body -> plenum -> 4 runners"],
        ["Exhaust", "4 runners -> turbine (hot side) -> downpipe, out under the car"],
        ["Adapter outlet", f"{P.OUTLET_OD / 25.4:.1f} in OD, {out_id:.1f} mm ID ({a_out:,.0f} mm2)"],
        ["Hose (mock)", f"2.5 in silicone, ~{hose_len / 25.4:.0f} in"],
        ["Ram pressure", f"{q(30):.2f} / {q(60):.2f} / {q(90):.2f} psi at 30 / 60 / 90 mph"],
        ["Turbo inlet flow", f"~{flow * 1000:.0f} L/s at 7000 rpm, 8 psi -> {flow / (a_out * 1e-6):.0f} m/s in the tube"],
        ["What it does", "feeds outside air (cooler, denser) to the compressor; ram adds well under 1 psi"],
        ["Note", "mock shapes, not measured - the adapter and the false turn signal are the real files"],
    ]


def make(out_dir):
    d = os.path.join(out_dir, "mock")
    os.makedirs(d, exist_ok=True)
    for f in os.listdir(d):                                         # parts that no longer exist
        os.remove(os.path.join(d, f))
    ps, g = parts()
    lst = []
    for name, (m, col, op, ex, grp) in ps.items():
        m.export(os.path.join(d, name + ".stl"))
        item = dict(name=name, file="mock/" + name + ".stl", color=col, opacity=op, explode=list(map(float, ex)), group=grp)
        if name in ("compressor_wheel", "turbine_wheel"):           # one shaft
            item["spin"] = dict(center=list(map(float, TURBO_AX)), axis=[1.0, 0.0, 0.0])
        if name.startswith("headlight_l") or name.startswith("headlight_r"):   # pops up about the hinge
            item["hinge"] = dict(center=HINGE, axis=[0.0, 1.0, 0.0], up=-math.radians(30),   # front face 60 deg -> vertical
                                 side="left" if "left" in name else "right")
        if name == "throttle_plate":                                # opens with the throttle slider
            item["throttle"] = dict(center=list(map(float, THROTTLE + [20, 0, 0])), axis=[0.0, 0.0, 1.0])
        if name == "blinker":                                       # blinks while the air plays
            item["blink"] = True
        lst.append(item)
    hose_len = float(np.linalg.norm(np.diff(g["hose"], axis=0), axis=1).sum())
    scene = dict(mock=dict(
        parts=lst,
        adapter=dict(matrix=_mat4().tolist(), explode=[400.0, 0.0, 0.0]),
        flows=flows(g),
        view=dict(target=[-600, 250, 450], camera=[1500, 2300, 1500]),
        dash_view=dict(target=[DASH_X, 220, 740], camera=[-2420, 330, 1010]),
        engine=engine(),
        spec=spec(hose_len)))
    with open(os.path.join(out_dir, "scene.json"), "w") as fh:
        json.dump(scene, fh)
    return d, len(lst)
