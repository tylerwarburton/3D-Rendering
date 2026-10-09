"""Build every fitting VARIANT, export the default STLs to out/stl/fittings/,
and pack a self-contained out/fittings_viewer.html (tools/viewer_template.html).

The viewer shows one entry per fitting FAMILY with toggles for each port
(F/M), the elbow angle and vents. Port labels are drawn on screen only -
nothing is embossed in any STL. Downloads come from exact packed geometry.

    python -m tools.fittings_viewer
"""
import base64
import zlib
import itertools
import json

import numpy as np
import trimesh
from trimesh import transformations as tf

from . import paths


UNITS = (1000.0, 10000.0)   # grids tried in turn: 1 um, then 0.1 um


def quantize(mesh):
    """Weld, then snap vertices to a 1 um grid (0.1 um if 1 um fails) - far
    below print resolution - and PROVE the result is still the same number of
    watertight bodies with the same volume; otherwise keep the mesh as it was.
    Exported STLs and the viewer both use this, so a download is identical to
    the exported file.
    Welding first is what makes 1 um work: the vented parts carry boolean
    sliver vertices < 1 um apart; snapping alone split them into broken
    edges, welding them at 1 um first (export_ready's merge) keeps the mesh
    watertight and saves ~9% of the viewer."""
    # The test must merge by POSITION, the way an STL is read. Checking by
    # vertex number passed parts that fell apart once saved (a vented u-bend
    # -> 578 pieces). Parts that fail keep their exact float geometry.
    import io
    want = len(mesh.split(only_watertight=False))
    for unit in UNITS:
        m = mesh.copy()
        m.merge_vertices(digits_vertex=int(round(np.log10(unit))))
        m.update_faces(m.nondegenerate_faces()); m.update_faces(m.unique_faces())
        m.remove_unreferenced_vertices()
        q = trimesh.Trimesh(np.round(np.asarray(m.vertices, float) * unit) / unit,
                            m.faces.copy(), process=False)
        buf = io.BytesIO(); q.export(buf, file_type='stl'); buf.seek(0)
        back = trimesh.load(buf, file_type='stl')
        parts = back.split(only_watertight=False)
        if (len(parts) == want and all(b.is_watertight for b in parts)
                and abs(back.volume - mesh.volume) <= 1e-4 * abs(mesh.volume)):
            q.metadata['um'] = True; q.metadata['unit'] = unit
            return q
    return mesh


def _encode(mesh):
    """Compact exact encoding ('q3'): integer micrometre coordinates, vertices
    sorted so neighbours sit together and stored as deltas; each triangle
    rotated so its smallest index leads (winding kept), triangles sorted, the
    lead index delta-coded and the other two stored relative to it; every
    int32 stream byte-shuffled; zlib. About a quarter smaller than raw
    float32 + uint32, lossless at 0.1 um. Meshes that failed quantize() are
    packed as exact float32 ('f32i') instead."""
    if not mesh.metadata.get('um'):
        v = np.ascontiguousarray(mesh.vertices, dtype='<f4')
        f = np.ascontiguousarray(mesh.faces, dtype='<u4')
        return dict(fmt='f32i', nv=int(len(v)), nf=int(len(f)), z=1,
                    b64=base64.b64encode(zlib.compress(v.tobytes() + f.tobytes(), 9)).decode('ascii'))
    UNIT = mesh.metadata.get('unit', 10000.0)
    Q = np.round(np.asarray(mesh.vertices, float) * UNIT).astype(np.int64)
    F = np.asarray(mesh.faces, np.int64)
    cell = Q // int(2 * UNIT)                       # 2 mm cells for the sort
    order = np.lexsort((Q[:, 2], Q[:, 1], Q[:, 0], cell[:, 2], cell[:, 1], cell[:, 0]))
    inv = np.empty_like(order); inv[order] = np.arange(len(order))
    Qs = Q[order]; Fs = inv[F]
    r = np.argmin(Fs, axis=1)
    Fs = np.stack([Fs[np.arange(len(Fs)), (r + k) % 3] for k in range(3)], axis=1)
    Fs = Fs[np.lexsort((Fs[:, 2], Fs[:, 1], Fs[:, 0]))]
    dV = np.diff(np.vstack([np.zeros((1, 3), np.int64), Qs]), axis=0).astype('<i4')
    d0 = np.diff(np.concatenate([[0], Fs[:, 0]])).astype('<i4')
    rel = (Fs[:, 1:] - Fs[:, :1]).astype('<i4')

    def shuf(a):                                   # int32 column -> 4 byte planes
        return np.ascontiguousarray(a).view(np.uint8).reshape(-1, 4).T.tobytes()
    blob = b''.join([shuf(dV[:, 0]), shuf(dV[:, 1]), shuf(dV[:, 2]),
                     shuf(d0), shuf(rel[:, 0]), shuf(rel[:, 1])])
    return dict(fmt='q3', u=int(UNIT), nv=int(len(Qs)), nf=int(len(Fs)), z=1,
                b64=base64.b64encode(zlib.compress(blob, 9)).decode('ascii'))


def _pack(mesh, group, note, meta, **extra):
    """Exact geometry: float32 vertices + uint32 faces (the same precision as
    a binary STL), so downloads from the viewer are identical to the exported
    files. Do NOT quantise: these meshes have distinct vertices < 1e-6 mm
    apart, and rounding merges them and breaks watertightness."""
    d = dict(group=group, note=note, meta=meta,
             dims=[round(float(x), 1) for x in mesh.extents],
             tris=int(len(mesh.faces)), vol=round(float(mesh.volume) / 1000, 1))
    d.update(_encode(mesh))
    d.update(extra)
    return d


def _sub(mesh):
    """One sub-mesh of a multi-part entry (same packing)."""
    return _encode(mesh)


_SUB_SEEN = {}


def _pack_multi(meshes, group, note, meta, pid=None, **extra):
    """Several bodies kept separate so the viewer can move them (slide gate). The
    download concatenates them - the same bodies, the same STL.
    With pid: a body identical to one already packed is stored as a
    reference {ref: [part id, index]} (variants that share bodies) - the
    page resolves refs on load."""
    import hashlib
    allm = trimesh.util.concatenate(meshes)
    sub = []
    for i, m in enumerate(meshes):
        enc = _sub(m)
        h = hashlib.sha1(enc['b64'].encode()).hexdigest()
        if pid and h in _SUB_SEEN:
            sub.append({'ref': list(_SUB_SEEN[h])})
        else:
            sub.append(enc)
            if pid:
                _SUB_SEEN[h] = (pid, i)
    d = dict(group=group, note=note, meta=meta, fmt='q3', sub=sub,
             dims=[round(float(x), 1) for x in allm.extents],
             tris=int(len(allm.faces)), vol=round(float(allm.volume) / 1000, 1))
    d.update(extra)
    return d


def _twin(F, fam, cfg):
    """A variant that is another one TURNED AROUND (same part, ports swapped):
    -> (source genders, 4x4 rotation, perm) or None. perm[i] = the port of
    this variant that the source's port i lands on. Every one of these is a
    proper rotation (det +1, never a mirror image), so latch slots and lugs
    keep their handedness; each was checked to land every port exactly on its
    twin's port. The viewer stores the source once and draws/exports the twin
    through the transform (~10 MB saved)."""
    import trimesh.transformations as tf
    g = cfg['g']
    if fam in ('elbow', 'coupler', 'u_bend', 'vent_tube') and g == 'MF':
        src, perm = 'FM', [1, 0]
        if fam in ('coupler', 'vent_tube'):
            L = 2 * F.LEG_LENGTH if fam == 'coupler' else F.VENT_TUBE_L
            T = tf.translation_matrix((0, 0, L)) @ tf.rotation_matrix(np.pi, (1, 0, 0))
        elif fam == 'elbow':
            th = np.radians(cfg.get('angle', F.ELBOW_ANGLE))
            T = tf.rotation_matrix(np.pi, (np.cos(th / 2), 0, np.sin(th / 2)))
        else:
            T = tf.rotation_matrix(np.pi, (0, 0, 1))
        return src, T, perm
    if fam == 'tee' and g[0] == 'M' and g[1] == 'F':
        return g[1] + g[0] + g[2], tf.rotation_matrix(np.pi, (0, 0, 1)), [1, 0, 2]
    if fam == 'y_fitting' and g[1] == 'M' and g[2] == 'F':
        return g[0] + g[2] + g[1], tf.rotation_matrix(np.pi, (0, 0, 1)), [0, 2, 1]
    return None


def _combos(n):
    return [''.join(c) for c in itertools.product('FM', repeat=n)]


def _file_name(fam, names, g, angle=None, vent=''):
    s = fam
    if angle is not None:
        s += f"_{angle:g}deg"
    if g:
        s += "_" + "_".join(f"{n}-{x}" for n, x in zip(names, g))
    if vent:
        s += f"_vent-{vent}"
    return s + ".stl"


def variants(F, mode='main'):
    """(family, cfg) for every combination the viewer offers. cfg['vent'] is
    '' (off) or a vent style name.
    mode 'site' (default): everything, vents at EVERY elbow angle - the
    hosted viewer (page + data chunks, no size ceiling). mode 'main': the
    single-file viewer, elbow vents on 90 deg only (it must stay under the
    ~31 MB a file can be sent at). mode 'elbows': elbow family only."""
    out = []
    styles = list(F.VENT_STYLES)
    for a in F.ELBOW_ANGLES:
        for g in _combos(2):
            out.append(('elbow', dict(g=g, angle=a, vent='')))
            if True:                      # vents at every angle (twins + 1 um keep it under the limit)
                out += [('elbow', dict(g=g, angle=a, vent=st)) for st in styles]
    if mode == 'elbows':
        return out
    for g in _combos(2):
        for v in [''] + styles:
            out.append(('coupler', dict(g=g, vent=v)))
            out.append(('u_bend', dict(g=g, vent=v)))
        out += [('vent_tube', dict(g=g, vent=st)) for st in styles]
        out.append(('slide_gate', dict(g=g)))
    for g in _combos(3):
        for v in [''] + styles:
            out.append(('tee', dict(g=g, vent=v)))
            out.append(('y_fitting', dict(g=g, vent=v)))
    for g in _combos(1):
        for gate in ('', 'slide'):
            out.append(('flange', dict(g=g, gate=gate)))
        out.append(('cap', dict(g=g)))
    return out


NOTES = {
    'slide_gate': 'Knife gate: the slide lives in the arm. Push the knob in to close, pull out to open - '
                  'it clicks at both ends and can\'t fall out (paperclip in the side hole releases it). '
                  'Two prints: gate body (stands on port A) and slide (flat, knob up).',
    'elbow': 'Elbow - pick the angle. A sits on the bed, B is the turned leg.',
    'coupler': 'Straight coupler.',
    'vent_tube': 'Straight vented section: airflow and a look inside.',
    'u_bend': '180 degree return.',
    'tee': 'Tee: A-B is the run, C the branch.',
    'y_fitting': 'Wye: trunk T, branches L and R at 45 degrees.',
    'flange': 'Tank wall port, 4 M6 bolts through any wall (thicker wall = longer bolts). '
              '94 x 94 plates, same 4 holes on both. Gate: blade 25 mm in, one-piece body; bolt heads outside, '
              'washer + nut on the flat back plate under the skirt (M6 x 16 + wall).',
    'cap': 'End cap. Male (M) closes a female port; female (F) closes a male port. '
           'Push on, twist to lock. Prints closed end down, no supports.',
}


def run(mode='site'):
    import fittings as F
    out = paths.STL / "fittings"
    out.mkdir(parents=True, exist_ok=True)
    meta = {'Socket': f"{F.SOCKET_ID:.2f} ID x {F.SOCKET_DEPTH:.0f} deep",
            'Bore': f"{F.BORE_ID:.2f} mm",
            'Latch': f"{F.LATCH_COUNT} lugs, {F.LATCH_ROT_DEG:.0f} deg twist, detent",
            'Ports': "F = socket + collar, M = built-in male end"}
    parts, built, defaults = {}, {}, {}

    def bed(m, labels=None):
        dz = round(-m.bounds[0][2], 4)                # on the 0.1 um grid
        um, unit = m.metadata.get('um'), m.metadata.get('unit', 10000.0)
        dz = round(dz * unit) / unit                  # on the mesh's grid
        m = m.copy(); m.apply_translation((0, 0, dz))
        if um:
            m.vertices = np.round(np.asarray(m.vertices) * unit) / unit
            m.metadata['um'] = True; m.metadata['unit'] = unit
        if labels:
            labels = [dict(l, pos=[l['pos'][0], l['pos'][1], round(l['pos'][2] + dz, 2)])
                      for l in labels]
        m.metadata['dz'] = dz
        return m, labels

    kept = {}                    # vid -> (bedded mesh, labels): sources for twins

    # --- families with toggles ---------------------------------------------
    for fam, cfg in variants(F, mode):
        kw = {}
        if 'angle' in cfg:
            kw['angle'] = cfg['angle']
        if 'vent' in cfg:
            kw['vent'] = bool(cfg['vent'])
            if cfg['vent']:
                kw['style'] = cfg['vent']
        if fam == 'slide_gate':
            # body + blade (packed OPEN) as separate bodies so the viewer can
            # slide the blade; downloads give the BODY only (dl=[0]) - the
            # blade is its own print (gate_blade.stl)
            bodies = [quantize(F.export_ready(F.make_slide_gate(cfg['g']))),
                      quantize(F.export_ready(F.gate_blade(0.0)))]
            labels = F.port_labels(F.gate_ports(), cfg['g'], F.PORT_NAMES[fam])
            d = F._gate_dims(); t = np.radians(F.GATE_TILT)
            anim = dict(kind='slide', rot=1.0, mover=1,
                        vec=[0.0, round(-d['T'] * np.cos(t), 4), round(-d['T'] * np.sin(t), 4)])
            names = F.PORT_NAMES[fam]
            fname = _file_name(fam, names, cfg['g'])
            parts[fname[:-4]] = _pack_multi(bodies, 'Fittings', NOTES[fam], meta, pid=fname[:-4], family=fam,
                                            cfg=cfg, ports=labels, file=fname, anim=anim, dl=[0],
                                            dl_parts=[['Gate body', '.'], ['Slide (blade)', 'gate_blade']])
            bodies[0].export(out / fname)
            if cfg['g'] == F.PORT_GENDER[fam]:
                defaults[fam] = fname[:-4]
                print(f"  {fname:34s} (default, exported: body; blade = gate_blade.stl)")
            continue
        if fam == 'flange':
            gate = bool(cfg.get('gate'))
            names = F.PORT_NAMES[fam]
            fname = _file_name(fam, names, cfg['g'])
            if gate:
                fname = fname[:-4] + "_gate.stl"
            vid = fname[:-4]
            pieces = F.flange_set(cfg['g'], gate, beta=0.0)          # gate packed OPEN
            bodies = [quantize(F.export_ready(m)) for _, m in pieces]
            dz = float(-min(b.bounds[0][2] for b in bodies))          # whole mm: stays on grid
            for b in bodies:
                b.apply_translation((0, 0, dz))
            labels = F.flange_labels(cfg['g'], gate)
            labels = [dict(l, pos=[l['pos'][0], l['pos'][1], round(l['pos'][2] + dz, 2)]) for l in labels]
            nice = {'flange': 'Flange', 'back_plate': 'Back plate', 'outer': 'Outer plate',
                    'body': 'Gate body', 'blade': 'Gate blade'}
            extra = dict(dl_parts=[[nice[n], '.', [i]] for i, (n, _) in enumerate(pieces)])
            if gate:
                extra['anim'] = dict(kind='slide', rot=1.0, mover=2, el=0.35,
                                     vec=[0.0, -float(F.GN_TRAVEL), 0.0])
            parts[vid] = _pack_multi(bodies, 'Fittings', NOTES[fam], meta, pid=vid, family=fam,
                                     cfg=cfg, ports=labels, file=fname, **extra)
            if cfg['g'] == F.PORT_GENDER[fam] and not gate:
                defaults[fam] = vid
                b0 = bodies[0].copy(); b0.apply_translation((0, 0, -b0.bounds[0][2]))
                b0.export(out / fname)
                print(f"  {fname:34s} (default, exported: flange body)")
            continue
        names = F.PORT_NAMES[fam]
        fname = _file_name(fam, names, cfg['g'], cfg.get('angle'), cfg.get('vent', ''))
        vid = fname[:-4]
        tw = _twin(F, fam, cfg)
        if tw:
            src_g, T, perm = tw
            svid = _file_name(fam, names, src_g, cfg.get('angle'), cfg.get('vent', ''))[:-4]
            sm, slabels = kept[svid]
            M = T @ trimesh.transformations.translation_matrix((0, 0, -sm.metadata['dz']))
            V = trimesh.transform_points(np.asarray(sm.vertices), M)
            X = trimesh.transformations.translation_matrix((0, 0, -V[:, 2].min())) @ M
            V[:, 2] -= V[:, 2].min()
            labels = [None] * len(slabels)
            for i, l in enumerate(slabels):
                pos = trimesh.transform_points(np.array([l['pos']], float), X)[0]
                labels[perm[i]] = dict(l, label=names[perm[i]], pos=[round(float(x), 2) for x in pos])
            parts[vid] = dict(group='Fittings', note=NOTES[fam], meta=meta, family=fam, cfg=cfg,
                              ports=labels, file=fname, fmt='q3', src=svid,
                              xf=[round(float(x), 10) for x in X[:3, :].ravel()],
                              dims=[round(float(x), 1) for x in V.max(0) - V.min(0)],
                              tris=parts[svid]['tris'], vol=parts[svid]['vol'])
            continue
        m, labels = F.FITTINGS[fam](cfg['g'], labels=True, **kw)
        m = quantize(F.export_ready(m))
        m, labels = bed(m, labels)
        if fam in ('elbow', 'coupler', 'u_bend', 'vent_tube', 'tee', 'y_fitting'):
            kept[vid] = (m, labels)
        parts[vid] = _pack(m, 'Fittings', NOTES[fam], meta, family=fam, cfg=cfg,
                           ports=labels, file=fname)
        default_g = F.PORT_GENDER[fam]
        dv = (F.VENT_STYLE if F.VENT.get(fam, False) else '') if 'vent' in cfg else ''
        is_default = (cfg['g'] == default_g
                      and cfg.get('angle', 90.0) == F.ELBOW_ANGLE
                      and cfg.get('vent', '') == dv)
        if is_default:
            defaults[fam] = vid
            m.export(out / fname)
            built[fam] = m
            print(f"  {fname:34s} {m.volume/1000:6.1f} cm3  (default, exported)")
    print(f"  + {len(parts)} variants packed")
    if mode == 'elbows':
        return _write(parts, defaults, "elbows_viewer.html")

    # --- single parts --------------------------------------------------------
    singles = ['gate_blade', 'latch_coupon', 'pipe_hook']
    for name in singles:
        fn = F.FITTINGS[name]
        m, labels = fn(), None
        m = quantize(F.export_ready(m))
        m, labels = bed(m, labels)
        built[name] = m
        m.export(out / f"{name}.stl")
        note = (fn.__doc__ or name).strip().splitlines()[0]
        parts[name] = _pack(m, 'Fittings', note, meta, ports=labels, file=f"{name}.stl")
        print(f"  {name + '.stl':34s} {m.volume/1000:6.1f} cm3")

    # --- shim: two bodies (shim + pull-off print ring), standing on a plug tip
    sb = [quantize(F.export_ready(b)) for b in F.make_shim_print()]
    z0 = min(b.bounds[0][2] for b in sb)
    for b in sb: b.apply_translation((0, 0, -z0))
    built['shim'] = sb[0]
    trimesh.util.concatenate(sb).export(out / "shim.stl")
    parts['shim'] = _pack_multi(sb, 'Fittings',
        'Shim: two cap-style male ends back to back, one grip ring each. Prints standing on a '
        'plug tip; the thin ring under the upper skirt is a print support - pull it off.',
        meta, file='shim.stl')
    print("  shim.stl  (shim + print ring)")

    # --- male fit coupons: three separate rings, one STL -------------------
    rings = [quantize(F.export_ready(c)) for c in F.make_male_fit_coupons()]
    trimesh.util.concatenate(rings).export(out / "male_fit_coupons.stl")
    parts['male_fit_coupons'] = _pack_multi(rings, 'Fittings',
        'Fit test for male ends: +0.00 / +0.15 / +0.30 mm (1, 2, 3 notches). Print band down; '
        'set MALE_FIT_EXTRA to the ring that fits like the cap.', meta, file='male_fit_coupons.stl')
    print("  male_fit_coupons.stl  (3 rings)")

    # --- assemblies (preview only) -------------------------------------------
    rot = tf.rotation_matrix(np.radians(F.LATCH_ROT_DEG), (0, 0, 1))
    unrot = tf.rotation_matrix(-np.radians(F.LATCH_ROT_DEG), (0, 0, 1))
    cap = F.make_cap()
    c1 = cap.copy(); c1.apply_transform(rot)
    parts['asm_cap_on_coupler'] = _pack(trimesh.util.concatenate([F.make_coupler(), c1]),
        'Assemblies', 'Cap locked on a coupler port (preview only).', meta)
    # tee with a male branch plugged straight into an elbow (no shim)
    tee = F.make_tee('FFM')
    (p, d) = F.port_list('tee')[2]
    el = F.make_elbow('FF')
    el.apply_transform(np.linalg.inv(F.port_frame(*F.port_list('elbow')[0])))
    el.apply_transform(unrot)
    el.apply_transform(F.port_frame(p, d) @ F.shim_side_frame())
    parts['asm_tee_male_into_elbow'] = _pack(trimesh.util.concatenate([tee, el]),
        'Assemblies', 'Tee with a male branch plugged straight into an elbow - no shim.', meta)

    # one build -> both: the single-file viewer (send/open locally) and the
    # hosted copy (page + data chunks); _write_site strips the geometry out
    # of `parts`, so the single file is written from a copy first
    import copy
    single = _write(copy.deepcopy(parts), defaults, "fittings_viewer.html")
    if single.stat().st_size > 31.0e6:
        print(f"  !! {single.name} is {single.stat().st_size/1e6:.2f} MB - over the ~31 MB send limit")
    return _write_site(parts, defaults)


CHUNK_MAX = 9.0e6        # bytes of geometry text per data file (host limit 16 MB)


def _site_page(js):
    """Write out/site/index.html from the template + the part index (js)."""
    import re
    tpl = (paths.TOOLS / "viewer_template.html").read_text()
    # the host wraps the page in its own doctype/html/head/body + charset and
    # viewport metas: strip ours, keep the title, fonts, style and scripts
    for pat in (r'<!DOCTYPE html>\s*', r'<html[^>]*>\s*', r'<head>\s*', r'</head>\s*',
                r'<body>\s*', r'</body>\s*', r'</html>\s*',
                r'<meta charset="utf-8">\s*', r'<meta name="viewport"[^>]*>\s*'):
        tpl = re.sub(pat, '', tpl)
    tpl = re.sub(r'<title>.*?</title>', '<title>Enclosure Hardware</title>', tpl)
    page = paths.OUT / "site" / "index.html"
    page.write_text(tpl.replace('/*DATA*/', js))
    return page


def site_page_only():
    """Template changed, geometry didn't: re-wrap the existing part index."""
    page = paths.OUT / "site" / "index.html"
    s = page.read_text()
    i = s.index("const PARTS = "); j = s.index("\n", s.index("const DEFAULTS = ", i)) + 1
    return _site_page(s[i:j])


def _write_site(parts, defaults):
    """Hosted viewer: out/site/index.html (the page + a small index of every
    part) and out/site/data/chunk_N.json (the geometry, by family, so a part's
    file is fetched only when it is first shown). The page is published as an
    Artifact with the chunks as its supporting files."""
    import shutil
    site = paths.OUT / "site"
    if site.exists():
        shutil.rmtree(site)
    (site / "data").mkdir(parents=True)
    # order parts so a family stays together
    order = sorted(parts, key=lambda k: (parts[k].get('family', k), k))
    chunks, cur, size, k = [], {}, 0, 0

    def put(key, obj):
        nonlocal cur, size, k
        b = obj.pop('b64')
        if size and size + len(b) > CHUNK_MAX:
            chunks.append(cur); cur, size, k = {}, 0, k + 1
        cur[key] = b; size += len(b)
        obj['ck'] = k; obj['key'] = key

    for pid in order:
        p = parts[pid]
        if 'b64' in p:
            put(pid, p)
        for i, q in enumerate(p.get('sub', [])):
            if 'b64' in q:
                put(f"{pid}#{i}", q)
    if cur:
        chunks.append(cur)
    for i, c in enumerate(chunks):
        (site / "data" / f"chunk_{i}.json").write_text(json.dumps(c, separators=(',', ':')))
    js = (f"const PARTS = {json.dumps(parts, separators=(',', ':'))};\nconst WATER = [];\n"
          f"const DEFAULTS = {json.dumps(defaults)};\n")
    page = _site_page(js)
    tot = sum((site / "data" / f"chunk_{i}.json").stat().st_size for i in range(len(chunks)))
    print(f"  {paths.rel(page)}  {page.stat().st_size/1e6:.2f} MB page + {len(chunks)} chunks "
          f"({tot/1e6:.1f} MB), {len(parts)} entries")
    return page


def _write(parts, defaults, name):
    tpl = (paths.TOOLS / "viewer_template.html").read_text()
    js = (f"const PARTS = {json.dumps(parts)};\nconst WATER = [];\n"
          f"const DEFAULTS = {json.dumps(defaults)};\n")
    html = paths.OUT / name
    html.write_text(tpl.replace('/*DATA*/', js))
    print(f"  {paths.rel(html)}  {html.stat().st_size/1e6:.2f} MB, {len(parts)} entries")
    return html


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'page':
        print(site_page_only())
    else:
        run(sys.argv[1] if len(sys.argv) > 1 else 'site')
