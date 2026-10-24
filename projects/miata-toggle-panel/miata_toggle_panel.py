"""Two-toggle insert for the downloaded Miata dashboard-switch bezel."""
from pathlib import Path

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
FRONT_SHOULDER_X = BODY_BASE_X + 2.0
FRONT_SHOULDER_DEPTH = 3.0
BODY_DEPTH = 20.0
BODY_CLEAR = 0.4       # per side around the provisional rear-body envelope
CHANNEL_X = max(BODY_ROT_X, FRONT_SHOULDER_X) + 2 * BODY_CLEAR
CHANNEL_Y = BODY_ROT_Y + 2 * BODY_CLEAR
PANEL_BACK_Z = FRONT_Z - PANEL_T
BODY_FRONT_Z = PANEL_BACK_Z - 0.1
PLUG_BACK_Z = -23.0    # original source ends at -18.5 mm
CENTER_WALL_T = HOLE_SPACING - CHANNEL_X
CENTER_WALL_Y = 27.3
CENTER_WALL_FRONT_Z = PANEL_BACK_Z + 0.1
SOURCE_INNER_LEFT_X = 4.875
SOURCE_INNER_RIGHT_X = 44.875
SOURCE_INDENT_Y = 27.3
SOURCE_INDENT_Z0 = PLUG_BACK_Z
SOURCE_INDENT_Z1 = PANEL_BACK_Z

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
    """Clear the old rear walls and the source's wider centre rib."""
    top = PANEL_BACK_Z
    channels = [
        pk.move(pk.box(CHANNEL_X, CHANNEL_Y, top - (-30.0)), x, y, -30.0)
        for x, y in hole_centres()
    ]
    channels.append(pk.move(
        pk.box(CENTER_WALL_T + 0.2, CHANNEL_Y, top - (-30.0)),
        BEZEL_CX,
        BEZEL_CY,
        -30.0,
    ))
    return channels


def _main_body(mesh):
    """Drop tiny wall slivers orphaned by the enlarged switch channels."""
    bodies = mesh.split(only_watertight=False)
    return pk._check(max(bodies, key=lambda body: abs(body.volume)))


def _center_wall():
    """One straight divider between the two switch clearance channels."""
    return pk.move(
        pk.box(CENTER_WALL_T, CENTER_WALL_Y, CENTER_WALL_FRONT_Z - PLUG_BACK_Z),
        BEZEL_CX,
        BEZEL_CY,
        PLUG_BACK_Z,
    )


def _rear_profile_envelope():
    """Solid extrusion of the original rear plug's curved XY outline."""
    band_z0, band_h = -18.49, 1.0
    band = pk.intersection(
        source_blank(),
        pk.move(pk.box(60.0, 40.0, band_h), BEZEL_CX, BEZEL_CY, band_z0),
    )
    envelope = band.convex_hull
    lo, hi = envelope.bounds[:, 2]
    envelope.vertices[:, 2] = (
        PLUG_BACK_Z
        + (envelope.vertices[:, 2] - lo)
        / (hi - lo)
        * (PANEL_BACK_Z - PLUG_BACK_Z)
    )
    return pk._check(envelope)


def _flush_outer_indents():
    """Fill both outer walls flush across each complete channel-side plane."""
    centres = hole_centres()
    left_plane = centres[0][0] - CHANNEL_X / 2
    right_plane = centres[1][0] + CHANNEL_X / 2
    h = SOURCE_INDENT_Z1 - SOURCE_INDENT_Z0
    envelope = _rear_profile_envelope()
    raw = [
        pk.move(
            pk.box(left_plane - SOURCE_INNER_LEFT_X, SOURCE_INDENT_Y, h),
            (SOURCE_INNER_LEFT_X + left_plane) / 2,
            BEZEL_CY,
            SOURCE_INDENT_Z0,
        ),
        pk.move(
            pk.box(SOURCE_INNER_RIGHT_X - right_plane, SOURCE_INDENT_Y, h),
            (right_plane + SOURCE_INNER_RIGHT_X) / 2,
            BEZEL_CY,
            SOURCE_INDENT_Z0,
        ),
    ]
    return [pk.intersection(part, envelope) for part in raw]


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
    cleared = _main_body(pk.difference(filled, *_rear_channels()))
    supported = pk.union(cleared, _center_wall(), *_flush_outer_indents())
    cutters = [
        pk.move(pk.cylinder(HOLE_D / 2, PANEL_T + 2, z0=FRONT_Z - PANEL_T - 1), x, y)
        for x, y in hole_centres()
    ]
    return _main_body(pk.difference(supported, *cutters))


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
