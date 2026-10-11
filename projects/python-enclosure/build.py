#!/usr/bin/env python3
"""Build the enclosure hardware (tube fittings).

    python build.py            # same as `fittings`
    python build.py fittings   # tube fittings: STLs + fittings_viewer.html + site/
    python build.py cover      # cover.stl - the home-page card picture (tee fitting)

Design sources live in src/. Edit those, then re-run. Nothing in tools/
needs touching to change the design. (The waterfall is projects/waterfall/.)
"""
import sys
import time

STEPS = ["fittings", "cover"]
ALL = STEPS


def main(argv):
    want = [a for a in argv[1:] if not a.startswith("-")] or ["all"]
    if "all" in want:
        want = ALL
    bad = [w for w in want if w not in STEPS]
    if bad:
        print(f"unknown step(s): {', '.join(bad)}")
        print(f"available: {', '.join(STEPS)}, all")
        return 1

    from tools import paths
    t0 = time.time()
    print(f"project root: {paths.ROOT}\n")

    if "fittings" in want:
        from tools import fittings_viewer
        print("fittings:")
        fittings_viewer.run('site')
        print()
    if "cover" in want:
        import fittings as F
        F.export_ready(F.make_tee()).export(str(paths.OUT / "cover.stl"))
        print("cover: cover.stl (tee fitting)\n")
    print(f"done in {time.time()-t0:.1f}s -> {paths.rel(paths.OUT)}/")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
