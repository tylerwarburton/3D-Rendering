"""Where does the support material come from, and does reorienting help?

A face needs support when it points downward more steeply than the slicer's
overhang threshold. Support VOLUME is what actually costs time and makes a
mess, so we ray-cast straight down from each overhanging face to find what
is underneath it and multiply by the area.
"""
import numpy as np
import trimesh

from . import paths, render as R, solids

THRESHOLD_DEG = 45.0          # slicer overhang threshold
SAMPLES = 4000                # ray-cast budget

ORIENTATIONS = {
    "as-is (basin down)": np.eye(4),
    "back wall down": trimesh.transformations.rotation_matrix(
        np.radians(-90), [1, 0, 0]),
    "front down": trimesh.transformations.rotation_matrix(
        np.radians(90), [1, 0, 0]),
    "on its side": trimesh.transformations.rotation_matrix(
        np.radians(90), [0, 1, 0]),
}


BED_EPS = 0.6                 # faces this close to the plate rest ON it


def overhang_faces(mesh, threshold_deg=THRESHOLD_DEG, bed_eps=BED_EPS):
    """Indices of faces steeper than the threshold, measured from vertical.

    Faces sitting on the build plate point straight down but need no support,
    so they are excluded - otherwise the 209 mm square base alone accounts for
    more area than every real overhang combined.
    """
    nz = mesh.face_normals[:, 2]
    steep = nz < -np.cos(np.radians(threshold_deg))
    on_bed = mesh.triangles_center[:, 2] < (mesh.bounds[0][2] + bed_eps)
    return np.where(steep & ~on_bed)[0]


def support_estimate(mesh, threshold_deg=THRESHOLD_DEG, samples=SAMPLES, seed=0):
    """Returns (overhang area mm2, support volume mm3, max unsupported height)."""
    idx = overhang_faces(mesh, threshold_deg)
    if len(idx) == 0:
        return 0.0, 0.0, 0.0

    areas = mesh.area_faces[idx]
    total_area = float(areas.sum())

    rng = np.random.default_rng(seed)
    n = min(samples, len(idx))
    pick = rng.choice(len(idx), size=n, replace=False, p=areas / areas.sum())
    faces = idx[pick]

    origins = mesh.triangles_center[faces] + np.array([0, 0, -0.05])
    dirs = np.tile([0, 0, -1.0], (len(faces), 1))

    inter = trimesh.ray.ray_triangle.RayMeshIntersector(mesh)
    locs, ray_idx, _ = inter.intersects_location(origins, dirs, multiple_hits=False)

    heights = origins[:, 2].copy()          # default: down to the build plate
    if len(ray_idx):
        heights[ray_idx] = origins[ray_idx, 2] - locs[:, 2]

    mean_h = float(heights.mean())
    volume = total_area * mean_h
    return total_area, volume, float(heights.max())


def compare():
    base = solids.load("waterfall")
    rows = []
    for name, T in ORIENTATIONS.items():
        m = base.copy()
        m.apply_transform(T)
        m.apply_translation([0, 0, -m.bounds[0][2]])     # drop onto the plate
        a, v, h = support_estimate(m)
        rows.append(dict(name=name, area=a, vol=v, tall=h,
                         bed=float(m.extents[0] * m.extents[1]),
                         height=float(m.extents[2])))
    return rows


def run():
    print("overhang analysis:")
    rows = compare()
    print(f"  {'orientation':<22}{'overhang area':>15}{'support vol':>14}"
          f"{'tallest gap':>13}{'part height':>13}")
    for r in rows:
        print(f"  {r['name']:<22}{r['area']/100:>12.0f} cm2"
              f"{r['vol']/1000:>11.0f} cm3{r['tall']:>10.0f} mm"
              f"{r['height']:>10.0f} mm")

    best = min(rows, key=lambda r: r["vol"])
    print(f"  -> least support: {best['name']}")

    plan_map(rows)

    m = solids.load("waterfall")
    sec = solids.load("waterfall_section_x")
    imgs, labs = [], []
    imgs.append(R.render(sec, view_dir=(-0.9, 0.5, 0.35), size=(640, 640),
                         bounds=m.vertices, ss=2,
                         accent_faces=overhang_faces(sec), accent=(224, 132, 62)))
    labs.append("Section from below - amber = unsupported")
    imgs.append(R.render(m, view_dir=(0.6, 0.9, 0.45), size=(640, 640),
                         bounds=m.vertices, ss=2,
                         accent_faces=overhang_faces(m), accent=(224, 132, 62)))
    labs.append("Whole part from below")
    R.grid(imgs, labs, 2, str(paths.IMG / "overhangs_3d.png"))
    print(f"  overhangs_3d -> {paths.rel(paths.IMG / 'overhangs_3d.png')}")
    return rows


def plan_map(rows):
    """Looking down: the footprint the slicer has to fill with support."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.collections import PolyCollection
    from matplotlib.patches import Rectangle
    import waterfall as W

    INK, DIM = "#1B2A30", "#6C858E"
    m = solids.load("waterfall")
    idx = overhang_faces(m)
    tris = m.triangles[idx]
    z = m.triangles_center[idx][:, 2]

    order = np.argsort(z)
    tris, z = tris[order], z[order]

    fig, (ax, bx) = plt.subplots(1, 2, figsize=(15.5, 7.4),
                                 gridspec_kw={"width_ratios": [1.15, 1]})
    fig.patch.set_facecolor("white")

    pc = PolyCollection(tris[:, :, :2], array=z, cmap="magma_r",
                        edgecolors="none", alpha=0.92)
    ax.add_collection(pc)
    ax.add_patch(Rectangle((-W.SIZE/2, -W.SIZE/2), W.SIZE, W.SIZE,
                           facecolor="none", edgecolor=INK, lw=1.4))
    inner = W.SIZE - 2*W.WALL
    ax.add_patch(Rectangle((-inner/2, -inner/2), inner, inner,
                           facecolor="none", edgecolor=DIM, lw=1.1, ls="--"))
    ax.set_xlim(-W.SIZE/2 - 10, W.SIZE/2 + 10)
    ax.set_ylim(-W.SIZE/2 - 10, W.SIZE/2 + 10)
    ax.set_aspect("equal"); ax.axis("off")
    ax.set_title("Support footprint, looking down", fontsize=14,
                 color=INK, weight="bold", pad=14)
    ax.text(0.5, -0.055, "dashed line = basin cavity. Everything shaded needs a "
            "support tower under it.",
            transform=ax.transAxes, ha="center", fontsize=10.5, color=DIM)
    cb = fig.colorbar(pc, ax=ax, orientation="horizontal", fraction=0.042,
                      pad=0.13, shrink=0.86)
    cb.set_label("height above the build plate (mm)", fontsize=10, color=DIM)
    cb.ax.tick_params(labelsize=9)

    names = [r["name"] for r in rows][::-1]
    vols = [r["vol"]/1000 for r in rows][::-1]
    cols = ["#2F9E8F" if v == min(vols) else "#B9C6CB" for v in vols]
    bx.barh(names, vols, color=cols, height=0.58)
    for i, v in enumerate(vols):
        bx.text(v + 40, i, f"{v:.0f} cm\u00b3", va="center", fontsize=11, color=INK)
    bx.set_xlim(0, max(vols)*1.22)
    bx.set_xlabel("estimated support volume (cm\u00b3)", fontsize=11, color=DIM)
    bx.set_title("Print orientation", fontsize=14, color=INK, weight="bold", pad=14)
    bx.spines[["top", "right"]].set_visible(False)
    bx.tick_params(labelsize=11)

    fig.suptitle("Why the supports fill the basin", fontsize=17, color=INK,
                 weight="bold", y=0.98)
    fig.subplots_adjust(top=0.84, bottom=0.16, wspace=0.30)
    out = paths.IMG / "overhangs.png"
    fig.savefig(str(out), dpi=115, facecolor="white")
    plt.close(fig)
    print(f"  overhangs -> {paths.rel(out)}")
