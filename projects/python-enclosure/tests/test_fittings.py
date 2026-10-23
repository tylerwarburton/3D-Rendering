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


def test_cap_no_plug(F):
    """Plug off: bottle-cap style - lighter, nothing inside the socket mouth."""
    full, bare = F.make_cap("M"), F.make_cap("M", plug=False)
    assert F.export_ready(bare).is_watertight
    assert bare.volume < full.volume
    assert bare.bounds[1][2] <= F.SKIRT_L + 1e-6      # only the skirt reaches into the port


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
    # blade: only the spring bumps touch. At both ends they sit in the notch
    # V (none / small overlap); mid-travel they ride the walls (big),
    # so it snaps into each end and stays put
    mid = _vol(F.intersection(F.gn_blade(0.5), P["body"]))
    assert 0.5 < mid < 40, mid
    for beta in (0.0, 1.0):
        end = _vol(F.intersection(F.gn_blade(beta), P["body"]))
        assert end < mid / 4, (beta, end)


def test_gate_blade_finger(F):
    import shapely.geometry as sg
    b = F._gn_blade_2d()
    tip = max(x for x, y in b.exterior.coords if abs(y - F.GN_DET_Y) < 4)
    assert tip > F.GN_A + F.GN_CLR + F.GATE_NOTCH_D - 0.05   # fills the notch: no rattle
    assert F.GN_FINGER[2] > tip - F.GN_A - F.GN_CLR          # finger never bottoms out
    assert b.contains(sg.Point(0, 0).buffer(F.BORE_R + 0.3, 128))   # still seals the bore


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
    # (each latch run's roof: a SLOT_DEPTH-deep ledge, one per slot)
    n, c, A = e.face_normals, e.triangles_center, e.area_faces
    z_roof = F.gn_levels()["top"] - F.gn_levels()["wall1"]
    flat = (n[:, 2] < -0.75) & (c[:, 2] > 0.5) & (np.abs(c[:, 2] - z_roof) > 0.5)
    runs = F.SLOT_COUNT * np.radians(F.LATCH_ROT_DEG) * F.COLLAR_R * F.SLOT_DEPTH
    assert A[flat].sum() < runs + 50, A[flat].sum()


@pytest.mark.parametrize("piece", ["outer", "blade"])
def test_gate_flat_pieces_print_clean(F, piece):
    m = dict(F.flange_set("F", True, 1.0))[piece]
    e = F.export_ready(m)
    e.apply_translation((0, 0, -e.bounds[0][2]))
    over, islands = L.run_print_audit(e, label=piece)
    assert over < 1 and not islands


# ---------------------------------------------------------------- gate coupler
@pytest.mark.parametrize("g", ["FF", "MF"])
def test_gate_coupler(F, g):
    m = F.gate_coupler(g)
    e = F.export_ready(m)
    assert e.is_watertight and e.volume > 0
    # same blade as the flange: clicks in at both ends, rides the walls between
    mid = _vol(F.intersection(F.gn_blade(0.5), m))
    assert 0.5 < mid < 40, mid
    for beta in (0.0, 1.0):
        assert _vol(F.intersection(F.gn_blade(beta), m)) < mid / 4, beta


def test_gate_coupler_prints_without_supports(F):
    e = F.export_ready(F.gate_coupler("FF"))
    z0 = e.bounds[0][2]
    e.apply_translation((0, 0, -z0))
    over, islands = L.run_print_audit(e, label="gate coupler")
    assert not islands
    # steep down-faces only at: the bed, the slot roof bridge, the two
    # collars' latch runs and the socket floor ledge (same as a plain coupler)
    n, c, A = e.face_normals, e.triangles_center, e.area_faces
    roof = F.gn_levels()["top"] - z0
    socket_floor = F.SOCKET_DEPTH
    steep = (n[:, 2] < -0.7072) & (c[:, 2] > 0.5) & (np.abs(c[:, 2] - roof) > 0.5)
    skirt = steep & (c[:, 2] > socket_floor + 1) & (c[:, 2] < roof - 0.5)
    assert A[skirt].sum() < 1.0, A[skirt].sum()


# ---------------------------------------------------------------- sizes
SIZED = [("coupler", "FF", {}), ("coupler", "MF", {}), ("elbow", "FF", dict(angle=22.5)),
         ("elbow", "FM", dict(angle=90.0)), ("tee", "FFF", {}), ("tee", "MFM", {}),
         ("y_fitting", "FFF", {}), ("y_fitting", "FMM", {})]


@pytest.mark.parametrize("size", ["min", "long"])
@pytest.mark.parametrize("fam,g,kw", SIZED)
def test_sizes_watertight(F, fam, g, kw, size):
    e = F.export_ready(F.FITTINGS[fam](g, size=size, **kw))
    assert e.is_watertight and e.volume > 0


def test_min_coupler_male_male_is_the_shim(F):
    a, b = F.make_coupler("MM", size="min"), F.make_shim()
    assert abs(a.volume - b.volume) < 1e-6


@pytest.mark.parametrize("fam,g,kw", [f for f in SIZED if "M" not in f[1]])
def test_min_tubes_and_caps_fit(F, fam, g, kw):
    """At min size a real tube sits in every socket without touching the
    tube in the next socket, and a cap locks on every port without hitting
    the fitting."""
    import trimesh.transformations as tf
    m = F.FITTINGS[fam](g, size="min", **kw)
    ports = F.port_list(fam, size="min", genders=g, **kw)
    tubes = []
    for p, d in ports:
        p, d = np.asarray(p, float), np.asarray(d, float)
        tubes.append(F.cylinder_between(p + d * 0.5, p + d * (F.SOCKET_DEPTH - 0.1), F.PIPE_OD / 2))
        cap = F.make_cap("M")
        cap.apply_transform(tf.rotation_matrix(np.radians(F.LATCH_ROT_DEG), (0, 0, 1)))
        cap.apply_transform(F.port_frame(p, d))
        assert _vol(F.intersection(cap, m)) < 0.5
    for i in range(len(tubes)):
        assert _vol(F.intersection(tubes[i], m)) < 0.5
        for j in range(i):
            assert _vol(F.intersection(tubes[i], tubes[j])) == 0.0, (i, j)
