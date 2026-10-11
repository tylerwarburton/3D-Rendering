"""Print-first test coupons, sliced out of the finished mesh.

Cutting the coupons from the exported part (rather than re-modelling them)
means a coupon can never quietly drift away from the thing it is testing.
Slicing is done at mesh level: the CAD-level intersect leaves real holes in
the cap at several cut heights.
"""
import numpy as np
import trimesh

import params as P


def _slice(mesh, normal, origin):
    return trimesh.intersections.slice_mesh_plane(
        mesh, plane_normal=normal, plane_origin=origin, cap=True)


def _slice_clean(mesh, normal, origin, axis, target, search=1.5):
    """Slice, nudging the plane until the cap comes out watertight.

    slice_mesh_plane(cap=True) fails outright at heights where the plane
    lands on existing mesh vertices, so the height is searched rather than
    assumed.
    """
    best = None
    for d in np.concatenate([[0.0], np.arange(0.1, search, 0.1),
                             -np.arange(0.1, search, 0.1)]):
        o = list(origin)
        o[axis] = target + float(d)
        out = _slice(mesh, normal, o)
        if out.is_watertight:
            return out, o[axis]
        best = best or out
    return best, target


def _slit(mesh, z_cut):
    """Cut a thin slit clean through one wall so the ring can spring open.

    Without it the coupon is a closed loop and either goes on or does not;
    with it the fit can be felt, and a tie closes it back up.
    """
    sgn = 1.0 if P.COUPON_SLIT_FACE == "+Y" else -1.0
    depth = P.SOCK_OD_HH + P.BOSS_T + 10.0
    cutter = trimesh.creation.box(
        extents=[P.COUPON_SLIT_W, depth, z_cut + 20.0])
    cutter.apply_translation([P.COUPON_SLIT_X,
                              sgn * (P.SOCK_ID_HH - 4.0 + depth / 2.0),
                              (z_cut + 20.0) / 2.0 - 5.0])
    out = trimesh.boolean.difference([mesh, cutter], engine="manifold")
    if not out.is_watertight:
        raise RuntimeError("slit left the coupon non-watertight")
    print(f"  ..  {P.COUPON_SLIT_W:.1f} mm flex slit through side "
          f"{P.COUPON_SLIT_FACE} at x={P.COUPON_SLIT_X:+.1f}")
    return out


def make(mesh):
    """Return {name: mesh}. Raises if a coupon does not come out watertight."""
    out = {}

    # cut just above the collar so the coupons carry their side labels
    z_cut = P.Z_TRANS_0 - 0.5

    # 1. the whole socket and collar: checks the 136 x 44 perimeter, both
    #    flare angles, how hard the crush ribs grip, and the tie path at all
    #    six connectors
    mouth, z1 = _slice_clean(mesh, [0, 0, -1], [0, 0, z_cut], 2, z_cut)
    if P.COUPON_SLIT:
        mouth = _slit(mouth, z_cut)
    out["coupon_mouth_ring"] = mouth

    # 2. the C end only - a few minutes of filament to check the pocket
    #    against the real tab before committing to the full print
    tab = _slice(mesh, [1, 0, 0], [P.SOCK_ID_HW - 6.0, 0, 0])
    tab = _slice(tab, [0, -1, 0], [0, 26.0, 0])
    tab = _slice(tab, [0, 1, 0], [0, -26.0, 0])
    tab, z2 = _slice_clean(tab, [0, 0, -1], [0, 0, z_cut], 2, z_cut)
    out["coupon_connector"] = tab
    print(f"  ..  cut heights: mouth ring z={z1:.1f}, connector z={z2:.1f}")

    for name, m in out.items():
        if not m.is_watertight:
            broken = len(trimesh.repair.broken_faces(m))
            raise RuntimeError(f"{name}: not watertight ({broken} broken faces)")
        print(f"  ok  {name:<24} vol={m.volume / 1000.0:6.2f} cm^3  "
              f"bbox {np.round(m.extents, 1)}")
    return out
