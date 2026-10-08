"""
Open-front tabletop waterfall - 9" cube  (v13)

Changes from v12:
  1. THREE slits per pool wall (left, center, right) instead of one.
     Slits narrower (28mm) so three fit with margins on every wall.
  2. Slit openings "polished" - the wall material is filleted around each
     slit on the OUTER face of the wall, so the cut looks blended into the
     wall surface instead of a sharp surgical cut. Inside face stays clean.
  3. Stubs (drip guides under the floor): only the BOTTOM is rounded, top
     is flush with the wall above. Previously they were rounded all 4 vert
     corners, looking pill-shaped from the front. Now they read as a small
     blade hanging down from the floor.
  4. The 1" x 1" back hole is REMOVED entirely.
"""

import math

import cadquery as cq

INCH = 25.4

SIZE        = 8.25 * INCH    # was 9.0 * INCH
WALL        = 6.0
FLOOR       = 8.0
LOW_WALL_H  = 3 * INCH

# Pools
POOL_WALL    = 4.5
POOL_FLOOR_T = 6.0
POOL_DEPTH_Z = 25.0     # was 16.0 - deeper pools for more water cushion
POOL_INNER   = [
    (4.0 * INCH, 3.0 * INCH),    # top
    (5.0 * INCH, 4.2 * INCH),    # mid
    (6.0 * INCH, 5.4 * INCH),    # bot
]
POOL_RIM_Z   = [7.5 * INCH, 6.0 * INCH, 4.5 * INCH]    # was [8.0, 6.5, 5.0]
BOTTOM_POOL_FLOOR_Z = POOL_RIM_Z[2] - POOL_DEPTH_Z - POOL_FLOOR_T

# Spine
# Spine bottom - 50% larger than v17
SPINE_BOT_W       = 2.6 * INCH * 1.5     # 3.9" wide (was 2.6")
SPINE_BOT_INNER_D = 2.0 * INCH * 1.5     # 3.0" forward (was 2.0")
SPINE_BOT_TOP     = 3.0 * INCH * 0.8     # 2.4" tall (was 3.0", 20% shorter)
SPINE_BOT_WALL    = 5.0
SPINE_FEED_BORDER = 0.25 * INCH          # uniform border around side feed holes (halved from 0.5")
SPINE_ROOF_T      = 3.0

SPINE_UP_W       = SPINE_BOT_W / 3       # keep upper at original 1.3" (was 1.3")
SPINE_UP_INNER_D = SPINE_BOT_INNER_D / 3 # keep at 1.0"
SPINE_UP_WALL    = 4.0
SPINE_TOP_Z      = POOL_RIM_Z[0] + 0.2 * INCH
SPINE_CUP_DEPTH  = 0.25 * INCH       # depth of the cup at top of spine
SPINE_CAP_T      = 4.0               # cap thickness (the roof slab)
SPINE_CAP_HOLE_D = 0.3125 * INCH     # 0.25 * 1.25 = 0.3125" hole through cap
SPINE_CAP_TOP_Z  = SPINE_TOP_Z - SPINE_CUP_DEPTH
SPINE_CAP_BOT_Z  = SPINE_CAP_TOP_Z - SPINE_CAP_T

# Back wall holes (circular, lead to spine cavity)
BACK_HOLE_D     = 0.78125 * INCH      # 0.78" diameter
BACK_HOLE_Z     = 3.25 * INCH         # lower hole - dropped 0.5 in
BACK_HOLE_2_Z   = 6.25 * INCH         # upper hole - raised 0.5 in (3 in apart)

# Slits - ONE per wall (front + left + right), 3 total per pool
SLIT_FRAC      = 8.0 / 25.0    # 0.32, keeps slit_h = 8mm with new 25mm pool depth
SLIT_W         = 38.0 / 3      # ~12.67mm, 1/3 of v24 (was 38.0)
SLIT_CORNER_R  = 1.5
SLIT_POLISH_R  = 1.5
SLIT_TOP_BUFFER = 4.0       # cutter extends this far above rim (clean cut, removes thin sliver)

# --- Drip guides -----------------------------------------------------------
# "stub"   : original 8mm nub. Water detaches at the tip and free-falls to the
#            vessel below (7mm between tiers, 22mm into the basin).
# "column" : the guide runs straight down and lands on the floor of the vessel
#            below. No detachment, no free fall, so no splash - and the column
#            props up the shelf it hangs from, which prints better too.
DRIP_MODE          = "column"
COLUMN_WIDEN       = 3.0    # mm added each side of the slit width; water
                            # spreads as it runs down, a slit-width guide
                            # lets the edges of the sheet escape
COLUMN_EDGE_R      = 0.0    # vertical corner rounding, 0 = square.
                            # A column that reaches the floor has no drip
                            # edge to shape, so this is cosmetic only.
COLUMN_FOOT_FLARE  = 3.0    # height of the splayed foot at the floor joint
COLUMN_FOOT_SPREAD = 2.0    # extra mm each side at the very bottom
COLUMN_LAND_GAP    = 0.0    # stop this far above the floor. 0 = touch down.

# --- Flow channels ---------------------------------------------------------
# A U-groove cut into the outer face below each slit, running unbroken from
# the slit invert down to the bottom of the guide. Keeps the stream from
# fanning out as it descends. CHANNEL_FRAC is a fraction of SLIT_W.
CHANNEL_ENABLE = True
CHANNEL_FRAC   = 0.75       # groove width = 0.75 x 12.67 = 9.5 mm
CHANNEL_DEPTH  = 1.2        # leaves 3.3 mm of the 4.5 mm wall

# --- Breakaway supports ----------------------------------------------------
# Sacrificial pins printed as part of the model, standing on the floor below
# and reaching up to a tiny contact dot under each shelf. Snap them off after
# printing. The point is to turn the slicer's supports OFF entirely: these
# touch only where you choose, and they release with a fingernail.
SUPPORT_ENABLE  = True
# "wall" is the community default for MODELED supports: thin ribs, 0.8-1.2 mm,
# which print stably, use little material and peel out along their length.
# "tree" and "pin" are what a SLICER generates automatically - good for organic
# shapes, but not what people hand-model. See README for sources.
SUPPORT_STYLE   = "wall"
SUPPORT_WALL_T      = 1.0   # rib thickness. 0.8-1.2 mm is 2-3 perimeters.
SUPPORT_WALL_TIP_T  = 0.45  # contact edge, about one extrusion width. The rib
                            # tapers to this so it bonds along a line rather
                            # than a 1 mm band - roughly half the interface.
SUPPORT_WALL_TAPER_H = 4.0  # height over which it narrows to the tip
SUPPORT_WALL_PITCH  = 12.0  # rib spacing. Span between ribs must stay inside
                            # what the printer can bridge cleanly (~10-15 mm).
SUPPORT_WALL_FOOT_T = 0.6   # NECK where the rib meets the floor below. This
                            # joint is the only fused one - a rib has to stand
                            # on something, so no Z-gap is possible here. Made
                            # NARROWER than the body on purpose: it puts the
                            # weakest point exactly at the joint so the rib
                            # snaps off at the floor instead of tearing
                            # somewhere up its length, and it cuts the fused
                            # area that has to be sanded afterwards.
                            # Trade-off: a tall rib on a thin neck is easier
                            # to knock over mid-print. Raise toward 1.0 if the
                            # 75 mm bottom-tier ribs come loose.
SUPPORT_WALL_FOOT_H = 1.2   # neck height before it opens out to the body
SUPPORT_MIN_RUN     = 8.0   # discard rib segments shorter than this
SUPPORT_TRUNK_D = 7.0       # trunk diameter for "tree"
SUPPORT_TRUNK_PITCH = 52.0  # trunk spacing; tips within this share a trunk
SUPPORT_BRANCH_ANGLE = 50.0 # max branch lean from vertical, degrees. Beyond
                            # about 50 a branch is itself an overhang.
SUPPORT_PITCH   = 18.0      # contact spacing under each shelf ("tree"/"pin")
SUPPORT_BASE_D  = 9.0       # base diameter - keeps tall pins from toppling
SUPPORT_TIP_D   = 0.8       # contact dot. Do NOT go below ~0.4 mm (one
                            # extrusion width) or it will not print at all.
SUPPORT_NECK_H  = 1.2       # straight neck under the tip, so it breaks there
SUPPORT_FOOT_D  = 2.5       # foot where the pin meets the floor below. Also a
                            # break point, so the pin lifts out in one piece
                            # instead of leaving its cone behind in the pool.
SUPPORT_FOOT_NECK_H = 1.0   # straight run at the foot
SUPPORT_FOOT_FLARE  = 2.5   # height over which the foot opens out to the base
SUPPORT_LAYER_H = 0.2       # the layer height you will actually print at
SUPPORT_GAP     = 0.10      # confirmed on the test coupon
                            # Z-gap under the shelf. The rule everywhere is
                            # EXACTLY one layer height - never zero. The first
                            # layer above droops onto the support just enough
                            # to print, then releases. Zero welds it on; too
                            # much lets the overhang sag. Re-set this if you
                            # change layer height.
SUPPORT_SNAP_TO_LAYER = True
                            # Snap every rib top DOWN to a layer boundary.
                            # Without this the gap is a lie: the three shelves
                            # sit at 797.5, 607.0 and 416.5 layers, so two of
                            # them put the rib top mid-layer and the slicer
                            # drops or rounds that layer unpredictably. The
                            # test coupon happened to land on a boundary,
                            # which is why 0.10 behaved there.
SUPPORT_MARGIN  = 2.5       # XY clearance from walls, spine and pump box.
                            # 0.4-0.8 mm is the usual guidance; 2.5 is already
                            # generous. 6 mm wiped out the outer third of
                            # every shelf.
SUPPORT_GUIDE_CLEAR = 1.5   # extra clearance around a drip guide
                            # Raise it above the water line to get a visible
                            # cascade back, at the cost of the support.

# Tapered back wall - now 1/4" taller than the spine top
BACK_TOP_W    = 4.05 * INCH          # absolute width (was SIZE * 0.45 = 4.05" at 9" cube)
BACK_WALL_TOP = SPINE_TOP_Z + 0.25 * INCH
TAPER_START_Z = BOTTOM_POOL_FLOOR_Z

# Edge rounding
CUBE_VERT_FILLET    = 5.0
RIM_EDGE_SIZE       = 5.0       # basin top rim - matches vertical corners
RIM_EDGE_STYLE      = "none"    # "none", "chamfer" or "fillet". Rim edges run out
                                # into the rising back wall, and OCCT can
                                # return a BROKEN result there WITHOUT raising
                                # - that is what put a hole in the back-right
                                # corner. Every candidate is now validated, so
                                # set this to "fillet" and watch the log: if
                                # your kernel reports the full 5.0 mm you get
                                # the rounded rim, and if it backs off you will
                                # be told instead of shipping a hole.
RIM_FILLET          = RIM_EDGE_SIZE   # backwards-compatible alias
POOL_RIM_FILLET     = 2.0
FLOOR_EDGE_FILLET   = 4.0


def _valid(shape):
    """OCCT can return a BROKEN solid from fillet() without raising.

    That is how a hole appeared at the back-right basin rim: the 4.0 mm
    fallback 'succeeded', the loop accepted it, and the corner face was
    malformed. Always check the result, never just the absence of an
    exception.
    """
    try:
        return bool(shape.val().isValid())
    except Exception:
        return False


def _try_progressive(shape, selector, radii, label=""):
    for r in radii:
        if r <= 0:
            continue
        try:
            out = shape.edges(selector).fillet(r)
        except Exception:
            continue
        if _valid(out):
            return out
        if label:
            print(f"  ! {label}: r={r} mm produced an invalid solid, backing off")
    if label:
        print(f"  ! {label}: no radius worked, left square")
    return shape


def make_slit_cut_xz(slit_w, slit_h, wall_thick, polish_r=0, x_offset=0):
    """Slit cutter for front/back walls. Cross-section in X-Z, extruded along Y.
    
    With polish_r > 0, the cutter is LOFTED with wider ends than middle:
      - Width at outer face: slit_w + 2*polish_r
      - Width in middle:     slit_w
      - Width at inner face: slit_w + 2*polish_r
    When subtracted, this creates a hole with wall material sloping smoothly
    DOWN from the wall surface into a narrower throat (chamfered opening).
    """
    if polish_r > 0:
        big_w = slit_w + 2*polish_r
        big_h = slit_h + 2*polish_r
        cutter = (
            cq.Workplane("XZ")
            .center(x_offset, 0)
            .rect(big_w, big_h)                                         # outer face flare
            .workplane(offset=polish_r)
            .rect(slit_w, slit_h)                                       # narrow waist start
            .workplane(offset=wall_thick - 2*polish_r)
            .rect(slit_w, slit_h)                                       # narrow waist end
            .workplane(offset=polish_r)
            .rect(big_w, big_h)                                         # inner face flare
            .loft(ruled=False)
        )
    else:
        cutter = (
            cq.Workplane("XZ")
            .center(x_offset, 0)
            .rect(slit_w, slit_h)
            .extrude(wall_thick + 1)
        )
    return cutter


def make_slit_cut_yz(slit_w, slit_h, wall_thick, polish_r=0, y_offset=0):
    """Slit cutter for left/right walls. Same loft approach, extrudes along X."""
    if polish_r > 0:
        big_w = slit_w + 2*polish_r
        big_h = slit_h + 2*polish_r
        cutter = (
            cq.Workplane("YZ")
            .center(y_offset, 0)
            .rect(big_w, big_h)
            .workplane(offset=polish_r)
            .rect(slit_w, slit_h)
            .workplane(offset=wall_thick - 2*polish_r)
            .rect(slit_w, slit_h)
            .workplane(offset=polish_r)
            .rect(big_w, big_h)
            .loft(ruled=False)
        )
    else:
        cutter = (
            cq.Workplane("YZ")
            .center(y_offset, 0)
            .rect(slit_w, slit_h)
            .extrude(wall_thick + 1)
        )
    return cutter


def make_stub(width_along, depth_into_wall, slit_h, axis):
    """Original short drip stub: a nub hanging below the shelf, bottom rounded.

    Water sheets down the outer wall face and detaches at the rounded tip,
    then free-falls to the vessel below. Kept for DRIP_MODE == "stub".

    axis: 'x' for front/back (stub width is X), 'y' for left/right (width is Y)
    """
    if axis == 'x':
        stub = (cq.Workplane("XY")
                .box(width_along, depth_into_wall, slit_h, centered=(True, False, False)))
    else:  # 'y'
        stub = (cq.Workplane("XY")
                .box(depth_into_wall, width_along, slit_h, centered=(False, True, False)))
    # Round only the BOTTOM edges (lowest Z)
    stub = _try_progressive(stub, "<Z", [SLIT_CORNER_R, 1.0], "stub bottom")
    return stub


def make_column(width_along, depth_into_wall, height, axis):
    """Full-height drip guide: runs straight down and lands on the floor below.

    Because it meets the floor there is no detachment point, so the tip is
    left FLAT rather than rounded - a rounded tip would only shrink the
    contact patch and leave a crevice ring where it merges with the floor.

    Flat foot also means the column carries load, so the cantilevered shelf
    above it is propped instead of hanging.

    Returns geometry with its BASE at local z=0, growing upward by `height`.
    """
    w = width_along + 2 * COLUMN_WIDEN
    d = depth_into_wall

    if axis == 'x':
        col = (cq.Workplane("XY")
               .box(w, d, height, centered=(True, False, False)))
        centre = (0.0, d / 2)
    else:  # 'y'
        col = (cq.Workplane("XY")
               .box(d, w, height, centered=(False, True, False)))
        centre = (d / 2, 0.0)

    # Optional easing of the vertical corners. Off by default: a straight
    # column needs no rounding to shed water once it reaches the floor.
    if COLUMN_EDGE_R > 0:
        col = _try_progressive(col, "|Z", [COLUMN_EDGE_R, 0.8], "column sides")

    # A splayed foot where the column meets the floor. This is not a drip
    # feature - it kills the sharp internal corner at the joint, which is
    # both a stress riser and the hardest spot in the pool to clean.
    if COLUMN_FOOT_FLARE > 0 and COLUMN_FOOT_SPREAD > 0:
        s, fh = COLUMN_FOOT_SPREAD, COLUMN_FOOT_FLARE
        if axis == 'x':
            lo_w, lo_d, hi_w, hi_d = w + 2 * s, d + 2 * s, w, d
        else:
            lo_w, lo_d, hi_w, hi_d = d + 2 * s, w + 2 * s, d, w
        try:
            foot = (cq.Workplane("XY")
                    .rect(lo_w, lo_d)
                    .workplane(offset=fh)
                    .rect(hi_w, hi_d)
                    .loft(ruled=True)
                    .translate((centre[0], centre[1], 0)))
            col = col.union(foot)
        except Exception as e:
            print(f"  ! column foot flare skipped: {e}")

    return col


def drip_guide(width_along, depth_into_wall, slit_h, axis, shelf_z, land_z):
    """Build the drip feature for one slit and return (solid, base_z).

    shelf_z : underside of the pool floor the guide hangs from
    land_z  : floor of the vessel below, where a column would touch down
    """
    if DRIP_MODE == "column":
        height = shelf_z - (land_z + COLUMN_LAND_GAP)
        if height > 0:
            return make_column(width_along, depth_into_wall, height, axis), \
                   land_z + COLUMN_LAND_GAP
        print(f"  ! column at z={shelf_z:.0f} has no room; falling back to a stub")
    return make_stub(width_along, depth_into_wall, slit_h, axis), shelf_z - slit_h


def make_channel(z0, z1, axis, face_pos, cross_pos):
    """A U-groove cut into the outer face, to keep the stream from spreading.

    Water leaving a slit fans out as it runs down, which is how droplets get
    thrown past the catch margin. A concave channel holds the stream together
    and hands it to the guide below without a step.

    Geometry note: for a cylinder to cut a groove `width` across and `depth`
    deep, its axis sits (r - depth) IN FRONT of the face, not behind it - the
    groove is the sliver of cylinder that reaches into the material. Putting
    the axis behind the face instead bores straight through a 4.5 mm wall.
    The cutter is also intersected with a box so it can never exceed `depth`
    however the numbers are tuned.

    axis      : 'x' front wall (groove runs in Y), 'y' side wall (runs in X)
    face_pos  : coordinate of the OUTER face the water runs down
    cross_pos : position along that wall
    """
    width = SLIT_W * CHANNEL_FRAC
    depth = CHANNEL_DEPTH
    r = (width ** 2 / 4 + depth ** 2) / (2 * depth)
    standoff = r - depth
    h = z1 - z0
    pad = 0.02                       # keeps coincident faces off each other

    if axis == 'x':
        inward = 1.0                 # material lies at greater y
        cyl = (cq.Workplane("XY").circle(r).extrude(h)
               .translate((cross_pos, face_pos - inward * standoff, z0)))
        clip = (cq.Workplane("XY")
                .box(width, depth + pad, h, centered=(True, False, False))
                .translate((cross_pos, face_pos - pad / 2, z0)))
    else:
        inward = 1.0 if face_pos < 0 else -1.0
        cyl = (cq.Workplane("XY").circle(r).extrude(h)
               .translate((face_pos - inward * standoff, cross_pos, z0)))
        x0 = face_pos - inward * pad / 2
        clip = (cq.Workplane("XY")
                .box(depth + pad, width, h, centered=(False, True, False))
                .translate((x0 if inward > 0 else x0 - (depth + pad),
                            cross_pos, z0)))

    return cyl.intersect(clip)


def make_support_pin(height):
    """A sacrificial pin: narrow foot, fat middle, tiny contact dot on top.

    Shape matters more than size here:

    - The taper runs INWARD going up, so every layer sits on the one below
      and the pin needs no support of its own.
    - The tip is a small FLAT, never a true point. A point smaller than one
      extrusion width simply does not get printed, and then the pin holds
      nothing. SUPPORT_TIP_D should not go below about 0.4 mm.
    - Short straight necks at BOTH ends put the breaks at predictable places.
      The foot matters as much as the tip: a pin fused to the floor below by
      its full base would snap at the top and leave the cone standing in the
      pool. A narrow foot lets the whole pin come away in one piece.
    - The foot is deliberately fatter than the tip. It is carrying the pin
      during printing, and a nozzle strike on a 75 mm spire will shear
      anything thinner.
    - The fat middle keeps the aspect ratio sane on the tall bottom-tier pins.

    Returns geometry with its base at local z=0.
    """
    tip_r = SUPPORT_TIP_D / 2
    base_r = SUPPORT_BASE_D / 2
    foot_r = SUPPORT_FOOT_D / 2

    neck_h = min(SUPPORT_NECK_H, height * 0.25)
    foot_h = min(SUPPORT_FOOT_NECK_H, height * 0.1)
    flare_h = min(SUPPORT_FOOT_FLARE, height * 0.2)
    cone_h = height - neck_h - foot_h - flare_h
    if cone_h <= 0.5:                       # too short to shape - plain taper
        return (cq.Workplane("XY").circle(base_r)
                .workplane(offset=height).circle(tip_r).loft(ruled=True))

    pin = (cq.Workplane("XY")
           .circle(foot_r)
           .workplane(offset=foot_h).circle(foot_r)
           .workplane(offset=flare_h).circle(base_r)
           .workplane(offset=cone_h).circle(tip_r)
           .loft(ruled=True))
    neck = (cq.Workplane("XY").circle(tip_r).extrude(neck_h)
            .translate((0, 0, height - neck_h)))
    return pin.union(neck)


def _cone_between(p0, p1, r0, r1):
    """A tapered cylinder from p0 to p1. Returns None for a zero-length span.

    makeCone throws on two identical radii, so equal ends go to makeCylinder.
    """
    v = cq.Vector(p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2])
    h = v.Length
    if h < 1e-6:
        return None
    d = v.normalized()
    if abs(r0 - r1) < 1e-6:
        return cq.Solid.makeCylinder(r0, h, cq.Vector(*p0), d)
    return cq.Solid.makeCone(r0, r1, h, cq.Vector(*p0), d)


def make_support_tree(tips, land_z, top_z):
    """One trunk rising from the floor, splitting into branches near the top.

    This is what a slicer's tree support does, and the reason to prefer it
    over a forest of separate spires:

    - Several contact points share one trunk, so there is far less material
      standing in the pool and far less to snap off.
    - A fat trunk is stiff. Tall lone needles get whipped by the nozzle.
    - Branches only need to be slender near their tips, where the load is
      almost nothing.

    The branch angle is capped by SUPPORT_BRANCH_ANGLE from vertical, because
    a branch leaning further than that is an overhang and needs support of its
    own - which defeats the point.

    Returns a list of cq.Solid.
    """
    import math
    tip_r = SUPPORT_TIP_D / 2
    trunk_r = SUPPORT_TRUNK_D / 2
    foot_r = SUPPORT_FOOT_D / 2

    cx = sum(t[0] for t in tips) / len(tips)
    cy = sum(t[1] for t in tips) / len(tips)
    reach = max((math.hypot(t[0] - cx, t[1] - cy) for t in tips), default=0.0)

    # vertical run the branches need to stay inside the angle limit
    drop = reach / math.tan(math.radians(SUPPORT_BRANCH_ANGLE)) if reach > 0 else 0.0
    avail = top_z - land_z
    drop = min(drop, avail * 0.6)
    fork_z = top_z - drop - SUPPORT_NECK_H

    out = []
    # foot -> trunk
    flare_z = land_z + SUPPORT_FOOT_NECK_H
    out.append(_cone_between((cx, cy, land_z), (cx, cy, flare_z), foot_r, foot_r))
    out.append(_cone_between((cx, cy, flare_z),
                             (cx, cy, min(flare_z + SUPPORT_FOOT_FLARE, fork_z)),
                             foot_r, trunk_r))
    out.append(_cone_between((cx, cy, min(flare_z + SUPPORT_FOOT_FLARE, fork_z)),
                             (cx, cy, fork_z), trunk_r, trunk_r * 0.8))

    branch_r = max(trunk_r * 0.8 / max(len(tips) ** 0.5, 1.0), tip_r * 1.6)
    for (tx, ty) in tips:
        neck_z = top_z - SUPPORT_NECK_H
        out.append(_cone_between((cx, cy, fork_z), (tx, ty, neck_z),
                                 branch_r, tip_r))
        out.append(_cone_between((tx, ty, neck_z), (tx, ty, top_z), tip_r, tip_r))
    return [s for s in out if s is not None]


def cluster_tips(spots, pitch):
    """Group contact points onto a coarser grid, one trunk per group."""
    groups = {}
    for (x, y) in spots:
        key = (round(x / pitch), round(y / pitch))
        groups.setdefault(key, []).append((x, y))
    return list(groups.values())


def _support_land(x, y, outer_w, f_out, back_y, land_z, tier):
    """The z a support at (x, y) stands on, or None if it may not stand there.

    Returns the pump-box roof for ribs over the pump box: the roof is solid
    and 22 mm below the bottom shelf, so it is a perfectly good floor. Treating
    the whole pump footprint as forbidden left the back half of the bottom
    shelf completely unsupported.
    """
    m = SUPPORT_MARGIN
    gw = SLIT_W / 2 + COLUMN_WIDEN + SUPPORT_GUIDE_CLEAR
    side_x = outer_w / 2 - POOL_WALL / 2
    side_y = (back_y + f_out) / 2

    # the riser passes straight up through here
    if abs(x) < SPINE_UP_W / 2 + m and y > (SIZE / 2 - WALL) - SPINE_UP_INNER_D - m:
        return None
    # front drip guide - only where it actually is, not the whole rib line
    if abs(x) < gw and abs(y - (f_out + POOL_WALL / 2)) < POOL_WALL + m:
        return None
    # side drip guides - likewise bounded in y
    if abs(abs(x) - side_x) < POOL_WALL / 2 + m and abs(y - side_y) < gw:
        return None

    if tier == len(POOL_RIM_Z) - 1:
        px, py = SPINE_BOT_W / 2, (SIZE / 2 - WALL) - SPINE_BOT_INNER_D
        inside = abs(x) < px - m and y > py + m
        outside = abs(x) > px + m or y < py - m
        if inside:
            return SPINE_BOT_TOP        # stand on the pump box roof
        if not outside:
            return None                 # straddling the edge - skip
    return land_z


def support_top_z(shelf_z):
    """Underside of the ceiling minus the gap, snapped to a printable layer."""
    top = shelf_z - SUPPORT_GAP
    if SUPPORT_SNAP_TO_LAYER and SUPPORT_LAYER_H > 0:
        top = math.floor(round(top / SUPPORT_LAYER_H, 6)) * SUPPORT_LAYER_H
    return top


def _rib_solid(x, y0, length, land_z, top_z):
    """One rib, profiled over its height.

    Bottom to top: a short foot wedge, the full-thickness body, then a taper
    to a thin contact edge.

    The taper matters. A rib that meets the ceiling at full thickness bonds
    along that whole width; narrowing the last few millimetres to about one
    extrusion width cuts the bonded interface by more than half without
    losing any support, because the load up there is negligible.

    The foot is deliberately modest. The usual advice to widen a support's
    foot is about BUILD PLATE adhesion, and none of these ribs touch the
    plate - they stand on already-printed pool floor, which bonds fine. The
    foot here is only for out-of-plane stiffness, and a fat one is just more
    material fused to a surface you have to clean afterwards.
    """
    h = top_z - land_z
    foot_h = min(SUPPORT_WALL_FOOT_H, h * 0.15)
    taper_h = min(SUPPORT_WALL_TAPER_H, h * 0.35)
    mid_h = h - foot_h - taper_h
    if mid_h <= 0.5:
        return cq.Solid.makeBox(SUPPORT_WALL_T, length, h,
                                cq.Vector(x - SUPPORT_WALL_T / 2, y0, land_z))
    w = (cq.Workplane("XY")
         .rect(SUPPORT_WALL_FOOT_T, length)
         .workplane(offset=foot_h).rect(SUPPORT_WALL_T, length)
         .workplane(offset=mid_h).rect(SUPPORT_WALL_T, length)
         .workplane(offset=taper_h).rect(SUPPORT_WALL_TIP_T, length)
         .loft(ruled=True)
         .translate((x, y0 + length / 2, land_z)))
    return w.val()


def support_wall_segments(rec):
    """Rib segments under one shelf as (x, y_start, y_end).

    Split out from support_walls so the coverage tool can reason about exactly
    the same segments the geometry uses, with no chance of the two drifting.
    """
    m = SUPPORT_MARGIN
    outer_w, f_out = rec["outer_w"], rec["f_out"]
    x_lim = min(outer_w, rec["below_iw"]) / 2 - m
    y_lo = max(f_out, rec["below_f_in"]) + m
    y_hi = rec["back_y"] - m
    top_z = support_top_z(rec["shelf_z"])
    if x_lim <= 0 or y_hi <= y_lo or top_z - rec["land_z"] <= 1.0:
        return []

    n = max(int((2 * x_lim) // SUPPORT_WALL_PITCH), 1)
    step = (2 * x_lim) / n
    xs = [-x_lim + step * (i + 0.5) for i in range(n)]

    segs, step_y = [], 1.0
    for x in xs:
        y, start, cur = y_lo, None, None
        while y <= y_hi + 1e-9:
            land = _support_land(x, y, outer_w, f_out, rec["back_y"],
                                 rec["land_z"], rec["tier"])
            if land is not None and start is None:
                start, cur = y, land
            elif start is not None and (land is None or land != cur):
                if y - start >= SUPPORT_MIN_RUN:
                    segs.append((x, start, y, cur))
                start, cur = (y, land) if land is not None else (None, None)
            y += step_y
        # Close a run that reaches the end. Without this, a rib with NO
        # obstruction anywhere along it was dropped entirely - which quietly
        # deleted every rib in the outer half of each shelf.
        if start is not None and y_hi - start >= SUPPORT_MIN_RUN:
            segs.append((x, start, y_hi, cur))
    return segs


def support_walls(rec):
    """Thin ribs under one shelf - the standard shape for modeled supports."""
    top_z = support_top_z(rec["shelf_z"])
    out, runs = [], 0.0
    for (x, y0, y1, land) in support_wall_segments(rec):
        out.append(_rib_solid(x, y0, y1 - y0, land, top_z))
        runs += y1 - y0
    return out, runs


def support_positions(outer_w, f_out, back_y, below_iw, below_f_in, tier):
    """Grid of pin centres under one shelf, skipping anything already solid.

    Pins must land on the floor below, so they are kept inside that vessel's
    cavity, clear of its walls, clear of the spine, and clear of the drip
    guides that already run down through the same space.
    """
    m = SUPPORT_MARGIN
    x_lim = min(outer_w / 2, below_iw / 2) - m
    y_lo = max(f_out, below_f_in) + m
    y_hi = back_y - m
    if x_lim <= 0 or y_hi <= y_lo:
        return []

    def axis_points(lo, hi):
        span = hi - lo
        n = max(int(span // SUPPORT_PITCH), 1)
        step = span / n
        return [lo + step * (i + 0.5) for i in range(n)]

    out = []
    for x in axis_points(-x_lim, x_lim):
        for y in axis_points(y_lo, y_hi):
            if not _support_blocked(x, y, outer_w, f_out, tier):
                out.append((x, y))
    return out


def build():
    inner_back_y = SIZE/2 - WALL

    # ============================================================
    # 1) Basin + back wall as ONE solid (block minus cuts)
    # ============================================================
    solid = cq.Workplane("XY").box(SIZE, SIZE, BACK_WALL_TOP, centered=(True, True, False))

    solid = solid.cut(
        cq.Workplane("XY")
        .box(SIZE - 2*WALL, SIZE - 2*WALL, LOW_WALL_H - FLOOR, centered=(True, True, False))
        .translate((0, 0, FLOOR))
    )

    solid = solid.cut(
        cq.Workplane("XY")
        .box(SIZE, SIZE - WALL, BACK_WALL_TOP - LOW_WALL_H + 1, centered=(True, False, False))
        .translate((0, -SIZE/2, LOW_WALL_H))
    )

    half_bot = SIZE / 2
    half_top = BACK_TOP_W / 2

    left_wedge = (
        cq.Workplane("XZ")
        .moveTo(-half_bot, TAPER_START_Z)
        .lineTo(-half_top, BACK_WALL_TOP)
        .lineTo(-half_bot, BACK_WALL_TOP)
        .close()
        .extrude(WALL + 2)
        .translate((0, SIZE/2 - WALL - 1, 0))
    )
    right_wedge = (
        cq.Workplane("XZ")
        .moveTo( half_bot, TAPER_START_Z)
        .lineTo( half_top, BACK_WALL_TOP)
        .lineTo( half_bot, BACK_WALL_TOP)
        .close()
        .extrude(WALL + 2)
        .translate((0, SIZE/2 - WALL - 1, 0))
    )
    solid = solid.cut(left_wedge).cut(right_wedge)

    body = solid

    # Outer fillets
    body = _try_progressive(body, "|Z", [CUBE_VERT_FILLET, 4, 3, 2], "cube vert corners")

    # --- Basin top rim (z = LOW_WALL_H = 76.2 mm) ---
    # Select HORIZONTAL edges at the basin top (those whose endpoints have the
    # same Z). This excludes vertical edges that would corrupt the geometry.
    def _horizontal_z_selector(z_target, tol=1.5, max_xy=None):
        """Selects horizontal edges whose midpoint z is near z_target.
        If max_xy is given, only keeps edges where all vertices satisfy
        |x| < max_xy AND |y| < max_xy. This excludes outer-perimeter edges
        and corner fillet artifacts."""
        from cadquery.selectors import Selector
        class _HZ(Selector):
            def filter(self, edges):
                kept = []
                for e in edges:
                    try:
                        c = e.Center()
                        if abs(c.z - z_target) >= tol:
                            continue
                        verts = e.Vertices()
                        if len(verts) >= 2:
                            zs = [v.Z for v in verts]
                            if max(zs) - min(zs) > 0.5:
                                continue   # skip non-horizontal
                            if max_xy is not None:
                                # ALL vertices must be strictly interior
                                if any(abs(v.X) >= max_xy or abs(v.Y) >= max_xy for v in verts):
                                    continue
                        kept.append(e)
                    except Exception:
                        pass
                return kept
        return _HZ()

    rim_applied = False
    # Only fillet interior edges (away from cube outer perimeter at |x|,|y|=104.8)
    # max_xy=100 keeps inner-rim edges (at |xy|=98.8) but excludes outer (104.8)
    #
    # These edges form a U (front + left + right) that dead-ends into the
    # rising back wall at both ends. That run-out is where OCCT struggles: a
    # fillet there can come back malformed WITHOUT raising, which is how a
    # hole appeared at the back-right corner. Every candidate is validated,
    # and a chamfer is tried first because it survives run-outs far better.
    _rim_sel = _horizontal_z_selector(LOW_WALL_H, tol=1.0, max_xy=100.0)
    if RIM_EDGE_STYLE == "none" or RIM_EDGE_SIZE <= 0:
        _order = []
    elif RIM_EDGE_STYLE == "chamfer":
        _order = [("chamfer", RIM_EDGE_SIZE), ("fillet", RIM_EDGE_SIZE)]
    else:
        _order = [("fillet", RIM_EDGE_SIZE), ("chamfer", RIM_EDGE_SIZE)]
    _candidates = [(style, r) for style, top in _order
                   for r in (top, 4.5, 4.0, 3.5, 3.0, 2.5, 2.0, 1.5, 1.0)]

    for style, r in _candidates:
        try:
            edges = body.edges(_horizontal_z_selector(LOW_WALL_H, tol=1.0,
                                                      max_xy=100.0))
            candidate = edges.chamfer(r) if style == "chamfer" else edges.fillet(r)
        except Exception:
            continue
        if not _valid(candidate):
            continue
        body = candidate
        print(f"  basin rim {style}: {r} mm")
        rim_applied = True
        break
    if not rim_applied:
        print("  basin rim edge: left square"
              if not _order else "  basin rim edge: SKIPPED (all attempts failed)")

    # --- Back wall top (z = BACK_WALL_TOP) ---
    # Smaller fillet to avoid bullnose on a 6mm-thick wall
    try:
        body = body.edges(_horizontal_z_selector(BACK_WALL_TOP, tol=1.0)).fillet(1.5)
    except Exception as e:
        print(f"  back wall top fillet skip: {type(e).__name__}")

    body = _try_progressive(body, "|X and <Z", [FLOOR_EDGE_FILLET, 3, 2], "floor X edges")
    body = _try_progressive(body, "|Y and <Z", [FLOOR_EDGE_FILLET, 3, 2], "floor Y edges")

    # ============================================================
    # 2) Spine bottom
    # ============================================================
    spine_bot_front_y = inner_back_y - SPINE_BOT_INNER_D
    spine_bot_h = SPINE_BOT_TOP - FLOOR
    spine_bot_outer = (
        cq.Workplane("XY")
        .box(SPINE_BOT_W, SPINE_BOT_INNER_D, spine_bot_h, centered=(True, False, False))
        .translate((0, spine_bot_front_y, FLOOR))
    )
    cavity_bw = SPINE_BOT_W - 2*SPINE_BOT_WALL
    cavity_bd = SPINE_BOT_INNER_D - SPINE_BOT_WALL
    spine_bot_cavity = (
        cq.Workplane("XY")
        .box(cavity_bw, cavity_bd, spine_bot_h - SPINE_ROOF_T, centered=(True, False, False))
        .translate((0, spine_bot_front_y + SPINE_BOT_WALL, FLOOR))
    )
    body = body.union(spine_bot_outer.cut(spine_bot_cavity))

    # Bottom-feed openings: LEFT and RIGHT only (front removed).
    # Sized for equidistant border on all four sides of each hole.
    # Side wall dimensions:
    #   - Length along Y (along the side wall) = SPINE_BOT_INNER_D
    #   - Height = spine_bot_h (column height above floor)
    # Hole = wall - 2 * border on each axis.
    feed_w_along_y = SPINE_BOT_INNER_D - 2 * SPINE_FEED_BORDER
    feed_h_along_z = spine_bot_h         - 2 * SPINE_FEED_BORDER
    # Center along Y of the side wall:
    feed_y_center  = spine_bot_front_y + SPINE_BOT_INNER_D / 2
    # Center along Z (vertical center between FLOOR and SPINE_BOT_TOP):
    feed_z_center  = FLOOR + spine_bot_h / 2
    # Box's Z origin (lower face) for centered=False on Z:
    feed_z_bottom  = feed_z_center - feed_h_along_z / 2

    # LEFT side feed
    body = body.cut(
        cq.Workplane("XY")
        .box(SPINE_BOT_WALL + 2, feed_w_along_y, feed_h_along_z, centered=(False, True, False))
        .translate((-SPINE_BOT_W/2 - 1, feed_y_center, feed_z_bottom))
    )
    # RIGHT side feed
    body = body.cut(
        cq.Workplane("XY")
        .box(SPINE_BOT_WALL + 2, feed_w_along_y, feed_h_along_z, centered=(False, True, False))
        .translate((SPINE_BOT_W/2 - SPINE_BOT_WALL - 1, feed_y_center, feed_z_bottom))
    )

    # ============================================================
    # 3) Spine upper - capped top with 1/4" center hole
    # ============================================================
    spine_up_front_y = inner_back_y - SPINE_UP_INNER_D
    spine_up_h = SPINE_TOP_Z - SPINE_BOT_TOP
    spine_up_outer = (
        cq.Workplane("XY")
        .box(SPINE_UP_W, SPINE_UP_INNER_D, spine_up_h, centered=(True, False, False))
        .translate((0, spine_up_front_y, SPINE_BOT_TOP))
    )
    cavity_uw = SPINE_UP_W - 2*SPINE_UP_WALL
    cavity_ud = SPINE_UP_INNER_D - SPINE_UP_WALL

    # LOWER cavity: from spine bottom roof up to the cap bottom
    lower_cavity_h = SPINE_CAP_BOT_Z - SPINE_BOT_TOP
    spine_lower_cavity = (
        cq.Workplane("XY")
        .box(cavity_uw, cavity_ud, lower_cavity_h, centered=(True, False, False))
        .translate((0, spine_up_front_y + SPINE_UP_WALL, SPINE_BOT_TOP))
    )
    spine_up_solid = spine_up_outer.cut(spine_lower_cavity)

    # CUP cavity: from cap top up through and a bit above the spine top
    cup_cavity_h = SPINE_TOP_Z - SPINE_CAP_TOP_Z + 1   # +1 to ensure clean cut through top
    spine_cup_cavity = (
        cq.Workplane("XY")
        .box(cavity_uw, cavity_ud, cup_cavity_h, centered=(True, False, False))
        .translate((0, spine_up_front_y + SPINE_UP_WALL, SPINE_CAP_TOP_Z))
    )
    spine_up_solid = spine_up_solid.cut(spine_cup_cavity)
    body = body.union(spine_up_solid)

    # Drill cavity DOWN through lower spine roof so tube can pass between sections
    body = body.cut(
        cq.Workplane("XY")
        .box(cavity_uw, cavity_ud, SPINE_ROOF_T + 1.5, centered=(True, False, False))
        .translate((0, spine_up_front_y + SPINE_UP_WALL, SPINE_BOT_TOP - SPINE_ROOF_T - 0.5))
    )

    # 1/4" hole through the cap (now at the lower position)
    cap_hole_y = spine_up_front_y + SPINE_UP_WALL + cavity_ud / 2
    body = body.cut(
        cq.Workplane("XY")
        .circle(SPINE_CAP_HOLE_D / 2)
        .extrude(SPINE_CAP_T + 4)
        .translate((0, cap_hole_y, SPINE_CAP_BOT_Z - 2))
    )

    # ============================================================
    # 4) Pools with THREE slits per wall + bottom-rounded stubs
    # ============================================================
    shelf_records = []
    for tier, ((iw, idp), rim_z) in enumerate(zip(POOL_INNER, POOL_RIM_Z)):
        # Where a full-height guide would touch down: the wetted floor of the
        # vessel below this tier - the next pool down, or the basin itself.
        if tier + 1 < len(POOL_RIM_Z):
            land_z = POOL_RIM_Z[tier + 1] - POOL_DEPTH_Z
        else:
            land_z = FLOOR
        outer_w = iw + 2*POOL_WALL
        outer_d = idp + POOL_WALL
        floor_z = rim_z - POOL_DEPTH_Z - POOL_FLOOR_T
        wall_h  = POOL_DEPTH_Z + POOL_FLOOR_T
        slit_h  = POOL_DEPTH_Z * SLIT_FRAC

        # Build pool body (3 walls + floor)
        pool = (cq.Workplane("XY")
                .box(outer_w, outer_d, POOL_FLOOR_T, centered=(True, False, False))
                .translate((0, inner_back_y - outer_d, floor_z)))
        pool = pool.union(cq.Workplane("XY")
                .box(POOL_WALL, outer_d, wall_h, centered=(False, False, False))
                .translate((-outer_w/2, inner_back_y - outer_d, floor_z)))
        pool = pool.union(cq.Workplane("XY")
                .box(POOL_WALL, outer_d, wall_h, centered=(False, False, False))
                .translate((outer_w/2 - POOL_WALL, inner_back_y - outer_d, floor_z)))
        pool = pool.union(cq.Workplane("XY")
                .box(outer_w, POOL_WALL, wall_h, centered=(True, False, False))
                .translate((0, inner_back_y - outer_d, floor_z)))

        pool = _try_progressive(pool, ">Z", [POOL_RIM_FILLET, 1.0],
                                 f"pool rim @ z={rim_z:.0f}")
        body = body.union(pool)

        # The cutter is made TALLER than the visible slit so it cuts cleanly
        # through the rim region. The visible slit bottom stays at rim_z - slit_h,
        # and the cutter extends SLIT_TOP_BUFFER above the rim.
        slit_bot_z = rim_z - slit_h            # visible slit bottom
        cutter_h = slit_h + SLIT_TOP_BUFFER    # cutter total height
        # Cutter center: bottom of cutter at slit_bot_z, top at rim_z + SLIT_TOP_BUFFER
        slit_center_z = slit_bot_z + cutter_h / 2

        # ----- FRONT wall: ONE slit, centered (faces the open basin) -----
        # Note: "XZ" workplane extrudes in -Y direction. So the cutter spans
        # from y=T to y=T-wall_thick after translate by T. To place it INSIDE
        # the wall (which spans front_y_outer to front_y_outer + POOL_WALL),
        # we translate by (front_y_outer + POOL_WALL).
        front_y_outer = inner_back_y - outer_d
        slit = make_slit_cut_xz(SLIT_W, cutter_h, POOL_WALL,
                                 polish_r=SLIT_POLISH_R)
        slit = slit.translate((0, front_y_outer + POOL_WALL, slit_center_z))
        body = body.cut(slit)

        shelf_records.append(dict(
            tier=tier, outer_w=outer_w, f_out=inner_back_y - outer_d,
            back_y=inner_back_y, shelf_z=floor_z, land_z=land_z,
            below_iw=(POOL_INNER[tier + 1][0] if tier + 1 < len(POOL_INNER)
                      else SIZE - 2 * WALL),
            below_f_in=(inner_back_y - (POOL_INNER[tier + 1][1] + POOL_WALL)
                        + POOL_WALL if tier + 1 < len(POOL_INNER)
                        else -(SIZE / 2 - WALL))))

        guide, base_z = drip_guide(SLIT_W, POOL_WALL, slit_h, 'x', floor_z, land_z)
        body = body.union(guide.translate((0, front_y_outer, base_z)))
        if CHANNEL_ENABLE and CHANNEL_DEPTH > 0:
            body = body.cut(make_channel(base_z, rim_z, 'x', front_y_outer, 0.0))

        # ----- LEFT wall: ONE slit, centered along the wall -----
        left_x_outer = -outer_w/2
        side_slit_y = inner_back_y - outer_d/2

        slit = make_slit_cut_yz(SLIT_W, cutter_h, POOL_WALL,
                                 polish_r=SLIT_POLISH_R)
        slit = slit.translate((left_x_outer, side_slit_y, slit_center_z))
        body = body.cut(slit)

        guide, base_z = drip_guide(SLIT_W, POOL_WALL, slit_h, 'y', floor_z, land_z)
        body = body.union(guide.translate((left_x_outer, side_slit_y, base_z)))
        if CHANNEL_ENABLE and CHANNEL_DEPTH > 0:
            body = body.cut(make_channel(base_z, rim_z, 'y', left_x_outer, side_slit_y))

        # ----- RIGHT wall: ONE slit, centered -----
        right_x_outer = outer_w/2

        slit = make_slit_cut_yz(SLIT_W, cutter_h, POOL_WALL,
                                 polish_r=SLIT_POLISH_R)
        slit = slit.translate((right_x_outer - POOL_WALL, side_slit_y, slit_center_z))
        body = body.cut(slit)

        guide, base_z = drip_guide(SLIT_W, POOL_WALL, slit_h, 'y', floor_z, land_z)
        body = body.union(guide.translate((right_x_outer - POOL_WALL,
                                           side_slit_y, base_z)))
        if CHANNEL_ENABLE and CHANNEL_DEPTH > 0:
            body = body.cut(make_channel(base_z, rim_z, 'y', right_x_outer, side_slit_y))

    # ============================================================
    # 5) Re-cut the spine cavity AFTER all pool unions
    # ============================================================
    # Each pool's floor extends back to the cube's back wall, which means it
    # passes through the spine column volume. The pool floor material BLOCKS
    # the spine cavity at each pool's z range. Re-cutting clears it.
    # Re-cut LOWER cavity (everything below the cap)
    body = body.cut(
        cq.Workplane("XY")
        .box(cavity_uw, cavity_ud, lower_cavity_h, centered=(True, False, False))
        .translate((0, spine_up_front_y + SPINE_UP_WALL, SPINE_BOT_TOP))
    )
    # Re-cut CUP cavity (above the cap, open at top)
    body = body.cut(
        cq.Workplane("XY")
        .box(cavity_uw, cavity_ud, cup_cavity_h, centered=(True, False, False))
        .translate((0, spine_up_front_y + SPINE_UP_WALL, SPINE_CAP_TOP_Z))
    )
    # Re-cut the pass-through hole through the lower spine roof
    body = body.cut(
        cq.Workplane("XY")
        .box(cavity_uw, cavity_ud, SPINE_ROOF_T + 1.5, centered=(True, False, False))
        .translate((0, spine_up_front_y + SPINE_UP_WALL, SPINE_BOT_TOP - SPINE_ROOF_T - 0.5))
    )
    # Re-cut the 1/4" cap hole (in case any pool material affected it)
    body = body.cut(
        cq.Workplane("XY")
        .circle(SPINE_CAP_HOLE_D / 2)
        .extrude(SPINE_CAP_T + 4)
        .translate((0, cap_hole_y, SPINE_CAP_BOT_Z - 2))
    )

    # ============================================================
    # 6) Two circular holes through the back wall, leading to spine cavity
    # ============================================================
    # Both 0.78" diameter. Cylinder spans y = 117.3 (3mm outside back face) to
    # y = 97.3 (in cavity, clear of spine front wall at y=73.4-77.4).
    def _back_hole_at_z(z_center):
        return (cq.Workplane("XZ")
                .center(0, z_center)
                .circle(BACK_HOLE_D / 2)
                .extrude(20)
                .translate((0, SIZE/2 + 3, 0)))

    body = body.cut(_back_hole_at_z(BACK_HOLE_Z))     # lower hole
    body = body.cut(_back_hole_at_z(BACK_HOLE_2_Z))   # upper hole

    # ============================================================
    # 7) Breakaway support pins (last, so nothing cuts them away)
    # ============================================================
    if SUPPORT_ENABLE:
        pieces, n_tips, n_trunks = [], 0, 0
        for rec in shelf_records:
            top_z = support_top_z(rec["shelf_z"])
            height = top_z - rec["land_z"]
            if height <= SUPPORT_NECK_H + 1.0:
                continue
            if SUPPORT_STYLE == "wall":
                solids_, run_len = support_walls(rec)
                pieces += solids_
                n_trunks += len(solids_)
                n_tips += run_len
                continue
            spots = support_positions(rec["outer_w"], rec["f_out"], rec["back_y"],
                                      rec["below_iw"], rec["below_f_in"], rec["tier"])
            if not spots:
                continue
            n_tips += len(spots)
            if SUPPORT_STYLE == "tree":
                for group in cluster_tips(spots, SUPPORT_TRUNK_PITCH):
                    pieces += make_support_tree(group, rec["land_z"], top_z)
                    n_trunks += 1
            else:
                for (x, y) in spots:
                    pieces.append(
                        make_support_pin(height).translate((x, y, rec["land_z"])).val())
                    n_trunks += 1

        if pieces:
            # One union of a compound instead of N sequential unions - the
            # sequential version turned a 10 s build into 150 s.
            comp = cq.Compound.makeCompound(pieces)
            body = body.union(cq.Workplane("XY").newObject([comp]))
        if SUPPORT_STYLE == "wall":
            eff = [f"{rec['shelf_z'] - support_top_z(rec['shelf_z']):.2f}"
                   for rec in shelf_records]
            print(f"  breakaway supports: wall, {n_trunks} ribs, "
                  f"{n_tips:.0f} mm of line contact")
            print(f"    z-gap requested {SUPPORT_GAP} mm at {SUPPORT_LAYER_H} mm "
                  f"layers -> effective {' / '.join(eff)} mm (top/mid/bottom)")
        else:
            print(f"  breakaway supports: {SUPPORT_STYLE}, {n_trunks} trunks, "
                  f"{n_tips} contact dots, z-gap {SUPPORT_GAP} mm")

    return body


if __name__ == "__main__":
    print("Building waterfall v13...")
    model = build()
    from pathlib import Path
    out = Path(__file__).resolve().parents[1] / "out" / "stl"
    out.mkdir(parents=True, exist_ok=True)
    cq.exporters.export(model, str(out / "waterfall.step"))
    cq.exporters.export(model, str(out / "waterfall.stl"),
                        tolerance=0.05, angularTolerance=0.1)
    bb = model.val().BoundingBox()
    print(f"Bounding box: {bb.xlen:.1f} x {bb.ylen:.1f} x {bb.zlen:.1f} mm = "
          f"{bb.xlen/INCH:.2f} x {bb.ylen/INCH:.2f} x {bb.zlen/INCH:.2f} in")
    print(f"\n1 slit per wall, 3 walls per pool (front + left + right)")
    print(f"Slit: {SLIT_W:.1f} mm wide x {POOL_DEPTH_Z*SLIT_FRAC:.1f} mm tall, polished perimeter")
    print(f"Spine top: 1/4\" cup with cap + 1/4\" hole through cap")
    print(f"Back wall: {BACK_WALL_TOP/INCH:.2f}\" tall (1/4\" above spine top)")
    print(f"Back holes: {BACK_HOLE_D/INCH:.3f}\" diameter at z={BACK_HOLE_Z/INCH:.2f}\" and z={BACK_HOLE_2_Z/INCH:.2f}\"")
    print(f"Lower spine: {SPINE_BOT_W/INCH:.2f}\" x {SPINE_BOT_INNER_D/INCH:.2f}\" x {SPINE_BOT_TOP/INCH:.2f}\" tall")
    print(f"Side feed border: {SPINE_FEED_BORDER/INCH:.2f}\" on all 4 sides")
    print("Done.")
