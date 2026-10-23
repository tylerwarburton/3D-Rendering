"""Scene-only lever-toggle reference geometry for the browser configurator.

These meshes live under mock/ and are never listed as printable parts.
"""
import json
import shutil
from pathlib import Path

import numpy as np
import trimesh


# Rear-body measurements are still approximate; the visible hardware is a
# conventional lever toggle. The threaded bushing stays at the first-round
# 12 mm assumption until measured.
BODY_W = 14.0
BODY_H = 29.0
BODY_DEPTH = 20.0
CLIP_W = 15.0
TERMINAL_DEPTH = 8.0
BUSHING_D = 12.0
WASHER_D = 18.0


def _box(size, center):
    mesh = trimesh.creation.box(extents=size)
    mesh.apply_translation(center)
    return mesh


def _cylinder_between(radius, a, b, sections=64):
    return trimesh.creation.cylinder(radius=radius, segment=np.array([a, b]), sections=sections)


def _toggle(center_z, lever_dz=0.0, rotation_deg=0.0):
    """Lever toggle in installed coordinates: x across, y rear, z vertical."""
    panel_back = 2.5
    body_center_y = panel_back + BODY_DEPTH / 2
    body = _box((BODY_W, BODY_DEPTH, BODY_H), (0, body_center_y, center_z))
    clips = [
        _box(((CLIP_W - BODY_W) / 2, 8.0, 21.0),
             (sx * (BODY_W + CLIP_W) / 4, panel_back + 7.0, center_z))
        for sx in (-1, 1)
    ]

    # The only visible front hardware: washer, hex nut, and metal lever.
    bushing = _cylinder_between(BUSHING_D / 2, (0, panel_back, center_z), (0, -5.0, center_z))
    washer = _cylinder_between(WASHER_D / 2, (0, -0.15, center_z), (0, -0.75, center_z))
    nut = _cylinder_between(7.2, (0, -0.8, center_z), (0, -3.3, center_z), sections=6)
    pivot = trimesh.creation.icosphere(subdivisions=2, radius=3.0)
    pivot.apply_translation((0, -4.2, center_z))
    lever = _cylinder_between(2.0, (0, -4.2, center_z), (0, -18.0, center_z + lever_dz), sections=48)

    # Exactly three rear blades per switch: top, bottom, and left-middle.
    terminal_y = panel_back + BODY_DEPTH + TERMINAL_DEPTH / 2
    terminals = [
        _box((3.0, TERMINAL_DEPTH, 5.0), (0, terminal_y, center_z + 9.0)),
        _box((3.0, TERMINAL_DEPTH, 5.0), (0, terminal_y, center_z - 9.0)),
        _box((3.0, TERMINAL_DEPTH, 5.0), (-5.0, terminal_y, center_z)),
    ]
    toggle = trimesh.util.concatenate([body, *clips, bushing, washer, nut, pivot, lever, *terminals])
    if rotation_deg:
        toggle.apply_transform(
            trimesh.transformations.rotation_matrix(
                np.radians(rotation_deg), [0, 1, 0], point=[0, 0, center_z]
            )
        )
    return toggle


def switch_parts():
    """Both 90-degree fit-trial references, independently toggleable."""
    return {
        "lower_toggle__connector_outside": (_toggle(17.0, lever_dz=-7.0, rotation_deg=-90),
                                             "#244b5c", 0.82, [0, 0, -34], True),
        "upper_toggle__connector_outside": (_toggle(36.75, lever_dz=7.0, rotation_deg=90),
                                             "#6a4937", 0.82, [0, 0, 34], True),
    }


def write_scene(out_dir):
    """Write hidden mock assets and scene.json next to the printable STL."""
    out_dir = Path(out_dir)
    mock = out_dir / "mock"
    if mock.exists():
        shutil.rmtree(mock)
    mock.mkdir(parents=True)

    parts = []
    for name, (mesh, color, opacity, explode, visible) in switch_parts().items():
        path = mock / f"{name}.stl"
        mesh.export(path)
        parts.append(dict(name=name, file=f"mock/{path.name}", color=color,
                          opacity=opacity, explode=explode, group="hardware",
                          visible=visible))

    # Printable file frame -> installed frame: short side across x, print depth
    # behind the dash on +y, and the 53.75 mm long side vertical on +z.
    matrix = [[0, 1, 0, 0],
              [0, 0, 1, 0],
              [1, 0, 0, 26.875],
              [0, 0, 0, 1]]
    scene = dict(mock=dict(
        label="Hardware",
        title="Scene-only lever toggles",
        auto=True,
        ground=False,
        controls=["explode"],
        parts=parts,
        adapter=dict(matrix=matrix, explode=[0, 0, 0]),
        flows=[],
        view=dict(target=[0, 6, 27], camera=[85, -175, 72]),
        isolate=[],
        ours=[],
        spec=[
            ["Reference", "scene-only; not printable"],
            ["Front", "round washer/nut with metal lever"],
            ["Rear body", "14 mm base; 15 mm at centred protrusion"],
            ["Side protrusion", "21 mm long and centred; 4 mm plain base at each end"],
            ["Terminals", "exactly 3 per switch: top, bottom, left-middle"],
            ["Orientation", "lower -90; upper +90; odd terminals face outward"],
            ["Tradeoff", "rear bodies fit vertically; lever throw becomes left/right"],
            ["Cage", "29 mm toggle edges are open; no long side walls"],
            ["Wall limits", "new walls stay inside original 27.3 mm plug width"],
            ["Wall fit", "outer faces 0.05 mm clear; centre wall flush"],
            ["Grip", "4 corner tongues per toggle; 8 total"],
            ["Spring", "tabs grip base with 1.00 mm interference closer to panel"],
            ["Flex room", "1.5 mm open pocket behind each tongue"],
            ["Retention", "washer/nut remains the primary mount"],
        ],
    ))
    (out_dir / "scene.json").write_text(json.dumps(scene), encoding="utf-8")
    return scene
