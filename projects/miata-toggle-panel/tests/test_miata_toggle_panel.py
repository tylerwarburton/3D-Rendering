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


def test_each_body_contacts_exactly_four_corner_hooks():
    finished = M.design_frame()
    for x, y in M.hole_centres():
        body = pk.move(pk.box(M.BODY_BASE_X, M.BODY_ROT_Y, M.BODY_DEPTH), x, y,
                       M.PANEL_BACK_Z - M.BODY_DEPTH - 0.1)
        overlap = pk.intersection(finished, body)
        # Flush wall faces create zero-volume coplanar surfaces; only the four
        # corner hooks may have positive-volume interference.
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message=".*divide by zero.*", category=RuntimeWarning)
            warnings.filterwarnings("ignore", message=".*invalid value.*", category=RuntimeWarning)
            contacts = [c for c in overlap.split(only_watertight=False)
                        if abs(c.volume) > 1e-4]
        assert len(contacts) == 4
        assert abs(overlap.volume) == pytest.approx(50.998, abs=0.10)


def test_fixed_walls_clear_centered_body_protrusions():
    finished = M.design_frame()
    for x, y in M.hole_centres():
        protrusion = pk.move(pk.box(M.BODY_ROT_X, M.PROTRUSION_Y, 8.0), x, y, -8.5)
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message=".*invalid value.*", category=RuntimeWarning)
            contact = abs(pk.intersection(finished, protrusion).volume)
        assert contact < 1e-6


def test_cage_is_connected_to_original_shell():
    assert M.design_frame().body_count == 1


def test_insert_adds_no_new_unsupported_area():
    source = pk.on_bed(pk.rotate(M.source_blank(), 180, (1, 0, 0)))
    # The four small ramp hooks are short enough for a 0.4 mm nozzle.
    assert pk.overhang_area(M.two_toggle_panel()) <= pk.overhang_area(source) + 12.0
