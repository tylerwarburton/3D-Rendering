"""Studio tools for any STL under out/: Blender renders, Bambu Studio slicing, GLB for AR.

    python shared/studio.py render out/<p>/.../part.stl [--turntable] [--color #hex]
    python shared/studio.py slice  out/<p>/.../part.stl
    python shared/studio.py glb    out/<p>/.../part.stl

Results are cached next to the project's outputs in out/<project>/.studio/,
keyed by the STL path and redone when the STL is newer. The configurator's
Render & print buttons call these through serve.py. Slicing uses Bambu Studio's own system profiles
(X1C 0.4, 0.20mm Standard, Bambu PLA Basic), flattened once into out/.slicer/.
"""
import json
import re
import shutil
import subprocess
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "out"
BLENDER_SCRIPT = ROOT / "shared" / "blender_render.py"
PRINTER = ("Bambu Lab X1 Carbon 0.4 nozzle", "0.20mm Standard @BBL X1C", "Bambu PLA Basic @BBL X1C")
_lock = threading.Lock()                       # one heavy job (Blender / slicer) at a time


def _find(names, globs):
    for n in names:
        if shutil.which(n):
            return shutil.which(n)
    hits = [h for g in globs for h in sorted(Path("C:/Program Files").glob(g))]
    return str(hits[-1]) if hits else None     # newest version sorts last


BLENDER = _find(["blender"], ["Blender Foundation/Blender */blender.exe"])
# Linux: the AppImage extracted to /opt/bambu-studio (AppRun next to resources/, like the .exe on Windows)
BAMBU = _find(["bambu-studio", "/opt/bambu-studio/AppRun"], ["Bambu Studio/bambu-studio.exe"])


def cached(stl, ext):
    """out/<project>/.studio/<path__to__part>.<ext>, and whether it is current."""
    stl = Path(stl).resolve()
    rel = stl.relative_to(OUT.resolve())
    f = OUT / rel.parts[0] / ".studio" / (rel.with_suffix("").as_posix().replace("/", "__") + ext)
    f.parent.mkdir(parents=True, exist_ok=True)
    return f, f.exists() and f.stat().st_mtime >= stl.stat().st_mtime


def render(stl, turntable=False, color="#c8d4dc"):
    if not BLENDER:
        raise RuntimeError("Blender not found - install it (winget install BlenderFoundation.Blender)")
    if not re.fullmatch(r"#[0-9a-fA-F]{6}", color):
        raise ValueError("color must be #rrggbb")
    f, ok = cached(stl, f"_{color[1:].lower()}" + (".mp4" if turntable else ".png"))
    if ok:
        return f
    with _lock:
        cmd = [BLENDER, "-b", "-P", str(BLENDER_SCRIPT), "--", str(stl), str(f), "--color", color]
        r = subprocess.run(cmd + (["--turntable"] if turntable else []), capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
    if r.returncode or not f.exists():
        raise RuntimeError("Blender failed:\n" + (r.stdout + r.stderr)[-1500:])
    return f


def _profiles():
    """Bambu system profiles inherit from each other; the CLI wants them flat."""
    d = OUT / ".slicer"
    files = [d / f"{k}.json" for k in ("machine", "process", "filament")]
    if all(f.exists() for f in files):
        return files
    base = Path(BAMBU).parent / "resources" / "profiles" / "BBL"
    index = {}
    for kind in ("machine", "process", "filament"):
        for j in (base / kind).rglob("*.json"):
            try:
                index[(kind, json.loads(j.read_text(encoding="utf-8")).get("name"))] = j
            except ValueError:
                pass

    def flat(kind, name):
        p = json.loads(index[(kind, name)].read_text(encoding="utf-8"))
        merged = flat(kind, p["inherits"]) if p.get("inherits") else {}
        merged.update(p)
        merged.pop("inherits", None)
        return merged

    d.mkdir(parents=True, exist_ok=True)
    for f, kind, name in zip(files, ("machine", "process", "filament"), PRINTER):
        f.write_text(json.dumps(flat(kind, name), indent=1))
    return files


def slice(stl):
    """Real print time + grams from Bambu Studio, and a .3mf ready to open/print."""
    if not BAMBU:
        raise RuntimeError("Bambu Studio not found")
    f, ok = cached(stl, ".slice.json")
    if ok:
        return json.loads(f.read_text())
    machine, process, filament = _profiles()
    work = f.with_suffix("").with_suffix(".slicing")
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir()
    with _lock:
        r = subprocess.run([BAMBU, "--debug", "1", "--slice", "0", "--arrange", "1", "--orient", "0",
                            "--outputdir", str(work), "--export-3mf", "plate.3mf",
                            "--load-settings", f"{machine};{process}", "--load-filaments", str(filament), str(stl)],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
    gcode = work / "plate_1.gcode"
    if not gcode.exists():
        raise RuntimeError("Bambu Studio failed:\n" + (r.stdout + r.stderr)[-1500:])
    head = gcode.read_text(encoding="utf-8", errors="replace")[:20000]
    grab = lambda pat: (re.search(pat, head) or [None, None])[1]
    mf = f.with_suffix("").with_suffix(".3mf")
    shutil.move(work / "plate.3mf", mf)
    shutil.rmtree(work, ignore_errors=True)
    res = {"time": grab(r"total estimated time: ([^\n;]+)"), "grams": float(grab(r"total filament weight \[g\] : ([\d.]+)")),
           "meters": round(float(grab(r"total filament length \[mm\] : ([\d.]+)")) / 1000, 2),
           "layers": int(grab(r"total layer number: (\d+)")), "printer": " / ".join(PRINTER),
           "file": "/" + mf.relative_to(OUT).as_posix()}
    f.write_text(json.dumps(res))
    return res


def glb(stl):
    """GLB copy of the STL for <model-viewer> / AR (mm -> m, z-up -> y-up)."""
    f, ok = cached(stl, ".glb")
    if not ok:
        import trimesh
        m = trimesh.load(str(stl), force="mesh")
        m.apply_scale(0.001)
        m.apply_transform(trimesh.transformations.rotation_matrix(-1.5707963, [1, 0, 0]))
        m.apply_translation([-m.bounds[:, 0].mean(), -m.bounds[0, 1], -m.bounds[:, 2].mean()])
        m.visual = trimesh.visual.ColorVisuals(m, face_colors=[200, 212, 220, 255])
        m.export(str(f))
    return f


if __name__ == "__main__":
    cmd, stl = sys.argv[1], sys.argv[2]
    if cmd == "render":
        c = sys.argv[sys.argv.index("--color") + 1] if "--color" in sys.argv else "#c8d4dc"
        print(render(stl, "--turntable" in sys.argv, c))
    elif cmd == "slice":
        print(json.dumps(slice(stl), indent=1))
    elif cmd == "glb":
        print(glb(stl))
