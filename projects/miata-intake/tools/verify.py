"""Analytic checks on the finished mesh.

Nominal dimensions are not evidence - every number below is measured off the
exported triangle mesh with ray casts and point containment, the way the
printed part will be. Probe locations are searched for rather than
hard-coded, because moving a connector once left a wall-thickness ray
pointing at a pocket floor and the check happily reported a 26 mm bore.
"""
import math

import numpy as np
import trimesh

import params as P


def _ray(mesh, origin, direction, limit=400.0):
    origin = np.asarray(origin, dtype=float)
    d = np.asarray(direction, dtype=float)
    d = d / np.linalg.norm(d)
    locs, _, _ = mesh.ray.intersects_location([origin], [d])
    if len(locs) == 0:
        return []
    t = np.sort(np.linalg.norm(locs - origin, axis=1))
    # a ray grazing a seam can report the same surface twice; collapse those
    out = []
    for v in t:
        if v <= limit and (not out or v - out[-1] > 1e-3):
            out.append(float(v))
    return out


def _clear_spot(bosses, ribs, limit, blocks=()):
    """A coordinate on a face clear of every boss, rib and other feature.

    `blocks` is (centre, half_width) for anything else in the way - the
    clamshell split and its clamp ears, for instance. Leaving those out once
    put the bore probe straight down the split, and the ray found nothing.
    """
    need_b = P.BOSS_LAT / 2.0 + 2.0
    need_r = P.RIB_WIDTH / 2.0 + 2.0
    for v in sorted(np.arange(-limit, limit + 0.01, 0.5), key=abs):
        if all(abs(v - b) > need_b for b in bosses) and \
                all(abs(v - r) > need_r for r in ribs) and \
                all(abs(v - c) > h + 2.0 for c, h in blocks):
            return float(v)
    raise RuntimeError("no clear wall left to probe - features cover the "
                       "whole face")


def report(mesh):
    import adapter as A

    ok = True
    out = []

    def line(flag, text):
        nonlocal ok
        ok = ok and flag
        out.append(("PASS" if flag else "FAIL") + "  " + text)

    lo, hi = mesh.bounds
    size = hi - lo
    line(mesh.is_watertight, f"mesh is watertight ({len(mesh.faces)} triangles)")
    line(mesh.is_winding_consistent, "winding is consistent")
    line(abs(mesh.volume) > 0, f"volume {mesh.volume / 1000.0:.1f} cm^3, "
                               f"surface {mesh.area / 100.0:.1f} cm^2")
    shells = len(mesh.split(only_watertight=False))
    line(shells == 1, f"single connected body ({shells} shells)")
    out.append(f"      bounding box {size[0]:.1f} x {size[1]:.1f} x "
               f"{size[2]:.1f} mm")

    # --- the flare on the two short ends -----------------------------------
    y_boss = P.TAB_Y_FACE_PX + (P.TAB_L + 2 * P.TAB_CLEAR) / 2.0 + 2.0
    y_flat = P.SOCK_ID_HH - P.SOCK_ID_R - 0.5      # flat wall past the boss
    for kind, want_deg in (("+X", P.FRAME_DRAFT_PX), ("-X", P.FRAME_DRAFT_NX)):
        sgn = 1.0 if kind == "+X" else -1.0
        za, zb = 4.0, P.SOCKET_DEPTH - 4.0
        ha = _ray(mesh, (0, sgn * y_flat, za), (sgn, 0, 0))[0]
        hb = _ray(mesh, (0, sgn * y_flat, zb), (sgn, 0, 0))[0]
        got = math.degrees(math.atan2(ha - hb, zb - za))
        line(abs(got - want_deg) < 0.4,
             f"end {A.SIDE_NAME[kind]} flares {got:.2f} deg "
             f"(want {want_deg:.2f})")
        want_a = A.half_x(kind, P.SOCK_ID_HW, za)  # flat wall, no boss
        line(abs(ha - want_a) < 0.2,
             f"end {A.SIDE_NAME[kind]} half-width at z={za:.0f} is "
             f"{ha:.2f} mm (want {want_a:.2f})")

    # --- socket bore, clear of ribs, pockets and bosses ---------------------
    z = P.SOCKET_DEPTH * 0.6
    blocks = []
    if P.SPLIT_ENABLE:
        blocks.append((P.SPLIT_X, P.SPLIT_W / 2.0))
        if P.EAR_ENABLE:
            blocks += [(x, P.EAR_LAT / 2.0) for x in A.ear_sites()]
    x_clear = _clear_spot(list(P.TAB_X_FACE_PY) + list(P.TAB_X_FACE_NY),
                          list(P.RIB_X_LONG),
                          P.SOCK_ID_HW - P.SOCK_ID_R - 6.0, blocks)
    out.append(f"      probes: long face x={x_clear:+.1f}, "
               f"short end y={y_boss:+.1f}")
    ty = _ray(mesh, (x_clear, 0, z), (0, 1, 0))
    line(abs(ty[0] - P.SOCK_ID_HH) < 0.15,
         f"socket half-height {ty[0]:.2f} mm (want {P.SOCK_ID_HH:.2f})")
    line(abs((ty[1] - ty[0]) - P.WALL) < 0.12,
         f"plain socket wall {ty[1] - ty[0]:.2f} mm (want {P.WALL:.2f})")

    z_boss = P.SOCKET_DEPTH - P.TAB_Z_FROM_RIM
    tb = _ray(mesh, (0, y_boss, z_boss), (1, 0, 0))
    horiz = (P.WALL + P.BOSS_T) * math.sqrt(1.0 + A.DRAFT["+X"] ** 2)
    line(abs((tb[1] - tb[0]) - horiz) < 0.35,
         f"wall through the C boss {tb[1] - tb[0]:.2f} mm (want {horiz:.2f} "
         f"measured horizontally across a {P.FRAME_DRAFT_PX:.1f} deg face)")

    # --- collar and stop ledge ----------------------------------------------
    # probed clear of the bosses, which now run up into the collar
    z_collar = P.SOCKET_DEPTH + P.COLLAR_LEN / 2.0
    tc = _ray(mesh, (x_clear, 0, z_collar), (0, 1, 0))
    line(abs(tc[0] - (P.SOCK_ID_HH - P.STOP_LEDGE)) < 0.15,
         f"bore steps in to {tc[0]:.2f} mm at the collar "
         f"(want {P.SOCK_ID_HH - P.STOP_LEDGE:.2f}, a "
         f"{P.STOP_LEDGE:.1f} mm stop ledge)")
    tcx = _ray(mesh, (0, sgn * y_flat, z_collar), (1, 0, 0))
    line(abs(tcx[1] - P.SOCK_OD_HW) < 0.15,
         f"collar is straight at {tcx[1]:.2f} mm half-width "
         f"(want {P.SOCK_OD_HW:.2f}, no draft)")

    # --- crush ribs ---------------------------------------------------------
    z_rib = P.RIB_START_Z + P.RIB_RAMP + 2.0
    hits, total = 0, 0
    for kind, lat in A.rib_sites():
        O, u, n, v = A.face_frame(kind, lat, z_rib)
        total += 1
        d = np.array([n.x, n.y, n.z])
        origin = np.array([O.x, O.y, O.z]) - d * 5.0
        t = _ray(mesh, origin, d)
        if t and abs(t[0] - (5.0 - P.RIB_PROUD)) < 0.15:
            hits += 1
    line(hits == total,
         f"crush ribs standing {P.RIB_PROUD} mm proud: {hits}/{total}")

    # --- connector pockets, tie slots, labels -------------------------------
    pocket_ok, slot_ok, wall_ok, label_ok = 0, 0, 0, 0
    slot_off = P.TIE_PORT_OUT_OFF
    for name, kind, lat, zc in A.connector_sites():
        O, u, n, v = A.face_frame(kind, lat, zc)
        o = np.array([O.x, O.y, O.z])
        nv = np.array([n.x, n.y, n.z])
        uv = np.array([u.x, u.y, u.z])
        vv = np.array([v.x, v.y, v.z])
        probes = np.array([o + nv * d for d in
                           np.linspace(P.TAB_PROUD + P.TAB_DEPTH_CLEAR + 0.3,
                                       P.WALL + P.BOSS_T - 0.3, 5)])
        if mesh.contains(probes).all():
            pocket_ok += 1
        for sgn in (-1.0, 1.0):
            # follow the slanted port from its outside opening down into the
            # pocket - every sample must be open air
            t0, t1 = P.TIE_PORT_START + 0.3, P.WALL + P.BOSS_T - 0.3
            span = (P.WALL + P.BOSS_T + 3.0) - P.TIE_PORT_START
            run = []
            for d in np.linspace(t0, t1, 9):
                frac = (d - P.TIE_PORT_START) / span
                ax = P.TIE_PORT_IN_OFF + frac * (P.TIE_PORT_OUT_OFF
                                                 - P.TIE_PORT_IN_OFF)
                run.append(o + vv * (sgn * ax) + nv * d)
            if not mesh.contains(np.array(run)).any():
                slot_ok += 1
            # and the inner wall directly behind the outside opening must
            # still be solid, or the port has broken into the duct
            behind = o + vv * (sgn * P.TIE_PORT_OUT_OFF) + nv * 0.8
            if mesh.contains(np.array([behind]))[0]:
                wall_ok += 1
    line(pocket_ok == 6,
         f"connector pockets backed by a "
         f"{P.WALL + P.BOSS_T - P.TAB_PROUD - P.TAB_DEPTH_CLEAR:.1f} mm "
         f"tie bridge: {pocket_ok}/6")
    line(slot_ok == 12,
         f"tie ports run from the outside into the pocket: {slot_ok}/12")
    line(wall_ok == 12,
         f"inner wall still solid behind each port - nothing opens into the "
         f"duct: {wall_ok}/12")

    # the pocket must be the ONLY break in the inner wall, and deep enough
    # for the tie to turn into the connector
    chan_ok, clear_ok = 0, 0
    for name, kind, lat, zc in A.connector_sites():
        O, u, n, v = A.face_frame(kind, lat, zc)
        o = np.array([O.x, O.y, O.z])
        nv = np.array([n.x, n.y, n.z])
        vv = np.array([v.x, v.y, v.z])
        # just past each end of the pocket, at the bore surface, the wall
        # must be solid - the pocket is the only inner-wall recess
        edge = (P.TAB_W + 2 * P.TAB_CLEAR_AX) / 2.0 + 1.0
        rim = np.array([o + vv * (sg * edge) + nv * 0.4
                        for sg in (-1.0, 1.0)])
        if mesh.contains(rim).all():
            chan_ok += 1
        over = np.array([o + nv * d for d in
                         np.linspace(P.TAB_PROUD + 0.1,
                                     P.TAB_PROUD + P.TAB_DEPTH_CLEAR - 0.2, 4)])
        if not mesh.contains(over).any():
            clear_ok += 1
    line(chan_ok == 6,
         f"inner wall closed either side of each pocket: {chan_ok}/6")
    line(clear_ok == 6,
         f"{P.TIE_THICK:.1f} mm of tie clearance over each tab: "
         f"{clear_ok}/6")

    if P.LABEL_ENABLE:
        names = []
        for txt, kind, lat, zc in A.label_sites():
            O, u, n, v = A.face_frame(kind, lat, zc)
            o = np.array([O.x, O.y, O.z])
            nv = np.array([n.x, n.y, n.z])
            uv = np.array([u.x, u.y, u.z])
            wall = A.wall_perp(kind, zc < P.SOCKET_DEPTH - 1e-9)
            # sweep across the label and look for material standing proud
            found = False
            for s in np.linspace(-P.LABEL_SIZE * 0.6, P.LABEL_SIZE * 0.6, 25):
                p = o + uv * s + nv * (wall + P.LABEL_PROUD * 0.5)
                if mesh.contains(np.array([p]))[0]:
                    found = True
                    break
            label_ok += int(found)
            if not found:
                names.append(txt)
        line(label_ok == len(A.label_sites()),
             f"side labels raised {P.LABEL_PROUD} mm: {label_ok}/"
             f"{len(A.label_sites())}"
             + (f"  missing {', '.join(names)}" if names else ""))

    # --- clamshell split and clamp ears -------------------------------------
    if P.SPLIT_ENABLE:
        sgn = 1.0 if P.SPLIT_FACE == "+Y" else -1.0
        open_pts = []
        for z in np.linspace(2.0, P.SPLIT_TOP - 2.0, 12):
            for y in np.linspace(P.SOCK_ID_HH + 0.4, P.SOCK_OD_HH - 0.4, 4):
                open_pts.append([P.SPLIT_X, sgn * y, z])
        line(not mesh.contains(np.array(open_pts)).any(),
             f"split runs clear through side {A.SIDE_NAME[P.SPLIT_FACE]} "
             f"from the mouth to z={P.SPLIT_TOP:.0f}")
        above = np.array([[P.SPLIT_X, sgn * (P.SOCK_OD_HH - 1.0),
                           P.SPLIT_TOP + 4.0]])
        line(mesh.contains(above)[0],
             "wall is continuous again above the split - the duct stays closed")

    if P.SPLIT_ENABLE and P.EAR_ENABLE:
        sgn = 1.0 if P.SPLIT_FACE == "+Y" else -1.0
        solid_ears = 0
        for x in A.ear_sites():
            p = np.array([[x, sgn * (P.SOCK_OD_HH + P.EAR_PROUD / 2.0),
                           P.EAR_Z]])
            solid_ears += int(mesh.contains(p)[0])
        line(solid_ears == 2, f"both clamp ears present: {solid_ears}/2")
        bore_line = np.array(
            [[x, sgn * (P.SOCK_OD_HH + P.EAR_PROUD / 2.0), P.EAR_HOLE_Z]
             for x in np.linspace(A.ear_sites()[0], A.ear_sites()[1], 15)])
        line(not mesh.contains(bore_line).any(),
             "tie hole runs through both ears and across the split")

    # --- outlet -------------------------------------------------------------
    z_out = P.Z_END - 3.0
    t = _ray(mesh, (0, 0, z_out), (1, 0, 0))
    line(abs(t[0] - (P.OUTLET_OD / 2.0 - P.OUTLET_WALL)) < 0.2,
         f"outlet bore radius {t[0]:.2f} mm "
         f"(want {P.OUTLET_OD / 2.0 - P.OUTLET_WALL:.2f})")
    line(abs(t[1] - P.OUTLET_OD / 2.0) < 0.2,
         f"outlet outer radius {t[1]:.2f} mm (want {P.OUTLET_OD / 2.0:.2f})")
    tbd = _ray(mesh, (0, 0, P.Z_END - P.BEAD_FROM_END), (1, 0, 0))
    line(abs(tbd[-1] - (P.OUTLET_OD / 2.0 + P.BEAD_HEIGHT)) < 0.2,
         f"bead outer radius {tbd[-1]:.2f} mm "
         f"(want {P.OUTLET_OD / 2.0 + P.BEAD_HEIGHT:.2f})")

    inlet = P.FRAME_W * P.FRAME_H - (4 - np.pi) * P.FRAME_CORNER_R ** 2
    outlet_a = np.pi * (P.OUTLET_OD / 2.0 - P.OUTLET_WALL) ** 2
    out.append(f"      inlet opening ~{inlet:.0f} mm^2, outlet bore "
               f"{outlet_a:.0f} mm^2 -> {outlet_a / inlet * 100:.0f}% of inlet")
    return ok, out
