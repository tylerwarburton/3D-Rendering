#!/usr/bin/env python3
"""Start a new project from templates/project.

    python new_project.py desk-hook "Hook that clips under my desk"
    python new_project.py vase-fix "Fix the base of a downloaded vase" --from ~/Downloads/vase.stl

Creates projects/<name>/ (CLAUDE.md with goal + dimension table, design log,
parts module, build.py, tests), copies any --from STLs into source/ (each one
becomes an editable part), and lists the project in the root CLAUDE.md.
"""
import argparse
import datetime
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TEMPLATE = ROOT / "templates" / "project"


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("name", help="folder name, lower-case-with-dashes")
    ap.add_argument("goal", help="one line: what it is and what it's for")
    ap.add_argument("--from", dest="sources", nargs="*", default=[], help="STL files to start from")
    a = ap.parse_args(argv[1:])

    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", a.name):
        ap.error("name: lower-case letters, digits and dashes, e.g. desk-hook")
    dest = ROOT / "projects" / a.name
    if dest.exists():
        ap.error(f"{dest.relative_to(ROOT)} already exists")
    for s in a.sources:
        if not Path(s).expanduser().is_file():
            ap.error(f"--from: no such file {s}")

    slug = a.name.replace("-", "_")
    subs = {"__NAME__": a.name, "__SLUG__": slug, "__GOAL__": a.goal,
            "__DATE__": datetime.date.today().isoformat()}
    for src in TEMPLATE.rglob("*"):
        rel = src.relative_to(TEMPLATE).as_posix()
        for k, v in subs.items():
            rel = rel.replace(k, v)
        out = dest / rel
        if src.is_dir():
            out.mkdir(parents=True, exist_ok=True)
            continue
        out.parent.mkdir(parents=True, exist_ok=True)
        if src.name == ".gitkeep":
            out.touch()
            continue
        text = src.read_text(encoding="utf-8")
        for k, v in subs.items():
            text = text.replace(k, v)
        out.write_text(text, encoding="utf-8")
    for s in a.sources:
        shutil.copy2(Path(s).expanduser(), dest / "source" / Path(s).name)

    # list it in the root CLAUDE.md
    cm = ROOT / "CLAUDE.md"
    text = cm.read_text(encoding="utf-8")
    line = f"- `projects/{a.name}/` - {a.goal}\n"
    head = "## Projects\n\n"
    if head in text and line not in text:
        i = text.index(head) + len(head)
        j = text.find("\n\n", i)
        j = len(text) if j < 0 else j + 1
        cm.write_text(text[:j] + line + text[j:], encoding="utf-8")

    print(f"created projects/{a.name}/")
    print(f"  parts:   projects/{a.name}/{slug}.py" + (f"  ({len(a.sources)} source STL(s) in source/)" if a.sources else ""))
    print(f"  context: projects/{a.name}/CLAUDE.md  (goal, measurements, rules)")
    print(f"  build:   python build.py {a.name}    view: python serve.py")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
