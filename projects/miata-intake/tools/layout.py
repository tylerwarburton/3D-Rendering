"""Dimensioned plan view of where the six connectors sit.

Looking straight into the mouth. Everything is drawn from the same params
the solid is built from, so if this picture disagrees with the real piece,
the numbers in params.py are what need changing.
"""
import math
from PIL import Image, ImageDraw, ImageFont

import params as P
import adapter as A

INK = (32, 34, 38)
MUTED = (140, 146, 154)
DIM = (32, 96, 168)
TAB = (214, 122, 58)
FRAME = (70, 76, 84)


def _font(sz, bold=False):
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/" + name, sz)
    except Exception:
        return ImageFont.load_default()


def draw(path, scale=6.4, pad=150):
    W = int(P.FRAME_W * scale) + 2 * pad
    H = int(P.FRAME_H * scale) + 2 * pad + 250
    img = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(img)
    cx, cy = W / 2.0, pad + P.FRAME_H * scale / 2.0 + 40

    def pt(x, y):
        return (cx + x * scale, cy - y * scale)

    d.text((pad - 40, 26), "Connector layout - looking into the mouth",
           fill=INK, font=_font(24, True))
    d.text((pad - 40, 58),
           "Sides A B C D are embossed on the collar; the two connectors on "
           "each long face are numbered 1 and 2 from the A end.",
           fill=MUTED, font=_font(14))
    d.text((pad - 40, 78),
           "All dimensions are measured from the A end face, at the outer "
           "rim. Dashed outline is the flared mouth.",
           fill=MUTED, font=_font(14))

    hw, hh, r = P.FRAME_W / 2.0, P.FRAME_H / 2.0, P.FRAME_CORNER_R
    # flared outline at the mouth, behind the rim outline
    mx_p = A.half_x("+X", hw, 0.0)
    mx_n = A.half_x("-X", hw, 0.0)
    a, b = pt(-mx_n, hh), pt(mx_p, -hh)
    for k in range(0, int(b[0] - a[0]), 12):
        d.line([a[0] + k, a[1], a[0] + min(k + 7, b[0] - a[0]), a[1]],
               fill=(196, 200, 206), width=2)
        d.line([a[0] + k, b[1], a[0] + min(k + 7, b[0] - a[0]), b[1]],
               fill=(196, 200, 206), width=2)
    d.line([a[0], a[1], a[0], b[1]], fill=(196, 200, 206), width=2)
    d.line([b[0], a[1], b[0], b[1]], fill=(196, 200, 206), width=2)
    d.text((a[0], a[1] - 8), f"mouth {mx_p + mx_n:.1f} mm wide",
           fill=(150, 154, 160), font=_font(12), anchor="ls")

    box = [pt(-hw, hh), pt(hw, -hh)]
    d.rounded_rectangle([box[0][0], box[0][1], box[1][0], box[1][1]],
                        radius=r * scale, outline=FRAME, width=3)
    d.text(pt(-hw, hh + 3.6),
           f"OEM frame at the rim  {P.FRAME_W:.0f} x {P.FRAME_H:.0f} mm   "
           f"(A end flares {P.FRAME_DRAFT_NX:.1f} deg, "
           f"C end {P.FRAME_DRAFT_PX:.1f} deg)",
           fill=FRAME, font=_font(14), anchor="ls")

    # side letters
    d.text(pt(-hw - 4.0, 0), "A", fill=INK, font=_font(26, True), anchor="rm")
    d.text(pt(hw + 4.0, 0), "C", fill=INK, font=_font(26, True), anchor="lm")
    d.text(pt(-hw * 0.74, hh + 7.0), "B", fill=INK, font=_font(26, True),
           anchor="ms")
    d.text(pt(-hw * 0.74, -hh - 12.0), "D", fill=INK, font=_font(26, True),
           anchor="mt")

    # connectors
    sites = A.connector_sites()
    for name, kind, lat, zc in sites:
        x, y = A.site_frame_xy(kind, lat, P.SOCKET_DEPTH)
        if kind in ("+Y", "-Y"):
            sgn = 1.0 if kind == "+Y" else -1.0
            x0, x1 = x - P.TAB_L / 2.0, x + P.TAB_L / 2.0
            y0 = hh * sgn
            y1 = y0 + sgn * P.TAB_PROUD
            aa, bb = pt(x0, min(y0, y1)), pt(x1, max(y0, y1))
            d.rectangle([aa[0], bb[1], bb[0], aa[1]], fill=TAB, outline=INK)
            d.text(pt(x, y0 + sgn * (P.TAB_PROUD + 3.0)), name, fill=INK,
                   font=_font(17, True),
                   anchor="ms" if sgn > 0 else "mt")
        else:
            sgn = 1.0 if kind == "+X" else -1.0
            yy = y
            y0, y1 = yy - P.TAB_L / 2.0, yy + P.TAB_L / 2.0
            x0 = hw * sgn
            x1 = x0 + sgn * P.TAB_PROUD
            aa, bb = pt(min(x0, x1), y1), pt(max(x0, x1), y0)
            d.rectangle([aa[0], aa[1], bb[0], bb[1]], fill=TAB, outline=INK)

    # dimensions from the left end face, one row per long face
    def dim_row(xs, ypix, label):
        left = pt(-hw, 0)[0]
        d.line([left, ypix, pt(hw, 0)[0], ypix], fill=(224, 226, 230), width=1)
        d.text((pad - 40, ypix - 9), label, fill=INK, font=_font(14, True),
               anchor="ls")
        for x in xs:
            px = pt(x, 0)[0]
            d.line([left, ypix, px, ypix], fill=DIM, width=2)
            d.line([px, ypix - 9, px, ypix + 9], fill=DIM, width=2)
            for tip in (left, px):
                d.polygon([(tip, ypix), (tip + (7 if tip == left else -7),
                                         ypix - 4),
                           (tip + (7 if tip == left else -7), ypix + 4)],
                          fill=DIM)
            d.text(((left + px) / 2.0, ypix - 8), f"{x + hw:.1f}",
                   fill=DIM, font=_font(15, True), anchor="ms")
        # spacing between the pair
        if len(xs) == 2:
            a, b = sorted(xs)
            d.text((pt((a + b) / 2.0, 0)[0], ypix + 13),
                   f"pair spacing {b - a:.1f}", fill=MUTED,
                   font=_font(13), anchor="ma")

    base = cy + hh * scale + 96
    dim_row(P.TAB_X_FACE_PY, base, "side B  (B1, B2)")
    dim_row(P.TAB_X_FACE_NY, base + 78, "side D  (D1, D2)")

    # vertical dimension for the short-end connectors
    for kind, yv, side in (("+X", P.TAB_Y_FACE_PX, 1.0),
                           ("-X", P.TAB_Y_FACE_NX, -1.0)):
        px = pt(side * (hw + P.TAB_PROUD + 9), 0)[0]
        top, mid = pt(0, hh)[1], pt(0, yv)[1]
        d.line([px, top, px, mid], fill=DIM, width=2)
        d.line([px - 7, mid, px + 7, mid], fill=DIM, width=2)
        d.text((px + side * 8, (top + mid) / 2.0), f"{hh - yv:.1f}",
               fill=DIM, font=_font(14, True),
               anchor="lm" if side > 0 else "rm")

    d.text((pad - 40, H - 68),
           f"socket {P.SOCKET_DEPTH:.0f} mm deep + {P.COLLAR_LEN:.0f} mm "
           f"labelled collar   |   overall "
           f"{A.half_x('-X', P.SOCK_OD_HW, 0) + A.half_x('+X', P.SOCK_OD_HW, 0):.0f}"
           f" mm across the mouth", fill=MUTED, font=_font(14))
    note = (f"connector footprint {P.TAB_L:.0f} x {P.TAB_W:.0f} mm, "
            f"assumed {P.TAB_PROUD:.1f} mm proud   |   "
            f"pocket {P.TAB_L + 2 * P.TAB_CLEAR:.1f} x "
            f"{P.TAB_W + 2 * P.TAB_CLEAR:.1f} x "
            f"{P.TAB_PROUD + P.TAB_DEPTH_CLEAR:.1f} deep   |   "
            f"boss {P.BOSS_LAT:.0f} x {P.BOSS_AX:.0f} mm")
    d.text((pad - 40, H - 46), note, fill=MUTED, font=_font(14))
    d.text((pad - 40, H - 24),
           "edit TAB_X_FACE_PY / TAB_X_FACE_NY / TAB_Y_FACE_PX / "
           "TAB_Y_FACE_NX in src/params.py", fill=MUTED, font=_font(13))
    img.save(path)
    return path
