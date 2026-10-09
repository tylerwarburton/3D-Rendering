"""Plan view of where each stream lands relative to the vessel below it."""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.lines import Line2D

from . import paths, hydro
import waterfall as W

AQUA, AMBER, INK, DIM = "#2F9E8F", "#D9812F", "#1B2A30", "#6C858E"
SPEEDS = [0.05, 0.10, 0.20, 0.30]


def run():
    ps, bs = hydro.pools(), hydro.basin()
    trans = hydro.transitions()

    targets = []
    for k in range(len(ps)):
        if k < len(ps) - 1:
            b = ps[k + 1]
            targets.append(dict(iw=b["iw"], ow=b["ow"], f_in=b["f_in"], f_out=b["f_out"],
                                back=b["back_y"]))
        else:
            targets.append(dict(iw=bs["iw"], ow=W.SIZE, f_in=-bs["half"],
                                f_out=-W.SIZE / 2, back=bs["half"]))

    fig, axes = plt.subplots(1, 3, figsize=(16.5, 7.2))
    fig.patch.set_facecolor("white")

    for ax, k in zip(axes, range(3)):
        g, below, t = ps[k], targets[k], trans[k]

        ax.add_patch(Rectangle((-below["ow"] / 2, below["f_out"]), below["ow"],
                               below["back"] - below["f_out"],
                               facecolor="#E7EDEF", edgecolor="#9FB2B9", lw=1.2, zorder=1))
        ax.add_patch(Rectangle((-below["iw"] / 2, below["f_in"]), below["iw"],
                               below["back"] - below["f_in"],
                               facecolor="#CDE8E3", edgecolor=AQUA, lw=1.8, zorder=2))
        ax.add_patch(Rectangle((-g["ow"] / 2, g["f_out"]), g["ow"],
                               g["back_y"] - g["f_out"],
                               facecolor="none", edgecolor=INK, lw=1.4, ls="--", zorder=4))

        y_side = g["back_y"] - g["od"] / 2
        exits = [(-g["ow"] / 2, y_side, (-1, 0)),
                 (g["ow"] / 2, y_side, (1, 0)),
                 (0.0, g["f_out"], (0, -1))]

        for ex, ey, dv in exits:
            ax.plot([ex], [ey], "o", color=AMBER, ms=7, zorder=6)
            for i, v in enumerate(SPEEDS):
                dist = hydro.throw(t["fall"], v)
                px, py = ex + dv[0] * dist, ey + dv[1] * dist
                ok = abs(px) <= below["iw"] / 2 and py >= below["f_in"]
                c = AQUA if ok else AMBER
                ax.plot([ex, px], [ey, py], "-", color=c, lw=1.6,
                        alpha=0.35 + 0.16 * i, zorder=5)
                ax.plot([px], [py], "s" if ok else "X", color=c, ms=6.5, zorder=7)

        ax.set_title(t["label"].replace("->", "\u2192"), fontsize=13.5, color=INK,
                     pad=16, weight="bold")
        ax.text(0.5, -0.085, f"free fall {t['fall']:.0f} mm   \u00b7   "
                             f"side catch margin {t['side']:.1f} mm",
                transform=ax.transAxes, ha="center", fontsize=10.5, color=DIM)

        xr = below["ow"] / 2 + 34
        ylo, yhi = below["f_out"] - 16, below["back"] + 16
        half = max(xr * 2, yhi - ylo) / 2
        ax.set_xlim(-half, half)
        ax.set_ylim((ylo + yhi) / 2 - half, (ylo + yhi) / 2 + half)
        ax.set_aspect("equal")
        ax.axis("off")

    handles = [
        Line2D([], [], marker="o", color=AMBER, ls="", ms=8, label="slit exit"),
        Line2D([], [], marker="s", color=AQUA, ls="", ms=8, label="lands in the pool below"),
        Line2D([], [], marker="X", color=AMBER, ls="", ms=9, label="lands on the rim or outside"),
        Line2D([], [], color=DIM, lw=1.6,
               label="exit speed " + " / ".join(f"{v:.2f}" for v in SPEEDS) + " m/s"),
    ]
    fig.legend(handles=handles, loc="lower center", ncol=4, frameon=False,
               fontsize=10.5, bbox_to_anchor=(0.5, 0.005))
    fig.suptitle("Where each stream lands  \u2014  plan view, looking down",
                 fontsize=16, color=INK, weight="bold", y=0.985)
    fig.text(0.5, 0.925, "Front slits have room to spare. The side slits sit almost "
             "directly over the wall of the pool below.",
             ha="center", fontsize=11.5, color=DIM)
    fig.subplots_adjust(top=0.845, bottom=0.11, wspace=0.06)

    out = paths.IMG / "spill_map.png"
    fig.savefig(str(out), dpi=115, facecolor="white")
    plt.close(fig)
    print(f"  spill_map -> {paths.rel(out)}")
