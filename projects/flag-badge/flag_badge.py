"""flag-badge - every part as a function returning a trimesh in PRINT
orientation (flat side down, mm). Put dimensions in the constants block and
note where real-world numbers came from in CLAUDE.md."""
from pathlib import Path

import numpy as np
import trimesh

from shared import printkit as pk

HERE = Path(__file__).resolve().parent

# ---- dimensions --------------------------------------------------------------
CLEAR = 0.3            # per side, for anything that fits into something

# Flag (US proportions: hoist 1 : fly 1.9, 13 stripes, canton 7 stripes x 0.76 hoist)
FLAG_H = 50.0          # hoist (height) of the flag, mm
FLAG_L = FLAG_H * 1.9  # fly (length)
STRIPE = FLAG_H / 13
CANTON_W = 0.76 * FLAG_H
CANTON_H = 7 * STRIPE
RAISE = 1.2            # stripes + star nubs stand this far off the backing (6 layers)
GAP = 0.01             # slit between neighbouring pieces -> separate faces to paint
STAR_D = 0.0616 * FLAG_H * 0.9   # nub base diameter (official star size, a bit smaller)
STAR_DOME = 0.4        # canton version: star = post in a canton hole (+GAP all round) with
                       # a rounded top this tall, peak level with the canton -> looks indented
EMBED = 0.3            # pieces sink this far into what they sit on (no flush booleans)

# Test plate the flag sits on
MARGIN = 6.0           # backing border around the flag
PLATE_T = 4.0          # backing thickness


# ---- flag pieces (flag frame: x along fly, y up the hoist, z out of the face) --
def _slab(x0, x1, y0, y1, z0, z1):
    return pk.move(pk.box(x1 - x0, y1 - y0, z1 - z0), (x0 + x1) / 2, (y0 + y1) / 2, z0)


def _star_centres():
    """50 stars: 9 rows alternating 6 and 5 (official spacing 0.063 / 0.054 hoist)."""
    gx, gy = 0.063 * FLAG_H, 0.054 * FLAG_H
    out = []
    for row in range(9):
        y = FLAG_H - gy * (row + 1)
        cols = range(6) if row % 2 == 0 else range(5)
        off = gx if row % 2 == 0 else 2 * gx
        out += [(off + 2 * gx * c, y) for c in cols]
    return out


def _nub(x, y, dome):
    """Star: STAR_D wide, peak level with the stripes (RAISE), rounded top
    `dome` tall. dome = RAISE -> a plain nub on the backing; less -> a post
    with a domed top (sits in a canton hole)."""
    a = STAR_D / 2
    r = (a * a + dome * dome) / (2 * dome)
    s = trimesh.creation.icosphere(subdivisions=3, radius=r)
    s.apply_translation((x, y, RAISE - r))
    if dome >= RAISE:
        return s
    return pk.intersection(s, pk.move(pk.cylinder(a, RAISE + 2 * EMBED, z0=-EMBED), x, y))


def flag_pieces(canton=False):
    """Every raised piece, each its own solid, GAP apart from its neighbours.
    canton=False: the backing is the blue, stars are nubs on it.
    canton=True: a raised blue canton with the stars in holes through it."""
    g = GAP / 2
    z0, z1 = -EMBED, RAISE
    stars = _star_centres()
    pieces = []
    if canton:
        c = _slab(0, CANTON_W - g, FLAG_H - CANTON_H + g, FLAG_H, z0, z1)
        holes = [pk.move(pk.cylinder(STAR_D / 2 + GAP, RAISE + 2, z0=-1), x, y) for x, y in stars]
        pieces.append(pk.difference(c, *holes))
    for i in range(13):                                       # stripe 0 = top (red)
        top, bot = FLAG_H - i * STRIPE, FLAG_H - (i + 1) * STRIPE
        x0 = CANTON_W + g if i < 7 else 0.0
        pieces.append(_slab(x0, FLAG_L, bot + (g if i < 12 else 0), top - (g if i else 0), z0, z1))
    pieces += [_nub(x, y, STAR_DOME if canton else RAISE) for x, y in stars]
    return pieces


def _to_print(m):
    """Flag frame -> print: plate stands on its long edge, flag face toward -Y,
    stripes horizontal, canton top-left (flying)."""
    return pk.on_bed(pk.rotate(m, 90, (1, 0, 0)))


# ---- parts -------------------------------------------------------------------
def flag_test_plate(canton=False):
    """Backing rectangle (one flat face around the flag) + raised paintable flag."""
    plate = _slab(-MARGIN, FLAG_L + MARGIN, -MARGIN, FLAG_H + MARGIN, -PLATE_T, 0)
    return _to_print(pk.union(plate, *flag_pieces(canton)))


# ---- the real thing: connector + left/right walls ---------------------------
# Source files are in one assembly frame except the walls, which sit 244.54 mm
# off in x and 18.73 low: their 3 rod holes line up with the connector ear
# holes (x 219.36 / 232.19 / 245.1) and they stand on the ear tops (z 208.21).
WALL_SHIFT = (219.36 + 25.14, 0.0, 208.2132 - 189.4812)
SEAM_Z = 208.2132      # ear top = wall bottom
WALL_FLIP_X = 232.19   # middle ear rod hole: walls flip about it
END_Y = {+1: -187.9262, -1: -273.9068}   # flat outer end faces (left wall end / right wall end)
# One upright banner per end (stripes run up/down, canton at the BOTTOM; the
# two ends mirror each other - Tyler). Entirely on the walls (Tyler), using
# the rounded edges: x where the face is within ~2 mm of flat.
END_X = (213.5, 250.5)
END_RAISE = 0.6        # Tyler: less raised than the 1.2 test plates
END_DOME = 0.3         # indented-star dome height
FLAG_GAP = 2.0         # flag starts this far past the seam (wall bottom), toward the wall's far end
LOGO_BOX = (212.5, 243.5, 165.5, 204.5)    # x0, x1, z0, z1 to search for the engraved logo (+y end)


def _src(name):
    """Source piece in assembly position. Walls: shifted onto the ears, then
    flipped end over end about the middle rod hole (Tyler: in use their
    rounded edge goes up / U edge down, like the connector's) - the rod holes
    still line up and the outer (flag) face stays outward."""
    m = pk.load(HERE / "source" / f"{name}.stl")
    if name not in ("left", "right"):
        return m
    m = pk.move(m, *WALL_SHIFT)
    zc = m.bounds[:, 2].mean()
    return pk.move(pk.rotate(pk.move(m, -WALL_FLIP_X, 0, -zc), 180, (0, 1, 0)), WALL_FLIP_X, 0, zc)


def _depth(m, sign, z, xs):
    """How far the surface sits below the flat end face at each x (>= 0)."""
    o = np.c_[xs, np.full_like(xs, END_Y[sign] + sign * 50), np.full_like(xs, z)]
    loc, ri, _ = m.ray.intersects_location(o, np.tile([0, -sign, 0], (len(xs), 1)))
    d = np.full(len(xs), np.nan)
    if len(loc) == 0:
        return d
    for k in range(len(xs)):
        h = loc[ri == k][:, 1]
        if len(h):
            d[k] = sign * (END_Y[sign] - (h.max() if sign > 0 else h.min()))
    return d


def _contour_piece(prof, sign, x0, x1, z0, z1, top):
    """Raised piece over x0..x1, z0..z1 that follows the surface profile
    (depth(x)), standing `top` off it and EMBED into it."""
    xs = np.linspace(x0, x1, max(2, int((x1 - x0) / 0.25) + 1))
    d = np.interp(xs, *prof)
    poly = trimesh.path.polygons.Polygon(np.r_[np.c_[xs, top - d], np.c_[xs, -EMBED - d][::-1]])
    m = trimesh.creation.extrude_polygon(poly, z1 - z0)     # (x, w) extruded along +z
    m.apply_transform([[1, 0, 0, 0], [0, sign, 0, END_Y[sign]], [0, 0, 1, z0], [0, 0, 0, 1]])
    if m.volume < 0:                                        # sign -1 mirrors
        m.invert()
    return pk._check(m)


def _y_cyl(r, x, z, yb, sign, w0, h):
    """Cylinder along the outward normal, w0 .. w0 + h off the surface at yb."""
    return pk.move(pk.rotate(pk.cylinder(r, h, z0=w0), -90 * sign, (1, 0, 0)), x, yb, z)


def _y_star(a, x, z, yb, sign):
    """Star: post `a` in radius from EMBED under the surface, domed top
    END_DOME tall, peak END_RAISE off the surface."""
    r = (a * a + END_DOME ** 2) / (2 * END_DOME)
    s = trimesh.creation.icosphere(subdivisions=3, radius=r)
    s.apply_translation((0, 0, END_RAISE - r))
    s = pk.move(pk.rotate(s, -90 * sign, (1, 0, 0)), x, yb, z)
    return pk.intersection(s, _y_cyl(a, x, z, yb, sign, -EMBED, END_RAISE + 2 * EMBED))


def _end_flag(sign, wall):
    """Flag pieces for one end, all on the wall's front (outer) face."""
    xs = np.arange(END_X[0] - 1, END_X[1] + 1.01, 0.1)
    pw = (xs, np.nan_to_num(_depth(wall, sign, 260.0, xs), nan=5.0))
    H = END_X[1] - END_X[0]                          # hoist runs across x
    cw, ch = 0.76 * H, 7 * H / 13                    # canton: fly length (z), hoist width (x)
    gx, gy = 0.063 * H, 0.054 * H                    # star pitch along fly (z) / hoist (x)
    bot = SEAM_Z + FLAG_GAP
    top = bot + 1.9 * H
    xl, k = END_X[1], -1     # canton on the high-x side at both ends: the two ends mirror each other (Tyler)
    g = GAP / 2

    def span(h0, h1):                                # hoist range from the left -> x range
        a, b = xl + k * h0, xl + k * h1
        return min(a, b), max(a, b)

    def piece(h0, h1, z0, z1):
        return _contour_piece(pw, sign, *span(h0, h1), z0, z1, END_RAISE)

    S = H / 13
    wal = [piece(i * S + (g if i else 0), (i + 1) * S - (g if i < 12 else 0),   # stripe 0 (red) on the canton side
                 bot + cw + g if i < 7 else bot, top) for i in range(13)]
    # canton: a hole per star, star = post with a domed top
    canton = piece(0, ch - g, bot, bot + cw - g)
    a = 0.0616 * H * 0.9 / 2
    holes = []
    for row in range(9):
        for c in (range(6) if row % 2 == 0 else range(5)):
            x = xl + k * gy * (row + 1)
            z = bot + (gx if row % 2 == 0 else 2 * gx) + 2 * gx * c
            yb = END_Y[sign] - sign * float(np.interp(x, *pw))
            holes.append(_y_cyl(a + GAP, x, z, yb, sign, -1, END_RAISE + 2))
            wal.append(_y_star(a, x, z, yb, sign))
    return wal + [pk.difference(canton, *holes)]


LOGO_DEPTH = (0.1, 0.4)    # the logo is engraved ~0.25 deep; deeper = a real edge/notch, leave it
LOGO_CELL = 0.25           # filler grid


def _logo_filler(conn):
    """Fills the engraved logo flush with the +y end face of the connector:
    one thin box per run of grid cells that touch the logo, each cell only if
    all of it is on the face (never bleeds into the notch or past an edge)."""
    from shapely.geometry import Polygon, box as sbox
    from shapely.ops import unary_union
    x0, x1, z0, z1 = LOGO_BOX
    n, tc = conn.face_normals, conn.triangles_center
    floor = (n[:, 1] > 0.999) & (abs(tc[:, 1] - (END_Y[1] - 0.25)) < 0.05)   # logo floor, 0.25 deep
    logo = unary_union([Polygon(tri[:, [0, 2]]) for tri in conn.triangles[floor]]).buffer(0.4)
    face = (n[:, 1] > 0.999) & (abs(tc[:, 1] - END_Y[1]) < 0.05)
    face_y = conn.vertices[conn.faces[face]][:, :, 1].max()   # the face's exact float32 y: flush, no slivers
    xs = np.arange(x0, x1 + 1e-9, LOGO_CELL / 2)            # cell corners + centres
    lo, hi = LOGO_DEPTH
    boxes = []
    for z in np.arange(z0, z1, LOGO_CELL):
        rows = np.array([_depth(conn, +1, zz, xs) for zz in (z, z + LOGO_CELL / 2, z + LOGO_CELL)])
        rows = np.nan_to_num(rows, nan=99.0)
        cells = []
        for i in range(0, len(xs) - 2, 2):
            d = rows[:, i:i + 3]
            cells.append(d.max() < hi and (d > lo).any()     # on the face, touches the logo
                         and logo.intersects(sbox(xs[i], z, xs[i + 2], z + LOGO_CELL)))
        i = 0
        while i < len(cells):                               # contiguous cells -> one box
            if not cells[i]:
                i += 1
                continue
            j = i
            while j + 1 < len(cells) and cells[j + 1]:
                j += 1
            bx0, bx1 = xs[2 * i], xs[2 * j + 2]
            b = pk.box(bx1 - bx0, 0.6, LOGO_CELL + 0.06)
            b.vertices[:, 1] = np.where(b.vertices[:, 1] > 0, face_y, face_y - 0.6)
            boxes.append(pk.move(b, (bx0 + bx1) / 2, 0, z - 0.03))
            i = j + 1
    return boxes


_ASM = {}


def assembly():
    """Connector, left, right in place, logo removed, a flag on each end (cached)."""
    if not _ASM:
        conn, left, right = _src("connecter"), _src("left"), _src("right")
        _ASM.update(connector=pk.union(conn, *_logo_filler(conn)),
                    left_wall=pk.union(left, *_end_flag(+1, left)),
                    right_wall=pk.union(right, *_end_flag(-1, right)))
    return _ASM


def connector_flag():
    """Prints as the source connector does (bottom down)."""
    return pk.on_bed(assembly()["connector"])


def left_wall_flag():
    """Prints upright like the source wall (flat lets the rod holes overhang)."""
    return pk.on_bed(assembly()["left_wall"])


def right_wall_flag():
    return pk.on_bed(assembly()["right_wall"])


def assembly_preview():
    """All three together - for looking at; print the three parts. Turned the
    way it's used: on its side, walls' rounded edge (+x) up, rods horizontal.
    Walls lifted 0.05 so their bottoms don't weld to the ear tops on export."""
    a = assembly()
    m = trimesh.util.concatenate([a["connector"], pk.move(a["left_wall"], z=0.05),
                                  pk.move(a["right_wall"], z=0.05)])
    return pk.on_bed(pk.rotate(m, -90, (0, 1, 0)))


PARTS = {
    "flag_test_plate": flag_test_plate,                          # backing = blue
    "flag_test_plate_canton": lambda: flag_test_plate(True),     # raised blue, stars indented
    "assembly_preview": assembly_preview,
    "connector_flag": connector_flag,
    "left_wall_flag": left_wall_flag,
    "right_wall_flag": right_wall_flag,
}

# Every STL in source/ is a part as-is ("<name>" -> out/.../<name>.stl). To
# change one, write a function that does pk.load(HERE / "source" / ...) and
# edits it, and register it under a new name above.
SOURCE = {p.stem: p for p in sorted((HERE / "source").glob("*.stl"))}
for _name, _path in SOURCE.items():
    PARTS.setdefault(_name, lambda p=_path: pk.on_bed(pk.load(p)))

# Overhang allowed per part (mm2 steeper than 45 deg). Bridges or source STLs
# that need supports go here, with the reason. Unlisted parts: 1 mm2.
OVERHANG_OK = {name: None for name in SOURCE}    # None = not checked (as downloaded)
# Flag printed upright: the underside of every stripe is a
# RAISE-deep flat ledge (prints fine, like embossed text on a wall), plus the
# lower half of each star nub / the undersides of the star posts and the tops
# of their holes in the canton (a quarter round each).
OVERHANG_OK["flag_test_plate"] = (RAISE * (13 * FLAG_L - 7 * CANTON_W)
                                  + 50 * np.pi * (STAR_D / 2) ** 2 / 2) * 1.05
OVERHANG_OK["flag_test_plate_canton"] = (RAISE * (13 * FLAG_L - 6 * CANTON_W)
                                         + 50 * np.pi * STAR_D / 2 * (RAISE + EMBED)) * 1.05
# End flags (stripes vertical): the RAISE-deep bottom ends of the stripes and
# of the canton, plus the star posts / holes - per flag. The connector has
# no flag: only its own source overhang (measured, not assumed).
_H = END_X[1] - END_X[0]
_END_FLAG = (END_RAISE * 2 * _H + 50 * np.pi * 0.0616 * _H * 0.9 * (END_RAISE + EMBED)) * 1.1
OVERHANG_OK["left_wall_flag"] = OVERHANG_OK["right_wall_flag"] = _END_FLAG
OVERHANG_OK["assembly_preview"] = None                     # not printed
OVERHANG_OK["connector_flag"] = pk.overhang_area(pk.on_bed(_src("connecter"))) * 1.01
