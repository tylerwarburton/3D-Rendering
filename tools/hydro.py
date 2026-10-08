"""One hydraulic model of the waterfall, read by the diagrams and the audit.

Everything here is derived from src/waterfall.py, so changing a design
parameter updates the analysis with no edits in this file.
"""
import numpy as np

from . import paths          # noqa: F401  (puts src/ on the path)
import waterfall as W

G = 9.81
INCH = 25.4
CD_WEIR = 0.62               # sharp-crested rectangular weir discharge coeff


def slit_h():
    return W.POOL_DEPTH_Z * W.SLIT_FRAC


def inner_back_y():
    return W.SIZE / 2 - W.WALL


def pools():
    """Geometry + water levels for each tier, top to bottom."""
    out = []
    iby, sh = inner_back_y(), slit_h()
    for k, ((iw, idp), rim_z) in enumerate(zip(W.POOL_INNER, W.POOL_RIM_Z)):
        ow, od = iw + 2 * W.POOL_WALL, idp + W.POOL_WALL
        floor_out = rim_z - W.POOL_DEPTH_Z - W.POOL_FLOOR_T
        out.append(dict(
            k=k, name=["top", "mid", "bottom"][k],
            iw=iw, idp=idp, ow=ow, od=od,
            rim_z=rim_z,
            floor_in=rim_z - W.POOL_DEPTH_Z,      # wetted floor
            floor_out=floor_out,                  # underside of the shelf
            surf=rim_z - sh,                      # water surface = weir invert
            depth=sh and (rim_z - sh) - (rim_z - W.POOL_DEPTH_Z),
            freeboard=sh,
            f_out=iby - od, f_in=iby - od + W.POOL_WALL,
            back_y=iby,
            volume_ml=iw * idp * ((rim_z - sh) - (rim_z - W.POOL_DEPTH_Z)) / 1000,
        ))
    return out


def basin():
    bi = W.SIZE - 2 * W.WALL
    return dict(iw=bi, idp=bi, half=bi / 2,
                floor_in=W.FLOOR, rim_z=W.LOW_WALL_H,
                usable_depth=W.LOW_WALL_H - W.FLOOR,
                area=bi * bi,
                gross_l=bi * bi * (W.LOW_WALL_H - W.FLOOR) / 1e6)


def weir_flow_lph(head_mm, crest_mm=None):
    """Rectangular sharp-crested weir discharge, litres/hour."""
    if crest_mm is None:
        crest_mm = 3 * W.SLIT_W
    b, h = crest_mm / 1000.0, max(head_mm, 0) / 1000.0
    return CD_WEIR * (2 / 3) * np.sqrt(2 * G) * b * h ** 1.5 * 1000 * 3600


def weir_capacity_lph():
    """Flow at which the slits are exactly full."""
    return weir_flow_lph(slit_h())


def outlet_jet(flow_lph, dia_mm=None):
    """Velocity and free rise height of the cap outlet jet."""
    d = (dia_mm or W.SPINE_CAP_HOLE_D) / 1000.0
    a = np.pi * (d / 2) ** 2
    v = (flow_lph / 1000 / 3600) / a
    return v, v ** 2 / (2 * G) * 1000


def transitions():
    """Fall height and catch margins for each tier-to-tier handoff."""
    ps, bs = pools(), basin()
    rows = []
    for k, g in enumerate(ps):
        if k < len(ps) - 1:
            below, label = ps[k + 1], f"{g['name']} -> {ps[k+1]['name']}"
            side = below["iw"] / 2 - g["ow"] / 2
            front = g["f_out"] - below["f_in"]
            catch_z = below["surf"]
            rim_clear = below["ow"] / 2 - g["ow"] / 2
        else:
            label = f"{g['name']} -> basin"
            side = bs["half"] - g["ow"] / 2
            front = g["f_out"] + bs["half"]
            catch_z = bs["floor_in"] + 45
            rim_clear = W.SIZE / 2 - g["ow"] / 2
        fall = g["surf"] - catch_z
        rows.append(dict(label=label, k=k, fall=fall, side=side, front=front,
                         rim_clear=rim_clear,
                         v_max=side / 1000 / np.sqrt(2 * (fall / 1000) / G)))
    return rows


def throw(fall_mm, v_ms):
    """Horizontal travel of a stream leaving with velocity v and falling fall_mm."""
    return v_ms * np.sqrt(2 * (fall_mm / 1000) / G) * 1000


def drain_back():
    """Water parked in the pools while running, and the safe basin fill window."""
    ps, bs = pools(), basin()
    parked = sum(p["volume_ml"] for p in ps)
    drop = parked * 1000 / bs["area"]
    return dict(parked_ml=parked, level_drop_mm=drop,
                min_fill_mm=drop + 20, max_fill_mm=bs["usable_depth"],
                min_fill_l=bs["area"] * (drop + 20) / 1e6,
                max_fill_l=bs["gross_l"])
