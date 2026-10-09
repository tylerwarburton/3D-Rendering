"""Every part: exports watertight, fits the bed, prints without supports."""
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(HERE), str(HERE.parents[1])]

from shared import printkit as pk   # noqa: E402
import __SLUG__ as M                 # noqa: E402


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
