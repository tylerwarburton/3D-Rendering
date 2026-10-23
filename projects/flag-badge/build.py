#!/usr/bin/env python3
"""Build flag-badge: python build.py [part ...]   (all parts if none given)
-> <repo>/out/flag-badge/stl/<part>.stl"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parents[1])]

from shared import printkit as pk   # noqa: E402
import flag_badge as M                 # noqa: E402


def main(argv):
    want = pk.apply_sets(argv[1:], M) or list(M.PARTS)   # --set NAME=VALUE: configurator options
    bad = [w for w in want if w not in M.PARTS]
    if bad:
        print("unknown part(s): " + ", ".join(bad) + "\nparts: " + ", ".join(M.PARTS))
        return 1
    out = pk.out_dir("flag-badge")
    for name in want:
        m = M.PARTS[name]()
        pk.export(m, out / f"{name}.stl")
        r = pk.report(m)
        print(f"  {name + '.stl':32s} {r['size'][0]} x {r['size'][1]} x {r['size'][2]} mm"
              f"  {r['volume_cm3']} cm3 ~{r['grams_pla']} g  overhang {r['overhang_mm2']} mm2"
              + ("" if r["fits_bed"] else "  TOO BIG FOR BED"))
    print(f"-> out/flag-badge/stl/   (view: python serve.py)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
