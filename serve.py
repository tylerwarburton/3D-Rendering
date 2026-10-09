#!/usr/bin/env python3
"""Local viewer server: http://localhost:8000

    python serve.py            # port 8000, opens the browser
    python serve.py 8080 -n    # other port, don't open a browser

Serves out/ (build first: `python build.py <project> ...`):
    /                 home: every project in out/<project>/ and its viewers
    /<project>/site/  a project's configurator (fittings: every port/angle/vent/gate combo)
    /stl.html         STL browser: every .stl under out/, or drop any STL file
    /api/stls         JSON list the STL browser reads
"""
import json
import sys
import webbrowser
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "out"
BROWSER = ROOT / "shared" / "stl_browser.html"


def stl_list():
    out = []
    for p in sorted(OUT.rglob("*.stl")):
        st = p.stat()
        out.append(dict(path=p.relative_to(OUT).as_posix(), size=st.st_size, mtime=st.st_mtime))
    return out


def home():
    rows = ""
    for proj in sorted(p for p in OUT.iterdir() if p.is_dir()) if OUT.exists() else []:
        links = []
        if (proj / "site" / "index.html").exists():
            links.append((f"/{proj.name}/site/", "Configurator",
                          "every variant: port genders, angles, vents, gate - downloads"))
        links += [(f"/{p.relative_to(OUT).as_posix()}", p.name, "single-file viewer")
                  for p in sorted(proj.rglob("*.html")) if "site" not in p.parts]
        n = sum(1 for _ in proj.rglob("*.stl"))
        links.append((f"/stl.html#{proj.name}/", "Exported STLs", f"{n} default STLs (STL browser)"))
        rows += f"<h3>{proj.name}</h3>" + "".join(
            f'<a href="{h}"><b>{t}</b><span>{d}</span></a>' for h, t, d in links)
    rows += '<h3>Any STL</h3><a href="/stl.html"><b>STL browser</b><span>drop any STL: bed fit, overhangs, grams</span></a>'
    return f"""<!doctype html><meta charset="utf-8"><title>3D Print Viewers</title>
<style>body{{font:15px system-ui;background:#0f1d25;color:#dfe9ee;max-width:640px;margin:40px auto;padding:0 16px}}
a{{display:block;padding:14px 16px;margin:8px 0;background:#18303c;border-radius:8px;color:inherit;text-decoration:none}}
a:hover{{background:#21404f}} h3{{margin:28px 0 4px;color:#8fa6b1}} span{{display:block;opacity:.65;font-size:13px;margin-top:3px}}</style>
<h2>3D print viewers</h2>{rows}"""


class Handler(SimpleHTTPRequestHandler):
    def _send(self, body, ctype):
        b = body.encode()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        route = self.path.split("?")[0]
        if route in ("/", "/index.html"):
            return self._send(home(), "text/html; charset=utf-8")
        if route == "/stl.html":
            return self._send(BROWSER.read_text(encoding="utf-8"), "text/html; charset=utf-8")
        if route == "/api/stls":
            return self._send(json.dumps(stl_list()), "application/json")
        return super().do_GET()

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")   # rebuilds show on reload
        super().end_headers()

    def log_message(self, *a):
        pass


def main(argv):
    nums = [a for a in argv[1:] if a.isdigit()]
    port = int(nums[0]) if nums else 8000
    OUT.mkdir(exist_ok=True)
    srv = ThreadingHTTPServer(("127.0.0.1", port), partial(Handler, directory=str(OUT)))
    url = f"http://localhost:{port}/"
    print(f"serving out/ at {url}  (Ctrl+C to stop)")
    if "-n" not in argv:
        webbrowser.open(url)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    sys.exit(main(sys.argv))
