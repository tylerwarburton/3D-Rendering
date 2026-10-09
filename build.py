#!/usr/bin/env python3
"""Build a project in projects/<name>/ (runs that project's own build.py).

    python build.py                              # list projects
    python build.py python-enclosure fittings    # project + its build steps

Outputs land in out/<name>/. View them with `python serve.py`.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROJECTS = ROOT / "projects"


def main(argv):
    names = sorted(p.name for p in PROJECTS.iterdir() if (p / "build.py").exists())
    if len(argv) < 2 or argv[1] not in names:
        print("usage: python build.py <project> [steps...]")
        print("projects: " + ", ".join(names))
        return 1
    proj = PROJECTS / argv[1]
    return subprocess.call([sys.executable, "-u", str(proj / "build.py"), *argv[2:]], cwd=proj)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
