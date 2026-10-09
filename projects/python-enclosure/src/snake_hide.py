#!/usr/bin/env python3
"""
snake_hide.py -- parametric generator for an L-shaped underground burrow hide
                 for small snakes.  Writes OBJ + STL.

GEOMETRY / ORIENTATION
----------------------
    +X = west      +Y = north      +Z = up      origin = the inside vertical
    corner where the two glass panes meet.

    * The right-hand glass pane lies in the plane x = 0  (hide's east face).
    * The front glass pane lies in the plane y = 0       (hide's south face).
    * So the hide sits in the bottom-right corner of the tank as viewed
      from the front.  Use --mirror for a bottom-LEFT corner.

    Plan view, top down, front glass along the bottom of the page:

        +Y north
          ^                 [=]  <- NE ESCAPE HATCH, a small rimmed
          |                  |      shaft straight up to the surface
          |                  |
          |         +--------+   <- short leg (4.5"), hugs the right glass
          |         |chamber |
          +---------+--------+------------------------------+=====+
            |^| |^| |^| |^| the tomb, roofed end to end     | /// |
          +---------------------------------------------------+ | <- doorway
          0"                                                 8"  10"

    Both faces that touch glass are LEFT OPEN: the tank glass forms those two
    walls, so you look straight into the tomb and see the stair flight in
    cross-section.  --closed prints all four walls.

THE TWO WAYS IN
---------------
    SW -- a covered stone stairway that climbs OUT of the hide.  It starts at
    the tomb floor where the long leg ends (8") and rises to grade at 10", so
    the tomb itself keeps its full length.  The flight is roofed the whole
    way in overlapping stone courses, and the treads are solid all the way
    down to the tank floor -- no cavity underneath.  It surfaces in a small
    stone doorway with a lintel; the top tread sits a little proud of grade
    so substrate does not run down the steps.

    NE -- a plain escape shaft at the north tip, roughly 0.85" square, with a
    low stepped rim at the surface.  --hatch-torii adds a small gate over it.

INSIDE THE TOMB
---------------
    * A corridor of torii gates at ~1" centres down both legs: posts either
      side, a kasagi lintel let into the ceiling, small nuki stubs in relief.
      They read as a receding row of gates through the glass and take almost
      nothing off the clear bore.
    * A coffered chamber at the corner -- the roof is thickened there and the
      ceiling recessed, so the turn opens into a taller room.
    * --floor-joints adds shallow flagstone lines across the floor.  Off by
      default.

BURIAL
------
    Shallow: the roof sits just under the surface, so the hide is not lost in
    the substrate.  --substrate sets the depth and everything follows from it.

EDGES
-----
    Nothing is left sharp.  Every primitive is a rounded box and every union
    and subtraction is a smooth blend, so convex arrises carry a radius, cut
    openings are filleted at the lip, and the tunnel bore is a rounded
    rectangle rather than a box.  --round and --blend control it.

HOW IT'S BUILT
--------------
    The model is an ordered list of rounded boxes, added or subtracted into a
    signed distance field sampled on a regular grid, then polygonised with
    naive surface nets.  Each primitive is only evaluated inside its own
    bounding box plus a blend margin, which keeps the field cheap to build.
    The mesh is checked for watertightness on every run.

USAGE
-----
    python3 snake_hide.py
    python3 snake_hide.py --substrate 4 --round 0.07
    python3 snake_hide.py --res 0.02 --preview preview.png   # finer, slower
    python3 snake_hide.py --units in --out hide_inches

Requires numpy.  matplotlib is used only by --preview.
"""

import argparse
import math
import struct
from dataclasses import dataclass, replace

import numpy as np

MM_PER_IN = 25.4
FAR = 1.0           # field is clamped to this far from any surface, inches


# ----------------------------------------------------------------------------
# parameters (inches)
# ----------------------------------------------------------------------------
@dataclass
class Params:
    # --- overall ---------------------------------------------------------
    leg_long: float = 8.00      # south leg, along the front glass
    leg_short: float = 5.50     # north leg, along the right glass
    tunnel_w: float = 1.70      # inner tunnel width
    tunnel_h: float = 1.15      # inner tunnel height
    wall: float = 0.16
    floor_t: float = 0.16
    roof_t: float = 0.16
    open_to_glass: bool = True
    corner_post: float = 0.18   # post in the glass corner, styled like a gate

    # --- burial ----------------------------------------------------------
    substrate: float = 1.75     # substrate at the FOOT of the hill (stair end)
    hill: float = 2.00          # extra depth at the top of the hill (corner +
                                # hatch end); the surface ramps between them

    # --- rounding --------------------------------------------------------
    round_r: float = 0.038      # radius on convex arrises
    round_in: float = 0.085     # radius on the tunnel bore and chamber
    blend: float = 0.025        # smooth-blend width at joins and cut lips

    # --- SW covered stairway (climbs OUT of the hide) --------------------
    stair_run: float = 2.00     # the flight runs this far past the tomb
    stair_end: float = 10.00    # derived: leg_long + stair_run
    stair_tread: float = 0.33   # nominal going; the run is divided to suit
    pass_head: float = 1.00     # clear headroom over each tread
    stair_curb: float = 0.16    # parapet above the top tread
    mouth_lip: float = 0.12     # top tread above grade, keeps substrate out
    roof_stop: float = 0.55     # roof stops this far short of the top
    eave: float = 0.00          # no overhang past the end of the flight
    door_h: float = 0.88        # doorway height, leaving room for a pediment
    battens: int = 3            # rolled tiles running down the roof slope
    entrance_detail: bool = False  # no structure past the last tread
    hatch_lantern: bool = True    # stone lantern over the escape hatch
    lantern_post: float = 0.70    # clear height of the lantern's openings

    # --- NE escape hatch -------------------------------------------------
    hatch_clear: float = 1.10   # the opening at the very top
    shaft_len: float = 1.34     # inner length; the walls stay thin
    hatch_rim: float = 0.14
    hatch_ribs: bool = True
    hatch_torii: bool = False

    # --- tomb interior ---------------------------------------------------
    torii_spacing: float = 1.00   # centres; 0 disables the gate corridor
    gate_end_gap: float = 0.25    # last gate's setback from the end of a leg
    torii_post: float = 0.15      # post width
    torii_thick: float = 0.14     # post depth along the run
    torii_head: float = 0.16      # kasagi depth, taken out of the headroom
    grand_gate: bool = True       # a heavier torii at the foot of the stairs
    courses: bool = True          # masonry coursing on the inner walls
    course_spacing: float = 0.52  # vertical joints along a course
    coffer: float = 0.00          # ceiling lift over the corner (0 = flat)
    floor_joints: bool = False
    joint_spacing: float = 0.55
    joint_depth: float = 0.045

    # --- meshing / output ------------------------------------------------
    res: float = 0.028          # grid cell, inches
    units: str = "mm"
    scale: float = 1.0
    mirror: bool = True         # +X is east; the hide runs west of the corner


# ----------------------------------------------------------------------------
# signed distance field
# ----------------------------------------------------------------------------
def smin(a, b, k):
    """Polynomial smooth minimum."""
    if k <= 0:
        return np.minimum(a, b)
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0.0, 1.0)
    return b + (a - b) * h - k * h * (1.0 - h)


class Field:
    """A signed distance field on a regular grid, built from rounded boxes."""

    def __init__(self, lo, hi, res):
        self.res = res
        self.x = np.arange(lo[0], hi[0] + res, res, dtype=np.float32)
        self.y = np.arange(lo[1], hi[1] + res, res, dtype=np.float32)
        self.z = np.arange(lo[2], hi[2] + res, res, dtype=np.float32)
        self.d = np.full((self.x.size, self.y.size, self.z.size), FAR,
                         dtype=np.float32)

    def _window(self, box, pad):
        out = []
        for axis, (a0, a1) in zip((self.x, self.y, self.z),
                                  ((box[0], box[1]), (box[2], box[3]),
                                   (box[4], box[5]))):
            i0 = int(np.searchsorted(axis, a0 - pad, "left"))
            i1 = int(np.searchsorted(axis, a1 + pad, "right"))
            out.append(slice(max(0, i0), min(axis.size, i1 + 1)))
        return out

    @staticmethod
    def _box_sdf(X, Y, Z, box, r):
        cx, cy, cz = ((box[0] + box[1]) / 2, (box[2] + box[3]) / 2,
                      (box[4] + box[5]) / 2)
        hx, hy, hz = ((box[1] - box[0]) / 2, (box[3] - box[2]) / 2,
                      (box[5] - box[4]) / 2)
        r = min(r, 0.45 * min(hx, hy, hz) * 2.0)     # keep the box a box
        qx = np.abs(X - cx) - (hx - r)
        qy = np.abs(Y - cy) - (hy - r)
        qz = np.abs(Z - cz) - (hz - r)
        outside = np.sqrt(np.maximum(qx, 0.0) ** 2 + np.maximum(qy, 0.0) ** 2
                          + np.maximum(qz, 0.0) ** 2)
        inside = np.minimum(np.maximum(qx, np.maximum(qy, qz)), 0.0)
        return (outside + inside - r).astype(np.float32)

    @staticmethod
    def _cyl_sdf(X, Y, Z, c, radius, half, axis, r):
        """Capped cylinder, rounded by r, with its axis on X, Y or Z."""
        d = [X - c[0], Y - c[1], Z - c[2]]
        a, b = [i for i in (0, 1, 2) if i != axis]
        r = min(r, 0.45 * min(radius, half) * 2.0)
        radial = np.sqrt(d[a] ** 2 + d[b] ** 2) - (radius - r)
        axial = np.abs(d[axis]) - (half - r)
        outside = np.sqrt(np.maximum(radial, 0.0) ** 2
                          + np.maximum(axial, 0.0) ** 2)
        inside = np.minimum(np.maximum(radial, axial), 0.0)
        return (outside + inside - r).astype(np.float32)

    def _apply(self, box, r, k, subtract, extra=None):
        sx, sy, sz = self._window(box, 3.0 * k + r + 3.0 * self.res)
        if sx.stop <= sx.start or sy.stop <= sy.start or sz.stop <= sz.start:
            return
        X = self.x[sx][:, None, None]
        Y = self.y[sy][None, :, None]
        Z = self.z[sz][None, None, :]
        if extra is None:
            db = self._box_sdf(X, Y, Z, box, r)
        elif extra[0] == "rot":
            # the box lives in a frame rotated by theta about one world axis
            _, ax, pu, pv, th, local = extra
            ct, st = math.cos(th), math.sin(th)
            U, V, keep = ((Y, Z, X) if ax == 0 else
                          (X, Z, Y) if ax == 1 else (X, Y, Z))
            du, dv = U - pu, V - pv
            Ul = du * ct + dv * st
            Vl = -du * st + dv * ct
            if ax == 0:
                db = self._box_sdf(keep, Ul, Vl, local, r)
            elif ax == 1:
                db = self._box_sdf(Ul, keep, Vl, local, r)
            else:
                db = self._box_sdf(Ul, Vl, keep, local, r)
        else:
            _, c, radius, half, axis = extra
            db = self._cyl_sdf(X, Y, Z, c, radius, half, axis, r)
        cur = self.d[sx, sy, sz]
        new = -smin(-cur, db, k) if subtract else smin(cur, db, k)
        self.d[sx, sy, sz] = np.minimum(new, FAR)

    def add(self, box, r, k, extra=None):
        self._apply(box, r, k, False, extra)

    def cut(self, box, r, k, extra=None):
        self._apply(box, r, k, True, extra)


# ----------------------------------------------------------------------------
# naive surface nets
# ----------------------------------------------------------------------------
def surface_nets(f):
    d, xs, ys, zs = f.d, f.x, f.y, f.z
    nx, ny, nz = xs.size - 1, ys.size - 1, zs.size - 1
    inside = d <= 0.0

    acc = np.zeros((nx, ny, nz, 3), dtype=np.float32)
    cnt = np.zeros((nx, ny, nz), dtype=np.int32)

    def crossings(axis):
        """Zero crossings on every grid edge along `axis`, as positions."""
        if axis == 0:
            a, b = d[:-1, :, :], d[1:, :, :]
            m = inside[:-1, :, :] != inside[1:, :, :]
            t = np.where(m, a / np.where(a == b, 1.0, a - b), 0.0)
            P = np.empty(m.shape + (3,), dtype=np.float32)
            P[..., 0] = xs[:-1, None, None] + t * f.res
            P[..., 1] = ys[None, :, None]
            P[..., 2] = zs[None, None, :]
        elif axis == 1:
            a, b = d[:, :-1, :], d[:, 1:, :]
            m = inside[:, :-1, :] != inside[:, 1:, :]
            t = np.where(m, a / np.where(a == b, 1.0, a - b), 0.0)
            P = np.empty(m.shape + (3,), dtype=np.float32)
            P[..., 0] = xs[:, None, None]
            P[..., 1] = ys[None, :-1, None] + t * f.res
            P[..., 2] = zs[None, None, :]
        else:
            a, b = d[:, :, :-1], d[:, :, 1:]
            m = inside[:, :, :-1] != inside[:, :, 1:]
            t = np.where(m, a / np.where(a == b, 1.0, a - b), 0.0)
            P = np.empty(m.shape + (3,), dtype=np.float32)
            P[..., 0] = xs[:, None, None]
            P[..., 1] = ys[None, :, None]
            P[..., 2] = zs[None, None, :-1] + t * f.res
        return m, P

    def accumulate(axis, m, P):
        free = [i for i in (0, 1, 2) if i != axis]      # the two spanned axes
        n = (nx, ny, nz)
        for o0 in (0, -1):
            for o1 in (0, -1):
                sl = [slice(None)] * 3
                sl[free[0]] = slice(0, n[free[0]]) if o0 == 0 \
                    else slice(1, n[free[0]] + 1)
                sl[free[1]] = slice(0, n[free[1]]) if o1 == 0 \
                    else slice(1, n[free[1]] + 1)
                sl[axis] = slice(0, n[axis])
                sl = tuple(sl)
                mm = m[sl]
                acc[..., 0] += np.where(mm, P[sl + (0,)], 0.0)
                acc[..., 1] += np.where(mm, P[sl + (1,)], 0.0)
                acc[..., 2] += np.where(mm, P[sl + (2,)], 0.0)
                cnt[...] += mm

    masks = {}
    for a in (0, 1, 2):        # one axis at a time: holding all three sets of
        m, P = crossings(a)    # crossing positions at once blows up the memory
        accumulate(a, m, P)
        masks[a] = m
        del P

    active = cnt > 0
    idx = np.full((nx, ny, nz), -1, dtype=np.int64)
    idx[active] = np.arange(int(active.sum()))
    verts = (acc[active] / cnt[active][:, None]).astype(np.float64)

    quads = []
    # X edges -> quads in the (y, z) plane
    m = masks[0][:, 1:-1, 1:-1]
    flip = inside[:-1, 1:-1, 1:-1]
    c00 = idx[:, 0:ny - 1, 0:nz - 1]
    c10 = idx[:, 1:ny, 0:nz - 1]
    c11 = idx[:, 1:ny, 1:nz]
    c01 = idx[:, 0:ny - 1, 1:nz]
    quads.append((m, flip, c00, c10, c11, c01))
    # Y edges -> quads in the (z, x) plane
    m = masks[1][1:-1, :, 1:-1]
    flip = inside[1:-1, :-1, 1:-1]
    c00 = idx[0:nx - 1, :, 0:nz - 1]
    c10 = idx[0:nx - 1, :, 1:nz]
    c11 = idx[1:nx, :, 1:nz]
    c01 = idx[1:nx, :, 0:nz - 1]
    quads.append((m, flip, c00, c10, c11, c01))
    # Z edges -> quads in the (x, y) plane
    m = masks[2][1:-1, 1:-1, :]
    flip = inside[1:-1, 1:-1, :-1]
    c00 = idx[0:nx - 1, 0:ny - 1, :]
    c10 = idx[1:nx, 0:ny - 1, :]
    c11 = idx[1:nx, 1:ny, :]
    c01 = idx[0:nx - 1, 1:ny, :]
    quads.append((m, flip, c00, c10, c11, c01))

    tris = []
    for m, flip, c00, c10, c11, c01 in quads:
        sel = m & (c00 >= 0) & (c10 >= 0) & (c11 >= 0) & (c01 >= 0)
        if not sel.any():
            continue
        fwd = sel & flip
        rev = sel & ~flip
        for mask, order in ((fwd, (c00, c10, c11, c01)),
                            (rev, (c00, c01, c11, c10))):
            if not mask.any():
                continue
            a, b, c, e = (o[mask] for o in order)
            tris.append(np.stack([a, b, c], axis=1))
            tris.append(np.stack([a, c, e], axis=1))
    tris = np.concatenate(tris, axis=0) if tris else np.zeros((0, 3), np.int64)
    return verts, tris


def check_manifold(tris):
    if tris.shape[0] == 0:
        return False, "empty mesh"
    e = np.concatenate([tris[:, [0, 1]], tris[:, [1, 2]], tris[:, [2, 0]]])
    key = np.minimum(e[:, 0], e[:, 1]) * (tris.max() + 1) + \
        np.maximum(e[:, 0], e[:, 1])
    _, counts = np.unique(key, return_counts=True)
    bad = int((counts != 2).sum())
    if bad:
        return False, "%d edges not shared by exactly 2 faces" % bad
    dkey = e[:, 0] * (tris.max() + 1) + e[:, 1]
    if np.unique(dkey).size != dkey.size:
        return False, "inconsistent winding"
    return True, "watertight, 2-manifold, consistently wound"


# ----------------------------------------------------------------------------
# the model
# ----------------------------------------------------------------------------
def rot_op(local, pu, pv, th, ax=1):
    """World AABB plus the payload for a box in a frame rotated about one
    world axis.  ax 0 rotates in (y, z), 1 in (x, z), 2 in (x, y).  `local`
    is the box written in that rotated frame."""
    ct, st = math.cos(th), math.sin(th)
    ui, vi, ki = ((1, 2, 0) if ax == 0 else (0, 2, 1) if ax == 1 else (0, 1, 2))
    lu = (local[2 * ui], local[2 * ui + 1])
    lv = (local[2 * vi], local[2 * vi + 1])
    us, vs = [], []
    for a in lu:
        for b in lv:
            us.append(pu + a * ct - b * st)
            vs.append(pv + a * st + b * ct)
    aabb = [0.0] * 6
    aabb[2 * ui], aabb[2 * ui + 1] = min(us), max(us)
    aabb[2 * vi], aabb[2 * vi + 1] = min(vs), max(vs)
    aabb[2 * ki], aabb[2 * ki + 1] = local[2 * ki], local[2 * ki + 1]
    return tuple(aabb), ("rot", ax, pu, pv, th, local)


def cyl_op(c, radius, half, axis):
    lo, hi = [], []
    for i in range(3):
        h = half if i == axis else radius
        lo.append(c[i] - h)
        hi.append(c[i] + h)
    aabb = (lo[0], hi[0], lo[1], hi[1], lo[2], hi[2])
    return aabb, ("cyl", c, radius, half, axis)


def resolve(p):
    """Round both legs up so the gate grid divides them exactly: the last gate
    on the long leg sits at the foot of the stairs, and the last on the short
    leg sits at the escape hatch.  Idempotent."""
    A, B = p.leg_long, p.leg_short
    if p.torii_spacing > 0:
        first = p.tunnel_w + p.torii_thick / 2.0 + 0.03
        sp, gap = p.torii_spacing, p.gate_end_gap
        tail = p.wall + p.shaft_len + gap
        k = max(0, int(math.ceil((A - gap - first) / sp - 1e-9)))
        m = max(0, int(math.ceil((B - tail - first) / sp - 1e-9)))
        A = first + k * sp + gap
        B = first + m * sp + tail
    return replace(p, leg_long=A, leg_short=B, stair_end=A + p.stair_run)


def stair_plan(p):
    """The flight climbs from the tomb floor at x = leg_long out to grade at
    x = stair_end, where the substrate is at its shallowest (foot of the hill).
    The roof is a single smooth ramp parallel to the treads."""
    run = max(p.stair_tread * 3, p.stair_end - p.leg_long)
    n = max(3, int(round(run / p.stair_tread)))
    tread = run / n
    z_top = p.substrate + p.mouth_lip          # top tread, just proud of grade
    rise = (z_top - p.floor_t) / (n - 1)
    slope = rise / tread
    th = math.atan(slope)
    ceil0 = p.floor_t + p.pass_head            # ceiling directly above tread 0
    ceil_end = ceil0 + n * tread * slope       # ceiling at the gable face
    proud = ceil_end + p.roof_t - p.substrate
    return dict(n=n, tread=tread, rise=rise, run=run, z_top=z_top, th=th,
                slope=slope, ceil0=ceil0, ceil_end=ceil_end, proud=proud)


def build(p):
    p = resolve(p)
    """Return (ops, z_body, stair plan, hatch top).  Each op is
    (kind, box, radius) applied in order."""
    A, B = p.leg_long, p.leg_short
    W, H, t = p.tunnel_w, p.tunnel_h, p.wall
    z0 = p.floor_t                      # tunnel floor
    z1 = z0 + H                         # tunnel ceiling
    zb = z1 + p.roof_t                  # top of the buried body
    s = stair_plan(p)
    R, RI = p.round_r, p.round_in

    ops = []
    add = lambda b, r=None: ops.append(("+", b, R if r is None else r))
    cut = lambda b, r=None: ops.append(("-", b, RI if r is None else r))

    ow = 0.0 if p.open_to_glass else t
    over = 0.30 if p.open_to_glass else 0.0    # push cuts clear of the glass
    g = -over if p.open_to_glass else t

    # ---- body -----------------------------------------------------------
    # the long leg runs a little past its nominal end so the stairway overlaps
    # it rather than butting against it
    lap = 0.10
    add((-ow, A + lap, -ow, W + t, 0, zb))
    add((-ow, W + t, -ow, B, 0, zb))

    # ---- tunnel bore ----------------------------------------------------
    cut((g, A + lap, g, W, z0, z1))
    cut((g, W, g, B - t, z0, z1))

    if p.corner_post > 0:
        # a post standing in the corner where the two panes meet, detailed
        # like the gate posts: a shaft with a capital under the ceiling.  Two
        # of its faces are the glass, so the capital can only flare inward.
        c = p.corner_post
        zkc = z1 - p.torii_head
        add((0, c, 0, c, 0, z1 + 0.03))
        add((0, c + 0.05, 0, c + 0.05, zkc - 0.14, zkc - 0.01))

    # ---- corner chamber: thicken the roof, then coffer the ceiling ------
    if p.coffer > 0:
        add((-ow, W + t, -ow, W + t, zb - 0.04, zb + p.coffer + 0.02))
        cut((0.20, W - 0.20, 0.20, W - 0.20, z1 - 0.02, z1 + p.coffer), RI)

    # ---- where the gates go (needed before the joints are placed) -------
    gates_x, gates_y = [], []
    if p.torii_spacing > 0:
        # the first pair sits right on the right angle, one facing down each
        # leg, so their lintels meet over the corner
        first = W + p.torii_thick / 2.0 + 0.03
        x = first
        while x < A - p.gate_end_gap + 1e-6:
            gates_x.append(x)
            x += p.torii_spacing
        y = first
        while y < B - t - p.shaft_len - p.gate_end_gap + 1e-6:
            gates_y.append(y)
            y += p.torii_spacing

    # ---- SW covered stairway: stepped treads under one smooth sloping roof
    n, tread, rise, th = s["n"], s["tread"], s["rise"], s["th"]
    xe = p.stair_end
    sec = 1.0 / math.cos(th)
    tall = s["ceil_end"] + p.roof_t + 0.02   # no higher than the ridge

    # one solid prism, then trim it to the roof plane and hollow the passage
    xr = xe - p.roof_stop                       # where the roof stops
    add((A, xr, -ow, W + t, 0, tall))
    ln = (xe + p.eave + 0.30 - A) * sec
    aabb, ex = rot_op((-0.02, ln, -1.0, W + t + 1.0, p.roof_t, p.roof_t + 2.5),
                      A, s["ceil0"], th)
    ops.append(("-", aabb, p.round_r, ex))                    # shape the slope
    # the hollow has to reach the floor at the junction; because the slab is
    # rotated, that means starting it well back along the slope
    back = -(s["ceil0"] * math.sin(th) + 0.15)
    # the stairway is walled on the glass side, unlike the tomb: the hollow
    # stops at the wall rather than running out to the glass plane
    aabb, ex = rot_op((back, ln, t, W, -5.0, 0.0), A, s["ceil0"], th)
    ops.append(("-", aabb, RI, ex))                           # hollow it out
    # neither rotated slab can be clipped in world X, so both bite into the
    # tomb before the junction: restore its floor and roof bands
    # Rebuild the junction zone outright rather than patching bands back: a
    # rotated cut plane grazing the tomb's flat ceiling leaves a wedge that
    # pinches at some grid alignments.  These two are axis-aligned, so the
    # restored bore lines up exactly with the original.
    back_x = A - 1.5
    add((back_x, A + lap, -ow, W + t, 0, zb))
    cut((back_x - 0.1, A + lap, g, W, z0, z1))

    for j in range(n):                                        # put the treads back
        x0 = A + j * tread - (lap if j == 0 else 0.0)
        add((x0, A + (j + 1) * tread, -ow, W + t, 0, z0 + j * rise))

    # ---- flagstone joints across the floor ------------------------------
    if p.floor_joints:
        jd, jw = p.joint_depth, 0.10
        clear = p.torii_thick / 2.0 + jw / 2.0 + 3.0 * p.res

        def free(v, gates):
            return all(abs(v - gv) > clear for gv in gates)

        x = W + 0.45
        while x < A - 0.30:
            if free(x, gates_x):
                cut((x - jw / 2, x + jw / 2, g, W + 0.02, z0 - jd, z0), 0.035)
            x += p.joint_spacing
        y = W + 0.45
        while y < B - t - p.hatch_clear - 0.25:
            if free(y, gates_y):
                cut((g, W + 0.02, y - jw / 2, y + jw / 2, z0 - jd, z0), 0.035)
            y += p.joint_spacing

    # ---- corridor of torii gates ---------------------------------------
    if gates_x or gates_y:
        pw, pt, kh = p.torii_post, p.torii_thick, p.torii_head
        z_head_i = z1 - kh                      # underside of the kasagi

        def gate(along, swap):
            """Posts + lintel across the bore at `along` (x if not swap)."""
            def box(a0, a1, s0, s1, zz0, zz1):
                return (s0, s1, a0, a1, zz0, zz1) if swap \
                    else (a0, a1, s0, s1, zz0, zz1)
            a0, a1 = along - pt / 2, along + pt / 2
            add(box(a0, a1, 0.05, 0.05 + pw, z0 - 0.05, z_head_i + 0.02))
            add(box(a0, a1, W - 0.05 - pw, W - 0.05, z0 - 0.05,
                    z_head_i + 0.02))
            add(box(a0 - 0.03, a1 + 0.03, -0.02, W + 0.02,
                    z_head_i, z1 + 0.03))                       # kasagi
            nz0 = z0 + 0.52                                     # nuki stubs
            add(box(a0 + 0.02, a1 - 0.02, 0.05, 0.05 + pw + 0.07,
                    nz0, nz0 + 0.09))
            add(box(a0 + 0.02, a1 - 0.02, W - 0.12 - pw, W - 0.05,
                    nz0, nz0 + 0.09))

        for gx in (gates_x[:-1] if (gates_x and p.grand_gate) else gates_x):
            gate(gx, False)

        if gates_x and p.grand_gate:
            # the gate at the foot of the stairs is a full torii: battered
            # posts with capitals, a nuki through them, a centre tablet and a
            # two-piece kasagi.  It sits on the existing gate position, so the
            # print does not get any longer.
            gx = gates_x[-1]
            pw2, ycg = 0.20, W / 2.0
            zk = z1 - p.torii_head                     # underside of the kasagi
            for ya in (0.05, W - 0.05 - pw2):
                add((gx - 0.10, gx + 0.10, ya, ya + pw2, z0 - 0.05, zk + 0.02))
                add((gx - 0.135, gx + 0.135, ya - 0.035, ya + pw2 + 0.035,
                     zk - 0.14, zk - 0.01))                        # daiwa
            add((gx - 0.07, gx + 0.07, 0.01, W - 0.01,
                 z0 + 0.78, z0 + 0.89))                            # nuki
            add((gx - 0.05, gx + 0.05, ycg - 0.06, ycg + 0.06,
                 z0 + 0.82, zk + 0.02))                            # gakuzuka
            add((gx - 0.105, gx + 0.105, -0.02, W + 0.02,
                 zk - 0.09, zk + 0.02))                            # shimaki
            add((gx - 0.155, gx + 0.155, -0.02, W + 0.02,
                 zk, z1 + 0.03))                                   # kasagi
        for gy in gates_y:
            gate(gy, True)

    # ---- the top of the flight is open: no roof, nothing past the treads
    z_dtop = s["z_top"] + p.door_h
    zso = s["ceil_end"]
    yc = (W + t) / 2.0
    lnr = (xr - A) * sec                          # roof tip, in the slope frame

    aabb, ex = rot_op((lnr - 0.34 * sec, lnr, -ow, W + t + 0.05,
                       p.roof_t - 0.02, p.roof_t + 0.09), A, s["ceil0"], th)
    ops.append(("+", aabb, p.round_r, ex))                    # eave edge band

    for i in range(max(0, p.battens)):                        # rolled tiles
        yb = (W + t) * (i + 0.5) / max(1, p.battens)
        aabb, ex = rot_op((-0.02, lnr - 0.38 * sec, yb - 0.06, yb + 0.06,
                           p.roof_t - 0.03, p.roof_t + 0.07),
                          A, s["ceil0"], th)
        ops.append(("+", aabb, 0.055, ex))

    # low parapets carry on to the last tread so the trench does not fill in,
    # but nothing stands above it
    ptop = s["z_top"] + p.stair_curb
    add((xr - lap, xe, -ow, t, 0, ptop))
    add((xr - lap, xe, W, W + t, 0, ptop))

    # ---- NE escape hatch ------------------------------------------------
    c = p.hatch_clear
    xc = (t + W) / 2.0
    ay1 = B - t                                  # inner face of the end wall
    ay0 = ay1 - p.shaft_len
    cxh, cyh = xc, (ay0 + ay1) / 2.0
    hx0, hx1 = cxh - c / 2.0, cxh + c / 2.0      # the opening at the very top
    hy0, hy1 = cyh - c / 2.0, cyh + c / 2.0
    z_rim = p.substrate + p.hill + p.hatch_rim   # top of the hill
    z_neck = z_rim - 0.34                        # it only narrows up here
    add((-ow, W + t, ay0 - t, B, z1, z_rim))                   # the shaft tube
    # thin walled: the bore is nearly the full tunnel section all the way up
    cut((t, W, ay0, ay1, z0, z_neck), RI)
    if p.hatch_lantern:
        # a round stone curb, then a little lantern roof on four corner posts
        # so the snake comes out through the openings between them
        # a square curb (igeta), not round: a circle big enough to carry the
        # corner posts would run into the glass
        add((cxh - 0.80, cxh + 0.80, cyh - 0.80, cyh + 0.80,
             z_rim - 0.14, z_rim + 0.10), 0.10)
        add((cxh - 0.70, cxh + 0.70, cyh - 0.70, cyh + 0.70,
             z_rim + 0.06, z_rim + 0.20), 0.08)
        cut((hx0, hx1, hy0, hy1, z_neck - 0.12, z_rim + 0.34), RI)   # neck
        zc = z_rim + 0.20
        ph = p.lantern_post
        for px in (hx0 - 0.19, hx1 + 0.03):
            for py in (hy0 - 0.19, hy1 + 0.03):
                add((px, px + 0.16, py, py + 0.16, zc - 0.06, zc + ph))
        zt2 = zc + ph
        add((hx0 - 0.28, hx1 + 0.28, hy0 - 0.28, hy1 + 0.28, zt2, zt2 + 0.10))
        add((hx0 - 0.16, hx1 + 0.16, hy0 - 0.16, hy1 + 0.16, zt2 + 0.06,
             zt2 + 0.19))
        # the kicked corners have to overlap the upper tier, not butt against
        # it: a coplanar butt joint leaves a hairline the mesher trips on
        for px in (hx0 - 0.29, hx1 + 0.10):
            for py in (hy0 - 0.29, hy1 + 0.10):
                add((px, px + 0.19, py, py + 0.19, zt2 + 0.04, zt2 + 0.26))
        aabb, ex = cyl_op((cxh, cyh, zt2 + 0.28), 0.10, 0.10, 2)
        ops.append(("+", aabb, 0.09, ex))                      # hoju finial
        z_hatch = zt2 + 0.38
    else:
        add((0, W + t + 0.08, ay0 - t - 0.08, B + 0.08,
             z_rim - 0.09, z_rim + 0.09))
        cut((hx0, hx1, hy0, hy1, z_neck - 0.12, z_rim + 0.30), RI)
        z_hatch = z_rim + 0.09

    if p.hatch_ribs:
        z = z1 + 0.30
        while z < z_rim - 0.35:
            add((t - 0.01, t + 0.09, ay0, ay1, z, z + 0.09), 0.04)
            add((W - 0.09, W + 0.01, ay0, ay1, z, z + 0.09), 0.04)
            z += 0.38

    if p.hatch_torii:
        zc, yc, pw = z_hatch, (hy0 + hy1) / 2.0, 0.17
        zt = zc + 0.42
        add((hx0 - 0.17, hx0, yc - pw / 2, yc + pw / 2, zc - 0.05, zt))
        add((hx1, hx1 + 0.17, yc - pw / 2, yc + pw / 2, zc - 0.05, zt))
        add((hx0 - .22, hx1 + .22, yc - .08, yc + .08, zt - .18, zt - .09))
        add((xc - .06, xc + .06, yc - .07, yc + .07, zt - .10, zt))
        k0, k1 = hx0 - .29, hx1 + .29
        add((k0, k1, yc - .11, yc + .11, zt, zt + .10))
        add((k0, k0 + .12, yc - .11, yc + .11, zt + .05, zt + .15))
        add((k1 - .12, k1, yc - .11, yc + .11, zt + .05, zt + .15))
        z_hatch = zt + .15

    # ---- masonry coursing on the walls you can see through the glass ----
    if p.courses:
        gd, gw = 0.055, 0.055                 # groove depth and width
        zc1, zc2 = z0 + 0.36, z0 + 0.74
        near = lambda v, gs: any(abs(v - g) < 0.13 for g in gs)
        # long leg: the north wall, and the stair parapets beyond it
        for zz in (zc1, zc2):
            cut((-ow, A + lap, W - 0.02, W + gd, zz, zz + gw), 0.02)
        for zz in (zc1, zc2):
            cut((-ow, W + 0.02, W - 0.02, W + gd, zz, zz + gw), 0.02)
        # short leg: the west wall
        for zz in (zc1, zc2):
            cut((W - 0.02, W + gd, -ow, B - t, zz, zz + gw), 0.02)
        # staggered vertical joints
        stag = 0.0
        for zlo, zhi in ((z0 + 0.02, zc1), (zc1 + gw, zc2), (zc2 + gw, z1 - 0.02)):
            xx = W + 0.30 + stag
            while xx < A + lap - 0.10:
                if not near(xx, gates_x):
                    cut((xx, xx + gw, W - 0.02, W + gd, zlo, zhi), 0.02)
                xx += p.course_spacing
            yy = W + 0.30 + stag
            while yy < B - t - p.shaft_len - 0.10:
                if not near(yy, gates_y):
                    cut((W - 0.02, W + gd, yy, yy + gw, zlo, zhi), 0.02)
                yy += p.course_spacing
            stag = p.course_spacing / 2.0 - stag

    # ---- a nosing on each stair tread -----------------------------------
    for j in range(1, n):
        xn = A + j * tread
        add((xn - 0.07, xn + 0.005, t, W,
             z0 + j * rise - 0.06, z0 + j * rise), 0.022)

    # ---- one continuous floor, and a dead flat base ---------------------
    # The body, the junction patch and the treads are separate solids, and
    # where they blend the underside bulges a little below z = 0.  That reads
    # as a mismatched patch of floor through the glass.  Lay a single slab
    # across the whole footprint, then trim everything back to the tank floor
    # so the base is one plane.
    add((-ow, xe, -ow, W + t, 0, z0))
    add((-ow, W + t, -ow, B, 0, z0))
    ops.append(("-", (-1.0, xe + 2.0, -1.0, B + 2.0, -2.0, 0.0), 0.0))

    return ops, zb, s, z_hatch, len(gates_x) + len(gates_y)


def rasterise(p, ops):
    lo = [min(op[1][2 * a] for op in ops) for a in range(3)]
    hi = [max(op[1][2 * a + 1] for op in ops) for a in range(3)]
    pad = 4.0 * p.blend + p.round_in + 6.0 * p.res
    lo = [v - pad for v in lo]
    hi = [v + pad for v in hi]
    f = Field(lo, hi, p.res)
    for op in ops:
        kind, box, r = op[0], op[1], op[2]
        extra = op[3] if len(op) > 3 else None
        if kind == "+":
            f.add(box, r, p.blend, extra)
        else:
            f.cut(box, r, p.blend, extra)
    return f


# ----------------------------------------------------------------------------
# writers
# ----------------------------------------------------------------------------
def transform(verts, p):
    k = (MM_PER_IN if p.units == "mm" else 1.0) * p.scale
    v = verts * k
    if p.mirror:
        v = v.copy()
        v[:, 0] *= -1.0
    return v


def write_obj(path, verts, tris, name):
    with open(path, "w") as fh:
        fh.write("# %s\n# %d verts / %d tris\no %s\n"
                 % (name, len(verts), len(tris), name))
        np.savetxt(fh, verts, fmt="v %.4f %.4f %.4f")
        np.savetxt(fh, tris + 1, fmt="f %d %d %d")


def write_stl(path, verts, tris, ascii_mode=False):
    a, b, c = verts[tris[:, 0]], verts[tris[:, 1]], verts[tris[:, 2]]
    n = np.cross(b - a, c - a)
    ln = np.linalg.norm(n, axis=1)
    n = n / np.where(ln[:, None] == 0, 1.0, ln[:, None])
    if ascii_mode:
        with open(path, "w") as fh:
            fh.write("solid snake_hide\n")
            for i in range(len(tris)):
                fh.write("  facet normal %.5f %.5f %.5f\n    outer loop\n"
                         % tuple(n[i]))
                for v in (a[i], b[i], c[i]):
                    fh.write("      vertex %.4f %.4f %.4f\n" % tuple(v))
                fh.write("    endloop\n  endfacet\n")
            fh.write("endsolid snake_hide\n")
        return
    rec = np.zeros(len(tris), dtype=np.dtype([
        ("n", "<f4", 3), ("a", "<f4", 3), ("b", "<f4", 3),
        ("c", "<f4", 3), ("attr", "<u2")]))
    rec["n"], rec["a"], rec["b"], rec["c"] = n, a, b, c
    with open(path, "wb") as fh:
        fh.write(b"snake_hide - L-shaped underground burrow".ljust(80, b" "))
        fh.write(struct.pack("<I", len(tris)))
        rec.tofile(fh)


def _render(verts, tris, elev, azim, W, H, ctr, span, ss=2):
    """Tiny orthographic z-buffer renderer: splat flat-shaded triangles."""
    e, a = math.radians(elev), math.radians(azim)
    view = np.array([math.cos(e) * math.cos(a), math.cos(e) * math.sin(a),
                     math.sin(e)])
    right = np.cross([0.0, 0.0, 1.0], view)
    right /= np.linalg.norm(right)
    up = np.cross(view, right)

    A, B, C = verts[tris[:, 0]], verts[tris[:, 1]], verts[tris[:, 2]]
    nrm = np.cross(B - A, C - A)
    ln = np.linalg.norm(nrm, axis=1)
    nrm = nrm / np.where(ln[:, None] == 0, 1.0, ln[:, None])
    facing = nrm @ view
    keep = facing > -0.02                      # cull the far side
    A, B, C, nrm = A[keep], B[keep], C[keep], nrm[keep]

    light = np.array([0.40, -0.62, 0.68])
    light /= np.linalg.norm(light)
    lam = np.clip(nrm @ light, 0.0, 1.0)
    sky = np.clip(nrm[:, 2], 0.0, 1.0)
    shade = 0.22 + 0.60 * lam + 0.18 * sky
    base = np.array([0.70, 0.67, 0.62])
    col = np.clip(shade[:, None] * base, 0, 1)

    w, h = W * ss, H * ss
    scale = min(w, h) / (2.10 * span)
    img = np.ones((h, w, 3), dtype=np.float32)

    pts, cols, dep = [], [], []
    cen = (A + B + C) / 3.0
    for P in (cen, A, B, C, (A + B) / 2, (B + C) / 2, (A + C) / 2):
        q = P - ctr
        pts.append(np.stack([q @ right, q @ up], axis=1))
        cols.append(col)
        dep.append(q @ view)
    pts = np.concatenate(pts)
    cols = np.concatenate(cols)
    dep = np.concatenate(dep)

    px = np.round(pts[:, 0] * scale + w / 2).astype(np.int64)
    py = np.round(-pts[:, 1] * scale + h / 2).astype(np.int64)
    ok = (px >= 1) & (px < w - 1) & (py >= 1) & (py < h - 1)
    px, py, cols, dep = px[ok], py[ok], cols[ok], dep[ok]
    order = np.argsort(dep)                     # far first, near overwrites
    px, py, cols = px[order], py[order], cols[order]
    for dx in (-1, 0, 1):                       # 3x3 splat closes the gaps
        for dy in (-1, 0, 1):
            img[py + dy, px + dx] = cols
    img = img.reshape(H, ss, W, ss, 3).mean(axis=(1, 3))
    return img


def write_preview(path, verts, tris, title, views=None):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("  preview skipped (matplotlib not installed)")
        return
    if views is None:
        views = [(24, -125, "iso"), (89, -90, "top (plan)"),
                 (4, -90, "through the front glass")]
    ctr = (verts.max(0) + verts.min(0)) / 2.0
    span = float((verts.max(0) - verts.min(0)).max()) / 2.0
    fig, axes = plt.subplots(1, len(views), figsize=(5.2 * len(views), 4.4))
    axes = np.atleast_1d(axes)
    for ax, (elev, azim, lbl) in zip(axes, views):
        ax.imshow(_render(verts, tris, elev, azim, 620, 520, ctr, span))
        ax.set_title(lbl, fontsize=10)
        ax.set_axis_off()
    fig.suptitle(title, fontsize=12)
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)
    print("  wrote %s" % path)


# ----------------------------------------------------------------------------
# self-contained browser viewer
# ----------------------------------------------------------------------------
VIEWER_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no,viewport-fit=cover">
<title>__TITLE__</title>
<style>
  :root { color-scheme: dark; }
  * { box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
  html, body { margin:0; height:100%; overflow:hidden; background:#14161a;
    font:14px/1.45 ui-sans-serif,-apple-system,"Segoe UI",Roboto,sans-serif;
    color:#e7e5e0; overscroll-behavior:none; }
  canvas { display:block; width:100%; height:100%; touch-action:none; }
  #hud { position:fixed; top:0; left:0; right:0; padding:10px 12px;
    padding-top:calc(10px + env(safe-area-inset-top));
    background:linear-gradient(#14161ad0,#14161a00); pointer-events:none; }
  #hud b { font-weight:600; letter-spacing:.01em; }
  #hud span { opacity:.62; }
  #bar { position:fixed; left:0; right:0; bottom:0;
    padding:10px 10px calc(10px + env(safe-area-inset-bottom));
    display:flex; gap:8px; flex-wrap:wrap; justify-content:center;
    background:linear-gradient(#14161a00,#14161ae0); }
  button { flex:0 0 auto; min-height:42px; padding:0 15px; border-radius:11px;
    border:1px solid #ffffff20; background:#ffffff10; color:#e7e5e0;
    font:inherit; font-weight:500; }
  button:active { background:#ffffff26; }
  button.on { background:#c9a26333; border-color:#c9a263aa; color:#f3e4c8; }
  #err { position:fixed; inset:0; display:none; place-items:center;
    padding:28px; text-align:center; background:#14161a; }
</style>
</head>
<body>
<canvas id="c"></canvas>
<div id="hud"><b>__TITLE__</b> &nbsp;<span id="sub">__SUBTITLE__</span><br><span id="stamp">build __BUILD__</span></div>
<div id="bar">
  <button id="b-iso">Iso</button>
  <button id="b-front">Front glass</button>
  <button id="b-side">Side glass</button>
  <button id="b-plan">Plan</button>
  <button id="b-sub" class="on">Substrate</button>
  <button id="b-glass" class="on">Glass</button>
  <button id="b-ruler" class="on">Ruler</button>
  <button id="b-spin">Spin</button>
</div>
<div id="err"></div>
<script>
const META = __META__;
const DATA = "__DATA__";

function fail(msg){ const e=document.getElementById('err');
  e.style.display='grid'; e.textContent=msg; }

function b64(s){ const bin=atob(s), a=new Uint8Array(bin.length);
  for(let i=0;i<bin.length;i++) a[i]=bin.charCodeAt(i); return a; }

async function inflate(bytes){
  if(typeof DecompressionStream==='undefined')
    throw new Error('This browser cannot decompress the model.');
  const s=new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'));
  return new Uint8Array(await new Response(s).arrayBuffer());
}

function parse(buf){
  const dv=new DataView(buf.buffer,buf.byteOffset,buf.byteLength);
  const nV=dv.getUint32(0,true), nT=dv.getUint32(4,true), ib=dv.getUint32(8,true);
  const bmin=[dv.getFloat32(12,true),dv.getFloat32(16,true),dv.getFloat32(20,true)];
  const bsz =[dv.getFloat32(24,true),dv.getFloat32(28,true),dv.getFloat32(32,true)];
  let o=36;
  const qp=new Uint16Array(buf.slice(o,o+nV*6).buffer); o+=nV*6;
  const qn=new Int8Array  (buf.slice(o,o+nV*3).buffer); o+=nV*3;
  o=Math.ceil(o/4)*4;
  const idx = ib===2 ? new Uint16Array(buf.slice(o,o+nT*6).buffer)
                     : new Uint32Array(buf.slice(o,o+nT*12).buffer);
  const pos=new Float32Array(nV*3), nrm=new Float32Array(nV*3);
  for(let i=0;i<nV;i++) for(let k=0;k<3;k++){
    pos[i*3+k]=bmin[k]+qp[i*3+k]/65535*bsz[k];
    nrm[i*3+k]=qn[i*3+k]/127;
  }
  return {pos,nrm,idx,nT,bmin,bsz};
}

/* --- tiny mat4 ---------------------------------------------------------- */
const M={
  persp(f,a,n,r){const t=1/Math.tan(f/2);return new Float32Array(
    [t/a,0,0,0, 0,t,0,0, 0,0,(r+n)/(n-r),-1, 0,0,2*r*n/(n-r),0]);},
  look(e,c,u){const z=M.n(M.s(e,c)),x=M.n(M.c(u,z)),y=M.c(z,x);
    return new Float32Array([x[0],y[0],z[0],0, x[1],y[1],z[1],0,
      x[2],y[2],z[2],0, -M.d(x,e),-M.d(y,e),-M.d(z,e),1]);},
  mul(a,b){const o=new Float32Array(16);
    for(let i=0;i<4;i++)for(let j=0;j<4;j++){let s=0;
      for(let k=0;k<4;k++)s+=a[k*4+j]*b[i*4+k]; o[i*4+j]=s;} return o;},
  s(a,b){return [a[0]-b[0],a[1]-b[1],a[2]-b[2]];},
  c(a,b){return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];},
  d(a,b){return a[0]*b[0]+a[1]*b[1]+a[2]*b[2];},
  n(a){const l=Math.hypot(a[0],a[1],a[2])||1;return [a[0]/l,a[1]/l,a[2]/l];}
};

const VS=`attribute vec3 aP; attribute vec3 aN;
uniform mat4 uMVP; uniform mat4 uM; varying vec3 vN; varying vec3 vP;
void main(){ vN=aN; vP=(uM*vec4(aP,1.0)).xyz; gl_Position=uMVP*vec4(aP,1.0); }`;

const FS=`precision mediump float; varying vec3 vN; varying vec3 vP;
uniform vec3 uCol; uniform float uAlpha; uniform float uFlat;
void main(){
  vec3 n=normalize(vN);
  vec3 L=normalize(vec3(0.42,-0.60,0.68));
  float lam=max(dot(n,L),0.0);
  float sky=0.5+0.5*n.z;
  vec3 warm=vec3(1.00,0.94,0.84), cool=vec3(0.55,0.60,0.70);
  vec3 c=uCol*(0.16+0.60*lam)+uCol*cool*0.26*sky+warm*0.06*pow(lam,6.0);
  c=mix(c,uCol,uFlat);
  gl_FragColor=vec4(pow(c,vec3(0.4545)),uAlpha);
}`;

function shader(gl,t,src){const s=gl.createShader(t);gl.shaderSource(s,src);
  gl.compileShader(s);
  if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))
    throw new Error(gl.getShaderInfoLog(s));
  return s;}

(async function main(){
 try{
  const mesh=parse(await inflate(b64(DATA)));
  const cv=document.getElementById('c');
  const opt={antialias:true,alpha:false,preserveDrawingBuffer:false};
  const gl=cv.getContext('webgl2',opt)||cv.getContext('webgl',opt);
  const gl2=!!(window.WebGL2RenderingContext&&gl instanceof WebGL2RenderingContext);
  if(!gl) return fail('WebGL is not available in this browser.');

  const prog=gl.createProgram();
  gl.attachShader(prog,shader(gl,gl.VERTEX_SHADER,VS));
  gl.attachShader(prog,shader(gl,gl.FRAGMENT_SHADER,FS));
  gl.bindAttribLocation(prog,0,'aP'); gl.bindAttribLocation(prog,1,'aN');
  gl.linkProgram(prog); gl.useProgram(prog);
  const uMVP=gl.getUniformLocation(prog,'uMVP'),
        uM=gl.getUniformLocation(prog,'uM'),
        uCol=gl.getUniformLocation(prog,'uCol'),
        uA=gl.getUniformLocation(prog,'uAlpha'),
        uF=gl.getUniformLocation(prog,'uFlat');

  function buf(target,data,type){const b=gl.createBuffer();
    gl.bindBuffer(target,b); gl.bufferData(target,data,gl.STATIC_DRAW); return b;}
  const bP=buf(gl.ARRAY_BUFFER,mesh.pos), bN=buf(gl.ARRAY_BUFFER,mesh.nrm);
  const bI=buf(gl.ELEMENT_ARRAY_BUFFER,mesh.idx);
  const idxType = mesh.idx.BYTES_PER_ELEMENT===2
    ? gl.UNSIGNED_SHORT : gl.UNSIGNED_INT;
  if(idxType===gl.UNSIGNED_INT && !gl2 && !gl.getExtension('OES_element_index_uint'))
    return fail('This browser cannot draw a mesh this large.');

  /* helper planes: substrate slab and the two glass panes */
  const lo=mesh.bmin, hi=[lo[0]+mesh.bsz[0],lo[1]+mesh.bsz[1],lo[2]+mesh.bsz[2]];
  const pad=Math.max(mesh.bsz[0],mesh.bsz[1])*0.10;
  function quad(v,n){ return {p:new Float32Array(v),
    n:new Float32Array([].concat(n,n,n,n,n,n))}; }
  /* the substrate is a hill: a profile of [x, z] pairs swept across Y */
  const prof=META.substrate.slice().sort((a,b)=>a[0]-b[0]);
  const y0=lo[1]-pad, y1=hi[1]+pad, sv=[], sn=[];
  for(let i=0;i<prof.length-1;i++){
    const [xa,za]=prof[i], [xb,zb2]=prof[i+1];
    const dx=xb-xa, dz=zb2-za, L=Math.hypot(dx,dz)||1;
    const nx=-dz/L, nz=dx/L;
    sv.push(xa,y0,za, xb,y0,zb2, xb,y1,zb2, xa,y0,za, xb,y1,zb2, xa,y1,za);
    for(let k=0;k<6;k++) sn.push(nx,0,nz);
  }
  const subQ={p:new Float32Array(sv), n:new Float32Array(sn),
              count:sv.length/3};
  const gx=META.glassX, gy=META.glassY, ztop=hi[2]+pad*0.4;
  const glassA=quad([gx,lo[1]-pad,lo[2], gx,hi[1]+pad,lo[2], gx,hi[1]+pad,ztop,
                     gx,lo[1]-pad,lo[2], gx,hi[1]+pad,ztop, gx,lo[1]-pad,ztop],
                    [META.mirror?1:-1,0,0]);
  const glassB=quad([lo[0]-pad,gy,lo[2], hi[0]+pad,gy,lo[2], hi[0]+pad,gy,ztop,
                     lo[0]-pad,gy,lo[2], hi[0]+pad,gy,ztop, lo[0]-pad,gy,ztop],
                    [0,-1,0]);
  for(const q of [subQ,glassA,glassB]){
    q.bP=buf(gl.ARRAY_BUFFER,q.p); q.bN=buf(gl.ARRAY_BUFFER,q.n);
  }

  /* a proper scale rule lying on the floor: graduated edge, three tick
     lengths, and numerals built from seven-segment bars */
  const RU=META.ruler;
  function pushBox(P,N,x0,x1,y0,y1,z0,z1){
    const c=[[x0,y0,z0],[x1,y0,z0],[x1,y1,z0],[x0,y1,z0],
             [x0,y0,z1],[x1,y0,z1],[x1,y1,z1],[x0,y1,z1]];
    const F=[[0,3,2,1,0,0,-1],[4,5,6,7,0,0,1],[0,1,5,4,0,-1,0],
             [2,3,7,6,0,1,0],[1,2,6,5,1,0,0],[3,0,4,7,-1,0,0]];
    for(const f of F)
      for(const tri of [[f[0],f[1],f[2]],[f[0],f[2],f[3]]])
        for(const k of tri){ P.push(c[k][0],c[k][1],c[k][2]);
                             N.push(f[4],f[5],f[6]); }
  }
  const SEG={0:"abcdef",1:"bc",2:"abged",3:"abgcd",4:"fgbc",5:"afgcd",
             6:"afgecd",7:"abc",8:"abcdefg",9:"abcdfg"};
  function pushDigit(P,N,ch,x0,y0,z0,z1){
    const w=RU.dw,h=RU.dh,t=RU.dt,S=SEG[ch]||"";
    const box={a:[x0,x0+w,y0+h-t,y0+h], g:[x0,x0+w,y0+h/2-t/2,y0+h/2+t/2],
               d:[x0,x0+w,y0,y0+t],     f:[x0,x0+t,y0+h/2,y0+h],
               b:[x0+w-t,x0+w,y0+h/2,y0+h], e:[x0,x0+t,y0,y0+h/2],
               c:[x0+w-t,x0+w,y0,y0+h/2]};
    for(const s of S){const q=box[s]; pushBox(P,N,q[0],q[1],q[2],q[3],z0,z1);}
  }
  function pushNumber(P,N,val,xc,y0,z0,z1){
    const s=String(val), adv=RU.dw+RU.dgap, tot=s.length*adv-RU.dgap;
    for(let i=0;i<s.length;i++)
      pushDigit(P,N,+s[i],xc-tot/2+i*adv,y0,z0,z1);
  }
  const rPlateP=[],rPlateN=[],rInkP=[],rInkN=[];
  {
    const xa=Math.min(lo[0],hi[0]), xb=Math.max(lo[0],hi[0]);
    const yEdge=lo[1]-pad*0.30;                 // graduated edge, nearest model
    const yBack=yEdge-RU.plate;
    const z0=lo[2], z1=z0+RU.thick, z2=z1+RU.thick*0.8;
    pushBox(rPlateP,rPlateN,xa-RU.major*0.12,xb+RU.major*0.12,yBack,yEdge,z0,z1);
    const dir=(xa<0)?-1:1;
    for(let k=0;;k++){
      const x=dir*k*RU.fine;
      if(x<xa||x>xb) break;
      const major=(k*RU.fine)%RU.major<1e-6, med=(k*RU.fine)%RU.med<1e-6;
      const len=major?RU.tickJ:med?RU.tickM:RU.tickF;
      const w=major?RU.thick*1.1:RU.thick*0.7;
      pushBox(rInkP,rInkN,x-w,x+w,yEdge-len,yEdge,z1,z2);
    }
    for(let k=0;;k++){
      const x=dir*k*RU.major;
      if(x<xa||x>xb) break;
      pushNumber(rInkP,rInkN,k*RU.labelStep,x,yEdge-RU.tickJ-RU.dh-RU.dgap*1.6,
                 z1,z2);
    }
  }
  const rBase={p:new Float32Array(rPlateP),n:new Float32Array(rPlateN),
               count:rPlateP.length/3};
  const rTick={p:new Float32Array(rInkP),n:new Float32Array(rInkN),
               count:rInkP.length/3};
  for(const q of [rBase,rTick]){
    q.bP=buf(gl.ARRAY_BUFFER,q.p); q.bN=buf(gl.ARRAY_BUFFER,q.n);
  }

  const ctr=[lo[0]+mesh.bsz[0]/2, lo[1]+mesh.bsz[1]/2, lo[2]+mesh.bsz[2]/2];
  const rad=Math.hypot(mesh.bsz[0],mesh.bsz[1],mesh.bsz[2])/2;
  let cam={th:META.mirror?-2.30:-0.84, ph:0.62, dist:rad*2.5,
           tgt:ctr.slice()};
  const home=JSON.parse(JSON.stringify(cam));
  let showSub=true, showGlass=true, showRuler=true, spin=false;

  function view(th,ph,dist){ cam.th=th; cam.ph=ph;
    cam.dist=dist*rad; cam.tgt=ctr.slice(); spin=false;
    document.getElementById('b-spin').classList.remove('on'); }
  const mir=META.mirror?-1:1;
  document.getElementById('b-iso').onclick  =()=>view(mir*-0.84,0.62,2.5);
  document.getElementById('b-front').onclick=()=>view(-Math.PI/2,0.05,2.2);
  document.getElementById('b-side').onclick =()=>view(mir*Math.PI,0.05,2.2);
  document.getElementById('b-plan').onclick =()=>view(-Math.PI/2,1.5507,2.3);
  const tog=(id,get,set)=>{const b=document.getElementById(id);
    b.onclick=()=>{set(!get()); b.classList.toggle('on',get());};};
  tog('b-sub',()=>showSub,v=>showSub=v);
  tog('b-glass',()=>showGlass,v=>showGlass=v);
  tog('b-ruler',()=>showRuler,v=>showRuler=v);
  tog('b-spin',()=>spin,v=>spin=v);

  /* --- input ----------------------------------------------------------- */
  let pts=new Map(), last=null, lastDist=0;
  cv.addEventListener('pointerdown',e=>{cv.setPointerCapture(e.pointerId);
    pts.set(e.pointerId,[e.clientX,e.clientY]); last=[e.clientX,e.clientY];
    lastDist=0;});
  cv.addEventListener('pointerup',e=>{pts.delete(e.pointerId);last=null;});
  cv.addEventListener('pointercancel',e=>{pts.delete(e.pointerId);last=null;});
  cv.addEventListener('pointermove',e=>{
    if(!pts.has(e.pointerId)) return;
    pts.set(e.pointerId,[e.clientX,e.clientY]);
    const a=[...pts.values()];
    if(a.length>=2){
      const d=Math.hypot(a[0][0]-a[1][0],a[0][1]-a[1][1]);
      if(lastDist) cam.dist*=lastDist/d;
      cam.dist=Math.min(Math.max(cam.dist,rad*0.25),rad*14);
      lastDist=d; last=null; return;
    }
    if(!last){ last=[e.clientX,e.clientY]; return; }
    const dx=e.clientX-last[0], dy=e.clientY-last[1];
    last=[e.clientX,e.clientY];
    if(e.shiftKey||e.buttons===2){
      const k=cam.dist*0.0016;
      cam.tgt[0]-= -Math.sin(cam.th)*dx*k; cam.tgt[1]-= Math.cos(cam.th)*dx*k;
      cam.tgt[2]+= dy*k;
    } else {
      cam.th-=dx*0.008;
      cam.ph=Math.min(Math.max(cam.ph+dy*0.008,-1.5507),1.5507);
    }
  });
  cv.addEventListener('contextmenu',e=>e.preventDefault());
  cv.addEventListener('wheel',e=>{e.preventDefault();
    cam.dist=Math.min(Math.max(cam.dist*Math.exp(e.deltaY*0.0012),rad*0.25),
                      rad*14);},{passive:false});
  cv.addEventListener('dblclick',()=>{cam=JSON.parse(JSON.stringify(home));});

  /* --- draw ------------------------------------------------------------ */
  gl.enable(gl.DEPTH_TEST);
  gl.clearColor(0.078,0.086,0.102,1);
  function bind(bp,bn){
    gl.bindBuffer(gl.ARRAY_BUFFER,bp);
    gl.enableVertexAttribArray(0); gl.vertexAttribPointer(0,3,gl.FLOAT,false,0,0);
    gl.bindBuffer(gl.ARRAY_BUFFER,bn);
    gl.enableVertexAttribArray(1); gl.vertexAttribPointer(1,3,gl.FLOAT,false,0,0);
  }
  const I=new Float32Array([1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1]);

  function frame(){
    const dpr=Math.min(window.devicePixelRatio||1,2);
    const w=Math.round(cv.clientWidth*dpr), h=Math.round(cv.clientHeight*dpr);
    if(cv.width!==w||cv.height!==h){cv.width=w;cv.height=h;}
    gl.viewport(0,0,w,h);
    gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);
    if(spin) cam.th+=0.0045;
    const cp=Math.cos(cam.ph), e=[
      cam.tgt[0]+cam.dist*cp*Math.cos(cam.th),
      cam.tgt[1]+cam.dist*cp*Math.sin(cam.th),
      cam.tgt[2]+cam.dist*Math.sin(cam.ph)];
    const P=M.persp(0.72,w/h,rad*0.05,rad*40);
    const V=M.look(e,cam.tgt,[0,0,1]);
    gl.uniformMatrix4fv(uMVP,false,M.mul(P,V));
    gl.uniformMatrix4fv(uM,false,I);

    gl.disable(gl.BLEND); gl.depthMask(true);
    gl.uniform3f(uCol,0.60,0.575,0.53); gl.uniform1f(uA,1.0);
    gl.uniform1f(uF,0.0);
    bind(bP,bN);
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER,bI);
    gl.drawElements(gl.TRIANGLES,mesh.nT*3,idxType,0);

    if(showRuler){
      gl.uniform1f(uF,1.0);
      gl.uniform3f(uCol,0.88,0.85,0.78); gl.uniform1f(uA,1.0);
      bind(rBase.bP,rBase.bN); gl.drawArrays(gl.TRIANGLES,0,rBase.count);
      gl.uniform3f(uCol,0.10,0.11,0.13);
      bind(rTick.bP,rTick.bN); gl.drawArrays(gl.TRIANGLES,0,rTick.count);
      gl.uniform1f(uF,0.0);
    }

    gl.enable(gl.BLEND);
    gl.blendFunc(gl.SRC_ALPHA,gl.ONE_MINUS_SRC_ALPHA);
    gl.depthMask(false); gl.uniform1f(uF,1.0);
    if(showSub){ gl.uniform3f(uCol,0.42,0.33,0.24); gl.uniform1f(uA,0.42);
      bind(subQ.bP,subQ.bN); gl.drawArrays(gl.TRIANGLES,0,subQ.count); }
    if(showGlass){ gl.uniform3f(uCol,0.42,0.62,0.68); gl.uniform1f(uA,0.13);
      bind(glassA.bP,glassA.bN); gl.drawArrays(gl.TRIANGLES,0,6);
      bind(glassB.bP,glassB.bN); gl.drawArrays(gl.TRIANGLES,0,6); }
    gl.depthMask(true);
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
 }catch(err){ fail(String(err && err.message || err)); }
})();
</script>
</body>
</html>
"""


def write_viewer(path, verts, tris, p, meta):
    """Write a single self-contained HTML file: no CDN, no dependencies."""
    import base64
    import gzip
    import json

    v = np.asarray(verts, dtype=np.float64)
    t = np.asarray(tris, dtype=np.int64)

    # area-weighted vertex normals
    a, b, c = v[t[:, 0]], v[t[:, 1]], v[t[:, 2]]
    fn = np.cross(b - a, c - a)
    nrm = np.zeros_like(v)
    for k in range(3):
        np.add.at(nrm, t[:, k], fn)
    ln = np.linalg.norm(nrm, axis=1)
    nrm = nrm / np.where(ln[:, None] == 0, 1.0, ln[:, None])

    lo = v.min(0)
    size = np.maximum(v.max(0) - lo, 1e-6)
    qp = np.clip(np.round((v - lo) / size * 65535.0), 0, 65535).astype("<u2")
    qn = np.clip(np.round(nrm * 127.0), -127, 127).astype("<i1")
    idx_bytes = 2 if len(v) < 65536 else 4
    idx = t.astype("<u2" if idx_bytes == 2 else "<u4")

    head = struct.pack("<III6f", len(v), len(t), idx_bytes,
                       *lo.astype(np.float32), *size.astype(np.float32))
    body = head + qp.tobytes() + qn.tobytes()
    body += b"\x00" * ((-len(body)) % 4)
    body += idx.tobytes()
    blob = base64.b64encode(gzip.compress(body, 9)).decode("ascii")

    html = (VIEWER_HTML
            .replace("__TITLE__", meta["title"])
            .replace("__SUBTITLE__", meta["subtitle"])
            .replace("__BUILD__", meta["build"])
            .replace("__META__", json.dumps(meta["js"]))
            .replace("__DATA__", blob))
    with open(path, "w") as fh:
        fh.write(html)
    return len(html)


# ----------------------------------------------------------------------------
def main():
    d = Params()
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default="snake_hide")
    ap.add_argument("--leg-long", type=float, default=d.leg_long)
    ap.add_argument("--leg-short", type=float, default=d.leg_short)
    ap.add_argument("--tunnel-w", type=float, default=d.tunnel_w)
    ap.add_argument("--tunnel-h", type=float, default=d.tunnel_h)
    ap.add_argument("--wall", type=float, default=d.wall)
    ap.add_argument("--substrate", type=float, default=d.substrate)
    ap.add_argument("--round", type=float, default=d.round_r,
                    dest="round_r", help="radius on convex arrises")
    ap.add_argument("--round-in", type=float, default=d.round_in,
                    help="radius on the bore and other cut features")
    ap.add_argument("--blend", type=float, default=d.blend)
    ap.add_argument("--res", type=float, default=d.res,
                    help="grid cell in inches; smaller is finer and slower")
    ap.add_argument("--stair-run", type=float, default=d.stair_run,
                    help="how far the flight runs past the tomb")
    ap.add_argument("--stair-tread", type=float, default=d.stair_tread)
    ap.add_argument("--pass-head", type=float, default=d.pass_head,
                    help="headroom in the covered stairway")
    ap.add_argument("--hatch-clear", type=float, default=d.hatch_clear)
    ap.add_argument("--no-ribs", action="store_true")
    ap.add_argument("--hatch-torii", action="store_true")
    ap.add_argument("--plain-entrance", action="store_true",
                    help="skip the shopfront: noren, signboard, lanterns")
    ap.add_argument("--plain-hatch", action="store_true",
                    help="skip the stone lantern over the escape hatch")
    ap.add_argument("--torii-spacing", type=float, default=d.torii_spacing,
                    help="gate centres inside the tomb; 0 for none")
    ap.add_argument("--floor-joints", action="store_true",
                    help="add shallow flagstone joints across the tomb floor")
    ap.add_argument("--coffer", type=float, default=d.coffer)
    ap.add_argument("--corner-post", type=float, default=d.corner_post)
    ap.add_argument("--closed", action="store_true")
    ap.add_argument("--units", choices=("mm", "in"), default=d.units)
    ap.add_argument("--scale", type=float, default=d.scale)
    ap.add_argument("--mirror", action=argparse.BooleanOptionalAction,
                    default=d.mirror,
                    help="+X east with the hide west of the corner (default);"
                         " --no-mirror gives the opposite hand")
    ap.add_argument("--ascii-stl", action="store_true")
    ap.add_argument("--preview", metavar="PNG", default=None,
                    help="also write a static PNG contact sheet")
    ap.add_argument("--no-viewer", action="store_true",
                    help="skip the interactive HTML viewer")
    ap.add_argument("--viewer-res", type=float, default=0.045,
                    help="grid cell for the viewer mesh; coarser keeps the"
                         " HTML small enough for a phone")
    a = ap.parse_args()

    p = Params(leg_long=a.leg_long, leg_short=a.leg_short, tunnel_w=a.tunnel_w,
               tunnel_h=a.tunnel_h, wall=a.wall, substrate=a.substrate,
               round_r=a.round_r, round_in=a.round_in, blend=a.blend,
               res=a.res, stair_run=a.stair_run, stair_tread=a.stair_tread,
               pass_head=a.pass_head,
               hatch_clear=a.hatch_clear, hatch_ribs=not a.no_ribs,
               hatch_torii=a.hatch_torii, torii_spacing=a.torii_spacing,
               entrance_detail=not a.plain_entrance,
               hatch_lantern=not a.plain_hatch,
               floor_joints=a.floor_joints, coffer=a.coffer,
               corner_post=a.corner_post, open_to_glass=not a.closed,
               units=a.units, scale=a.scale, mirror=a.mirror)

    p = resolve(p)                 # legs snap to the gate grid
    ops, z_body, s, z_hatch, ng = build(p)
    f = rasterise(p, ops)
    verts_in, tris = surface_nets(f)
    ok, msg = check_manifold(tris)
    vol_in3 = float((f.d <= 0).sum()) * p.res ** 3
    verts = transform(verts_in, p)

    obj_path, stl_path = a.out + ".obj", a.out + ".stl"
    write_obj(obj_path, verts, tris, "snake_hide")
    write_stl(stl_path, verts, tris, a.ascii_stl)

    half = p.tunnel_w / 2.0
    covered = ((p.leg_long - half)
               + (p.leg_short - p.wall - p.hatch_clear - half))
    bbmin, bbmax = verts.min(0), verts.max(0)
    print("\n  snake hide -- covered stairway SW, escape hatch NE, %s corner"
          % ("front-right (SE)" if p.mirror else "front-left (SW)"))
    print("  " + "-" * 66)
    print("  buried footprint        %.2f (S leg) x %.2f (N leg) in"
          % (p.leg_long, p.leg_short))
    print("  gate grid               %d gates at %.2f in centres; the last on"
          " each leg lands %.2f in short of the end"
          % (ng, p.torii_spacing, p.gate_end_gap))
    print("  tunnel bore             %.2f w x %.2f h in, corners r%.2f"
          % (p.tunnel_w, p.tunnel_h, p.round_in))
    print("  edge radius             %.3f in (%.1f mm) on convex arrises,"
          " %.2f blend" % (p.round_r, p.round_r * MM_PER_IN, p.blend))
    print("  body height (buried)    %.2f in" % z_body)
    print("  covered dark tunnel     %.1f in of roofed run" % covered)
    print("  torii gates inside      %d, %.2f in centres, %.2f x %.2f clear"
          % (ng, p.torii_spacing, p.tunnel_w - 2 * (0.05 + p.torii_post),
             p.tunnel_h - p.torii_head))
    print("  corner chamber          ceiling coffered +%.2f in" % p.coffer)
    print("  floor joints            %s"
          % ("%.2f in centres, %.3f deep"
             % (p.joint_spacing, p.joint_depth) if p.floor_joints else "none"))
    print("  covered stairway        %.2f -> %.2f in, %d treads @ %.3f rise"
          " / %.3f going" % (p.leg_long, p.stair_end, s["n"], s["rise"],
                             s["tread"]))
    print("                          one smooth roof at %.0f deg, %.2f in"
          " headroom, doorway %.2f in, sill %.2f above grade"
          % (math.degrees(s["th"]), p.pass_head, p.door_h, p.mouth_lip))
    print("  hill                    %.2f in at the foot (stair end) ->"
          " %.2f in at the top (corner + hatch)"
          % (p.substrate, p.substrate + p.hill))
    print("  proud of the surface    gable %.2f in at the foot, hatch %.2f in"
          " at the top" % (s["proud"], z_hatch - (p.substrate + p.hill)))
    print("  glass-facing sides      %s"
          % ("tomb OPEN (glass forms 2 walls), stairway walled in"
             if p.open_to_glass else "all walled in"))
    print("  bounding box (%s)       %.2f x %.2f x %.2f"
          % (p.units, *(bbmax - bbmin)))
    print("  material volume         %.1f cm^3  (~%.0f g at 100%% PETG)"
          % (vol_in3 * 16.387, vol_in3 * 16.387 * 1.27))
    print("  grid                    %d x %d x %d cells @ %.3f in"
          % (f.x.size, f.y.size, f.z.size, p.res))
    print("  mesh                    %d verts / %d tris"
          % (len(verts), len(tris)))
    print("  integrity check         %s -- %s" % ("PASS" if ok else "FAIL", msg))
    if not ok:
        print("     a coarse --res cannot always resolve the small details;"
              " try --res %.3f" % (p.res * 0.7))
    if p.substrate < z_body + 0.1:
        print("  !! substrate is shallower than the body -- it will not bury")
    if s["rise"] > 0.45:
        print("  !! %.2f in rise per tread is very steep -- push --stair-end"
              " further out or lower --substrate" % s["rise"])
    print("  wrote %s\n  wrote %s" % (obj_path, stl_path))
    if not a.no_viewer:
        if p.res >= a.viewer_res * 0.95:
            vv, vt = verts, tris
        else:
            pv = replace(p, res=a.viewer_res)
            fv = rasterise(pv, build(pv)[0])
            vin, vt = surface_nets(fv)
            vv = transform(vin, p)
        k = (MM_PER_IN if p.units == "mm" else 1.0) * p.scale
        html = a.out + "_viewer.html"
        import datetime
        stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        n = write_viewer(html, vv, vt, p, dict(
            title="Snake hide",
            build=stamp,
            subtitle="%.0f x %.0f %s - ruler is graduated in %s, numbered"
                     " every %s; the substrate slopes from the hilltop"
                     % (p.stair_end * k, p.leg_short * k, p.units,
                        "5 mm" if p.units == "mm" else "1/8 in",
                        "50 mm" if p.units == "mm" else "1 in"),
            js=dict(substrate=[[(-x if p.mirror else x) * k, z * k]
                               for x, z in [(0.0, p.substrate + p.hill),
                                            (p.leg_long, p.substrate),
                                            (p.stair_end + 0.8, p.substrate)]],
                    glassX=0.0, glassY=0.0, mirror=bool(p.mirror),
                    ruler=(dict(fine=5.0, med=10.0, major=50.0, labelStep=50,
                               plate=27.0, tickJ=13.0, tickM=8.0, tickF=4.5,
                               dh=9.0, dw=5.4, dt=1.4, dgap=1.8, thick=1.1)
                           if p.units == "mm" else dict(fine=0.125, med=0.5, major=1.0, labelStep=1,
                               plate=1.06, tickJ=0.51, tickM=0.31, tickF=0.18,
                               dh=0.35, dw=0.21, dt=0.055, dgap=0.07,
                               thick=0.045)))))
        print("  wrote %s  (%.1f MB, %d tris, opens offline)"
              % (html, n / 1e6, len(vt)))
    if a.preview:
        write_preview(a.preview, verts, tris, "snake hide  (%s)" % p.units)
    print()


if __name__ == "__main__":
    main()
