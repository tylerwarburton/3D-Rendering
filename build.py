#!/usr/bin/env python3
"""Build everything for the enclosure hardware project.

    python build.py            # everything
    python build.py stl        # just re-export the meshes
    python build.py sheets     # just the static PNG review sheets
    python build.py viewer     # just the interactive viewer
    python build.py audit      # just the numbers
    python build.py concept    # the guide-column design study
    python build.py overhang   # overhang + print orientation analysis
    python build.py coverage   # support coverage map of the shelf ceilings
    python build.py testprint  # support test coupon + instructions
    python build.py fittings   # tube fittings: STLs + out/fittings_viewer.html + out/site/

Design sources live in src/. Edit those, then re-run. Nothing in tools/
needs touching to change the design.
"""
import sys
import time

STEPS = ["fittings", "stl", "sheets", "water", "spill", "audit", "viewer", "concept", "overhang", "coverage", "testprint"]
# "concept" is a design study, not a deliverable, so `all` leaves it out.
ALL = [s for s in STEPS if s not in ("concept", "overhang", "coverage", "testprint", "fittings")]


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
    if "viewer" in want:
        from tools import viewer
        print("viewer:")
        viewer.run()
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
