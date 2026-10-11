#!/usr/bin/env python3
"""Build the waterfall.

    python build.py            # stl sheets water spill audit (the default)
    python build.py stl        # just the printable STL (+ STEP, section meshes)
    python build.py sheets     # static PNG review sheets
    python build.py water      # water-level diagram
    python build.py spill      # spill map
    python build.py audit      # numbers: geometry + hydraulics -> report.txt
    python build.py concept    # the guide-column design study
    python build.py overhang   # overhang + print orientation analysis
    python build.py coverage   # support coverage map of the shelf ceilings
    python build.py testprint  # support test coupon + instructions

Outputs land in <repo>/out/waterfall/. With OUT_DIR set (the configurator's
presets.py) and no steps named, only the printable waterfall.stl is written,
straight into OUT_DIR. Design source: src/waterfall.py (needs cadquery).
"""
import os
import sys
import time

STEPS = ["stl", "sheets", "water", "spill", "audit", "concept", "overhang", "coverage", "testprint"]
ALL = ["stl", "sheets", "water", "spill", "audit"]   # studies + coupon only by name


def main(argv):
    want = [a for a in argv[1:] if not a.startswith("-")]
    preset = bool(os.environ.get("OUT_DIR")) and not want
    want = want or ["all"]
    if "all" in want:
        want = ALL
    bad = [w for w in want if w not in STEPS]
    if bad:
        print(f"unknown step(s): {', '.join(bad)}")
        print(f"available: {', '.join(STEPS)}, all")
        return 1

    from tools import paths
    t0 = time.time()

    if preset:
        from tools import solids
        solids.run(sections=False)
        print(f"done in {time.time()-t0:.1f}s")
        return 0

    print(f"project root: {paths.ROOT}\n")
    if "stl" in want:
        from tools import solids
        solids.run()
        print()
    if "sheets" in want:
        from tools import sheets
        sheets.run()
        print()
    if "water" in want:
        from tools import water_diagram
        print("water diagram:")
        water_diagram.run()
        print()
    if "spill" in want:
        from tools import spill_map
        print("spill map:")
        spill_map.run()
        print()
    if "audit" in want:
        from tools import audit
        print("audit:")
        audit.run()
        print()
    if "testprint" in want:
        from tools import support_test
        support_test.run()
        print()
    if "coverage" in want:
        from tools import coverage
        coverage.run()
        print()
    if "overhang" in want:
        from tools import overhang
        overhang.run()
        print()
    if "concept" in want:
        from tools import concept
        concept.run()
        print()

    print(f"done in {time.time()-t0:.1f}s -> {paths.rel(paths.OUT)}/")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
