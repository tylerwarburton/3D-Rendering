"""How much of each shelf ceiling is actually held up, and how wide are the gaps?

Rib pitch alone is misleading. Ribs get chopped wherever they would cross the
riser, the pump box or a drip guide, so the real question is the size of the
largest unsupported void on each ceiling, not the nominal spacing.

Masks are built from the same segment list the geometry uses, so this cannot
drift from what actually gets printed.
"""
import numpy as np
from scipy import ndimage

from . import paths
import waterfall as W

STEP = 1.0          # grid resolution, mm
BRIDGE_OK = 15.0    # span a well-tuned printer bridges cleanly, mm


def shelf_records():
    """The same records build() assembles, rebuilt here for analysis."""
    iby = W.SIZE / 2 - W.WALL
    out = []
    for tier, ((iw, idp), rim) in enumerate(zip(W.POOL_INNER, W.POOL_RIM_Z)):
        ow, od = iw + 2 * W.POOL_WALL, idp + W.POOL_WALL
        land = (W.POOL_RIM_Z[tier + 1] - W.POOL_DEPTH_Z
                if tier + 1 < len(W.POOL_RIM_Z) else W.FLOOR)
        below_iw = (W.POOL_INNER[tier + 1][0] if tier + 1 < len(W.POOL_INNER)
                    else W.SIZE - 2 * W.WALL)
        below_f_in = (iby - (W.POOL_INNER[tier + 1][1] + W.POOL_WALL) + W.POOL_WALL
                      if tier + 1 < len(W.POOL_INNER) else -(W.SIZE / 2 - W.WALL))
        out.append(dict(
            tier=tier, name=["top", "mid", "bottom"][tier],
            outer_w=ow, f_out=iby - od, back_y=iby,
            shelf_z=rim - W.POOL_DEPTH_Z - W.POOL_FLOOR_T,
            land_z=land, below_iw=below_iw, below_f_in=below_f_in))
    return out


def _masks(rec):
    ow, f_out, back = rec["outer_w"], rec["f_out"], rec["back_y"]
    xs = np.arange(-ow / 2, ow / 2 + STEP, STEP)
    ys = np.arange(f_out, back + STEP, STEP)
    gx, gy = np.meshgrid(xs, ys, indexing="ij")

    ceiling = np.ones(gx.shape, bool)
    held = np.zeros(gx.shape, bool)

    half = W.SUPPORT_WALL_T / 2
    for (x, y0, y1, _land) in W.support_wall_segments(rec):
        held |= (np.abs(gx - x) <= half) & (gy >= y0) & (gy <= y1)

    # drip guides run to the floor below, so they hold the shelf as well
    gw = W.SLIT_W / 2 + W.COLUMN_WIDEN
    side_x = ow / 2 - W.POOL_WALL / 2
    side_y = back - (rec["outer_w"] - 2 * W.POOL_WALL + W.POOL_WALL) / 2
    held |= (np.abs(gx) <= gw) & (np.abs(gy - (f_out + W.POOL_WALL / 2)) <= W.POOL_WALL)
    for sx in (-side_x, side_x):
        held |= (np.abs(gx - sx) <= W.POOL_WALL) & (np.abs(gy - side_y) <= gw)

    # the riser passes straight through the shelf, so that patch is solid
    spine = (np.abs(gx) <= W.SPINE_UP_W / 2) & (gy >= back - W.SPINE_UP_INNER_D)
    held |= spine
    ceiling &= ~spine

    return gx, gy, ceiling, held


def analyse():
    rows = []
    for rec in shelf_records():
        gx, gy, ceiling, held = _masks(rec)
        dist = ndimage.distance_transform_edt(~held, sampling=STEP)
        d = np.where(ceiling, dist, 0.0)
        area = max(ceiling.sum() * STEP ** 2, 1.0)
        beyond = (d > BRIDGE_OK / 2).sum() * STEP ** 2
        rows.append(dict(
            name=rec["name"], rec=rec, gx=gx, gy=gy, dist=d,
            ceiling=ceiling, held=held,
            area_cm2=area / 100,
            worst_span=2 * float(d.max()),
            beyond_cm2=beyond / 100,
            beyond_pct=100 * beyond / area))
    return rows


def run(quiet=False):
    rows = analyse()
    if not quiet:
        print("coverage:")
        print(f"  {'shelf':<8}{'ceiling':>11}{'worst span':>13}"
              f"{'over bridge limit':>22}")
        for r in rows:
            print(f"  {r['name']:<8}{r['area_cm2']:>8.0f} cm2"
                  f"{r['worst_span']:>10.1f} mm"
                  f"{r['beyond_cm2']:>14.0f} cm2 ({r['beyond_pct']:.0f}%)")
        print(f"  worst span = widest unsupported void; bridge limit taken as "
              f"{BRIDGE_OK:.0f} mm")
        heatmap(rows)
    return rows


def heatmap(rows=None):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    rows = rows or analyse()
    fig, axes = plt.subplots(1, 3, figsize=(15.5, 6.2))
    fig.patch.set_facecolor("white")
    vmax = max(float(r["dist"].max()) for r in rows)
    im = None
    for ax, r in zip(axes, rows):
        m = np.where(r["ceiling"], r["dist"], np.nan)
        im = ax.pcolormesh(r["gx"], r["gy"], m, cmap="magma_r", vmin=0, vmax=vmax)
        ax.contour(r["gx"], r["gy"], np.nan_to_num(m), levels=[BRIDGE_OK / 2],
                   colors="#2F9E8F", linewidths=1.8)
        ax.set_aspect("equal")
        ax.axis("off")
        ax.set_title(f"{r['name']} shelf   worst span {r['worst_span']:.0f} mm",
                     fontsize=12.5, color="#1B2A30", weight="bold", pad=10)
    cb = fig.colorbar(im, ax=axes, fraction=0.025, pad=0.02)
    cb.set_label("distance to nearest support (mm)", fontsize=10, color="#6C858E")
    fig.suptitle("Support coverage on the shelf ceilings", fontsize=16,
                 color="#1B2A30", weight="bold", y=0.97)
    fig.text(0.5, 0.05, f"teal contour = {BRIDGE_OK:.0f} mm bridge limit; "
             "anything inside it bridges further than that",
             ha="center", fontsize=11, color="#6C858E")
    out = paths.IMG / "coverage.png"
    fig.savefig(str(out), dpi=115, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    print(f"  coverage map -> {paths.rel(out)}")
