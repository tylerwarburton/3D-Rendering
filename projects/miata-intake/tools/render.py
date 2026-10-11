"""Orthographic z-buffer renderer.

Pure numpy - no GL, no headless display. Rasterises the exported triangle
mesh into a depth buffer, shades it with two directional lights plus a wrap
term, then darkens depth and normal discontinuities so edges read clearly.
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont

BG = np.array([248, 248, 246], dtype=float)
BASE = np.array([0.70, 0.74, 0.80])
CUT = np.array([0.88, 0.55, 0.38])


def view_matrix(eye, up=(0, 0, 1)):
    """Rows are (right, up, toward-camera). Orthographic, no perspective."""
    f = np.asarray(eye, dtype=float)
    f = f / np.linalg.norm(f)
    u0 = np.asarray(up, dtype=float)
    if abs(np.dot(f, u0 / np.linalg.norm(u0))) > 0.98:
        u0 = np.array([0.0, 1.0, 0.0])
    r = np.cross(u0, f)
    r /= np.linalg.norm(r)
    u = np.cross(f, r)
    return np.stack([r, u, f])


def corner_normals(mesh, crease_deg=38.0):
    """Per-face-corner normals: smooth across gentle joins, hard at creases.

    A flat-shaded lofted blend looks like a disco ball; averaging everything
    instead rounds off the real edges. So average per vertex, then fall back
    to the face normal wherever that average has swung too far.
    """
    faces = np.asarray(mesh.faces)
    fn = np.asarray(mesh.face_normals)
    fa = np.asarray(mesh.area_faces)
    acc = np.zeros((len(mesh.vertices), 3))
    np.add.at(acc, faces.ravel(), np.repeat(fn * fa[:, None], 3, axis=0))
    ln = np.linalg.norm(acc, axis=1)
    ln[ln < 1e-12] = 1.0
    vn = acc / ln[:, None]
    out = vn[faces]                                   # (F,3,3)
    dot = np.einsum("fcj,fj->fc", out, fn)
    hard = dot < np.cos(np.radians(crease_deg))
    out[hard] = np.repeat(fn[:, None, :], 3, axis=1)[hard]
    return out


def rasterize(verts, faces, colors, size, R, margin=0.08, scale_ref=None,
              vnormals=None):
    """Return (depth, normal, color, mask) buffers for one orthographic view."""
    P = verts @ R.T
    tri = P[faces]                                   # (F,3,3)

    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    ln = np.linalg.norm(n, axis=1)
    keep = ln > 1e-12
    tri, n, ln = tri[keep], n[keep], ln[keep]
    cols = colors[keep]
    n = n / ln[:, None]
    cn = None
    if vnormals is not None:
        cn = vnormals[keep] @ R.T                    # (F,3,3) in view space

    lo = P.min(axis=0)
    hi = P.max(axis=0)
    span = (hi - lo)[:2].max() if scale_ref is None else scale_ref
    s = size * (1.0 - 2 * margin) / span
    cx, cy = (lo[0] + hi[0]) / 2.0, (lo[1] + hi[1]) / 2.0

    sx = (tri[:, :, 0] - cx) * s + size / 2.0
    sy = size / 2.0 - (tri[:, :, 1] - cy) * s
    sz = tri[:, :, 2]

    depth = np.full((size, size), -1e18)
    normal = np.zeros((size, size, 3))
    color = np.zeros((size, size, 3))
    mask = np.zeros((size, size), dtype=bool)

    x0 = np.clip(np.floor(sx.min(axis=1)).astype(int), 0, size - 1)
    x1 = np.clip(np.ceil(sx.max(axis=1)).astype(int), 0, size - 1)
    y0 = np.clip(np.floor(sy.min(axis=1)).astype(int), 0, size - 1)
    y1 = np.clip(np.ceil(sy.max(axis=1)).astype(int), 0, size - 1)

    ax, ay = sx[:, 0], sy[:, 0]
    bx, by = sx[:, 1], sy[:, 1]
    ccx, ccy = sx[:, 2], sy[:, 2]
    area = (bx - ax) * (ccy - ay) - (ccx - ax) * (by - ay)

    order = np.argsort(-sz.mean(axis=1))            # far to near helps cache
    for i in order:
        if abs(area[i]) < 1e-9:
            continue
        xs = np.arange(x0[i], x1[i] + 1)
        ys = np.arange(y0[i], y1[i] + 1)
        if xs.size == 0 or ys.size == 0:
            continue
        gx, gy = np.meshgrid(xs + 0.5, ys + 0.5)
        w0 = ((bx[i] - ax[i]) * (gy - ay[i]) - (gx - ax[i]) * (by[i] - ay[i]))
        w1 = ((ccx[i] - bx[i]) * (gy - by[i]) - (gx - bx[i]) * (ccy[i] - by[i]))
        w2 = ((ax[i] - ccx[i]) * (gy - ccy[i]) - (gx - ccx[i]) * (ay[i] - ccy[i]))
        if area[i] > 0:
            inside = (w0 >= 0) & (w1 >= 0) & (w2 >= 0)
        else:
            inside = (w0 <= 0) & (w1 <= 0) & (w2 <= 0)
        if not inside.any():
            continue
        l0 = w1 / area[i]
        l1 = w2 / area[i]
        l2 = 1.0 - l0 - l1
        z = l0 * sz[i, 0] + l1 * sz[i, 1] + l2 * sz[i, 2]
        if cn is not None:
            nx = l0 * cn[i, 0, 0] + l1 * cn[i, 1, 0] + l2 * cn[i, 2, 0]
            ny = l0 * cn[i, 0, 1] + l1 * cn[i, 1, 1] + l2 * cn[i, 2, 1]
            nz = l0 * cn[i, 0, 2] + l1 * cn[i, 1, 2] + l2 * cn[i, 2, 2]
            nl = np.sqrt(nx * nx + ny * ny + nz * nz)
            nl[nl < 1e-9] = 1.0
            pn = (nx / nl, ny / nl, nz / nl)
        else:
            pn = (n[i, 0], n[i, 1], n[i, 2])
        sub = depth[ys[0]:ys[-1] + 1, xs[0]:xs[-1] + 1]
        upd = inside & (z > sub)
        if not upd.any():
            continue
        ysl = slice(ys[0], ys[-1] + 1)
        xsl = slice(xs[0], xs[-1] + 1)
        depth[ysl, xsl] = np.where(upd, z, sub)
        for k in range(3):
            normal[ysl, xsl, k] = np.where(upd, pn[k], normal[ysl, xsl, k])
            color[ysl, xsl, k] = np.where(upd, cols[i, k], color[ysl, xsl, k])
        mask[ysl, xsl] |= upd
    return depth, normal, color, mask


def shade(depth, normal, color, mask):
    L1 = np.array([-0.35, 0.55, 0.76]);  L1 /= np.linalg.norm(L1)
    L2 = np.array([0.62, -0.30, 0.72]);  L2 /= np.linalg.norm(L2)
    nd = normal
    d1 = np.clip(nd @ L1, 0, 1)
    d2 = np.clip(nd @ L2, 0, 1)
    wrap = np.clip((nd[:, :, 2] + 0.35) / 1.35, 0, 1)
    lit = 0.20 + 0.62 * d1 + 0.26 * d2 + 0.10 * wrap
    spec = np.clip(nd @ L1, 0, 1) ** 28 * 0.30

    img = color * lit[:, :, None] + spec[:, :, None]

    # edge darkening from depth + normal discontinuities
    dz = np.zeros_like(depth)
    dz[1:-1, 1:-1] = (np.abs(depth[2:, 1:-1] - depth[:-2, 1:-1])
                      + np.abs(depth[1:-1, 2:] - depth[1:-1, :-2]))
    dn = np.zeros_like(depth)
    dn[1:-1, 1:-1] = (np.linalg.norm(normal[2:, 1:-1] - normal[:-2, 1:-1], axis=2)
                      + np.linalg.norm(normal[1:-1, 2:] - normal[1:-1, :-2], axis=2))
    span = max(float(np.ptp(depth[mask])), 1e-6) if mask.any() else 1.0
    edge = np.clip(dz / (span * 0.035), 0, 1) * 0.85 + np.clip(dn / 1.1, 0, 1) * 0.55
    edge = np.clip(edge, 0, 1) * mask
    img *= (1.0 - 0.75 * edge)[:, :, None]

    out = np.where(mask[:, :, None], np.clip(img, 0, 1) * 255.0, BG[None, None, :])
    return out.astype(np.uint8)


def render_view(mesh, size, eye, up=(0, 0, 1), cut_faces=None,
                scale_ref=None, ss=2, smooth=True):
    v = np.asarray(mesh.vertices, dtype=float)
    f = np.asarray(mesh.faces, dtype=np.int64)
    cols = np.tile(BASE, (len(f), 1))
    if cut_faces is not None:
        cols[cut_faces] = CUT
    vn = corner_normals(mesh) if smooth else None
    big = size * ss
    d, n, c, m = rasterize(v, f, cols, big, view_matrix(eye, up),
                           scale_ref=scale_ref, vnormals=vn)
    rgb = shade(d, n, c, m)
    return Image.fromarray(rgb).resize((size, size), Image.LANCZOS)


def _font(sz):
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(p, sz)
        except Exception:
            pass
    return ImageFont.load_default()


def contact_sheet(panels, cols, size, title, path, pad=14, label_h=30):
    rows = (len(panels) + cols - 1) // cols
    W = cols * size + (cols + 1) * pad
    H = rows * (size + label_h) + (rows + 1) * pad + 46
    sheet = Image.new("RGB", (W, H), (255, 255, 255))
    dr = ImageDraw.Draw(sheet)
    dr.text((pad, 14), title, fill=(25, 25, 28), font=_font(22))
    for i, (img, label) in enumerate(panels):
        r, c = divmod(i, cols)
        x = pad + c * (size + pad)
        y = 46 + pad + r * (size + label_h + pad)
        sheet.paste(img, (x, y))
        dr.rectangle([x, y, x + size - 1, y + size - 1], outline=(214, 214, 210))
        dr.text((x + 3, y + size + 7), label, fill=(60, 60, 66), font=_font(15))
    sheet.save(path)
    return path
