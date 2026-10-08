#!/usr/bin/env python3
"""
Parametric dust-collection fittings for 2-1/2" clear PVC pipe
(Sasylvia / POWERTEC-class, 63.1 mm actual OD, 59.5 mm ID).

All fittings share the same socket/bore dimensions, defined ONCE at the top
of this file.  Change PIPE_OD / PIPE_ID and the entire family resizes.

Run this file with no arguments to generate every STL into
out/stl/ (or pass a custom directory as the first argument).

Adding a new fitting:
    1. Write a `def make_<name>(): ... return trimesh.Trimesh` using the
       helpers `cylinder_between`, `torus_arc`, `union`, `difference`.
    2. Add it to the FITTINGS dict at the bottom.
"""
import os
import sys
import numpy as np
import trimesh
from trimesh import transformations as tf

# ===========================================================================
#                  BASE PARAMETERS  -- the only knobs
# ===========================================================================
PIPE_OD          = 63.1     # actual outer diameter of the pipe (~2-31/64")
PIPE_ID          = 59.5     # actual inner diameter of the pipe (~2-21/64")
PRINT_CLEARANCE  = 0.70     # diametric slip-fit clearance for FDM printing

WALL          = 3.0         # connector wall thickness (was 4.0; thinner = slimmer
                            # tubes and a wider view through the vents)
SOCKET_DEPTH  = 30.0        # how far a pipe slips into a socket
LEAD_IN       = 12.0        # bore-only section between socket and junction/bend
BEND_R        = 70.0        # centerline bend radius for elbows / U-bend

# ---- derived ----
SOCKET_ID = PIPE_OD + PRINT_CLEARANCE       # 63.80 mm
BORE_ID   = PIPE_ID                         # 59.50 mm
SOCKET_R  = SOCKET_ID / 2                   # 31.90 mm
BORE_R    = BORE_ID   / 2                   # 29.75 mm
OUTER_R   = SOCKET_R + WALL                 # 35.90 mm
TUBE_OD   = OUTER_R * 2                     # 71.80 mm
LEG_LENGTH = SOCKET_DEPTH + LEAD_IN         # 42.00 mm

# At tee/wye junctions, two perpendicular pipes inserted into adjacent
# sockets can collide inside the fitting if their tips reach too close to
# the centerline.  Geometric constraint:  leg > SOCKET_DEPTH + PIPE_OD/2.
# JUNCTION_CLEARANCE adds extra clear space between inserted pipe surfaces.
JUNCTION_CLEARANCE = 10.0                   # → tee/wye legs = 71.55 mm

# Mesh density
SEG_CYL         = 96
SEG_TORUS_MAJOR = 96
SEG_TORUS_MINOR = 64

# ---------------------------------------------------------------------------
# QUARTER-TURN LATCH  (female on every socket, male on the cap)
#
# Female: a short raised COLLAR around the outside of each socket mouth, with
#   LATCH_COUNT J-slots cut into it: an axial entry channel from the mouth,
#   then a circumferential run of LATCH_ROT_DEG ending at a hard stop. A small
#   rounded DETENT bump in the slot floor sits just behind the locked lug, so
#   the cap clicks in and cannot drift back to the entry.
#   Everything is on the OUTSIDE: tubes still slide into the socket exactly as
#   before, and the slots cut only the collar, never the 4 mm socket wall.
# Male: the cap plugs into the socket (a ring, ID = bore, so a capped port is
#   a smooth dead end) AND wraps the collar with a skirt carrying the lugs.
#
# Local port frame used below: z = 0 at the socket mouth face, +z runs INTO
# the fitting along the socket axis.
# ---------------------------------------------------------------------------
LATCH_ENABLE   = True
LATCH_COUNT    = 3         # lugs / slots per port
LATCH_ROT_DEG  = 30.0      # twist from entry to locked
COLLAR_T       = 2.2       # radial thickness of the collar over OUTER_R
SLOT_DEPTH     = 1.6       # slot depth into the collar (collar keeps 0.6 mm)
LATCH_Z        = 5.0       # mouth face -> lug bearing face (the locking ledge)
LUG_L          = 4.0       # lug axial length
LUG_W          = 8.0       # lug width, arc length at the collar surface
LUG_RAD_CL     = 0.25      # lug tip -> slot floor, radial
SLOT_AX_CL     = 0.30      # axial clearance each side of the lug in the run
SLOT_CIRC_CL   = 0.50      # circumferential clearance each side of the lug
DETENT_H       = 0.50      # bump height above the slot floor
DETENT_R       = 1.20      # bump radius (rounded, so the lug rides over it)
COLLAR_L       = LATCH_Z + LUG_L + SLOT_AX_CL + 3.5   # 12.8 mm

SKIRT_CL       = 0.30      # radial clearance, skirt ID over the collar
SKIRT_T        = 2.4       # skirt wall
CAP_DISK_T     = 3.0       # end disk that closes the port
CAP_PLUG_CL    = 0.20      # plug prints this much under pipe OD (diameter)
CAP_GRIP_RIBS  = 24        # small axial ribs on the skirt for twisting
# MALE ends (shim, built-in male ports) are EXACTLY the cap's latch: short
# skirt (SKIRT_L) with one ring of grip ribs, same clearances, same lead-ins.
# The first male ends had a full-length sleeve (29.5 mm) so the shim could
# stand on either end without support - far too much surface; they bound
# while the cap fit perfectly (Tyler, 2026-09-28). MALE_FIT_EXTRA stays
# available as a tuning knob; the fit coupons test 0 / 0.15 / 0.30.
MALE_FIT_EXTRA = 0.0       # extra RADIAL clearance over the cap (0 = cap fit)
MALE_FIT_TEST  = (0.0, 0.15, 0.30)   # the three rings in the fit coupon set
MALE_LEADIN_SKIRT = 0.4    # same lead-ins as the cap
MALE_LEADIN_PLUG  = 0.8

# ---- derived ----
COLLAR_R   = OUTER_R + COLLAR_T                   # 38.10 mm
PORT_OD    = 2 * COLLAR_R if LATCH_ENABLE else TUBE_OD
SLOT_FLOOR = COLLAR_R - SLOT_DEPTH                # 36.50 mm
SKIRT_RI   = COLLAR_R + SKIRT_CL
SKIRT_RO   = SKIRT_RI + SKIRT_T
SKIRT_L    = LATCH_Z + LUG_L + 1.5                # ends on the collar


# ===========================================================================
#                              HELPERS
# ===========================================================================
def union(parts):
    return trimesh.boolean.union(parts, engine='manifold')

def difference(a, b):
    return a.difference(b, engine='manifold')

def intersection(a, b):
    return a.intersection(b, engine='manifold')


def export_ready(mesh, digits=4):
    """Make a mesh safe to write as STL, and PROVE it.

    STL stores float32. Boolean output can hold distinct vertices < 1e-6 mm
    apart; float32 rounding then merges some and leaves non-manifold edges
    (the tee and wye both did this). Weld at 10**-digits mm, drop degenerate
    and duplicate faces, then round-trip through a real binary STL and
    require it to be watertight. Raises rather than export a broken file."""
    import io
    m = mesh.copy()
    m.merge_vertices(digits_vertex=digits)
    m.update_faces(m.nondegenerate_faces())
    m.update_faces(m.unique_faces())
    m.remove_unreferenced_vertices()
    buf = io.BytesIO(); m.export(buf, file_type='stl'); buf.seek(0)
    back = trimesh.load(buf, file_type='stl')
    if not back.is_watertight or len(back.split(only_watertight=False)) != 1:
        raise RuntimeError("mesh is not a single watertight body after STL round trip")
    if abs(back.volume - mesh.volume) > 1e-3 * abs(mesh.volume):
        raise RuntimeError("welding changed the volume")
    return m


def cylinder_between(p1, p2, radius, sections=SEG_CYL):
    """Solid cylinder of `radius` whose ends are at p1 and p2."""
    p1 = np.asarray(p1, dtype=float)
    p2 = np.asarray(p2, dtype=float)
    vec = p2 - p1
    length = np.linalg.norm(vec)
    if length < 1e-9:
        raise ValueError("cylinder_between: p1 == p2")
    direction = vec / length
    cyl = trimesh.creation.cylinder(radius=radius, height=length, sections=sections)
    z_axis = np.array([0.0, 0.0, 1.0])
    cos_a = np.clip(np.dot(z_axis, direction), -1.0, 1.0)
    if cos_a < 1 - 1e-9:
        if cos_a > -1 + 1e-9:
            axis = np.cross(z_axis, direction)
            axis /= np.linalg.norm(axis)
            cyl.apply_transform(tf.rotation_matrix(np.arccos(cos_a), axis))
        else:
            cyl.apply_transform(tf.rotation_matrix(np.pi, (1, 0, 0)))
    cyl.apply_translation((p1 + p2) / 2.0)
    return cyl


def torus_arc(major, minor, fraction, plane='xz'):
    """A fractional torus (fraction=0.25 -> quarter, 0.5 -> half, 1.0 -> full).
    Centerline lies in the named plane and starts at angle 0 going CCW.
    For 'xz' plane: starts at (major, 0, 0), goes through (0, 0, major).
    """
    full = trimesh.creation.torus(
        major_radius=major, minor_radius=minor,
        major_sections=SEG_TORUS_MAJOR,
        minor_sections=SEG_TORUS_MINOR,
    )
    if plane == 'xz':
        full.apply_transform(tf.rotation_matrix(np.pi/2, (1, 0, 0)))
    elif plane == 'yz':
        full.apply_transform(tf.rotation_matrix(np.pi/2, (0, 1, 0)))
    elif plane != 'xy':
        raise ValueError(plane)

    if fraction >= 0.999:
        return full

    big = 1000.0
    cuts = []
    if plane == 'xz':
        if abs(fraction - 0.25) < 1e-6:
            # keep x>=0, z>=0
            cuts = [((-big/2, 0, 0), (big, big, big)),
                    ((0, 0, -big/2), (big, big, big))]
        elif abs(fraction - 0.5) < 1e-6:
            # keep z>=0
            cuts = [((0, 0, -big/2), (big, big, big))]
        else:
            raise ValueError(f"unsupported fraction: {fraction}")
    else:
        raise ValueError(f"only xz fractional arcs implemented")
    for translate, extents in cuts:
        box = trimesh.creation.box(extents=extents)
        box.apply_translation(translate)
        full = full.difference(box, engine='manifold')
    return full


def socket_at(open_end, axis_dir, length=SOCKET_DEPTH, overshoot=0.5):
    """Socket pocket cylinder.  `open_end` is the point where the pipe enters,
    `axis_dir` points INTO the connector along the bore axis."""
    axis_dir = np.asarray(axis_dir, dtype=float)
    axis_dir = axis_dir / np.linalg.norm(axis_dir)
    p_out = np.asarray(open_end) - axis_dir * overshoot
    p_in  = np.asarray(open_end) + axis_dir * length
    return cylinder_between(p_out, p_in, SOCKET_R)


def bore_along(p_open, axis_dir, leg_length=LEG_LENGTH, into_junction=5.0,
               overshoot=0.5):
    """Bore (small ID) cylinder running from the open end into the junction."""
    axis_dir = np.asarray(axis_dir, dtype=float)
    axis_dir = axis_dir / np.linalg.norm(axis_dir)
    p_out = np.asarray(p_open) - axis_dir * overshoot
    junction_point = np.asarray(p_open) + axis_dir * (leg_length + into_junction)
    return cylinder_between(p_out, junction_point, BORE_R)


# ---------------------------------------------------------------------------
#                        LATCH GEOMETRY
# ---------------------------------------------------------------------------
def port_frame(open_end, axis_dir):
    """4x4 transform from the local port frame (z into the fitting, origin at
    the mouth) to world."""
    d = np.asarray(axis_dir, float)
    d = d / np.linalg.norm(d)
    T = trimesh.geometry.align_vectors([0, 0, 1], d)
    T[:3, 3] = np.asarray(open_end, float)
    return T


def _revolve(profile_rz, sections=SEG_CYL):
    """Solid of revolution about z from a closed (r, z) outline."""
    p = np.asarray(profile_rz, float)
    if not np.allclose(p[0], p[-1]):
        p = np.vstack([p, p[:1]])
    return trimesh.creation.revolve(p, sections=sections)


def _sector(r0, r1, a0, a1, z0, z1):
    """Annular sector (angles in radians about z), extruded from z0 to z1."""
    import shapely.geometry as sg
    from trimesh.creation import extrude_polygon
    n = max(int(np.degrees(a1 - a0) / 1.5), 4)
    a = np.linspace(a0, a1, n + 1)
    pts = np.vstack([np.column_stack([r1 * np.cos(a), r1 * np.sin(a)]),
                     np.column_stack([r0 * np.cos(a[::-1]), r0 * np.sin(a[::-1])])])
    m = extrude_polygon(sg.Polygon(pts), height=z1 - z0)
    m.apply_translation((0, 0, z0))
    return m


def _arc(length, radius=COLLAR_R):
    """Arc length at `radius` -> angle in radians."""
    return length / radius


def _lug_angles(count=None):
    n = count or LATCH_COUNT
    return [2 * np.pi * k / n for k in range(n)]


def collar_local():
    """Raised latch collar, local frame. Tapers back into the leg at 45 deg
    so there is no flat ledge to print or snag."""
    r_in = SOCKET_R + 0.5            # buried in the wall: fuses cleanly
    return _revolve([(r_in, 0.0), (COLLAR_R, 0.0), (COLLAR_R, COLLAR_L),
                     (OUTER_R - 0.3, COLLAR_L + COLLAR_T + 0.3),
                     (r_in, COLLAR_L + COLLAR_T + 0.3)])


def slot_cutter_local(R=COLLAR_R, count=None):
    """Everything cut from a collar of radius R: entry channels, runs, minus
    detents. R defaults to the fitting collar; rooms pass their own."""
    floor = R - SLOT_DEPTH
    hw = _arc(LUG_W / 2 + SLOT_CIRC_CL, R)      # half-width of the channel
    rot = np.radians(LATCH_ROT_DEG)
    r0, r1 = floor, R + 1.0
    z_run0 = LATCH_Z - SLOT_AX_CL
    z_run1 = LATCH_Z + LUG_L + SLOT_AX_CL
    parts, bumps = [], []
    for a in _lug_angles(count):
        parts.append(_sector(r0, r1, a - hw, a + hw, -1.0, z_run1))       # entry
        parts.append(_sector(r0, r1, a - hw, a + rot + hw, z_run0, z_run1))  # run
        # Detent: a cylinder standing parallel to the axis, sunk so only
        # DETENT_H of it rises above the slot floor. Its crest sits just
        # behind the trailing edge of the locked lug.
        foot = np.sqrt(DETENT_R**2 - (DETENT_R - DETENT_H)**2)
        ad = a + rot - _arc(LUG_W / 2 + SLOT_CIRC_CL * 0.5 + foot, R)
        rc = floor + DETENT_H - DETENT_R
        b = trimesh.creation.cylinder(radius=DETENT_R, height=z_run1 - z_run0 + 2,
                                      sections=32)
        b.apply_translation((rc * np.cos(ad), rc * np.sin(ad),
                             (z_run0 + z_run1) / 2))
        bumps.append(b)
    return difference(union(parts), union(bumps))


def lugs_local(R=COLLAR_R, count=None, skirt_ri=None):
    """Male lugs for a collar of radius R, local frame at the ENTRY angle
    (twist +LATCH_ROT_DEG to lock). The bearing face (z = LATCH_Z) is flat;
    it is what holds the cap on."""
    hw = _arc(LUG_W / 2, R)
    s_ri = R + SKIRT_CL if skirt_ri is None else skirt_ri
    return union([_sector(R - SLOT_DEPTH + LUG_RAD_CL, s_ri + 0.4,
                          a - hw, a + hw, LATCH_Z, LATCH_Z + LUG_L)
                  for a in _lug_angles(count)])


def latch_parts(open_end, axis_dir):
    """(solid to add, solid to cut) for one female port, in world coords."""
    if not LATCH_ENABLE:
        return [], []
    T = port_frame(open_end, axis_dir)
    c = collar_local(); c.apply_transform(T)
    s = slot_cutter_local(); s.apply_transform(T)
    return [c], [s]


def with_latches(outer_parts, inner_parts, ports):
    """Union the collars into the body and the slots into the cutter."""
    add, cut = [], []
    for p_open, p_dir in ports:
        a, c = latch_parts(p_open, p_dir)
        add += a
        cut += c
    return drop_slivers(difference(union(list(outer_parts) + add),
                                   union(list(inner_parts) + cut)))


def drop_slivers(mesh, min_vol=1.0):
    """Remove zero-volume shells left by coplanar booleans. Never silently
    drops real geometry: raises if more than one solid body survives."""
    bodies = mesh.split(only_watertight=False)
    keep = [b for b in bodies if abs(b.volume) > min_vol]
    if len(keep) != 1:
        raise RuntimeError(f"expected 1 solid body, got {len(keep)}")
    return keep[0] if len(bodies) > 1 else mesh


def outer_leg(p_open, axis_dir, length=LEG_LENGTH):
    """Outer body cylinder for a leg."""
    axis_dir = np.asarray(axis_dir, dtype=float)
    axis_dir = axis_dir / np.linalg.norm(axis_dir)
    # Overlap 0.3 mm into the bend/junction: a leg ending exactly flush with
    # the torus cut face leaves coplanar faces and zero-volume sliver shells.
    return cylinder_between(np.asarray(p_open),
                            np.asarray(p_open) + axis_dir * (length + 0.3),
                            OUTER_R)


# ===========================================================================
#                   PORT GENDER TOGGLES  +  OPTIONS
# ===========================================================================
# Every port on every fitting can be 'F' or 'M':
#   'F'  socket + latch collar. Takes an acrylic tube, a cap, a shim, or a
#        male port on another fitting.
#   'M'  built-in shim end (plug + lugged skirt). Plugs straight into another
#        fitting's F port, so two fittings join with no shim and no tube.
# Port order and names per fitting are in PORT_NAMES. The viewer labels the
# ports on screen only; nothing is ever embossed into the STL.
PORT_NAMES = {
    'elbow':     ['A', 'B'],             # A = the leg on the bed, B = the turned leg
    'coupler':   ['A', 'B'],
    'vent_tube': ['A', 'B'],
    'tee':       ['A', 'B', 'C'],        # A, B = the run, C = the branch
    'u_bend':    ['A', 'B'],
    'slide_gate': ['A', 'B'],            # A = on the bed
    'y_fitting': ['T', 'L', 'R'],        # trunk, left branch, right branch
    'flange':    ['A'],
    'cap':       ['A'],
}
PORT_GENDER = {                          # the build defaults - edit freely
    'elbow': 'FF', 'coupler': 'FF', 'vent_tube': 'FF', 'tee': 'FFF',
    'u_bend': 'FF', 'y_fitting': 'FFF', 'flange': 'F', 'slide_gate': 'FF', 'cap': 'M',
}
ELBOW_ANGLE   = 90.0          # any angle 0 < a <= 180
ELBOW_ANGLES  = [22.5, 30.0, 45.0, 60.0, 90.0]   # the set the viewer offers
VENT = {                      # vent lattice on the body, away from the ports
    'elbow': False, 'u_bend': False, 'coupler': False, 'vent_tube': True,
    'tee': False, 'y_fitting': False,
}
VENT_STYLE    = 'scale'       # 'scale' = snake-scale diamonds, 'hex' = honeycomb
VENT_STYLES   = ['scale', 'hex']
VENT_HOLE     = 8.0           # hole width on the INSIDE (what she touches)
VENT_STRUT    = 3.0           # solid between holes, on the inside surface
VENT_FLARE    = 12.0          # deg: holes widen outward -> every inside edge is
                              # obtuse (102 deg), none sharp, and the view in is wider
VENT_MIN      = 3.0           # holes that would shrink below this are left out
VENT_STRUT_OUT = 1.5          # thinnest strut allowed on the OUTSIDE surface
VENT_MARGIN   = 2.0           # solid band before each collar
VENT_JUNC     = 5.0           # (legacy near_leg band - no longer used by tee/wye)
VENT_SEAM     = 2.0           # solid band kept between a hole and another leg's wall
VENT_SEAM_SHRINK = (1.0, 0.85, 0.7, 0.55, 0.45)   # hole sizes tried near a seam
VENT_MALE_MARGIN = 4.0        # solid from a MALE port's mouth (no collar in the body)


def vm(g):
    """Vent margin from a port's mouth: past the latch collar for F, short for M."""
    return (COLLAR_L + COLLAR_T + 0.3 + VENT_MARGIN) if g.upper() == 'F' else VENT_MALE_MARGIN
VENT_TUBE_L   = 150.0         # straight vent section, mouth to mouth


def male_port(open_end, axis_dir):
    """Built-in male end at a port -> (solid to ADD, cutter to REMOVE).

    In the port frame the fitting body sits at z > 0; the band and the male
    half stick OUT (z < 0), exactly like the second side of a shim, and the
    mating fitting's mouth sits at z = -SHIM_BAND_T.

    Added as SOLID (the plug is a full cylinder) before the difference, and
    the bore is then cut through leg + band + plug by ONE cutter coaxial with
    the leg's own bore cutter (same direction -> same polygon phase). Adding a
    hollow ring afterwards leaves near-coincident bore surfaces that turn into
    slivers on tilted axes (non-90 elbows, wye branches)."""
    t = SHIM_BAND_T
    plug_ro = (PIPE_OD - CAP_PLUG_CL) / 2
    plug_l = SOCKET_DEPTH - 0.5
    sro = male_skirt_ro()
    local = [_revolve([(0, -t), (sro, -t), (sro, 0.4), (0, 0.4)])]   # band
    half = male_parts(SHIM_SKIRT_L, -t / 2, solid_plug=True)
    M = shim_side_frame()
    for m in half:
        m = m.copy(); m.apply_transform(M); local.append(m)
    solid = union(local)
    solid.apply_transform(port_frame(open_end, axis_dir))
    d = np.asarray(axis_dir, float); d /= np.linalg.norm(d)
    o = np.asarray(open_end, float)
    # 0.06 mm under the bore: where this cutter overlaps the leg's own bore
    # it sits strictly inside it, with room to spare for the leg's facets
    # (0.02 was inside the facet sag of the swept bend tube - 0.004 mm). Two coincident cylinders (same radius,
    # axis and facets) union into sliver edges at random - it broke the MM
    # scale-vent elbow. A 0.02 mm step is far below print resolution.
    cutter = cylinder_between(o - d * (t + plug_l + 2.0), o + d * 2.0, BORE_R - 0.06)
    return solid, cutter


def male_tip(open_end, axis_dir):
    """Where a male port ends, for labels."""
    d = np.asarray(axis_dir, float); d /= np.linalg.norm(d)
    return np.asarray(open_end, float) - d * (SHIM_BAND_T + SHIM_SKIRT_L)


def assemble(outer, inner, ports, genders, vent_cutters=()):
    """Turn a bare body into a finished fitting.
    outer/inner: solids (inner = bores only, NO sockets).
    ports: [(open_end, axis_into_fitting)], genders: 'F'/'M' per port."""
    genders = genders.upper()
    assert len(genders) == len(ports), (genders, len(ports))
    add, cut = [], []
    for (p, d), g in zip(ports, genders):
        if g == 'F':
            cut.append(socket_at(p, d))
            a, c = latch_parts(p, d)
            add += a; cut += c
        elif g == 'M':
            a, c = male_port(p, d)
            add.append(a); cut.append(c)
        else:
            raise ValueError(f"port gender must be F or M, got {g!r}")
    body = difference(union(list(outer) + add),
                      union(list(inner) + cut + list(vent_cutters)))
    return drop_slivers(body)


def assemble_vented(outer, inner, ports, genders, cut_fn):
    """assemble() with a vent lattice, proven printable. The hole ring can
    fall into step with the tube's facets (16 holes around, 96 facets) and
    leave a hole corner a hair off a facet edge, which saves as a broken STL.
    Try tiny rotations of the pattern (VENT_PHASES, fractions of a hole
    pitch - under half a degree) until the part passes export_ready()."""
    last = None
    for ph in VENT_PHASES:
        try:
            m = assemble(outer, inner, ports, genders, cut_fn(ph))
            export_ready(m)
            return m
        except RuntimeError as e:
            last = e
    raise RuntimeError(f"vent lattice: no clean pattern phase ({last})")


def port_labels(ports, genders, names):
    """[{label, g, pos}] for the viewer. pos = mouth (F) or male tip (M)."""
    out = []
    for (p, d), g, n in zip(ports, genders.upper(), names):
        pos = np.asarray(p, float) if g == 'F' else male_tip(p, d)
        out.append(dict(label=n, g=g, pos=[round(float(x), 2) for x in pos]))
    return out


# ---------------------------------------------------------------------------
#                             VENT HOLES
# ---------------------------------------------------------------------------
def _tile(style):
    """One lattice tile + hole (shapely, u = around the tube, v = along it,
    mm on the INSIDE surface). Returns (hole polygon, pitch_u, pitch_v, row
    offset in u for odd rows). Holes are the tile inset by half a strut,
    with rounded corners - softer look, stronger struts, no sharp points."""
    import shapely.geometry as sg
    w = VENT_HOLE + VENT_STRUT                    # tile width across u
    if style == 'hex':                            # pointy ends along the tube
        h = 2 * w / np.sqrt(3)
        tile = sg.Polygon([(0, h / 2), (w / 2, h / 4), (w / 2, -h / 4),
                           (0, -h / 2), (-w / 2, -h / 4), (-w / 2, h / 4)])
        pv = 0.75 * h
    elif style == 'scale':                        # diamonds, long along the tube
        h = w * 1.7
        tile = sg.Polygon([(0, h / 2), (w / 2, 0), (0, -h / 2), (-w / 2, 0)])
        pv = h / 2
    else:
        raise ValueError(style)
    hole = tile.buffer(-VENT_STRUT / 2, join_style=2).buffer(0.9, join_style=1)\
               .buffer(-0.9, join_style=1)        # inset, then round the corners
    return hole, w, pv, w / 2


VENT_PHASES = [0.0, 0.013, 0.029, 0.047, 0.071]   # tiny pattern rotations, tried in turn


def vent_path(segments, style=None, r_in=None, r_out=None,
              margin_start=None, margin_end=None, keep=None, phase=0.0, avoid=None):
    """Lattice of flared holes along a tube centreline.

    segments: [('line', p0, p1), ('arc', R, th0, th1)] in order; an arc is a
    bend in the xz plane about the y axis (centreline radius R).

    The lattice is laid out FLAT - u around the tube (mm at the bore), s along
    the centreline - and every hole corner is WRAPPED onto the tube through
    the same map. So on a bend the whole lattice compresses on the inside and
    stretches on the outside together and its lines stay continuous; they no
    longer kink where holes were resized individually. Where the lattice is
    compressed, holes shrink about their own centres (lines still line up) so
    the struts keep their full width; holes that would get too small are left
    out, so the inside of a tight bend stays solid.

    Holes flare outward (VENT_FLARE): every inside edge is obtuse.
    keep(point_on_bore) -> bool can veto holes.
    avoid: other legs as solid cylinders [(origin, dir, t0, t1)], radius
    OUTER_R. A hole is kept only if its WHOLE cutter (every edge, through the
    full wall depth) stays VENT_SEAM clear of them - so holes run right up to
    a tee/wye seam instead of stopping a fixed distance from it."""
    style = style or VENT_STYLE
    r_in = BORE_R if r_in is None else r_in
    r_out = OUTER_R if r_out is None else r_out
    base = COLLAR_L + COLLAR_T + 0.3 + VENT_MARGIN
    m0 = base if margin_start is None else margin_start
    m1 = base if margin_end is None else margin_end
    hole, pu, pv, off = _tile(style)
    hv = hole.bounds[3] - hole.bounds[1]
    xy = np.asarray(hole.exterior.coords)[:-1]
    k = np.tan(np.radians(VENT_FLARE))
    # frames over the path's arc length
    segs, total = [], 0.0
    for sgm in segments:
        if sgm[0] == 'line':
            p0, p1 = np.asarray(sgm[1], float), np.asarray(sgm[2], float)
            L = np.linalg.norm(p1 - p0); segs.append(('line', total, L, p0, (p1 - p0) / L))
        else:
            R, a0, a1 = sgm[1], sgm[2], sgm[3]
            L = R * (a1 - a0); segs.append(('arc', total, L, R, a0))
        total += L
    # a frame whose e1 never flips: for a line not in a bend, pick e1 from a
    # fixed reference so straight parts (tee/wye legs) are well defined
    def frame(s):
        s = min(max(s, 0.0), total)
        for n_, (kind, s0, L, *a) in enumerate(segs):
            if s <= s0 + L + 1e-9 or n_ == len(segs) - 1:
                t_ = s - s0
                if kind == 'line':
                    p0, d = a
                    c = p0 + d * t_; t = d; kap = 0.0
                else:
                    R, a0 = a
                    th = a0 + t_ / R
                    c = np.array([R * np.cos(th), 0, R * np.sin(th)])
                    t = np.array([-np.sin(th), 0, np.cos(th)]); kap = 1.0 / R
                ref = np.array([0, 1.0, 0])
                if abs(np.dot(ref, t)) > 0.9:
                    ref = np.array([1.0, 0, 0])
                e2 = ref - np.dot(ref, t) * t; e2 /= np.linalg.norm(e2)
                e1 = np.cross(e2, t)               # outward from any xz-plane bend centre
                return c, t, e1, e2, kap

    def wrap(s, phi, rho):
        c, t, e1, e2, _ = frame(s)
        return c + rho * (np.cos(phi) * e1 + np.sin(phi) * e2)

    usable = total - m0 - m1
    rows = int((usable - hv) // pv) + 1
    if rows < 1:
        return []
    s_first = m0 + (usable - (rows - 1) * pv) / 2
    r_mid = (r_in + r_out) / 2
    n_ring = max(int(2 * np.pi * r_in // pu), 6)
    su = (2 * np.pi * r_in / n_ring) / pu              # stretch u to close the ring
    out = []
    for i in range(rows):
        sc = s_first + i * pv
        _, _, _, _, kap = frame(sc)
        for kk in range(n_ring):
            ph = 2 * np.pi * (kk + 0.5 * (i % 2) + phase) / n_ring
            kc = kap * np.cos(ph)
            loc = 1.0 + kc * r_in                          # squish on the inside surface
            f = _hole_f(style, kc, su)
            if f * hv * loc < VENT_MIN or f < 0.35:
                continue
            centre = wrap(sc, ph, r_in)
            if keep is not None and not keep(centre):
                continue
            # near a tee/wye seam, shrink the hole in steps until it clears
            for shrink in ((1.0,) if not avoid else VENT_SEAM_SHRINK):
                ff = f * shrink
                if ff * hv * loc < VENT_MIN:
                    break
                pts = []
                for rho in (r_in - 1.0, r_out + 1.5):
                    g = 1.0 + 2 * k * (rho - r_in) / VENT_HOLE
                    for u, v in xy:
                        uu = u * su * ff * g; vv = v * ff * g
                        pts.append(wrap(sc + vv, ph + uu / r_in, rho))
                pts = np.asarray(pts)
                if not avoid or _clear_of(pts, len(xy), avoid):
                    out.append(trimesh.convex.convex_hull(pts))
                    break
    return out


def _clear_of(pts, n, cyls, m=None):
    """pts = two rings of n hole corners (inner, outer). Densify (edge
    subdivisions x wall depth) and test against each solid cylinder grown by m."""
    m = VENT_SEAM if m is None else m
    a, b = pts[:n], pts[n:]
    # rings run r_in-1 .. r_out+1.5. Inside the own wall the cutter only
    # removes own wall (other legs' walls that overlap it are the same solid),
    # and inside the own bore it cuts nothing. What must not be touched is
    # another leg's wall where it stands PROUD of this leg's outer surface -
    # so test from the own outer surface outward.
    w_out = (OUTER_R - BORE_R + 1.0) / (OUTER_R + 1.5 - BORE_R + 1.0)
    rings = [a + (b - a) * w for w in np.linspace(w_out, 1.0, 4)]
    q = []
    for r in rings:
        nx = np.roll(r, -1, axis=0)
        for w in (0.0, 0.25, 0.5, 0.75):
            q.append(r + (nx - r) * w)
        q.append(r.mean(0, keepdims=True))
    q = np.vstack(q)
    for cyl in cyls:
        o, d, t0, t1 = cyl[:4]
        b0 = cyl[4] if len(cyl) > 4 else None      # bore starts here (t); None = no bore test
        d = np.asarray(d, float); d = d / np.linalg.norm(d)
        v = q - np.asarray(o, float)
        t = v @ d
        perp = np.linalg.norm(v - t[:, None] * d, axis=1)
        hit = (t > t0 - m) & (t < t1 + m) & (perp < OUTER_R + m)
        if b0 is not None:                         # inside that leg's hollow bore = empty, fine
            hit &= ~((perp < BORE_R - m) & (t > b0 + m) & (t < t1))
        if np.any(hit):
            return False
    return True


_HOLE_F_CACHE = {}


def _hole_f(style, kc, su):
    """Largest hole scale (0..1, about the hole's centre) whose struts stay
    >= VENT_STRUT on the inside surface and >= VENT_STRUT_OUT on the outside,
    measured to all six neighbours of the lattice as it actually sits there:
    squished or stretched along the tube by loc(rho) = 1 + kc*rho (kc =
    curvature * cos(angle around the tube)), widened around it by rho/r_in,
    and with the outward flare. The old rule scaled from the row spacing
    alone - with nested rows (scale, hex) it barely shrank anything and the
    struts on the inside of a bend thinned to ~2 mm."""
    import shapely.affinity as sa
    key = (style, round(kc * 1000, 1), round(su, 4))
    if key in _HOLE_F_CACHE:
        return _HOLE_F_CACHE[key]
    hole, pu, pv, _ = _tile(style)
    k = np.tan(np.radians(VENT_FLARE))
    checks = []
    for rho, need in ((BORE_R, VENT_STRUT), (OUTER_R, VENT_STRUT_OUT)):
        loc = 1.0 + kc * rho
        wu = rho / BORE_R
        g = 1.0 + 2 * k * (rho - BORE_R) / VENT_HOLE
        checks.append((loc, wu, g, need))

    def ok(f):
        for loc, wu, g, need in checks:
            if loc <= 0.05:
                return False
            H = sa.scale(hole, su * f * g * wu, f * g * loc, origin=(0, 0))
            for du, dv in ((pu, 0), (pu / 2, pv), (-pu / 2, pv)):
                N = sa.translate(H, du * su * wu, dv * loc)
                if H.distance(N) < need - 1e-3:
                    return False
        return True
    if ok(1.0):
        f = 1.0
    else:
        lo, hi = 0.0, 1.0
        for _ in range(18):
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if ok(mid) else (lo, mid)
        f = lo
    _HOLE_F_CACHE[key] = f
    return f


def near_leg(p, origin, direction, margin=None):
    """True if point p is within the junction band of a leg (a cylinder of
    OUTER_R starting at `origin` along `direction`)."""
    margin = VENT_JUNC if margin is None else margin
    d = np.asarray(direction, float); d /= np.linalg.norm(d)
    q = np.asarray(p, float) - np.asarray(origin, float)
    t = np.dot(q, d)
    if t < -(margin + OUTER_R * 0.2):
        return False
    return np.linalg.norm(q - t * d) < OUTER_R + margin


# ===========================================================================
#                             FITTINGS
# ===========================================================================
def bend_arc(major, minor, theta):
    """Torus section in the xz plane: centreline starts at (major, 0, 0)
    heading +z and sweeps `theta` radians toward -x. Capped, watertight."""
    import shapely.geometry as sg
    from trimesh.creation import extrude_polygon
    full = trimesh.creation.torus(major_radius=major, minor_radius=minor,
                                  major_sections=SEG_TORUS_MAJOR,
                                  minor_sections=SEG_TORUS_MINOR)
    full.apply_transform(tf.rotation_matrix(np.pi / 2, (1, 0, 0)))
    big = 4 * (major + minor)
    a = np.linspace(0, theta, max(int(np.degrees(theta) / 5), 2) + 1)
    wedge2d = sg.Polygon([(0, 0)] + [(big * np.cos(t), big * np.sin(t)) for t in a])
    w = extrude_polygon(wedge2d, height=big)
    w.apply_translation((0, 0, -big / 2))
    w.apply_transform(tf.rotation_matrix(np.pi / 2, (1, 0, 0)))  # (x,y)->(x,z)
    return full.intersection(w, engine='manifold')


def bend_path(segments, extend=0.0):
    """Centreline samples [(point, e1, e2)] for a path of straight legs and
    xz-plane arcs (same segment format as vent_path). Arcs are sampled at the
    torus density; e1/e2 are the same frame vent_path uses, so the tube's
    facets and the vent lattice share one parametrisation. `extend` pushes
    both ends out along the path (bore cutters overshoot the mouths)."""
    out = []
    for n_, sg_ in enumerate(segments):
        if sg_[0] == 'line':
            p0, p1 = np.asarray(sg_[1], float), np.asarray(sg_[2], float)
            t = (p1 - p0) / np.linalg.norm(p1 - p0)
            e2 = np.array([0, 1.0, 0]) if abs(t[1]) < 0.9 else np.array([1.0, 0, 0])
            e2 = e2 - np.dot(e2, t) * t; e2 /= np.linalg.norm(e2)
            e1 = np.cross(e2, t)
            if n_ == 0:
                out.append((p0 - t * extend, e1, e2))
            out.append((p1 + (t * extend if n_ == len(segments) - 1 else 0), e1, e2))
        else:
            R, a0, a1 = sg_[1], sg_[2], sg_[3]
            k = max(int(np.ceil(SEG_TORUS_MAJOR * (a1 - a0) / (2 * np.pi))), 2)
            for th in np.linspace(a0, a1, k + 1)[1:-1]:
                c = np.array([R * np.cos(th), 0, R * np.sin(th)])
                t = np.array([-np.sin(th), 0, np.cos(th)])
                e2 = np.array([0, 1.0, 0]); e1 = np.cross(e2, t)
                out.append((c, e1, e2))
    return out


def tube_along(samples, radius, sections=SEG_CYL):
    """One seamless, capped tube through the samples: an exact circle square
    to the path at every sample, rings joined by quads. Replaces legs +
    torus unions, whose 0.3 mm overlap left near-coincident surfaces that a
    vent hole cutting across the seam turned into hair-thin shards."""
    a = np.linspace(0, 2 * np.pi, sections, endpoint=False)
    rings = [c + radius * (np.cos(a)[:, None] * e1 + np.sin(a)[:, None] * e2)
             for c, e1, e2 in samples]
    V = np.vstack(rings + [samples[0][0][None], samples[-1][0][None]])
    n, m = len(rings), sections
    F = []
    for i in range(n - 1):
        for j in range(m):
            a0, a1 = i * m + j, i * m + (j + 1) % m
            b0, b1 = a0 + m, a1 + m
            F += [(a0, a1, b1), (a0, b1, b0)]
    c0, c1 = n * m, n * m + 1
    for j in range(m):
        F.append((c0, (j + 1) % m, j))
        F.append((c1, (n - 1) * m + j, (n - 1) * m + (j + 1) % m))
    mesh = trimesh.Trimesh(V, np.array(F), process=True)
    if mesh.volume < 0:
        mesh.invert()
    return mesh


def _elbow_parts(angle_deg=None, radius=None):
    th = np.radians(angle_deg if angle_deg is not None else ELBOW_ANGLE)
    R = radius if radius is not None else BEND_R
    L = LEG_LENGTH
    A_open, A_dir = (R, 0, -L), (0, 0, 1)
    end = np.array([R * np.cos(th), 0, R * np.sin(th)])
    tang = np.array([-np.sin(th), 0, np.cos(th)])
    B_open, B_dir = end + tang * L, -tang
    path = [('line', A_open, (R, 0, 0)), ('arc', R, 0.0, th), ('line', end, B_open)]
    outer = [tube_along(bend_path(path), OUTER_R)]
    inner = [tube_along(bend_path(path, extend=0.5), BORE_R)]
    return outer, inner, [(A_open, A_dir), (B_open, B_dir)], (R, th)


def make_elbow(genders=None, angle=None, vent=None, radius=None, labels=False, style=None):
    """Elbow, any angle (ELBOW_ANGLE). Two ports, A on the bed leg, B turned."""
    g = genders or PORT_GENDER['elbow']
    outer, inner, ports, (R, th) = _elbow_parts(angle, radius)
    v = VENT['elbow'] if vent is None else vent
    (A, _), (B, dB) = ports
    end = np.array([R * np.cos(th), 0, R * np.sin(th)])
    if v:
        m = assemble_vented(outer, inner, ports, g, lambda ph: vent_path(
            [('line', A, (R, 0, 0)), ('arc', R, 0.0, th), ('line', end, B)], style, phase=ph,
            margin_start=vm(g[0]), margin_end=vm(g[1])))
    else:
        m = assemble(outer, inner, ports, g)
    return (m, port_labels(ports, g, PORT_NAMES['elbow'])) if labels else m


def make_elbow_90(genders=None, vent=None, labels=False, style=None):
    """90 degree elbow (the classic)."""
    return make_elbow(genders, 90.0, vent, labels=labels, style=style)


def make_coupler(genders=None, vent=None, labels=False, length=None, style=None):
    """Straight coupler, a port at each end."""
    g = genders or PORT_GENDER['coupler']
    L = length or 2 * LEG_LENGTH
    outer = [cylinder_between((0, 0, 0), (0, 0, L), OUTER_R)]
    inner = [cylinder_between((0, 0, -1), (0, 0, L + 1), BORE_R)]
    ports = [((0, 0, 0), (0, 0, 1)), ((0, 0, L), (0, 0, -1))]
    v = VENT['coupler'] if vent is None else vent
    if v:
        m = assemble_vented(outer, inner, ports, g, lambda ph: vent_path(
            [('line', (0, 0, 0), (0, 0, L))], style, phase=ph,
            margin_start=vm(g[0]), margin_end=vm(g[1])))
    else:
        m = assemble(outer, inner, ports, g)
    return (m, port_labels(ports, g, PORT_NAMES['coupler'])) if labels else m


def make_vent_tube(genders=None, vent=None, labels=False, style=None):
    """Straight vented section (VENT_TUBE_L): airflow + a look inside."""
    g = genders or PORT_GENDER['vent_tube']
    v = VENT['vent_tube'] if vent is None else vent
    return make_coupler(g, v, labels, length=VENT_TUBE_L, style=style)


def make_tee(genders=None, labels=False, vent=None, style=None):
    """Tee: A-B run, C branch. Legs sized so tubes in A and C cannot collide."""
    g = genders or PORT_GENDER['tee']
    L = SOCKET_DEPTH + PIPE_OD / 2 + JUNCTION_CLEARANCE   # 71.55 mm
    ports = [((-L, 0, 0), (1, 0, 0)), ((L, 0, 0), (-1, 0, 0)), ((0, 0, L), (0, 0, -1))]
    outer = [cylinder_between((-L, 0, 0), (L, 0, 0), OUTER_R),
             cylinder_between((0, 0, 0), (0, 0, L), OUTER_R)]
    inner = [cylinder_between((-L - 1, 0, 0), (L + 1, 0, 0), BORE_R),
             cylinder_between((0, 0, -1), (0, 0, L + 1), BORE_R)]
    v = VENT['tee'] if vent is None else vent

    def cuts(ph):
        # the run, all the way through - but solid around the branch seam
        c = vent_path([('line', (-L, 0, 0), (L, 0, 0))], style, phase=ph,
                      margin_start=vm(g[0]), margin_end=vm(g[1]),
                      avoid=[((0, 0, 0), (0, 0, 1), 0.0, L, -1.0)])
        # the branch, down to the run - solid around the seam
        c += vent_path([('line', (0, 0, L), (0, 0, 0))], style, margin_end=0.0, phase=ph,
                       margin_start=vm(g[2]),
                       avoid=[((-L, 0, 0), (1, 0, 0), 0.0, 2 * L, -1.0)])
        return c
    m = assemble_vented(outer, inner, ports, g, cuts) if v else assemble(outer, inner, ports, g)
    return (m, port_labels(ports, g, PORT_NAMES['tee'])) if labels else m


def make_u_bend(genders=None, vent=None, labels=False, style=None):
    """180 degree U-bend: two parallel ports on a half torus."""
    g = genders or PORT_GENDER['u_bend']
    L = LEG_LENGTH
    A_open, A_dir = (BEND_R, 0, -L), (0, 0, 1)
    B_open, B_dir = (-BEND_R, 0, -L), (0, 0, 1)
    path = [('line', A_open, (BEND_R, 0, 0)), ('arc', BEND_R, 0.0, np.pi),
            ('line', (-BEND_R, 0, 0), B_open)]
    outer = [tube_along(bend_path(path), OUTER_R)]
    inner = [tube_along(bend_path(path, extend=0.5), BORE_R)]
    v = VENT['u_bend'] if vent is None else vent
    ports = [(A_open, A_dir), (B_open, B_dir)]
    if v:
        m = assemble_vented(outer, inner, ports, g, lambda ph: vent_path(
            [('line', A_open, (BEND_R, 0, 0)), ('arc', BEND_R, 0.0, np.pi),
             ('line', (-BEND_R, 0, 0), B_open)], style, phase=ph,
            margin_start=vm(g[0]), margin_end=vm(g[1])))
    else:
        m = assemble(outer, inner, ports, g)
    return (m, port_labels(ports, g, PORT_NAMES['u_bend'])) if labels else m


def make_y_fitting(genders=None, labels=False, vent=None, style=None):
    """Wye: trunk T plus branches L and R at +-45 degrees."""
    g = genders or PORT_GENDER['y_fitting']
    ba = np.deg2rad(45)
    bl = SOCKET_DEPTH + PIPE_OD / 2 + JUNCTION_CLEARANCE
    tl = LEG_LENGTH
    T_open, T_dir = (0, 0, -tl), (0, 0, 1)
    d1 = np.array([np.sin(ba), 0, np.cos(ba)]); d2 = np.array([-np.sin(ba), 0, np.cos(ba)])
    B1, B2 = bl * d1, bl * d2
    outer = [cylinder_between((0, 0, 0), T_open, OUTER_R),
             cylinder_between((0, 0, 0), B1, OUTER_R),
             cylinder_between((0, 0, 0), B2, OUTER_R)]
    inner = [bore_along(T_open, T_dir, leg_length=tl, into_junction=8.0),
             bore_along(B1, -d1, leg_length=bl, into_junction=8.0),
             bore_along(B2, -d2, leg_length=bl, into_junction=8.0)]
    ports = [(T_open, T_dir), (B2, -d2), (B1, -d1)]      # T, L (-x), R (+x)
    v = VENT['y_fitting'] if vent is None else vent
    legs = [(np.asarray(T_open, float), np.array([0, 0, -1.0])), (B1, d1), (B2, d2)]

    def cuts(ph):
        c = []
        for i, (mouth, out_dir) in enumerate(legs):
            others = [((0, 0, 0), legs[j][1], 0.0, float(np.linalg.norm(legs[j][0])), -8.0)
                      for j in range(3) if j != i]
            c += vent_path([('line', mouth, (0, 0, 0))], style, margin_end=0.0, phase=ph,
                           margin_start=vm(g[[0, 2, 1][i]]), avoid=others)
        return c
    m = assemble_vented(outer, inner, ports, g, cuts) if v else assemble(outer, inner, ports, g)
    return (m, port_labels(ports, g, PORT_NAMES['y_fitting'])) if labels else m


CAP_F_FLOOR = 3.0            # female cap: closed end behind the socket


def cap_female_local():
    """FEMALE cap in the port frame (mouth at z = 0, cap at z > 0): a short
    socket with the standard latch collar, closed by a floor right behind the
    socket. A male end plugs in, skirt over the collar, twist to lock - the
    same latch as every female port. Grip ribs on the barrel for the twist."""
    L = SOCKET_DEPTH + CAP_F_FLOOR
    outer = [cylinder_between((0, 0, 0), (0, 0, L), OUTER_R)]
    for k in range(CAP_GRIP_RIBS):
        a = 2 * np.pi * (k + 0.5) / CAP_GRIP_RIBS
        outer.append(_sector(OUTER_R - 0.3, OUTER_R + 1.0, a - _arc(0.8, OUTER_R),
                             a + _arc(0.8, OUTER_R), COLLAR_L + COLLAR_T + 1.0, L))   # down to the bed
    return assemble(outer, [], [((0, 0, 0), (0, 0, 1))], 'F')


def make_cap(genders=None, labels=False):
    """End cap. genders 'M' (default): the male cap below - closes a FEMALE
    port. 'F': a female cap - closes a MALE port. Both print closed end
    down, no supports."""
    g = (genders or PORT_GENDER['cap']).upper()[0]
    if g == 'F':
        m = cap_female_local()
        m.apply_transform(tf.rotation_matrix(np.pi, (1, 0, 0)))     # floor down
        L = SOCKET_DEPTH + CAP_F_FLOOR
        m.apply_translation((0, 0, L))
        lab = [dict(label='A', g='F', pos=[0.0, 0.0, round(L, 2)])]
    else:
        m = make_cap_male()
        lab = [dict(label='A', g='M', pos=[0.0, 0.0, round(float(m.bounds[1][2]), 2)])]
    return (m, lab) if labels else m


def make_cap_male():
    """Latching end cap - closes off any port.

    Plugs INTO the socket (a ring whose ID equals the bore, so the snake sees
    a smooth dead end with no ledge) and wraps AROUND the latch collar with a
    skirt carrying the male lugs. Push on, twist LATCH_ROT_DEG clockwise
    looking at the cap, click past the detent. Print disk-down, no supports.

    Built in the port frame: z = 0 is the fitting's mouth face, the fitting
    occupies z > 0, the disk sits at z < 0.
    """
    plug_ro = (PIPE_OD - CAP_PLUG_CL) / 2
    plug_l  = SOCKET_DEPTH - 0.5          # tip stops just short of the bore step
    z0 = -CAP_DISK_T
    body = [
        _revolve([(0, z0), (SKIRT_RO, z0), (SKIRT_RO, 0.0), (0, 0.0)]),     # disk
        _revolve([(SKIRT_RI, z0 + 0.5), (SKIRT_RO, z0 + 0.5),
                  (SKIRT_RO, SKIRT_L), (SKIRT_RI + 0.4, SKIRT_L),
                  (SKIRT_RI, SKIRT_L - 0.4)]),                              # skirt
        _revolve([(BORE_R, -0.5), (plug_ro, -0.5), (plug_ro, plug_l - 0.8),
                  (plug_ro - 0.8, plug_l), (BORE_R, plug_l)]),              # plug
    ]
    if LATCH_ENABLE:
        body.append(lugs_local())
    for k in range(CAP_GRIP_RIBS):
        a = 2 * np.pi * (k + 0.5) / CAP_GRIP_RIBS
        body.append(_sector(SKIRT_RO - 0.3, SKIRT_RO + 1.0,
                            a - _arc(0.8, SKIRT_RO), a + _arc(0.8, SKIRT_RO),
                            z0 + 0.6, SKIRT_L - 1.0))
    return union(body)


def male_skirt_ro(extra=None):
    e = MALE_FIT_EXTRA if extra is None else extra
    return SKIRT_RI + e + SKIRT_T


def male_parts(skirt_l, rib_z0, solid_plug=False, plug_l=None, extra=None):
    """One male latch side in the port frame (fitting at z > 0), shared by
    the shim, built-in male ports and the fit coupons: plug into the socket,
    skirt around the collar, lugs, grip ribs. Carries MALE_FIT_EXTRA and the
    MALE_LEADIN chamfers. Starts 0.5 mm below z = 0 to fuse into its band."""
    e = MALE_FIT_EXTRA if extra is None else extra
    cs, cp = MALE_LEADIN_SKIRT, MALE_LEADIN_PLUG
    s_ri = SKIRT_RI + e
    s_ro = s_ri + SKIRT_T
    plug_ro = (PIPE_OD - CAP_PLUG_CL) / 2 - e
    plug_l = SOCKET_DEPTH - 0.5 if plug_l is None else plug_l
    r0 = 0.0 if solid_plug else BORE_R
    body = [
        _revolve([(s_ri, -0.5), (s_ro, -0.5), (s_ro, skirt_l),
                  (s_ri + cs, skirt_l), (s_ri, skirt_l - cs)]),               # skirt
        _revolve([(r0, -0.5), (plug_ro, -0.5), (plug_ro, plug_l - cp),
                  (plug_ro - cp, plug_l), (r0, plug_l)]),                     # plug
    ]
    if LATCH_ENABLE:
        body.append(lugs_local(COLLAR_R, None, skirt_ri=s_ri))
    for k in range(CAP_GRIP_RIBS):
        a = 2 * np.pi * (k + 0.5) / CAP_GRIP_RIBS
        body.append(_sector(s_ro - 0.3, s_ro + 1.0,
                            a - _arc(0.8, s_ro), a + _arc(0.8, s_ro),
                            rib_z0, skirt_l - 1.0))
    return body


def _male_half(skirt_l, rib_z0):
    return male_parts(skirt_l, rib_z0)


def _male_half_old(skirt_l, rib_z0):
    """One male latch side in the port frame (fitting at z > 0): plug ring into
    the socket, skirt around the collar, lugs, grip ribs. Starts 0.5 mm below
    z = 0 so it fuses into whatever closes it off (cap disk / shim band)."""
    plug_ro = (PIPE_OD - CAP_PLUG_CL) / 2
    plug_l  = SOCKET_DEPTH - 0.5          # tip stops just short of the bore step
    body = [
        _revolve([(SKIRT_RI, -0.5), (SKIRT_RO, -0.5), (SKIRT_RO, skirt_l),
                  (SKIRT_RI + 0.4, skirt_l), (SKIRT_RI, skirt_l - 0.4)]),     # skirt
        _revolve([(BORE_R, -0.5), (plug_ro, -0.5), (plug_ro, plug_l - 0.8),
                  (plug_ro - 0.8, plug_l), (BORE_R, plug_l)]),              # plug
    ]
    if LATCH_ENABLE:
        body.append(lugs_local())
    for k in range(CAP_GRIP_RIBS):
        a = 2 * np.pi * (k + 0.5) / CAP_GRIP_RIBS
        body.append(_sector(SKIRT_RO - 0.3, SKIRT_RO + 1.0,
                            a - _arc(0.8, SKIRT_RO), a + _arc(0.8, SKIRT_RO),
                            rib_z0, skirt_l - 1.0))
    return body


IRIS_LAYER    = 0.2           # layer height interfaces snap to (shim print ring)
IRIS_ZGAP     = 0.2           # one-layer modelled support gap (shim print ring)
SHIM_BAND_T   = 4.0     # centre band: the gap between the two fitting mouths
SHIM_SKIRT_L  = SKIRT_L   # the cap's short skirt (a full-length sleeve bound up)
SHIM_PRINT_RING = True    # snap-off support ring under the lower skirt


def shim_side_frame():
    """Port frame of the shim's SECOND side (mouth at z = -SHIM_BAND_T, fitting
    extending toward -z). A rotation, not a mirror, so the lugs and the twist
    direction are identical on both sides as seen from each fitting."""
    M = tf.rotation_matrix(np.pi, (1, 0, 0))
    M[:3, 3] = (0, 0, -SHIM_BAND_T)
    return M


def shim_print_ring():
    """Snap-off support for printing the shim standing on side B's plug: a
    thin ring from the bed up to one layer under the lower skirt (the same
    modelled-support style as the waterfall ribs). It sits outside the plug,
    so it pulls straight off over the plug end after printing. Built in the
    shim's own frame."""
    t = SHIM_BAND_T
    s_ri = SKIRT_RI + MALE_FIT_EXTRA
    s_ro = s_ri + SKIRT_T
    bed = -t - (SOCKET_DEPTH - 0.5)                  # tip of side B's plug
    skirt_bottom = -t - SHIM_SKIRT_L
    top = bed + np.floor((skirt_bottom - bed - IRIS_ZGAP) / IRIS_LAYER + 1e-9) * IRIS_LAYER
    r0, r1 = s_ri + MALE_LEADIN_SKIRT + 0.1, s_ro - 0.1
    return _revolve([(r0, bed), (r1, bed), (r1, top), (r0, top)], sections=SEG_CYL)


def make_shim_print():
    """[shim, support ring] as printed - one STL, two bodies."""
    return [make_shim(), shim_print_ring()] if SHIM_PRINT_RING else [make_shim()]


def make_shim():
    """Fitting-to-fitting connector (no acrylic between them).

    Double-ended male latch: each side plugs into a socket and wraps that
    port's collar with a lugged skirt. Bore runs straight through at BORE_ID
    so the snake sees one smooth tube. Latch each fitting on with the usual
    push + twist. Print standing on either end, no supports.

    Built in side A's port frame: fitting A at z > 0, band at -SHIM_BAND_T..0,
    fitting B beyond (see shim_side_frame()).
    """
    t = SHIM_BAND_T
    sro = male_skirt_ro()
    band = _revolve([(BORE_R, -t), (sro, -t), (sro, 0.0), (BORE_R, 0.0)])
    a = _male_half(SHIM_SKIRT_L, -t / 2)
    b = [m.copy() for m in _male_half(SHIM_SKIRT_L, -t / 2)]
    M = shim_side_frame()
    for m in b:
        m.apply_transform(M)
    return drop_slivers(union([band] + a + b))


# ---------------------------------------------------------------------------
#   FLANGE (tank wall port) + BACK PLATE, optional NECK GATE
# ---------------------------------------------------------------------------
# Plain: the flange plate sits on the outside of the tank wall, its tube
# passes through the wall, the back plate slides over the tube on the inside;
# 4 M6 bolts clamp the wall between them.
#
# GATE variant - the blade crosses the tube 25 mm up the neck, square to it.
# Three prints:
#   OUTER plate  outside the wall, a 1.5 mm lip centres it in the wall hole.
#   GATE BODY    one piece: back plate (inside the wall), an even 45 deg taper
#                up to the gate block, the blade slot through the block (open
#                at the far end, roof printed as a bridge), then tube + port.
#   BLADE        slides in from the open end; a spring finger on each edge
#                clicks into a notch open and closed.
# 4 short M6 bolts clamp only the two plates and the wall (4 + wall + 4 + nut).
FLANGE_W          = 3.5 * 25.4     # standard plate (88.9)
FLANGE_T          = 4.0
FLANGE_HOLE_INSET = 10.0
FLANGE_HOLE_D     = 6.5            # M6
FLANGE_TUBE_L     = 42.0
FLANGE_WALL       = 3.0            # only the gap drawn in the viewer - nothing depends on it
GN_LIP     = 1.5                   # centring lip on the outer plate (fits in the wall hole, any wall >= 1.5)
BACK_HOLE_R       = SKIRT_RO + 1.0 + 0.7   # clears a female collar AND a male skirt + ribs

GN_A       = BORE_R + 4.0          # blade half-width: 4 mm over the bore each side
GN_CLR     = 0.3                   # blade in channel, per side (in the plane)
GN_BLADE_T = 3.0
GN_CH_T    = GN_BLADE_T + 0.8      # slot height: 0.4 each face (roof is a bridge, allow for sag)
GN_UP      = 25.0                  # blade centre above the inside wall face
GN_W       = 38.5                  # gate block half-width (slot walls 4.4 thick)
GN_Y0      = -37.6                 # frame near end (y)
GN_Y1      = 52.0                  # frame far end: the channel opens here
GN_BOLT    = (48.0, 32.0)          # wall bolts (+-x, +-y): clear of the frame for a socket wrench
GN_BOSS_R  = 8.5
GN_PLATE_T = 4.0                   # outer plate, back plate, neck base
GN_NECK_L  = 36.0                  # neck tube above its base, to the port mouth
GN_TRAVEL  = np.ceil(2 * BORE_R + 1.0 + (GN_A - BORE_R)) + 0.5   # bottom edge clears the bore by 1 mm
GN_DET_Y   = -21.0                 # spring bump (y) with the blade closed (open notch at +44.5)


def _plate_box(w, y0, y1, z0, z1):
    b = trimesh.creation.box(extents=(w, y1 - y0, z1 - z0))
    b.apply_translation((0, (y0 + y1) / 2, (z0 + z1) / 2))
    return b


def _bolt_holes(pitch, z0, z1, d=FLANGE_HOLE_D):
    out = []
    for hx, hy in [(pitch, pitch), (-pitch, pitch), (pitch, -pitch), (-pitch, -pitch)]:
        out.append(cylinder_between((hx, hy, z0), (hx, hy, z1), d / 2, sections=32))
    return out


def make_flange(genders=None, labels=False):
    """Square mounting flange (tank wall port) with one port on its tube."""
    g = genders or PORT_GENDER['flange']
    W, T = FLANGE_W, FLANGE_T
    total_h = T + FLANGE_TUBE_L
    outer = [_plate_box(W, -W / 2, W / 2, 0, T),
             cylinder_between((0, 0, 0), (0, 0, total_h), OUTER_R)]
    holes = [cylinder_between((0, 0, -1), (0, 0, total_h + 1), BORE_R)]
    holes += _bolt_holes(W / 2 - FLANGE_HOLE_INSET, -1, T + 1)
    ports = [((0, 0, total_h), (0, 0, -1))]
    m = assemble(outer, holes, ports, g)
    return (m, port_labels(ports, g, PORT_NAMES['flange'])) if labels else m


def make_back_plate():
    """Square back plate that slides over the flange's tube inside the tank."""
    W = FLANGE_W
    plate = _plate_box(W, -W / 2, W / 2, 0, FLANGE_T)
    holes = [cylinder_between((0, 0, -1), (0, 0, FLANGE_T + 1), BACK_HOLE_R)]
    holes += _bolt_holes(W / 2 - FLANGE_HOLE_INSET, -1, FLANGE_T + 1)
    return difference(plate, union(holes))


# ---- neck gate: 2D outlines (x across, y along the blade), z set per piece
def _gn_bolt_pts():
    bx, by = GN_BOLT
    return [(sx * bx, sy * by) for sx in (1, -1) for sy in (1, -1)]


def _gn_plate2d():
    """Outer plate / back plate outline: bolt ears, covers the bore."""
    import shapely.geometry as sg
    bx, by = GN_BOLT
    hy = max(by + GN_BOSS_R, OUTER_R + 8.6)
    return sg.box(-bx - GN_BOSS_R, -hy, bx + GN_BOSS_R, hy).buffer(-4, join_style=1).buffer(4, join_style=1)


def _gn_holes2d():
    import shapely.geometry as sg
    from shapely.ops import unary_union
    return unary_union([sg.Point(x, y).buffer(FLANGE_HOLE_D / 2, 32) for x, y in _gn_bolt_pts()])


def _gn_notch(y, side):
    """V notch in the channel wall (+x side=1 / -x side=-1), 45 deg flanks."""
    import shapely.geometry as sg
    u0, u1 = GN_A + GN_CLR - 0.05, GN_A + GN_CLR + GATE_NOTCH_D
    h = GATE_NOTCH_D + 1.3
    p = sg.Polygon([(u0, y - h), (u1, y - 0.5), (u1, y + 0.5), (u0, y + h)])
    return p if side > 0 else sg.Polygon([(-x, yy) for x, yy in p.exterior.coords])


def _gn_extrude(poly, z0, z1):
    from trimesh.creation import extrude_polygon
    if poly.geom_type == 'MultiPolygon':
        return union([_gn_extrude(g, z0, z1) for g in poly.geoms])
    m = extrude_polygon(poly, height=z1 - z0)
    m.apply_translation((0, 0, z0))
    return m


def gn_levels():
    """z of every interface, outer plate bottom = 0."""
    d = {}
    d['plate1'] = GN_PLATE_T                         # outer plate top = outside wall face
    d['wall1'] = d['plate1'] + FLANGE_WALL           # inside wall face = back plate bottom
    d['bp1'] = d['wall1'] + GN_PLATE_T               # back plate top
    d['blade'] = d['wall1'] + GN_UP                  # blade centre
    d['ch0'] = d['blade'] - GN_CH_T / 2              # channel floor
    d['zb'] = d['ch0'] - 2.5                         # gate block bottom = top of the taper
    d['top'] = d['blade'] + GN_CH_T / 2              # slot roof
    d['base1'] = d['top'] + GN_PLATE_T               # gate block top
    d['mouth'] = d['base1'] + GN_NECK_L              # port mouth
    return d


def gn_outer():
    """Outer plate (outside the wall) + a short centring lip that sits in the
    wall hole. Works for any wall thickness - only the bolts get longer."""
    d = gn_levels()
    plate = _gn_extrude(_gn_plate2d().difference(_gn_holes2d()), 0, d['plate1'])
    stub = cylinder_between((0, 0, d['plate1'] - 0.3), (0, 0, d['plate1'] + GN_LIP), OUTER_R)
    bore = cylinder_between((0, 0, -1), (0, 0, d['plate1'] + GN_LIP + 1), BORE_R)
    return difference(union([plate, stub]), bore)


def gn_body(genders=None):
    """Gate body, one print: back plate, even 45 deg taper, gate block with the
    blade slot (open at the far end), click notches, tube + port."""
    import shapely.geometry as sg
    d = gn_levels()
    bp, zb = d['bp1'], d['zb']
    plate = _gn_extrude(_gn_plate2d().difference(_gn_holes2d()), d['wall1'], bp)
    blk = sg.box(-GN_W, GN_Y0, GN_W, GN_Y1)
    h = zb - bp
    low = blk.buffer(-h, join_style=2)                       # even 45 deg on all four faces
    taper = trimesh.util.concatenate([_gn_extrude(blk, zb - 0.01, zb + 0.3),
                                      _gn_extrude(low, bp - 0.3, bp - 0.29)]).convex_hull
    block = _gn_extrude(blk, zb, d['base1'])
    tube_in = cylinder_between((0, 0, bp - 0.3), (0, 0, zb + 0.3), OUTER_R)
    outer = [plate, taper, tube_in, block,
             cylinder_between((0, 0, d['base1'] - 0.3), (0, 0, d['mouth']), OUTER_R)]
    ac = GN_A + GN_CLR
    ch2d = sg.box(-ac, -GN_A - GN_CLR, ac, GN_Y1 + 5)
    for y in (GN_DET_Y, GN_DET_Y + GN_TRAVEL):
        for sd in (1, -1):
            ch2d = ch2d.union(_gn_notch(y, sd))
    inner = [_gn_extrude(ch2d, d['ch0'], d['top']),
             cylinder_between((0, 0, d['wall1'] - 1), (0, 0, d['mouth'] + 1), BORE_R)]
    g = (genders or PORT_GENDER['flange']).upper()
    return assemble(outer, inner, gn_ports(), g)


def gn_ports():
    return [((0, 0, gn_levels()['mouth']), (0, 0, -1))]


def _gn_blade_2d():
    """Blade outline, CLOSED: covers the bore, pull tab beyond the housing,
    a spring finger on each edge, all corners rounded."""
    import shapely.geometry as sg
    import shapely.affinity as sa
    a = GN_A
    top = GN_Y1 + 3.0
    tab = sg.box(-a, top - 1, a, top + 20).buffer(-4, join_style=1).buffer(4, join_style=1)
    hole = sg.box(-16, top + 5, 16, top + 14).buffer(-4.4, join_style=1).buffer(4.4, join_style=1)
    body = sg.box(-a, -a, a, top).union(tab).difference(hole)
    fw, fl, fh = GATE_FINGER
    f = GN_DET_Y - 2.5; r = f + fl
    cut = sg.box(a - fw - 1.0, f - 1.0, a - fw, r).union(sg.box(a - fw - 1.0, f - 1.0, a + 1.0, f))
    bump = sg.Polygon([(a - 0.2, GN_DET_Y - fh - 0.2), (a + fh, GN_DET_Y), (a - 0.2, GN_DET_Y + fh + 0.2)])
    bump = bump.buffer(-0.35, join_style=1).buffer(0.35, join_style=1)
    for mside in (1, -1):
        c_, b_ = (cut, bump) if mside > 0 else (sa.scale(cut, -1, 1, origin=(0, 0)), sa.scale(bump, -1, 1, origin=(0, 0)))
        body = body.difference(c_).union(b_)
    return body.buffer(0.3, join_style=1).buffer(-0.3, join_style=1)


def gn_blade(beta=1.0):
    """Blade in place: beta 0 = OPEN (pulled out GN_TRAVEL), 1 = CLOSED."""
    d = gn_levels()
    m = _gn_extrude(_gn_blade_2d(), d['blade'] - GN_BLADE_T / 2, d['blade'] + GN_BLADE_T / 2)
    m.apply_translation((0, GN_TRAVEL * (1.0 - beta), 0))
    return m


def flange_set(genders=None, gate=False, beta=0.0):
    """[(name, mesh)] assembled, outer face at z = 0, wall = FLANGE_WALL gap.
    Plain: flange, back plate. Gate: outer plate, gate body, blade
    (beta 0 = open)."""
    if not gate:
        bp = make_back_plate(); bp.apply_translation((0, 0, FLANGE_T + FLANGE_WALL))
        return [('flange', make_flange(genders)), ('back_plate', bp)]
    return [('outer', gn_outer()), ('body', gn_body(genders)),
            ('blade', gn_blade(beta))]


def flange_labels(genders=None, gate=False):
    g = (genders or PORT_GENDER['flange']).upper()
    if not gate:
        return make_flange(g, labels=True)[1]
    return port_labels(gn_ports(), g, PORT_NAMES['flange'])


def make_pipe_hook():
    """Wall-mounted pipe hook — unified plate/cradle thickness + gusset.

    Plate and cradle wall share the same thickness so they read as one
    continuous piece. The plate is sized so the cradle sits in the upper
    portion: the below-cradle length carries the gusset and the bottom
    screw; the above-cradle length is just enough for the top screw plus
    a small edge margin.

    A triangular gusset under the cradle bottom carries the pipe weight
    directly back to the plate.

    Two #8 wood screw holes (5 mm clearance): one above the cradle, one
    below the gusset.
    """
    import shapely.geometry as sg
    from trimesh.creation import extrude_polygon

    # --- Unified plate/cradle thickness -----------------------------------
    thickness    = 6.5

    # --- Cradle -----------------------------------------------------------
    cradle_id    = PIPE_OD                       # 63.1 mm — snug fit
    cradle_wall  = thickness                     # 6.5 mm
    cradle_od    = cradle_id + 2 * cradle_wall   # 76.1 mm
    cradle_width = 40.0                          # along pipe axis (x)
    wrap_deg     = 200.0                         # 200° wrap → 160° opening

    # --- Back plate (top trimmed, bottom unchanged) ----------------------
    plate_w      = 70.0
    plate_t      = thickness                     # 6.5 mm
    plate_z_top  = 32.5                          # was +65
    plate_z_bot  = -65.0                         # unchanged — gusset stays
    plate_h      = plate_z_top - plate_z_bot     # 97.5 mm  (3/4 of 130)
    plate_z_c    = (plate_z_top + plate_z_bot) / 2

    hole_d       = 5.0                           # #8 wood screw clearance
    top_hole_z   = 22.0                          # above cradle, below new top
    bot_hole_z   = -50.0                         # unchanged

    # --- Cradle position --------------------------------------------------
    embed = 5.0
    y_pipe = plate_t + cradle_od / 2 - embed     # 39.55 (preserved)

    # --- Build back plate (asymmetric — top trimmed) ---------------------
    plate = trimesh.creation.box(extents=[plate_w, plate_t, plate_h])
    plate.apply_translation([0, plate_t / 2, plate_z_c])

    # --- Build cradle as extruded annular sector --------------------------
    open_half = (360.0 - wrap_deg) / 2
    a_start = np.deg2rad(90 + open_half)
    a_end   = np.deg2rad(90 - open_half + 360)
    n = 80
    out_a = np.linspace(a_start, a_end, n)
    in_a  = np.linspace(a_end, a_start, n)
    Ro, Ri = cradle_od / 2, cradle_id / 2
    out_pts = np.column_stack([y_pipe + Ro * np.cos(out_a), Ro * np.sin(out_a)])
    in_pts  = np.column_stack([y_pipe + Ri * np.cos(in_a),  Ri * np.sin(in_a)])
    poly    = sg.Polygon(np.vstack([out_pts, in_pts]))
    cradle  = extrude_polygon(poly, height=cradle_width)

    M = np.array([[0, 0, 1, 0],
                  [1, 0, 0, 0],
                  [0, 1, 0, 0],
                  [0, 0, 0, 1]], dtype=float)
    cradle.apply_transform(M)
    cradle.apply_translation([-cradle_width / 2, 0, 0])

    # --- Build load-bearing gusset under the cradle -----------------------
    gusset_top_z = -19.0                         # where cradle outer meets plate
    gusset_bot_z = -42.0                         # above bottom screw hole
    gusset_pts = np.array([
        [plate_t, gusset_top_z],
        [plate_t, gusset_bot_z],
        [y_pipe, -Ro],
    ])
    gusset_poly = sg.Polygon(gusset_pts)
    gusset = extrude_polygon(gusset_poly, height=cradle_width)
    gusset.apply_transform(M)
    gusset.apply_translation([-cradle_width / 2, 0, 0])

    # --- Combine and drill screw holes ------------------------------------
    body = union([plate, cradle, gusset])
    h_top = cylinder_between((0, -1, top_hole_z),
                             (0, plate_t + 1, top_hole_z), hole_d / 2)
    h_bot = cylinder_between((0, -1, bot_hole_z),
                             (0, plate_t + 1, bot_hole_z), hole_d / 2)
    return difference(body, union([h_top, h_bot]))


def make_latch_coupon():
    """Latch test coupon: one full-depth latched port on a short ring (~40 g).
    Print it with a cap to check the push-on, the twist, the detent click
    and the pull-off hold before committing to full fittings. Also checks
    that a real tube still slides into the socket past the collar."""
    # Full-depth socket, exactly like a real port: the cap and shim plugs run
    # SOCKET_DEPTH - 0.5 deep, so a shorter coupon socket would block them.
    L = SOCKET_DEPTH + 3.0
    outer = cylinder_between((0, 0, 0), (0, 0, L), OUTER_R)
    inner = union([cylinder_between((0, 0, -1), (0, 0, L + 1), BORE_R),
                   socket_at((0, 0, 0), (0, 0, 1))])
    return with_latches([outer], [inner], [((0, 0, 0), (0, 0, 1))])


def port_list(fam, angle=None, **_):
    """[(open_end, axis_into_fitting)] for a family, in the same order as
    PORT_NAMES - for tools and checks, derived from the same parameters."""
    L = LEG_LENGTH
    Lt = SOCKET_DEPTH + PIPE_OD / 2 + JUNCTION_CLEARANCE
    if fam == 'elbow':
        return _elbow_parts(angle)[2]
    if fam in ('coupler', 'vent_tube'):
        Lc = VENT_TUBE_L if fam == 'vent_tube' else 2 * L
        return [((0, 0, 0), (0, 0, 1)), ((0, 0, Lc), (0, 0, -1))]
    if fam == 'tee':
        return [((-Lt, 0, 0), (1, 0, 0)), ((Lt, 0, 0), (-1, 0, 0)), ((0, 0, Lt), (0, 0, -1))]
    if fam == 'u_bend':
        return [((BEND_R, 0, -L), (0, 0, 1)), ((-BEND_R, 0, -L), (0, 0, 1))]
    if fam == 'y_fitting':
        a = np.deg2rad(45)
        d1 = np.array([np.sin(a), 0, np.cos(a)]); d2 = np.array([-np.sin(a), 0, np.cos(a)])
        return [((0, 0, -L), (0, 0, 1)), (tuple(Lt * d2), tuple(-d2)), (tuple(Lt * d1), tuple(-d1))]
    if fam == 'flange':
        return [((0, 0, 46.0), (0, 0, -1))]
    raise KeyError(fam)


def make_male_fit_coupons():
    """Three short male rings - MALE_FIT_TEST extra clearance, 1, 2 and 3
    notches on the band rim - printed together, band down, like the cap.
    Push each onto a latch_coupon (or any port) and twist: set MALE_FIT_EXTRA
    to the one that goes on like the cap does. Separate bodies, one STL."""
    out = []
    for i, e in enumerate(MALE_FIT_TEST):
        sro = male_skirt_ro(e)
        band = _revolve([(BORE_R, -3.0), (sro, -3.0), (sro, 0.0), (BORE_R, 0.0)])
        parts = [band] + male_parts(SKIRT_L + 2.0, -2.5, plug_l=14.0, extra=e)
        m = union(parts)
        # i+1 notches cut in the band's rim, so the rings can't be mixed up
        notches = [_sector(sro - 1.2, sro + 2.0, a - _arc(1.0, sro), a + _arc(1.0, sro), -3.5, -1.5)
                   for a in [np.radians(90 + 14 * k) for k in range(i + 1)]]
        m = drop_slivers(difference(m, union(notches)))
        m.apply_translation(((i - 1) * (2 * sro + 12.0), 0, 3.0))
        out.append(m)
    return out


# ===========================================================================
#                    SLIDE GATE  (knife gate: the blade lives inside)
# ===========================================================================
# A straight fitting with a flat pocket ARM on one side. The blade lives in
# the arm: pulled out (OPEN) it sits entirely inside the arm and the tube is
# clear; pushed in (CLOSED) it crosses the bore and seats in a groove in the
# far wall. Move it with the knob that sticks out through a slot in the
# underside of the arm.
#
# It clicks into place at both ends: a springy finger on the blade's edge
# drops into a notch in the arm wall at OPEN and at CLOSED. The OPEN notch has
# a square back face, so the blade can't be pulled out of the arm - it is
# captive. To take it out (cleaning), push a paperclip into the small hole in
# the side of the arm (it presses the finger in) and pull the knob.
#
# Assembly: slide the blade into the open far end of the arm, knob through the
# knob slot, until it clicks (OPEN). That's it - 2 parts, no hardware.
#
# The blade crosses at GATE_TILT (45 deg) to the tube axis: the body prints
# standing on port A and the arm rises at 45 deg - every overhang is 45 deg,
# no supports. The blade prints flat, knob up.
GATE_TILT     = 45.0          # blade plane vs the tube axis (deg)
GATE_T        = 3.0           # blade thickness
GATE_CLR      = 0.25          # blade in its pocket, per side
GATE_GROOVE   = 1.4           # how far the blade reaches into the far wall
GATE_PAD      = 4.0           # arm wall
GATE_L        = 130.0         # mouth to mouth
GATE_ZC       = 66.0          # blade centre on the axis
GATE_TOP      = 70.0          # blade top (w) when closed
# knob: a STEM through the arm's slot and a wide rounded CAP outside it
GATE_STEM     = (12.0, 14.0)  # stem: width (u), length (w)
GATE_CAP      = (26.0, 22.0, 9.0, 4.0)   # cap: width, length, height, edge radius
GATE_GRIP     = 4             # grip grooves across the cap (push/pull direction)
# detent: a spring finger on EACH blade edge, bump into notches in the arm wall
GATE_FINGER   = (2.6, 18.0, 1.15)  # finger: width, length, bump height
GATE_NOTCH_D  = 1.3           # notch depth (> bump - clearance: it snaps fully home)


def _gate_dims():
    c = np.cos(np.radians(GATE_TILT))
    d = dict(c=c)
    d['a'] = BORE_R + GATE_GROOVE                        # blade half-width
    d['b'] = d['a'] / c                                  # blade tip (w) when closed
    d['T'] = np.ceil(BORE_R / c + 1.0 + d['b'])          # travel: tip clears the bore
    d['ap'] = d['a'] + GATE_CLR                          # pocket half-width
    d['tp'] = GATE_T / 2 + GATE_CLR                      # pocket half-thickness
    d['tb'] = d['tp'] + GATE_PAD                         # arm half-thickness
    d['Rb'] = d['ap'] + GATE_PAD                         # arm half-width
    d['wend'] = GATE_TOP + d['T'] + 2.0                  # arm far end (open)
    fw, fl, fh = GATE_FINGER
    d['f_root'] = GATE_TOP - 6.0
    d['f_free'] = d['f_root'] - fl
    d['bump'] = d['f_free'] + 2.5                        # bump peak, closed
    d['k_u'] = 0.0                                       # knob centre across (u)
    d['k_w'] = GATE_TOP - 1.0 - GATE_CAP[1] / 2          # knob centre along (w), closed
    return d


def _gate_frame():
    """4x4: blade-plane coords (u across, w out along the arm, n normal) -> world.
    w = 0 on the tube axis at GATE_ZC; the arm goes up and out (+y, +z)."""
    t = np.radians(GATE_TILT)
    X = np.array([1.0, 0, 0]); S = np.array([0, np.cos(t), np.sin(t)])
    N = np.cross(X, S)
    M = np.eye(4); M[:3, 0] = X; M[:3, 1] = S; M[:3, 2] = N
    M[:3, 3] = (0, 0, GATE_ZC)
    return M


def _gate_extrude(poly, n0, n1, frame=True):
    from trimesh.creation import extrude_polygon
    m = extrude_polygon(poly, height=n1 - n0)
    m.apply_translation((0, 0, n0))
    if frame:
        m.apply_transform(_gate_frame())
    return m


def _gate_ellipse(a, b):
    import shapely.geometry as sg
    import shapely.affinity as sa
    return sa.scale(sg.Point(0, 0).buffer(1.0, 128), a, b)


def gate_ports():
    return [((0, 0, 0), (0, 0, 1)), ((0, 0, GATE_L), (0, 0, -1))]


def _gate_notch(w_peak, square_out, side=1):
    """Notch in the pocket wall on side +u (side=1) or -u (blade plane), 45 deg
    flanks so the bump snaps fully home. square_out: the outer (+w) face is
    square - the bump can drop in from outside but never climb back out."""
    import shapely.geometry as sg
    import shapely.affinity as sa
    d = _gate_dims(); u0 = d['ap'] - 0.05; u1 = d['ap'] + GATE_NOTCH_D
    h = GATE_NOTCH_D + 1.3                               # half-width along w at the wall
    if square_out:
        p = sg.Polygon([(u0, w_peak - h), (u1, w_peak - 0.2), (u1, w_peak + 1.0), (u0, w_peak + 1.0)])
    else:
        p = sg.Polygon([(u0, w_peak - h), (u1, w_peak - 0.5), (u1, w_peak + 0.5), (u0, w_peak + h)])
    return p if side > 0 else sa.scale(p, -1, 1, origin=(0, 0))


def make_slide_gate(genders=None, labels=False):
    """Knife-gate body: straight fitting + 45 deg pocket arm the blade lives
    in. Prints standing on port A, no supports."""
    import shapely.geometry as sg
    g = genders or PORT_GENDER['slide_gate']
    d = _gate_dims()
    outer = [cylinder_between((0, 0, 0), (0, 0, GATE_L), OUTER_R),
             _gate_extrude(sg.box(-d['Rb'], 12.0, d['Rb'], d['wend']), -d['tb'], d['tb'])]
    a_s = d['ap'] + 0.1
    pocket = _gate_ellipse(a_s, a_s / d['c']).union(sg.box(-d['ap'], 0, d['ap'], d['wend'] + 3))
    inner = [cylinder_between((0, 0, -1), (0, 0, GATE_L + 1), BORE_R),
             _gate_extrude(pocket, -d['tp'], d['tp'])]
    # detent notches, both walls. CLOSED: V both sides. OPEN: +u square back
    # (captive), -u V (so one paperclip on the +u side releases the blade)
    for wp, sq, side in ((d['bump'], False, 1), (d['bump'], False, -1),
                         (d['bump'] + d['T'], True, 1), (d['bump'] + d['T'], False, -1)):
        inner.append(_gate_extrude(_gate_notch(wp, sq, side), -d['tp'], d['tp']))
    # knob slot through the underside (n-) wall, open at the far end
    sw, sl = GATE_STEM
    ks = sg.box(d['k_u'] - sw / 2 - 0.4, d['k_w'] - sl / 2 - 0.4,
                d['k_u'] + sw / 2 + 0.4, d['wend'] + 3)
    inner.append(_gate_extrude(ks, -d['tb'] - 1, -d['tp'] + 0.3))
    # release hole: through the +u wall into the OPEN notch (paperclip)
    wp = d['bump'] + d['T']
    P0 = _gate_frame() @ np.array([d['ap'] - 0.5, wp, 0, 1]); P1 = _gate_frame() @ np.array([d['Rb'] + 1, wp, 0, 1])
    inner.append(cylinder_between(P0[:3], P1[:3], 0.8, sections=16))
    ports = gate_ports()
    m = assemble(outer, inner, ports, g)
    return (m, port_labels(ports, g, PORT_NAMES['slide_gate'])) if labels else m


def _gate_blade_2d():
    """Blade outline in the blade plane, CLOSED position."""
    import shapely.geometry as sg
    d = _gate_dims(); a, b = d['a'], d['b']
    body = _gate_ellipse(a, b).intersection(sg.box(-a - 1, -b - 1, a + 1, 0)).union(
        sg.box(-a, -0.01, a, GATE_TOP))
    import shapely.affinity as sa
    fw, fl, fh = GATE_FINGER
    r, f, bp = d['f_root'], d['f_free'], d['bump']
    cut = sg.box(a - fw - 1.0, f - 1.0, a - fw, r).union(sg.box(a - fw - 1.0, f - 1.0, a + 1.0, f))
    # bump: 45 deg flanks, tip rounded so it rolls in and out with a crisp snap
    bump = sg.Polygon([(a - 0.2, bp - fh - 0.2), (a + fh, bp), (a - 0.2, bp + fh + 0.2)])
    bump = bump.buffer(-0.35, join_style=1).buffer(0.35, join_style=1)
    for m in (1, -1):
        cut_m, bump_m = (cut, bump) if m > 0 else (sa.scale(cut, -1, 1, origin=(0, 0)),
                                                    sa.scale(bump, -1, 1, origin=(0, 0)))
        body = body.difference(cut_m).union(bump_m)
    return body.buffer(0.25, join_style=1).buffer(-0.25, join_style=1)


def _gate_knob():
    """Knob in the blade frame (n- side): a stem through the arm's slot, a
    45 deg flare (prints unsupported, knob up) and a wide cap with fully
    rounded edges and shallow round grip grooves across the push direction.
    Nothing sharp anywhere a finger goes."""
    import shapely.geometry as sg
    d = _gate_dims()
    sw, sl = GATE_STEM
    cw, cl, ch, cr = GATE_CAP
    ku, kw_ = d['k_u'], d['k_w']
    n_face = -GATE_T / 2 + 0.3                       # into the blade
    n_out = -d['tb'] - 0.6                           # just clear of the arm's face
    stem = _gate_extrude(sg.box(ku - sw / 2, kw_ - sl / 2, ku + sw / 2, kw_ + sl / 2).buffer(
        1.5, join_style=1).buffer(-1.5, join_style=1), n_out, n_face, frame=False)
    # flare + cap as ONE convex hull: stem outline at n_out, full cap at the
    # flare top, then the rounded top edge (quarter circles inset by cr)
    flare = 1.35 * max(cw - sw, cl - sl) / 2         # under 45 deg even at the corners
    n_c0 = n_out - flare                             # cap bottom
    n_top = n_out - ch - flare                       # cap top
    pts = []
    def rect(hw, hl, n, rr=2.0):
        p = sg.box(ku - hw, kw_ - hl, ku + hw, kw_ + hl).buffer(-rr, join_style=1).buffer(rr, join_style=1)
        for x, y in np.asarray(p.exterior.coords)[::3]:
            pts.append((x, y, n))
    rect(sw / 2, sl / 2, n_out + 0.01)
    rect(cw / 2, cl / 2, n_c0)
    for t in np.linspace(0, np.pi / 2, 7):
        inset = cr * (1 - np.cos(t)); dn = cr * np.sin(t)
        rect(cw / 2 - inset, cl / 2 - inset, n_top + cr - dn, rr=max(2.0, 2.0 + inset))
    cap = trimesh.convex.convex_hull(np.array(pts))
    knob = union([stem, cap])
    # grip grooves: round-bottomed, across u, on the cap top
    gr = 1.6
    grooves = []
    for i in range(GATE_GRIP):
        w = kw_ + (i - (GATE_GRIP - 1) / 2) * (cl - 2 * cr) / GATE_GRIP
        grooves.append(cylinder_between((ku - cw, w, n_top - gr + 0.8), (ku + cw, w, n_top - gr + 0.8),
                                        gr, sections=24))
    return difference(knob, union(grooves))


def gate_blade(beta=0.0, inserted=True):
    """The blade. inserted=True: in the body at position beta (0 = OPEN,
    1 = CLOSED); False: flat on the bed, knob up, as printed."""
    import shapely.geometry as sg
    d = _gate_dims()
    plate = _gate_extrude(_gate_blade_2d(), -GATE_T / 2, GATE_T / 2, frame=False)
    m = union([plate, _gate_knob()])
    if not inserted:
        m.apply_transform(tf.rotation_matrix(np.pi, (1, 0, 0)))   # knob up
        m.apply_translation((0, 0, -m.bounds[0][2]))
        return m
    m.apply_translation((0, d['T'] * (1.0 - beta), 0))           # open = pulled out by T
    m.apply_transform(_gate_frame())
    return m


def make_gate_blade():
    """Slide (blade) for the slide gate - print flat, knob up. Slide it into
    the open far end of the arm, knob through the slot, until it clicks."""
    return gate_blade(inserted=False)


# ===========================================================================
#                            REGISTRY
# ===========================================================================
FITTINGS = {
    'elbow':       make_elbow,          # angle = ELBOW_ANGLE
    'coupler':     make_coupler,
    'tee':         make_tee,
    'u_bend':      make_u_bend,
    'y_fitting':   make_y_fitting,
    'cap':         make_cap,
    'flange':      make_flange,
    'back_plate':  make_back_plate,
    'gate_flange_body': gn_body,
    'pipe_hook':   make_pipe_hook,
    'latch_coupon': make_latch_coupon,
    'shim':        lambda: trimesh.util.concatenate(make_shim_print()),
    'vent_tube':   make_vent_tube,
    'slide_gate':  make_slide_gate,
    'gate_blade':  make_gate_blade,
    'male_fit_coupons': lambda: trimesh.util.concatenate(make_male_fit_coupons()),
}


# ===========================================================================
#                              MAIN
# ===========================================================================
def main(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    print(f"Base parameters:")
    print(f"  PIPE_OD       = {PIPE_OD:.2f} mm")
    print(f"  PIPE_ID       = {PIPE_ID:.2f} mm")
    print(f"  SOCKET_ID     = {SOCKET_ID:.2f} mm")
    print(f"  BORE_ID       = {BORE_ID:.2f} mm")
    print(f"  TUBE_OD       = {TUBE_OD:.2f} mm")
    print(f"  WALL          = {WALL:.1f} mm")
    print(f"  SOCKET_DEPTH  = {SOCKET_DEPTH:.1f} mm")
    print(f"  BEND_R        = {BEND_R:.1f} mm")
    print()
    print(f"Generating {len(FITTINGS)} fittings into {out_dir} ...")

    for name, factory in FITTINGS.items():
        print(f"  {name:14s} ", end='', flush=True)
        try:
            mesh = export_ready(factory())
            # Drop the part onto z=0 so the slicer sees it sitting on the bed
            mesh.apply_translation((0, 0, -mesh.bounds[0][2]))
            path = os.path.join(out_dir, f"{name}_2-5in.stl")
            mesh.export(path)
            print(f"vol={mesh.volume/1000:6.1f} cm³  "
                  f"box={mesh.extents[0]:5.1f}x{mesh.extents[1]:5.1f}x{mesh.extents[2]:5.1f}  "
                  f"watertight={mesh.is_watertight}")
        except Exception as e:
            print(f"FAILED: {e}")
            raise

    print("done.")


if __name__ == '__main__':
    out_dir = sys.argv[1] if len(sys.argv) > 1 else str(__import__('pathlib').Path(__file__).resolve().parents[1] / 'out' / 'stl')
    main(out_dir)
