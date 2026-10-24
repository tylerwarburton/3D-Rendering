"""Every part: exports watertight, fits the bed, prints without supports."""
import sys
import warnings
from pathlib import Path

import numpy as np
import pytest

HERE = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(HERE), str(HERE.parents[1])]

from shared import printkit as pk   # noqa: E402
import miata_toggle_panel as M                 # noqa: E402


@pytest.fixture(scope="module", params=list(M.PARTS))
def part(request):
    return request.param, M.PARTS[request.param]()


def test_watertight_export(part, tmp_path):
    name, m = part
    pk.export(m, tmp_path / f"{name}.stl")


def test_fits_bed(part):
    name, m = part
    assert pk.report(m)["fits_bed"], (name, m.extents)


def test_no_supports_needed(part):
    name, m = part
    ok = M.OVERHANG_OK.get(name, 1.0)
    if ok is not None:
        assert pk.overhang_area(pk.on_bed(m)) <= ok, name


def test_preserves_downloaded_bezel_front_footprint():
    source = M.source_blank()
    finished = M.design_frame()
    assert np.allclose(finished.bounds[:, :2], source.bounds[:, :2])
    assert finished.bounds[1, 2] == pytest.approx(source.bounds[1, 2])
    assert finished.bounds[0, 2] == pytest.approx(M.PLUG_BACK_Z)


def test_two_washers_fit_without_overlap():
    washer_d = 18.0
    centres = M.hole_centres()
    assert centres[1][0] - centres[0][0] >= washer_d
    left = M.BEZEL_CX - M.OPENING_X / 2
    right = M.BEZEL_CX + M.OPENING_X / 2
    assert centres[0][0] - washer_d / 2 >= left
    assert centres[1][0] + washer_d / 2 <= right


@pytest.mark.filterwarnings("ignore:invalid value encountered in divide:RuntimeWarning")
def test_switch_bodies_clear_continuous_walls():
    finished = M.design_frame()
    for x, y in M.hole_centres():
        body = pk.move(pk.box(M.BODY_BASE_X, M.BODY_ROT_Y, M.BODY_DEPTH), x, y,
                       M.PANEL_BACK_Z - M.BODY_DEPTH - 0.1)
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message=".*divide by zero.*", category=RuntimeWarning)
            warnings.filterwarnings("ignore", message=".*invalid value.*", category=RuntimeWarning)
            seated = pk.intersection(finished, body)
            backing_out = pk.move(body, z=-0.4)
            overlap = pk.intersection(finished, backing_out)
        assert abs(seated.volume) < 1e-6
        assert abs(overlap.volume) < 1e-6


def test_fixed_walls_clear_centered_body_protrusions():
    finished = M.design_frame()
    for x, y in M.hole_centres():
        protrusion = pk.move(pk.box(M.BODY_ROT_X, M.PROTRUSION_Y, 8.0), x, y, -8.5)
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message=".*divide by zero.*", category=RuntimeWarning)
            warnings.filterwarnings("ignore", message=".*invalid value.*", category=RuntimeWarning)
            contact = abs(pk.intersection(finished, protrusion).volume)
        assert contact < 1e-6


def test_front_shoulder_has_three_mm_clearance_zone():
    finished = M.design_frame()
    for x, y in M.hole_centres():
        shoulder = pk.move(
            pk.box(M.FRONT_SHOULDER_X, M.BODY_ROT_Y, M.FRONT_SHOULDER_DEPTH),
            x, y, M.BODY_FRONT_Z - M.FRONT_SHOULDER_DEPTH,
        )
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=RuntimeWarning)
            contact = abs(pk.intersection(finished, shoulder).volume)
        assert contact < 1e-6


def test_single_center_wall_exactly_fills_gap_between_channels():
    wall = M._center_wall()
    lower_channel_edge = M.hole_centres()[0][0] + M.CHANNEL_X / 2
    upper_channel_edge = M.hole_centres()[1][0] - M.CHANNEL_X / 2
    assert wall.bounds[:, 0] == pytest.approx(
        [lower_channel_edge, upper_channel_edge]
    )
    assert wall.extents[0] == pytest.approx(M.CENTER_WALL_T)
    assert wall.bounds[:, 1] == pytest.approx([0.0, 27.3])
    assert wall.bounds[:, 2] == pytest.approx(
        [M.PLUG_BACK_Z, M.CENTER_WALL_FRONT_Z]
    )


def test_center_wall_has_shoulder_clearance_and_joins_panel():
    wall = M._center_wall()
    lower_shoulder_edge = M.hole_centres()[0][0] + M.FRONT_SHOULDER_X / 2
    upper_shoulder_edge = M.hole_centres()[1][0] - M.FRONT_SHOULDER_X / 2
    assert wall.bounds[0, 0] - lower_shoulder_edge == pytest.approx(M.BODY_CLEAR)
    assert upper_shoulder_edge - wall.bounds[1, 0] == pytest.approx(M.BODY_CLEAR)
    assert M.CENTER_WALL_FRONT_Z > M.PANEL_BACK_Z


def test_original_outer_indents_are_filled_flush_to_channel_planes():
    finished = M.design_frame()
    fillers = M._flush_outer_indents()
    expected_planes = (
        M.hole_centres()[0][0] - M.CHANNEL_X / 2,
        M.hole_centres()[1][0] + M.CHANNEL_X / 2,
    )
    assert fillers[0].bounds[1, 0] == pytest.approx(expected_planes[0])
    assert fillers[1].bounds[0, 0] == pytest.approx(expected_planes[1])
    for filler in fillers:
        lo, hi = filler.bounds
        assert 27.0 < filler.extents[1] < 27.3
        raw_volume = filler.extents[0] * 27.3 * filler.extents[2]
        assert filler.volume < raw_volume
        assert filler.bounds[:, 2] == pytest.approx(
            [M.PLUG_BACK_Z, M.PANEL_BACK_Z]
        )
        probe = pk.move(
            pk.box(hi[0] - lo[0], 1.0, hi[2] - lo[2]),
            (lo[0] + hi[0]) / 2,
            M.BEZEL_CY,
            lo[2],
        )
        assert abs(pk.intersection(finished, probe).volume) == pytest.approx(
            (hi[0] - lo[0]) * (hi[2] - lo[2]), abs=1e-4
        )


def test_minimal_insert_is_one_connected_body():
    assert M.design_frame().body_count == 1


def test_channel_walls_end_flush_with_toggle_mount_backs():
    for channel in M._rear_channels():
        assert channel.bounds[1, 2] == pytest.approx(M.PANEL_BACK_Z)


def test_insert_adds_no_new_unsupported_area():
    source = pk.on_bed(pk.rotate(M.source_blank(), 180, (1, 0, 0)))
    assert pk.overhang_area(M.two_toggle_panel()) <= pk.overhang_area(source) + 12.0
