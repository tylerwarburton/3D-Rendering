"""Support test coupon.

Three questions this print answers, in one plate:

  ROW A - Z-gap.  The single most important number, and the one that changes
          with material. PETG usually needs more clearance than PLA. Five
          towers at 0.10 / 0.15 / 0.20 / 0.25 / 0.30 mm.
  ROW B - foot neck.  How thin the fused joint can be before ribs come loose
          mid-print, and how cleanly they snap when they don't. Four towers at
          0.4 / 0.6 / 0.8 / 1.0 mm.
  ROW C - bare bridging, NO ribs at all.  Clear spans of 12 / 16 / 20 / 25 mm.
          If your machine bridges these cleanly, the honest answer may be to
          skip modeled supports on the shelf undersides entirely.

Every rib is built by waterfall._rib_solid, the same function the real part
uses, with the module parameters temporarily overridden. Nothing here is a
lookalike - what breaks here breaks the same way there.
"""
import cadquery as cq

from . import paths
import waterfall as W

# --- coupon geometry -------------------------------------------------------
BASE_T = 2.5          # shared base pad, stands in for a pool floor
WALL_T = 2.5          # end walls holding the ceiling up
CEIL_T = 3.0          # ceiling slab, stands in for a pool floor above
TOWER_D = 22.0        # depth (Y) of every tower
RIB_MARGIN = 2.0      # rib inset from the tower ends in Y
GAP_X = 8.0           # clear space between towers
GAP_Y = 10.0          # clear space between rows

TALL_H = 25.0         # rib height for rows A and B
SHORT_H = 10.0        # post height for row C, which has no ribs

LABEL_SIZE = 6.0
LABEL_H = 0.6

ROW_A = [0.10, 0.15, 0.20, 0.25, 0.30]      # Z-gap, mm
ROW_B = [0.4, 0.6, 0.8, 1.0]                # foot neck, mm
ROW_C = [12.0, 16.0, 20.0, 25.0]            # bare bridge span, mm

RIB_PITCH = 10.5      # matches the ~11 mm span the real part runs at
SPAN_A = 28.0         # clear span between the walls of a rows A/B tower


def _label(txt, x, y, z):
    try:
        return (cq.Workplane("XY").workplane(offset=z)
                .text(txt, LABEL_SIZE, LABEL_H, font="DejaVu Sans")
                .translate((x, y, 0)))
    except Exception:
        return None


def _tower(span, height, gap, foot_t, ribs=True, label=""):
    """One test cell: base pad, two end walls, a ceiling, and ribs beneath."""
    w = span + 2 * WALL_T
    solid = cq.Workplane("XY").box(w, TOWER_D, BASE_T,
                                   centered=(True, True, False))
    for sx in (-(span + WALL_T) / 2, (span + WALL_T) / 2):
        solid = solid.union(
            cq.Workplane("XY").box(WALL_T, TOWER_D, height,
                                   centered=(True, True, False))
            .translate((sx, 0, BASE_T)))
    solid = solid.union(
        cq.Workplane("XY").box(w, TOWER_D, CEIL_T, centered=(True, True, False))
        .translate((0, 0, BASE_T + height)))

    if ribs:
        prev_gap, prev_foot = W.SUPPORT_GAP, W.SUPPORT_WALL_FOOT_T
        W.SUPPORT_GAP, W.SUPPORT_WALL_FOOT_T = gap, foot_t
        try:
            n = max(round(span / RIB_PITCH), 1)
            step = span / n
            xs = [-span / 2 + step * (i + 0.5) for i in range(n)]
            y0 = -TOWER_D / 2 + RIB_MARGIN
            length = TOWER_D - 2 * RIB_MARGIN
            top_z = BASE_T + height - gap
            for x in xs:
                rib = W._rib_solid(x, y0, length, BASE_T, top_z)
                solid = solid.union(cq.Workplane("XY").newObject([rib]))
        finally:
            W.SUPPORT_GAP, W.SUPPORT_WALL_FOOT_T = prev_gap, prev_foot

    if label:
        lab = _label(label, 0, 0, BASE_T + height + CEIL_T)
        if lab is not None:
            solid = solid.union(lab)
    return solid, w


def build():
    rows = [
        [(SPAN_A, TALL_H, g, W.SUPPORT_WALL_FOOT_T, True, f"{int(g*100):02d}")
         for g in ROW_A],
        [(SPAN_A, TALL_H, 0.20, f, True, f"{int(f*10)}") for f in ROW_B],
        [(s, SHORT_H, 0.0, 0.0, False, f"{int(s)}") for s in ROW_C],
    ]

    assembly = None
    y_cursor = 0.0
    row_depths = []
    for row in rows:
        widths = []
        x_cursor = 0.0
        built = []
        for (span, h, gap, foot, ribs, label) in row:
            t, w = _tower(span, h, gap, foot, ribs, label)
            built.append((t, w))
            widths.append(w)
        total_w = sum(widths) + GAP_X * (len(widths) - 1)
        x = -total_w / 2
        for (t, w) in built:
            piece = t.translate((x + w / 2, y_cursor, 0))
            assembly = piece if assembly is None else assembly.union(piece)
            x += w + GAP_X
        row_depths.append(TOWER_D)
        y_cursor += TOWER_D + GAP_Y

    # recentre on the origin
    bb = assembly.val().BoundingBox()
    return assembly.translate((-(bb.xmin + bb.xmax) / 2,
                               -(bb.ymin + bb.ymax) / 2, 0))


INSTRUCTIONS = """\
SUPPORT TEST COUPON - what to do with it
========================================

Print settings: use the SAME layer height, material and profile you will use
for the waterfall. The Z-gap results are only valid for the layer height you
test at. Slicer supports OFF - the ribs are part of the model.

ROW A - Z-GAP  (labels 10 / 15 / 20 / 25 / 30 = 0.10 - 0.30 mm)
  Every tower has the same ribs; only the gap under the tip changes.
  Look for:
    - ribs that are WELDED on and tear the ceiling when removed -> gap too small
    - ceilings that SAG or show stringing between ribs           -> gap too large
    - the largest gap that still gives a clean ceiling            -> your number
  Set SUPPORT_LAYER_H / SUPPORT_GAP in src/waterfall.py to the winner.

ROW B - FOOT NECK  (labels 4 / 6 / 8 / 10 = 0.4 - 1.0 mm)
  All at 0.20 gap; only the fused joint at the floor changes.
  Look for:
    - ribs knocked loose or wobbling during the print -> neck too thin
    - ribs that tear mid-height instead of snapping at the floor -> too thick
    - the thinnest neck that survived printing and snapped at the base
  Set SUPPORT_WALL_FOOT_T to the winner.

ROW C - BARE BRIDGING, NO RIBS  (labels 12 / 16 / 20 / 25 = clear span in mm)
  This is the control, and possibly the most useful row. If these ceilings
  bridge cleanly at 20 or 25 mm, you may not need modeled supports on the
  shelf undersides at all - those are exterior surfaces nobody sees, and
  skipping them keeps 3 m of rib scarring out of the water pools.
  Set SUPPORT_ENABLE = False if the bridges look good enough.

HOW TO JUDGE REMOVAL
  Snap each rib with fingers or flush cutters. Note:
    - where it broke (at the floor is right; mid-rib is not)
    - how much force it took
    - what the pool-floor side looks like afterwards - that surface holds
      water in the real part, so residue there matters more than on the ceiling
    - run a fingernail across the ceiling; you should feel witness lines but
      not ridges

The ribs are generated by the same function as the real part, so whatever
these do, the real ones will do too.
"""


def run():
    print("support test coupon:")
    solid = build()
    bb = solid.val().BoundingBox()
    out = paths.STL / "support_test.stl"
    cq.exporters.export(solid, str(out), tolerance=0.02, angularTolerance=0.05)
    print(f"  plate {bb.xlen:.0f} x {bb.ylen:.0f} x {bb.zlen:.0f} mm, "
          f"{solid.val().Volume()/1000:.0f} cm3, valid={solid.val().isValid()}")
    txt = paths.OUT / "support_test_instructions.txt"
    txt.write_text(INSTRUCTIONS)
    print(f"  {paths.rel(out)}")
    print(f"  {paths.rel(txt)}")
    return solid
