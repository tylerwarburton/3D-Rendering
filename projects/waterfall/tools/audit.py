"""Writes out/waterfall/report.txt: geometry audit + hydraulics."""
import numpy as np

from . import paths, hydro
import waterfall as W

IN = 25.4


def _i(x):
    return x / IN


def report():
    L = []
    def p(s=""):
        L.append(s)

    ps, bs, dr = hydro.pools(), hydro.basin(), hydro.drain_back()
    sh = hydro.slit_h()

    p("=" * 76)
    p("WATERFALL")
    p("=" * 76)
    p(f"Outer cube        : {_i(W.SIZE):.2f} in square x {_i(W.BACK_WALL_TOP):.2f} in tall")
    p(f"Basin             : inner {_i(bs['iw']):.2f} in square, usable depth "
      f"{bs['usable_depth']:.1f} mm, {bs['gross_l']:.2f} L gross")
    p("")
    p("POOLS")
    for g in ps:
        p(f"  {g['name'].upper():<7} inner {_i(g['iw']):.2f} x {_i(g['idp']):.2f} in   "
          f"rim z={_i(g['rim_z']):.2f} in")
        p(f"          water {g['depth']:.0f} mm deep = {g['volume_ml']:.0f} mL, "
          f"freeboard {g['freeboard']:.0f} mm to the rim")
        p(f"          footprint x=[{-g['ow']/2:.1f}, {g['ow']/2:.1f}]  "
          f"y=[{g['f_out']:.1f}, {g['back_y']:.1f}]")
    p(f"  Slits: {W.SLIT_W:.2f} x {sh:.1f} mm, 3 per pool, "
      f"{3*W.SLIT_W*sh:.0f} mm2 open area per pool")
    p("")

    p("WEIR CAPACITY  (Q = Cd (2/3) sqrt(2g) b h^1.5, Cd=0.62)")
    p(f"  crest width {3*W.SLIT_W:.1f} mm, slit height {sh:.1f} mm")
    for h in [1, 2, 4, 6, 8, 10]:
        note = "  <-- slits full" if abs(h - sh) < 0.01 else (
            "  slits drowned, water sheets over the rim" if h > sh else "")
        p(f"    head {h:>2.0f} mm  ->  {hydro.weir_flow_lph(h):>6.0f} L/h{note}")
    p(f"  CAPACITY = {hydro.weir_capacity_lph():.0f} L/h before the pool overtops")
    p("")

    p("OUTLET JET  (cap hole into the cup)")
    p(f"  {W.SPINE_CAP_HOLE_D:.2f} mm dia, "
      f"{np.pi*(W.SPINE_CAP_HOLE_D/2)**2:.0f} mm2, cup {W.SPINE_CUP_DEPTH:.1f} mm deep")
    for q in [200, 400, 600, 800]:
        v, rise = hydro.outlet_jet(q)
        p(f"    {q:>4} L/h -> {v:>5.2f} m/s, free rise {rise:>6.0f} mm")
    p("")

    p("LANDING MARGINS")
    p(f"  {'transition':<22}{'fall':>8}{'side':>9}{'front':>9}{'max exit speed':>17}")
    for t in hydro.transitions():
        p(f"  {t['label']:<22}{t['fall']:>6.0f}mm{t['side']:>7.1f}mm"
          f"{t['front']:>7.1f}mm{t['v_max']:>13.2f} m/s")
    p("  (max exit speed = the speed at which the stream clears the side catch margin)")
    p("")
    p("  Horizontal throw for each fall height:")
    p(f"  {'transition':<22}" + "".join(f"{v:>9.2f}" for v in [0.05, 0.1, 0.2, 0.3, 0.5]))
    for t in hydro.transitions():
        p(f"  {t['label']:<22}" +
          "".join(f"{hydro.throw(t['fall'], v):>8.1f}mm" for v in [0.05, 0.1, 0.2, 0.3, 0.5]))
    p("")

    p("BASIN FILL WINDOW")
    p(f"  water parked in the pools while running: {dr['parked_ml']:.0f} mL")
    p(f"  that drops the basin {dr['level_drop_mm']:.1f} mm at startup")
    p(f"  fill between {dr['min_fill_mm']:.0f} and {dr['max_fill_mm']:.0f} mm "
      f"({dr['min_fill_l']:.2f} - {dr['max_fill_l']:.2f} L)")
    p("    below the minimum the pump runs dry on startup")
    p("    above the maximum the basin overflows on shutdown when the pools drain back")
    p("")

    p("KNOWN DEFECT")
    p(f"  BACK_TOP_W ({_i(W.BACK_TOP_W):.2f} in) and TAPER_START_Z are declared but never")
    p( "  cut: the wedge cutters land at y=89.8..97.8 mm while the back wall occupies")
    p( "  y=98.8..104.8 mm. The back wall prints full width.")
    p("")

    return "\n".join(L)


def run():
    txt = report()
    out = paths.OUT / "report.txt"
    out.write_text(txt)
    print(f"  report -> {paths.rel(out)}")
    return txt
