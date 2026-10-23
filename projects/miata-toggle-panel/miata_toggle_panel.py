"""Two-toggle insert for the downloaded Miata dashboard-switch bezel."""
from pathlib import Path

import trimesh

from shared import printkit as pk

HERE = Path(__file__).resolve().parent

# ---- measured from the source STL --------------------------------------------
BEZEL_CX = 24.875
BEZEL_CY = 13.65
OPENING_X = 41.5
OPENING_Y = 24.5
FRONT_Z = 2.0

# ---- first-print assumptions: confirm against the actual toggle hardware -----
HOLE_D = 12.2          # 12 mm threaded bushing + 0.1 mm radial clearance
HOLE_SPACING = 19.75
PANEL_T = 2.4          # thin enough for a normal threaded bushing and nut
PANEL_OVERLAP = 0.25   # into the bezel on every edge; booleans must overlap

# Rotated rear-body clearance and stabilizer cage (first fit-test assumptions)
BODY_ROT_X = 15.0      # centred protrusion envelope after Tyler's correction
BODY_ROT_Y = 29.0      # body height turned across the bezel's short axis
BODY_BASE_X = 14.0
PROTRUSION_Y = 21.0    # centred, leaving ~4 mm plain base at each end
BODY_DEPTH = 20.0
BODY_CLEAR = 0.4       # per side around the provisional rear-body envelope
CHANNEL_X = BODY_ROT_X + 2 * BODY_CLEAR
CHANNEL_Y = BODY_ROT_Y + 2 * BODY_CLEAR
PANEL_BACK_Z = FRONT_Z - PANEL_T
PLUG_BACK_Z = -23.0    # original source ends at -18.5 mm
GUIDE_Y = 8.0
OUTER_ARM_T = 1.6
CENTER_FINGER_T = 1.2
CENTER_CORE_T = 0.65
CENTER_SLOT = 0.10
GUIDE_CLEAR = 0.05
SNAP_INTERFERENCE = 0.10
CLIP_WALL_Y = 27.3       # never exceed the downloaded plug-wall width
CLIP_TAB_Y = 2.6
CLIP_SLOT = 1.0
CLIP_ANCHOR_Z = -1.2
CLIP_TIP_Z = -22.5
FLEX_BACK_CLEAR = 1.5
FLEX_FRONT_CLEAR = 0.2
HOOK_INTERFERENCE = 1.00
HOOK_PROTRUSION = GUIDE_CLEAR + HOOK_INTERFERENCE
HOOK_Y = 2.2
HOOK_PEAK_Z = -14.0    # moved closer to the printed face
HOOK_RELEASE_Z = -10.0

SOURCE_FILE = HERE / "source" / "miata_starter_switch_blank (1).stl"


def source_blank():
    """Downloaded bezel, with its one missing source triangle repaired."""
    mesh = pk.load(SOURCE_FILE)
    if not mesh.is_watertight and not mesh.fill_holes():
        raise RuntimeError("source bezel could not be repaired")
    return pk._check(mesh)


def hole_centres():
    """Hole centres in the downloaded bezel's coordinate frame."""
    half = HOLE_SPACING / 2
    return ((BEZEL_CX - half, BEZEL_CY),
            (BEZEL_CX + half, BEZEL_CY))


def _extended_blank():
    """Stretch the source's rear-most profile to 23 mm without changing x/y."""
    source = source_blank()
    band_z0, band_h = -18.49, 1.0
    band = pk.intersection(
        source,
        pk.move(pk.box(60.0, 40.0, band_h), BEZEL_CX, BEZEL_CY, band_z0),
    )
    band.vertices[:, 2] = PLUG_BACK_Z + (band.vertices[:, 2] - band_z0) * 5.0
    return pk.union(source, pk._check(band))


def _rear_channels():
    """Clear the old rear walls around both 90-degree switch bodies."""
    top = PANEL_BACK_Z - 0.05
    return [
        pk.move(pk.box(CHANNEL_X, CHANNEL_Y, top - (-30.0)), x, y, -30.0)
        for x, y in hole_centres()
    ]


def _hook_wedge(tab_x, tab_y, inward, tab_t):
    """Two-way ramp at a tab tip: forced aside on insertion and removal."""
    face_x = tab_x + inward * tab_t / 2
    tip_x = face_x + inward * HOOK_PROTRUSION
    points = []
    for y in (tab_y - HOOK_Y / 2, tab_y + HOOK_Y / 2):
        points += [(face_x, y, CLIP_TIP_Z),
                   (tip_x, y, HOOK_PEAK_Z),
                   (face_x, y, HOOK_RELEASE_Z)]
    wedge = trimesh.convex.convex_hull(points)
    if wedge.volume < 0:
        wedge.invert()
    return pk._check(wedge)


def _clip_wall(wall_x, wall_t, tabs):
    """A solid short wall with U-channels and flex tongues inside them.

    tabs: (tab_x, tab_y, inward, tab_thickness). The channel opens at the
    rear and sides; the tongue remains joined to the wall only at its front.
    """
    guide_h = -PLUG_BACK_Z
    wall = pk.move(pk.box(wall_t, CLIP_WALL_Y, guide_h), wall_x, BEZEL_CY, PLUG_BACK_Z)
    channel_z0 = PLUG_BACK_Z - 0.1
    channel_h = CLIP_ANCHOR_Z - channel_z0
    cutters = []
    wall_lo, wall_hi = wall_x - wall_t / 2, wall_x + wall_t / 2
    for tab_x, tab_y, inward, tab_t in tabs:
        # The cavity is deliberately larger behind the tongue (opposite its
        # hook direction), giving a 1 mm-deflecting tab 1.5 mm of travel.
        back = tab_x - inward * (tab_t / 2 + FLEX_BACK_CLEAR)
        front = tab_x + inward * (tab_t / 2 + FLEX_FRONT_CLEAR)
        x0, x1 = min(wall_lo, wall_hi, back, front), max(wall_lo, wall_hi, back, front)
        cutters.append(pk.move(
            pk.box(x1 - x0, CLIP_TAB_Y + 2 * CLIP_SLOT, channel_h),
            (x0 + x1) / 2, tab_y, channel_z0,
        ))
    parts = [pk.difference(wall, *cutters)]
    tab_h = -CLIP_TIP_Z
    for tab_x, tab_y, inward, tab_t in tabs:
        parts += [pk.move(pk.box(tab_t, CLIP_TAB_Y, tab_h), tab_x, tab_y, CLIP_TIP_Z),
                  _hook_wedge(tab_x, tab_y, inward, tab_t)]
    return parts


def _stabilizer_cage():
    """Open-sided cage with four U-slotted, hooked flex tongues."""
    centres = hole_centres()
    half_clip = BODY_ROT_X / 2
    half_base = BODY_BASE_X / 2
    left_x = centres[0][0] - half_clip - GUIDE_CLEAR - OUTER_ARM_T / 2
    right_x = centres[1][0] + half_clip + GUIDE_CLEAR + OUTER_ARM_T / 2
    protrusion_low = BEZEL_CY - PROTRUSION_Y / 2
    protrusion_high = BEZEL_CY + PROTRUSION_Y / 2
    low_tab_y = (0.0 + protrusion_low) / 2
    high_tab_y = (protrusion_high + 27.3) / 2
    guide_h = -PLUG_BACK_Z
    rails = []

    # Bottom/top short walls: one tongue at each plain-base end.
    left_tab_x = centres[0][0] - half_base - GUIDE_CLEAR - OUTER_ARM_T / 2
    right_tab_x = centres[1][0] + half_base + GUIDE_CLEAR + OUTER_ARM_T / 2
    rails += _clip_wall(
        left_x, OUTER_ARM_T,
        [(left_tab_x, low_tab_y, +1, OUTER_ARM_T),
         (left_tab_x, high_tab_y, +1, OUTER_ARM_T)],
    )
    rails += _clip_wall(
        right_x, OUTER_ARM_T,
        [(right_tab_x, low_tab_y, -1, OUTER_ARM_T),
         (right_tab_x, high_tab_y, -1, OUTER_ARM_T)],
    )

    # The centre column is a narrow fixed core with an independent finger on
    # each side, so each switch can deflect its own clip without moving the other.
    lower_inner = centres[0][0] + half_base + GUIDE_CLEAR
    upper_inner = centres[1][0] - half_base - GUIDE_CLEAR
    lower_finger_x = lower_inner + CENTER_FINGER_T / 2
    upper_finger_x = upper_inner - CENTER_FINGER_T / 2
    # Fill the complete 2.75 mm gap between the provisional body envelopes;
    # outside each tongue channel the centre wall is flush to both switches.
    center_wall_t = HOLE_SPACING - BODY_ROT_X
    rails += _clip_wall(
        BEZEL_CX,
        center_wall_t,
        [(lower_finger_x, low_tab_y, -1, CENTER_FINGER_T),
         (lower_finger_x, high_tab_y, -1, CENTER_FINGER_T),
         (upper_finger_x, low_tab_y, +1, CENTER_FINGER_T),
         (upper_finger_x, high_tab_y, +1, CENTER_FINGER_T)],
    )

    # No walls along the 29 mm switch faces: their broad edges remain open to
    # tolerate measurement error and prevent a too-tight rectangular sleeve.
    return rails


def design_frame():
    """Completed part in the source STL frame, front face at z=FRONT_Z."""
    panel_x = OPENING_X + 2 * PANEL_OVERLAP
    panel_y = OPENING_Y + 2 * PANEL_OVERLAP
    panel = pk.move(
        pk.box(panel_x, panel_y, PANEL_T),
        BEZEL_CX,
        BEZEL_CY,
        FRONT_Z - PANEL_T,
    )
    filled = pk.union(_extended_blank(), panel)
    cleared = pk.difference(filled, *_rear_channels())
    supported = pk.union(cleared, *_stabilizer_cage())
    cutters = [
        pk.move(pk.cylinder(HOLE_D / 2, PANEL_T + 2, z0=FRONT_Z - PANEL_T - 1), x, y)
        for x, y in hole_centres()
    ]
    return pk.difference(supported, *cutters)


def two_toggle_panel():
    """One dashboard shim for two panel-mount toggle switches; print 3."""
    # Front face on the bed: clean face, vertical holes, original shell upward.
    return pk.on_bed(pk.rotate(design_frame(), 180, (1, 0, 0)))


PARTS = {
    "two_toggle_panel": two_toggle_panel,
}

# The original bezel contains intentional bridge faces. A dedicated test checks
# that the insert adds no new unsupported area relative to that source geometry.
OVERHANG_OK = {"two_toggle_panel": None}
