"""Tiny orthographic z-buffer renderer (numpy only). Good enough for CAD review."""
import numpy as np
import trimesh


def _basis(view_dir, up=(0, 0, 1)):
    f = np.asarray(view_dir, float)
    f = f / np.linalg.norm(f)
    up = np.asarray(up, float)
    if abs(np.dot(f, up)) > 0.999:
        up = np.array([0.0, 1.0, 0.0])
    r = np.cross(f, up); r /= np.linalg.norm(r)
    u = np.cross(r, f)
    return r, u, f


def render(mesh, view_dir=(1, -1, 0.6), up=(0, 0, 1), size=(900, 900),
           bg=(255, 255, 255), base=(205, 211, 219), pad=0.06,
           bounds=None, light=(0.45, -0.75, 0.55), edges=False,
           accent_faces=None, accent=(232, 120, 70), ss=2):
    """Render mesh to an HxWx3 uint8 array. ss = supersample factor."""
    W, H = size
    W *= ss; H *= ss
    V = mesh.vertices.view(np.ndarray).astype(float)
    F = mesh.faces.view(np.ndarray)
    r, u, f = _basis(view_dir, up)

    # camera space
    x = V @ r
    y = V @ u
    z = V @ f  # depth, bigger = farther

    src = V if bounds is None else np.asarray(bounds, float)
    bx = src @ r; by = src @ u
    cx, cy = (bx.min() + bx.max()) / 2, (by.min() + by.max()) / 2
    span = max(bx.max() - bx.min(), by.max() - by.min()) * (1 + 2 * pad)
    scale = min(W, H) / span

    px = (x - cx) * scale + W / 2
    py = H / 2 - (y - cy) * scale

    tri = np.stack([px[F], py[F]], -1)          # (n,3,2)
    tz = z[F].mean(1)

    # shading
    n = mesh.face_normals.view(np.ndarray)
    L = np.asarray(light, float); L /= np.linalg.norm(L)
    diff = np.clip(n @ L, 0, 1)
    back = np.clip(n @ (-L), 0, 1)
    shade = 0.42 + 0.62 * diff + 0.16 * back
    col = np.asarray(base, float)[None, :] * shade[:, None]
    if accent_faces is not None:
        a = np.asarray(accent, float)[None, :] * shade[accent_faces][:, None]
        col[accent_faces] = a
    col = np.clip(col, 0, 255)

    img = np.zeros((H, W, 3), float); img[:] = bg
    zbuf = np.full((H, W), np.inf)

    order = np.argsort(-tz)  # far to near not needed w/ zbuf but helps cache
    for i in order:
        t = tri[i]
        x0 = max(int(np.floor(t[:, 0].min())), 0)
        x1 = min(int(np.ceil(t[:, 0].max())) + 1, W)
        y0 = max(int(np.floor(t[:, 1].min())), 0)
        y1 = min(int(np.ceil(t[:, 1].max())) + 1, H)
        if x1 <= x0 or y1 <= y0:
            continue
        xs = np.arange(x0, x1) + 0.5
        ys = np.arange(y0, y1) + 0.5
        gx, gy = np.meshgrid(xs, ys)
        ax, ay = t[0]; bxp, byp = t[1]; cxp, cyp = t[2]
        d = (byp - cyp) * (ax - cxp) + (cxp - bxp) * (ay - cyp)
        if abs(d) < 1e-12:
            continue
        w0 = ((byp - cyp) * (gx - cxp) + (cxp - bxp) * (gy - cyp)) / d
        w1 = ((cyp - ay) * (gx - cxp) + (ax - cxp) * (gy - cyp)) / d
        w2 = 1 - w0 - w1
        m = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
        if not m.any():
            continue
        zt = z[F[i]]
        zz = w0 * zt[0] + w1 * zt[1] + w2 * zt[2]
        sub = zbuf[y0:y1, x0:x1]
        upd = m & (zz < sub)
        if not upd.any():
            continue
        sub[upd] = zz[upd]
        img[y0:y1, x0:x1][upd] = col[i]

    if ss > 1:
        h2, w2 = H // ss, W // ss
        img = img[:h2 * ss, :w2 * ss].reshape(h2, ss, w2, ss, 3).mean((1, 3))
    return np.clip(img, 0, 255).astype(np.uint8)


def grid(images, labels, cols, path, cell_pad=10, bg=255, title_h=34):
    from PIL import Image, ImageDraw, ImageFont
    try:
        font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
    except Exception:
        font = ImageFont.load_default()
    h, w = images[0].shape[:2]
    rows = int(np.ceil(len(images) / cols))
    Wt = cols * w + (cols + 1) * cell_pad
    Ht = rows * (h + title_h) + (rows + 1) * cell_pad
    canvas = Image.new("RGB", (Wt, Ht), (bg, bg, bg))
    d = ImageDraw.Draw(canvas)
    for i, (im, lb) in enumerate(zip(images, labels)):
        c, rw = i % cols, i // cols
        x = cell_pad + c * (w + cell_pad)
        y = cell_pad + rw * (h + title_h + cell_pad)
        d.text((x + 4, y + 4), lb, fill=(30, 30, 30), font=font)
        canvas.paste(Image.fromarray(im), (x, y + title_h))
    canvas.save(path)
    return path


def save(img, path):
    from PIL import Image
    Image.fromarray(img).save(path)
    return path


def cutaway(mesh, normal=(0, 1, 0), origin=None):
    """Half-section with capped faces; keeps the side the normal points to.
    Never put the plane exactly on a vertex plane (e.g. y=0 on a fitting):
    the cap fill breaks and draws a false slab. Offset by a fraction of a mm."""
    if origin is None:
        origin = mesh.bounds.mean(0)
    return mesh.slice_plane(plane_origin=origin, plane_normal=normal, cap=True)
