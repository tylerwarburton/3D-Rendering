#!/usr/bin/env python3
"""Pre-build every preset of a project's configurator: all on/off
combinations of the options in projects/<name>/configurator.json.

    python presets.py <project>        # builds missing or out-of-date presets
    python presets.py --all            # every project

-> out/<project>/presets/<key>/ (+ result.json). A build may also write
scene.json - {dirt, glass, snake} drawn around the part (see snake-hide). The configurator page only
switches between these - it never builds anything itself. Re-run after any
change to a project's generator.
"""
import itertools
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "out"
PROJECTS = ROOT / "projects"


def config(p):
    f = PROJECTS / p / "configurator.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}


def combos(cfg):
    opts = cfg.get("options", [])
    for vals in itertools.product((True, False), repeat=len(opts)):
        yield dict(zip((o["id"] for o in opts), vals))


def key(vals):
    """Same string the page builds: 'hill=1,lantern=0' ('default' with no options)."""
    return ",".join(f"{k}={int(v)}" for k, v in vals.items()) or "default"


def args(cfg, vals):
    a = list(cfg.get("targets", []))
    for o in cfg.get("options", []):
        a += o.get("on" if vals[o["id"]] else "off", [])
    return a


def code_stamp(p):
    """Newest generator file (code, configurator.json, source STLs)."""
    fs = [f for f in (PROJECTS / p).rglob("*") if f.is_file() and f.suffix in (".py", ".json", ".stl")
          and "tests" not in f.parts and "__pycache__" not in f.parts]
    return max((f.stat().st_mtime for f in fs), default=0)


def results(p):
    """{key: result} of the presets built so far, each marked stale if the generator changed since."""
    stamp, res = code_stamp(p), {}
    for f in (OUT / p / "presets").glob("*/result.json"):
        r = json.loads(f.read_text(encoding="utf-8"))
        r["stale"] = r.get("stamp", 0) < stamp
        res[f.parent.name] = r
    return res


def build(p):
    cfg = config(p)
    if cfg.get("page"):
        print(f"{p}: has its own configurator page ({cfg['page']}) - build it with build.py")
        return 0
    stamp, base, bad = code_stamp(p), OUT / p / "presets", 0
    want = list(combos(cfg))
    keep = {key(v) for v in want}
    for d in base.glob("*") if base.exists() else []:          # presets of options that no longer exist
        if d.name not in keep:
            shutil.rmtree(d, ignore_errors=True)
    for n, vals in enumerate(want, 1):
        k, d = key(vals), base / key(vals)
        done = d / "result.json"
        if done.exists() and json.loads(done.read_text(encoding="utf-8")).get("stamp", 0) >= stamp:
            continue
        shutil.rmtree(d, ignore_errors=True)
        d.mkdir(parents=True)
        t0 = time.time()
        r = subprocess.run([sys.executable, "build.py", *args(cfg, vals)], cwd=PROJECTS / p,
                           env=dict(os.environ, OUT_DIR=str(d)), capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        url = lambda f: "/" + f.relative_to(OUT).as_posix()
        files = [dict(name=f.stem, url=url(f), size=f.stat().st_size,
                      obj=url(f.with_suffix(".obj")) if f.with_suffix(".obj").exists() else None)
                 for f in sorted(d.glob("*.stl")) if not f.name.startswith("_")]
        ok = r.returncode == 0 and bool(files)
        sc = d / "scene.json"                                   # optional extras the page draws around the part
        scene = json.loads(sc.read_text(encoding="utf-8")) if sc.exists() else None
        done.write_text(json.dumps(dict(ok=ok, files=files, scene=scene, stamp=stamp, args=args(cfg, vals),
                                        log=(r.stdout + r.stderr)[-4000:])), encoding="utf-8")
        print(f"{p} [{n}/{len(want)}] {k}: {'ok' if ok else 'FAILED'} ({time.time() - t0:.0f} s)")
        bad += not ok
    return 1 if bad else 0


def main(argv):
    names = sorted(p.name for p in PROJECTS.iterdir() if (p / "build.py").exists())
    want = names if argv[1:] == ["--all"] else argv[1:]
    if not want or any(w not in names for w in want):
        print(__doc__ + "\nprojects: " + ", ".join(names))
        return 2
    return max(build(p) for p in want)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
