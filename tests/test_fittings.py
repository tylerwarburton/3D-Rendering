"""Geometry checks for the tube fittings. Run: pytest -q  (about 20 s).

Every probe derives from fittings.py parameters - never hard-code a number
that the design could change.
"""
import numpy as np
import pytest

from tools import latch_check as L


def _vol(m):
    return float(m.volume) if len(m.faces) else 0.0


# ---------------------------------------------------------------- latches
def test_cap_latch_on_coupler(F):
    ok, res, _ = L.run(F, verbose=False)
    assert ok, res


def test_male_ports_latch(F):
    assert L.run_male(F)


# ---------------------------------------------------------------- every family exports
@pytest.mark.parametrize("fam,g,kw", [
    ("elbow", "FF", dict(angle=90.0)), ("elbow", "FM", dict(angle=45.0)),
    ("coupler", "FF", {}), ("tee", "FFF", {}), ("y_fitting", "FFF", {}),
    ("u_bend", "FF", {}), ("flange", "F", {}), ("flange", "M", {}),
])
def test_fitting_watertight(F, fam, g, kw):
    m = F.FITTINGS[fam](g, **kw)
    e = F.export_ready(m)
    assert e.is_watertight and e.volume > 0


@pytest.mark.parametrize("g", ["M", "F"])
def test_cap_watertight(F, g):
    assert F.export_ready(F.make_cap(g)).is_watertight


# ---------------------------------------------------------------- gate flange
@pytest.fixture(scope="module", params=["F", "M"])
def gate_set(F, request):
    return request.param, dict(F.flange_set(request.param, True, 1.0))


def test_gate_flange_pieces(F, gate_set):
    g, P = gate_set
    assert set(P) == {"outer", "body", "blade"}
    for n, m in P.items():
        e = F.export_ready(m)
        assert e.is_watertight and e.volume > 0, n


def test_gate_flange_no_collisions(F, gate_set):
    g, P = gate_set
    assert _vol(F.intersection(P["outer"], P["body"])) < 0.01
    # blade: free at both ends (bumps sit in the notches), only the spring
    # bumps touch mid-travel
    for beta in (0.0, 1.0):
        assert _vol(F.intersection(F.gn_blade(beta), P["body"])) < 0.01, beta
    mid = _vol(F.intersection(F.gn_blade(0.5), P["body"]))
    assert 0.5 < mid < 20, mid


def test_gate_blade_open_and_closed(F):
    lo_open = F.gn_blade(0.0).bounds[0][1]
    lo_closed = F.gn_blade(1.0).bounds[0][1]
    assert lo_open > F.BORE_R + 1.0           # open: clear of the bore
    assert lo_closed < -F.BORE_R - 3.0        # closed: covers it with margin


def test_gate_body_prints_without_supports(F):
    e = F.export_ready(F.gn_body("F"))
    e.apply_translation((0, 0, -e.bounds[0][2]))
    over, islands = L.run_print_audit(e, label="gate body")
    assert not islands
    # the only flat overhang allowed is the slot roof bridge + female collar
    n, c, A = e.face_normals, e.triangles_center, e.area_faces
    z_roof = F.gn_levels()["top"] - F.gn_levels()["wall1"]
    flat = (n[:, 2] < -0.75) & (c[:, 2] > 0.5) & (np.abs(c[:, 2] - z_roof) > 0.5)
    assert A[flat].sum() < 150, A[flat].sum()


@pytest.mark.parametrize("piece", ["outer", "blade"])
def test_gate_flat_pieces_print_clean(F, piece):
    m = dict(F.flange_set("F", True, 1.0))[piece]
    e = F.export_ready(m)
    e.apply_translation((0, 0, -e.bounds[0][2]))
    over, islands = L.run_print_audit(e, label=piece)
    assert over < 1 and not islands
