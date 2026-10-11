"""
Parametric constants for the Miata NA turn-signal air duct -> 2.5in tube adapter.

Coordinate system:
    X = across the 136 mm dimension of the OEM frame (width)
    Y = across the 44 mm dimension of the OEM frame (height)
    Z = flow axis. Z=0 is the open mouth that slides onto the frame,
        +Z is downstream toward the 2.5 in tube.

Every dimension the physical part depends on lives here. Change a number,
re-run `python build.py all`, re-check the renders.
"""

# ---------------------------------------------------------------- OEM frame
FRAME_W          = 136.0   # long dimension, external
FRAME_H          = 44.0    # short dimension, external
FRAME_CORNER_R   = 6.0     # corner radius of the frame's external outline

# The long faces are flat and parallel. The two SHORT ends flare outward,
# opening up as you go away from the outlet - so 136 mm is the narrowest
# width, at the outer rim, and the mouth of the adapter is wider.
# Angles are measured from the push direction (Z). The aggressive end is the
# one the first connector is further from (30 mm in, the -X end here).
FRAME_DRAFT_NX   = 20.0    # degrees, -X short end (15 read too shallow)
FRAME_DRAFT_PX   = 7.5     # degrees, +X short end

# ---------------------------------------------------------------- fit
SOCKET_CLEAR     = 0.75    # radial gap between frame OD and socket ID
                           # 0.40 printed a touch too snug
SOCKET_DEPTH     = 28.0    # how far the adapter swallows the frame
WALL             = 3.0     # nominal wall on the socket / transition
STOP_LEDGE       = 2.0     # inward step at the end of the socket: frame butts here
COLLAR_LEN       = 11.0    # straight band above the socket - carries the
                           # side labels and stiffens the mouth
MOUTH_LEADIN     = 2.0     # chamfer at the mouth so it starts onto the frame easily

# friction ribs (crush ribs) inside the socket -------------------------------
RIB_ENABLE       = True
RIB_PROUD        = 0.60    # how far each rib intrudes into the bore
RIB_WIDTH        = 2.4
RIB_START_Z      = 1.5     # ribs start this far in from the mouth
RIB_RAMP         = 4.0     # length of the 45-ish lead-in ramp
RIB_END_INSET    = 1.0     # stop this far short of the stop ledge
RIB_EMBED        = 0.6     # how far each rib is buried in the wall
RIB_X_LONG       = (-56.0, 6.0, 60.0)   # rib positions on the two long faces
RIB_Y_SHORT      = (-18.0, 18.0)        # rib positions on the two short faces

# ---------------------------------------------------------------- connectors
# The OEM piece has six raised rectangular connectors: one centred on each
# short end, two evenly spaced on each long end.
TAB_L            = 14.0    # connector length (along the face it sits on)
                           # measured on the car: 30 mm -> 44 mm from one end
TAB_W            = 6.0     # connector width
TAB_PROUD        = 3.0     # how far it stands off the frame  (best guess - tune me)
TAB_CLEAR        = 1.0     # lateral clearance around the tab in its pocket
TAB_CLEAR_AX     = 0.5     # ... and along the flow axis (pocket 7.0 tall)
# The pocket has to clear the tab AND leave room for the zip tie to pass
# over it - at 0.6 mm there was only 0.6 mm of gap and a tie is ~1.4 mm.
TIE_THICK        = 1.4     # zip-tie strap thickness
TAB_DEPTH_CLEAR  = TIE_THICK + 0.4   # extra pocket depth over TAB_PROUD

# --- where the six connectors sit -------------------------------------------
# All positions are in FRAME coordinates, measured from the centre of the
# 136 x 44 opening:
#   X runs along the 136 mm dimension, +X toward one short end
#   Y runs along the 44 mm dimension
# The two long faces are independent, so they do NOT have to mirror each
# other, and neither pair has to be centred.
#
# Measured off the car, from the -X end face:
#   first connector   30.0 -> 44.0 mm      centre 37.0
#   61 mm edge to edge, so the second runs 105.0 -> 119.0, centre 112.0
# Converted to frame centre coordinates (subtract FRAME_W / 2 = 68):
#   112 -> 105 -> 109 for the second, and 37 -> 33 -> 38 for the first,
#   each step checked against a print
_MEAS_FROM_NX    = (38.0, 109.0)
TAB_X_FACE_PY    = tuple(v - FRAME_W / 2.0 for v in _MEAS_FROM_NX)  # -31, +44
TAB_X_FACE_NY    = tuple(v - FRAME_W / 2.0 for v in _MEAS_FROM_NX)

# for reference only - derived, not inputs
TAB_LONG_SPACING = TAB_X_FACE_PY[1] - TAB_X_FACE_PY[0]          # 75.0
TAB_LONG_SKEW    = (TAB_X_FACE_PY[0] + TAB_X_FACE_PY[1]) / 2.0  # +6.5
TAB_Y_FACE_PX    = 0.0     # the single connector on the +X short end
TAB_Y_FACE_NX    = 0.0     # ... and on the -X short end

# The connectors sit at the TOP of the frame, flush with the outer rim -
# not recessed. This is the distance from the rim to the tab CENTRE, so
# TAB_W / 2 puts the tab's top edge exactly on the rim.
TAB_Z_FROM_RIM   = TAB_W / 2.0

# The connector's 12 mm axis is assumed to run ACROSS the face (laterally),
# its 6 mm axis along the flow direction Z.
# local boss that thickens the wall around each connector
BOSS_LAT         = 28.0    # boss size across the face
BOSS_AX          = 24.0    # boss size along Z
BOSS_T           = 4.2     # extra wall added outward at the boss
BOSS_R           = 5.0     # boss corner radius
BOSS_DRAFT       = 2.0     # per-side taper from wall face to boss tip

# zip-tie slots: one each side of the connector (offset along Z). The tie
# drops through slot A, passes through/around the connector, comes back up
# slot B and closes over the bridge of material between them.
TIE_SLOT_LAT     = 9.0     # slot length across the face
TIE_SLOT_AX      = 5.2     # slot width along Z - takes a 4.8 mm heavy tie
TIE_SLOT_GAP     = 1.2     # axial gap between pocket edge and slot edge

# The OEM connector is HOLLOW, so the tie does not wrap the tab: it enters
# the upper port, threads down through the connector, and leaves by the
# lower port. Each port therefore slants from the outside face into the
# POCKET and stops there - the pockets are the only breaks in the inner
# wall, and nothing opens into the duct itself.
TIE_PORT_IN_AX   = 4.0     # axial size of the port where it meets the pocket
TIE_PORT_IN_OFF  = 1.3     # ... and how far that opening sits off tab centre
TIE_PORT_OUT_OFF = 7.6     # axial offset of the opening on the outside face
TIE_PORT_START   = 0.5     # depth at which the port begins, inside the pocket
                           # (never 0 - that would sit on the bore surface)
TIE_SLOT_R       = 1.6     # slot corner radius

# ---------------------------------------------------------------- labels
# A / B / C / D are embossed on the four outside walls, and the two
# connectors on each long face are numbered 1 and 2 counting from the A end.
#   A = -X short end (the 15 deg flare)   B = +Y long face
#   C = +X short end (the 7.5 deg flare)  D = -Y long face
LABEL_ENABLE     = True
LABEL_SIZE       = 8.0     # cap height, mm
LABEL_Z_FRAC     = 0.23    # height up the socket, as a fraction of its depth
LABEL_PROUD      = 0.8     # how far the letters stand off the wall
LABEL_FONT       = "DejaVu Sans"
# the letters live on the collar, so each number sits directly above the
# connector it names

# ---------------------------------------------------------------- transition
TRANS_LEN        = 68.0    # rectangle -> round blend length
TRANS_LEAD       = 2.0     # straight lead at each end of the blend (tangency)
TRANS_SECTIONS   = 17      # loft sections across the blend

# ---------------------------------------------------------------- outlet
OUTLET_OD        = 63.5    # 2.5 in external diameter
OUTLET_WALL      = 2.5
OUTLET_LEN       = 42.0

BEAD_ENABLE      = True
BEAD_HEIGHT      = 2.0     # radial rise of the retention bead
BEAD_FLAT        = 1.6
BEAD_RAMP        = 2.2
BEAD_FROM_END    = 12.0    # bead centre, measured back from the outlet face

# ---------------------------------------------------------------- clamshell
# The socket is split down one wall so it springs over the frame, then a zip
# tie across two clamp ears pulls the split shut and stops it flexing again.
# The split stops at the collar - the blend and tube stay closed.
SPLIT_ENABLE     = True
SPLIT_FACE       = "+Y"    # side B
SPLIT_X          = 0.0     # frame X of the split
SPLIT_W          = 1.2     # split width
SPLIT_TOP        = 37.0    # how far up the split runs
SPLIT_RELIEF_R   = 1.6     # round at the top of the split - a square end
                           # there is exactly where a flexing part cracks

EAR_ENABLE       = True
EAR_GAP          = 2.0     # inner edge of each ear, from the split centre
EAR_LAT          = 10.0    # ear width along the wall
EAR_AX           = 18.0    # ear height at its base
EAR_AX_TIP       = 10.0    # ... and at its tip
EAR_TIP_SHIFT    = 4.0     # tip shifted up, so the underside self-supports
EAR_PROUD        = 8.0     # how far the ears stand off the wall
EAR_R            = 2.5     # corner radius
EAR_Z            = 14.0    # centre height of the ear base
EAR_HOLE_Z       = 18.0    # centre height of the tie hole
EAR_HOLE_H       = 5.6     # tie hole, along Z
EAR_HOLE_T       = 2.4     # tie hole, through the wall direction

# ---------------------------------------------------------------- coupons
# The mouth-ring coupon gets a thin slit through one wall so it is a C, not
# a closed loop, and can spring open over the frame.
COUPON_SLIT      = False   # the part carries the split itself now
COUPON_SLIT_FACE = "+Y"    # side B
COUPON_SLIT_X    = 0.0     # frame X of the slit centre
COUPON_SLIT_W    = 1.2     # slit width

# ---------------------------------------------------------------- output
STL_TOLERANCE    = 0.05
STL_ANG_TOL      = 0.15
LAYER_HEIGHT     = 0.20    # used only for reporting / print notes

# derived ---------------------------------------------------------------
# A function, not module-level lines, so `build.py --set` can override
# SOCKET_CLEAR / WALL / SOCKET_DEPTH / COLLAR_LEN and then re-derive.
def derive():
    global SOCK_ID_HW, SOCK_ID_HH, SOCK_ID_R, SOCK_OD_HW, SOCK_OD_HH,         SOCK_OD_R, Z_TRANS_0, LABEL_Z, Z_TRANS_1, Z_END
    SOCK_ID_HW = FRAME_W / 2.0 + SOCKET_CLEAR
    SOCK_ID_HH = FRAME_H / 2.0 + SOCKET_CLEAR
    SOCK_ID_R  = FRAME_CORNER_R + SOCKET_CLEAR
    SOCK_OD_HW = SOCK_ID_HW + WALL
    SOCK_OD_HH = SOCK_ID_HH + WALL
    SOCK_OD_R  = SOCK_ID_R + WALL

    Z_TRANS_0  = SOCKET_DEPTH + COLLAR_LEN
    # the bosses now run right up into the collar, so the letters go BELOW
    # the connectors instead of above them
    LABEL_Z    = SOCKET_DEPTH * LABEL_Z_FRAC
    Z_TRANS_1  = SOCKET_DEPTH + TRANS_LEN
    Z_END      = Z_TRANS_1 + OUTLET_LEN


derive()


# ---------------------------------------------------------------- sanity
def _check_layout():
    """Connector bosses and crush ribs must not land on top of each other."""
    half_boss = BOSS_LAT / 2.0
    half_rib = RIB_WIDTH / 2.0
    flat = SOCK_ID_HW - SOCK_ID_R
    problems = []
    for face, xs in (("+Y", TAB_X_FACE_PY), ("-Y", TAB_X_FACE_NY)):
        for x in xs:
            if abs(x) + half_boss > flat:
                problems.append(f"boss on {face} at x={x:+.1f} runs into the "
                                f"corner radius (flat ends at {flat:.1f})")
            for r in RIB_X_LONG:
                if abs(r - x) < half_boss + half_rib:
                    problems.append(f"crush rib at x={r:+.1f} collides with "
                                    f"the {face} boss at x={x:+.1f}")
    if len(TAB_X_FACE_PY) == 2 and \
            abs(TAB_X_FACE_PY[1] - TAB_X_FACE_PY[0]) < BOSS_LAT:
        problems.append("the two +Y connectors are closer together than one "
                        "boss is wide")
    if problems:
        raise ValueError("connector layout problem:\n  - "
                         + "\n  - ".join(problems))


_check_layout()
