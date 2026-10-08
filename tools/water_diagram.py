"""Section through the centre plane with the running water level drawn in."""
import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFont

from . import paths, render as R, solids, hydro
import waterfall as W

AQUA = (70, 190, 178)
PAD = 0.20
SIZE = (1000, 950)


def _font(sz, bold=False):
    p = "/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf" % ("-Bold" if bold else "")
    try:
        return ImageFont.truetype(p, sz)
    except Exception:
        return ImageFont.load_default()


def _water_slabs(half=True):
    """Boxes representing standing water. half=True clips to x<=0 for the section."""
    ps, bs = hydro.pools(), hydro.basin()
    out = []
    for p in ps:
        w = p["iw"] / 2 if half else p["iw"]
        cx = -p["iw"] / 4 if half else 0.0
        b = trimesh.creation.box(extents=(w, p["back_y"] - p["f_in"],
                                          p["surf"] - p["floor_in"]))
        b.apply_translation((cx, (p["f_in"] + p["back_y"]) / 2,
                             (p["floor_in"] + p["surf"]) / 2))
        out.append(b)
    lvl = bs["floor_in"] + 45
    w = bs["iw"] / 2 if half else bs["iw"]
    cx = -bs["iw"] / 4 if half else 0.0
    b = trimesh.creation.box(extents=(w, bs["idp"], lvl - bs["floor_in"]))
    b.apply_translation((cx, 0, (bs["floor_in"] + lvl) / 2))
    out.append(b)
    return out


def run():
    solid = solids.load("waterfall_section_x")
    full = solids.load("waterfall")
    water = trimesh.util.concatenate(_water_slabs(half=True))
    combined = trimesh.util.concatenate([solid, water])
    acc = np.arange(len(solid.faces), len(combined.faces))

    view = (-1.0, 0.02, -0.02)
    img = R.render(combined, view_dir=view, up=(0, 0, 1), size=SIZE,
                   bounds=full.vertices, ss=2, accent_faces=acc, accent=AQUA, pad=PAD)

    im = Image.fromarray(img)
    d = ImageDraw.Draw(im)

    r, u, f = R._basis(view, (0, 0, 1))
    V = full.vertices.view(np.ndarray)
    bx, by = V @ r, V @ u
    cx, cy = (bx.min() + bx.max()) / 2, (by.min() + by.max()) / 2
    Wd, Hd = SIZE
    span = max(bx.max() - bx.min(), by.max() - by.min()) * (1 + 2 * PAD)
    sc = min(Wd, Hd) / span

    def proj(p):
        p = np.asarray(p, float)
        return ((p @ r - cx) * sc + Wd / 2, Hd / 2 - (p @ u - cy) * sc)

    d.text((18, 14), "Water levels at running state  -  section on the centre plane",
           fill=(25, 40, 46), font=_font(21, True))
    d.text((18, 42), "aqua = standing water   |   the slit bottom is the weir invert, "
                     "which sets the surface", fill=(90, 110, 118), font=_font(14))

    for p in hydro.pools():
        y_mid = p["back_y"] - p["od"] / 2
        x1, y1 = proj((0, y_mid, p["surf"]))
        tx = x1 - 300
        d.line([(x1 - 6, y1), (tx + 250, y1 - 16)], fill=(60, 140, 135), width=2)
        d.text((tx, y1 - 40), f"{p['name'].upper()} pool", fill=(20, 60, 62), font=_font(16, True))
        d.text((tx, y1 - 20), f"{p['volume_ml']:.0f} mL  \u00b7  {p['depth']:.0f} mm deep",
               fill=(70, 95, 100), font=_font(13))
        d.text((tx, y1 - 3), f"freeboard {p['freeboard']:.0f} mm to rim",
               fill=(70, 95, 100), font=_font(13))

    bs = hydro.basin()
    x1, y1 = proj((0, -40, bs["floor_in"] + 45))
    d.text((x1 - 330, y1 - 6), f"basin / reservoir  \u00b7  {bs['gross_l']:.2f} L to rim",
           fill=(20, 60, 62), font=_font(16, True))
    d.text((x1 - 330, y1 + 15), "pump box sits here, 2 side intakes",
           fill=(70, 95, 100), font=_font(13))

    x1, y1 = proj((0, 86, W.SPINE_TOP_Z))
    d.text((x1 - 360, y1 - 40), f"cup + {W.SPINE_CAP_HOLE_D:.2f} mm outlet",
           fill=(20, 60, 62), font=_font(16, True))
    d.text((x1 - 360, y1 - 19),
           f"lip is {W.SPINE_TOP_Z - W.POOL_RIM_Z[0]:.0f} mm above the top pool rim",
           fill=(70, 95, 100), font=_font(13))

    out = paths.IMG / "water_levels.png"
    im.save(str(out))
    print(f"  water_levels -> {paths.rel(out)}")
