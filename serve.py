#!/usr/bin/env python3
"""Local viewer server: http://localhost:8000

    python serve.py            # port 8000, opens the browser
    python serve.py 8080 -n    # other port, don't open a browser

Every project opens in a configurator: on/off presets from
projects/<name>/configurator.json, pre-built by `python presets.py <name>`
(the page never builds anything), 3D view, download.
    {"note": "...", "targets": [build.py args first],
     "options": [{"id", "label", "default": true|false, "on": [build.py args], "off": [args]}]}
or {"page": "/<project>/site/"} for a project with its own configurator page.
    /                 home: one folder card per project (goal, status, thumbnail)
    /p/<project>      the project's configurator (shared/configurator.html)
    /thumb/<path>     cached PNG thumbnail of out/<path>.stl
    GET  /api/config?project=<name>     configurator.json + every pre-built preset

Project chat (shared/chat.js, injected into every page): a Claude Code
session per project, run with `claude -p` in projects/<name>/ - it can edit
that project's files and run its build + tests, nothing else. One ongoing
conversation per project (out/<name>/.chat/: session id + transcript).
    GET  /api/projects
    GET  /api/chat/history?project=<name>
    POST /api/chat        {project, message, context}  -> NDJSON stream
    POST /api/chat/new    {project}

Render & print (configurator sidebar + Realistic/AR buttons; shared/studio.py, shared/realistic.js):
    /glb/<path>.stl                      GLB of that STL (for model-viewer / AR)
    POST /api/studio/render  {stl, turntable, color}  -> {url}  (Blender PNG / MP4)
    POST /api/studio/slice   {stl}                    -> time, grams, layers, 3MF url
"""
import html as H
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import webbrowser
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

import presets
from shared import studio

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "out"
PROJECTS = ROOT / "projects"
CONFIGURATOR = ROOT / "shared" / "configurator.html"
SHARED = ROOT / "shared"
CLAUDE = shutil.which("claude")
TOOLS = ("Read,Edit,Write,Glob,Grep,Bash(python build.py:*),Bash(python ../../presets.py:*),"
         "Bash(python -m pytest:*),Bash(pytest:*)")
SYSTEM = """You are chatting with Tyler through his local 3D viewer (serve.py) about the
project "{p}". Your working directory is projects/{p}/ - read its CLAUDE.md first
if you haven't this conversation; the repo-wide rules are in ../../CLAUDE.md.
His messages may end with a [Viewer context] block: what is on screen and points
he clicked on the model (point_mm + surface_normal, in the coordinate system
named there). Use it to know exactly which part/feature he means.
Each pick also has `face`: the whole flat or curved surface around the click, highlighted
on his screen in its own colour, with an id (F1, F2...), a rough name ("flat top (+Z)"),
normal, plane_offset_mm (flat: normal . p = offset) or axis (curved, wraps round), area,
centroid and bounds. When he
points at faces, first say in one line which feature of the geometry code makes each one
("F2 = the lid's top plate, `lid_t` thick") so he knows you have the right side; if unsure
which feature it is, say so and ask. Always call faces by their id (F2) - the chat turns
ids into coloured tags he can click to re-highlight that face.
Keep replies SHORT (he has ADHD): lead with the answer, a few bullets at most.
When you change geometry: rebuild what the configurator shows - `python ../../presets.py {p}`
(python-enclosure: `python build.py fittings`) - and run its tests (`python -m pytest -q`),
so the page reloads; record measurements and decisions in CLAUDE.md and a round in
docs/DESIGN_LOG.md. Sizes are changed by talking to you - the configurator only has
on/off presets.
You may only edit this project's files and run its build/tests."""

_running = {}            # project -> Popen
_lock = threading.Lock()


def projects():
    return sorted(p.name for p in PROJECTS.iterdir() if (p / "CLAUDE.md").exists()) if PROJECTS.exists() else []


def chat_dir(p):
    d = OUT / p / ".chat"
    d.mkdir(parents=True, exist_ok=True)
    return d


def history(p):
    f = chat_dir(p) / "log.jsonl"
    msgs = [json.loads(x) for x in f.read_text(encoding="utf-8").splitlines() if x] if f.exists() else []
    return {"messages": msgs, "running": p in _running}


def log_msg(p, **m):
    with open(chat_dir(p) / "log.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(m) + "\n")


def meta(p):
    """Goal + status lines from a project's CLAUDE.md."""
    t = (PROJECTS / p / "CLAUDE.md").read_text(encoding="utf-8")
    goal = re.search(r"\*\*Goal:\*\*\s*(.+?)(?:\n\*\*|\n\n)", t, re.S)
    status = re.search(r"\*\*Status:\*\*\s*([^\n<]+)", t)
    return (" ".join(goal.group(1).split()) if goal else "", status.group(1).strip() if status else "")


def hero(p):
    """Card picture: out/<p>/cover.stl if the build writes one, else the main
    (biggest) part of the default preset."""
    if (OUT / p / "cover.stl").exists():
        return OUT / p / "cover.stl"
    cfg = presets.config(p)
    d = OUT / p / "presets" / presets.key({o["id"]: o["default"] for o in cfg.get("options", [])})
    stls = [f for f in d.glob("*.stl") if not f.name.startswith("_")]
    return max(stls, key=lambda f: f.stat().st_size) if stls else None


_thumb_lock = threading.Lock()


def thumb(stl):
    """PNG thumbnail for an STL under out/, cached in out/<project>/.thumbs/."""
    rel = stl.relative_to(OUT)
    png = OUT / rel.parts[0] / ".thumbs" / (rel.as_posix().replace("/", "__") + ".png")
    if png.exists() and png.stat().st_mtime >= stl.stat().st_mtime:
        return png
    with _thumb_lock:                                        # one render at a time (they're heavy)
        if png.exists() and png.stat().st_mtime >= stl.stat().st_mtime:
            return png
        import trimesh
        sys.path.insert(0, str(ROOT))
        from shared import render as R
        m = trimesh.load(str(stl), force="mesh")
        png.parent.mkdir(parents=True, exist_ok=True)
        view = presets.config(rel.parts[0]).get("cover_view", (-1, 1.3, -0.9))   # look direction: from above, front
        R.save(R.render(m, view_dir=view, size=(360, 260), bg=(24, 46, 58), ss=1), str(png))
    return png


def warm_thumbs():
    for f in filter(None, map(hero, projects())):
        try:
            thumb(f)
        except Exception as e:                                # a bad STL must not stop the rest
            print(f"thumbnail failed: {f.relative_to(OUT)}: {e}")


STYLE = """<style>
body{font:15px system-ui,sans-serif;background:#0f1d25;color:#dfe9ee;margin:0;padding:28px 24px 80px}
a{color:inherit;text-decoration:none} h1{margin:0 0 4px;font-size:24px} .dim{color:#8fa6b1}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:16px;margin-top:18px}
.card{background:#18303c;border-radius:10px;overflow:hidden;display:flex;flex-direction:column;transition:background .15s}
.card:hover{background:#21404f}
.card img,.card .noimg{width:100%;aspect-ratio:36/26;object-fit:cover;background:#182e3a;display:block}
.card .noimg{display:flex;align-items:center;justify-content:center;font-size:44px;color:#3d5a68}
.card .b{padding:10px 12px 12px} .card b{display:block;font-size:15px} .card span{font-size:13px;color:#8fa6b1}
.folder{position:relative;margin-top:10px} .folder:before{content:"";position:absolute;top:-10px;left:0;width:42%;height:14px;
  background:#18303c;border-radius:8px 8px 0 0} .folder:hover:before{background:#21404f}
.pill{display:inline-block;background:#24414e;border-radius:10px;padding:1px 8px;font-size:12px;margin-top:6px}
.btns{display:flex;gap:8px;flex-wrap:wrap;margin:14px 0 4px}
.btn{background:#2a8a7e;color:#fff;border-radius:8px;padding:8px 14px;font-weight:600}
.btn.alt{background:#24414e;color:#dfe9ee}
h2{font-size:15px;color:#8fa6b1;text-transform:uppercase;letter-spacing:.05em;margin:28px 0 0}
.top{margin-bottom:10px;display:inline-block}
</style>"""


def home():
    cards = ""
    for p in projects():
        goal, status = meta(p)
        h = hero(p)
        img = (f'<img loading="lazy" src="/thumb/{h.relative_to(OUT).as_posix()}" alt="">' if h
               else '<div class="noimg">&#128193;</div>')
        cards += (f'<a class="card folder" href="/p/{p}">{img}<div class="b"><b>{H.escape(p)}</b>'
                  f'<span>{H.escape(goal[:140])}{"..." if len(goal) > 140 else ""}</span><br>'
                  f'<span class="pill">{H.escape(status.split(" - ")[0][:40]) or "-"}</span></div></a>')
    return f"""<!doctype html><meta charset="utf-8"><title>3D Projects</title>{STYLE}
<body><h1>3D projects</h1><div class="dim">One folder per project - open one to configure and generate its parts.
New: <code>python new_project.py &lt;name&gt; "&lt;goal&gt;"</code></div>
<div class="grid">{cards}</div></body>"""


def out_stl(path):
    """An STL under out/ from a URL path like /<project>/presets/x/part.stl, else None."""
    f = (OUT / unquote(path).lstrip("/")).resolve()
    return f if f.suffix.lower() == ".stl" and OUT.resolve() in f.parents and f.is_file() else None


def tool_line(b):
    """One short line for a tool call: 'Edit screen_protector.py', 'Bash python build.py'."""
    i = b.get("input") or {}
    arg = i.get("file_path") or i.get("command") or i.get("pattern") or i.get("path") or ""
    if i.get("file_path"):
        arg = Path(arg).name
    return f"{b.get('name')} {str(arg)[:80]}".strip()


class Handler(SimpleHTTPRequestHandler):
    def _send(self, body, ctype, code=200):
        b = body.encode() if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def _local(self):
        """Only pages served from this server may call the API (no other
        website can drive the chat through your browser). Behind a proxy, list
        its public host[:port]s in SERVE_HOSTS (comma separated)."""
        port = self.server.server_address[1]
        ok = {f"localhost:{port}", f"127.0.0.1:{port}"} | set(filter(None, os.environ.get("SERVE_HOSTS", "").split(",")))
        origin = self.headers.get("Origin")
        return (self.headers.get("Host") in ok
                and (origin is None or origin.split("//", 1)[-1] in ok))

    def _page(self, html, project=""):
        tag = f'<script src="/_shared/chat.js" data-project="{project}"></script>'
        i = html.rfind("</body>")
        html = html[:i] + tag + html[i:] if i >= 0 else html + tag
        return self._send(html, "text/html; charset=utf-8")

    def do_GET(self):
        u = urlparse(self.path)
        route = u.path
        if route in ("/", "/index.html"):
            return self._page(home())
        if route in ("/_shared/chat.js", "/_shared/realistic.js"):
            return self._send((SHARED / route[9:]).read_text(encoding="utf-8"), "text/javascript; charset=utf-8")
        if route.startswith("/p/"):
            p = route[3:].strip("/")
            if p not in projects():
                return self._send("no such project", "text/plain", 404)
            if presets.config(p).get("page"):                      # project with its own configurator
                self.send_response(302)
                self.send_header("Location", presets.config(p)["page"])
                return self.end_headers()
            return self._page(CONFIGURATOR.read_text(encoding="utf-8"), p)
        if route.startswith("/glb/"):
            f = out_stl(route[4:])
            if not f:
                return self._send("not found", "text/plain", 404)
            return self._send(studio.glb(f).read_bytes(), "model/gltf-binary")
        if route.startswith("/thumb/"):
            f = (OUT / unquote(route[7:])).resolve()
            if f.suffix.lower() != ".stl" or OUT.resolve() not in f.parents or not f.is_file():
                return self._send("not found", "text/plain", 404)
            try:
                return self._send(thumb(f).read_bytes(), "image/png")
            except Exception as e:
                return self._send(f"thumbnail failed: {e}", "text/plain", 500)
        if route.startswith("/api/") and not self._local():
            return self._send("forbidden", "text/plain", 403)
        if route == "/api/projects":
            return self._send(json.dumps(projects()), "application/json")
        if route == "/api/config":
            p = parse_qs(u.query).get("project", [""])[0]
            if p not in projects():
                return self._send("unknown project", "text/plain", 404)
            goal, status = meta(p)
            return self._send(json.dumps(dict(presets.config(p), project=p, goal=goal, status=status,
                                              presets=presets.results(p))), "application/json")
        if route == "/api/chat/history":
            p = parse_qs(u.query).get("project", [""])[0]
            if p not in projects():
                return self._send("[]", "application/json")
            return self._send(json.dumps(history(p)), "application/json")
        f = Path(self.translate_path(self.path))
        if f.is_dir():
            f = f / "index.html"
        if f.suffix == ".html" and f.is_file():                     # viewer page: add the chat
            seg = route.strip("/").split("/")[0]
            return self._page(f.read_text(encoding="utf-8"), seg if seg in projects() else "")
        return super().do_GET()

    def do_POST(self):
        route = urlparse(self.path).path
        if not self._local() or self.headers.get("Content-Type", "").split(";")[0] != "application/json":
            return self._send("forbidden", "text/plain", 403)
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        if route.startswith("/api/studio/"):
            return self._studio(route, body)
        p = body.get("project", "")
        if p not in projects():
            return self._send("unknown project", "text/plain", 400)
        if route == "/api/chat/new":
            if p in _running:
                return self._send("busy", "text/plain", 409)
            shutil.rmtree(OUT / p / ".chat", ignore_errors=True)
            return self._send("{}", "application/json")
        if route == "/api/chat":
            return self._chat(p, body.get("message", ""), body.get("context"))

        return self._send("not found", "text/plain", 404)

    def _studio(self, route, body):
        f = out_stl(body.get("stl", ""))
        if not f:
            return self._send(json.dumps({"error": "no such STL under out/"}), "application/json", 404)
        try:
            if route == "/api/studio/render":
                r = studio.render(f, bool(body.get("turntable")), body.get("color") or "#c8d4dc")
                res = {"url": "/" + r.relative_to(OUT).as_posix()}
            elif route == "/api/studio/slice":
                res = studio.slice(f)
            else:
                return self._send(json.dumps({"error": "not found"}), "application/json", 404)
        except Exception as e:
            return self._send(json.dumps({"error": str(e)}), "application/json", 500)
        return self._send(json.dumps(res), "application/json")

    def _chat(self, p, message, context):
        self.send_response(200)
        self.send_header("Content-Type", "application/x-ndjson")
        self.end_headers()

        def emit(**e):
            try:
                self.wfile.write((json.dumps(e) + "\n").encode())
                self.wfile.flush()
            except OSError:
                pass                                   # page closed: keep going, the log still gets it

        if not CLAUDE:
            return emit(t="error", v="`claude` CLI not found on PATH")
        with _lock:
            if p in _running:
                return emit(t="error", v="this project's chat is still working on the last message")
            prompt = message
            if context:
                prompt += "\n\n[Viewer context]\n" + json.dumps(context, indent=1)
            sid_f = chat_dir(p) / "session.txt"
            cmd = [CLAUDE, "-p", "--output-format", "stream-json", "--verbose", "--include-partial-messages",
                   "--permission-mode", "acceptEdits", "--allowedTools", TOOLS,
                   "--append-system-prompt", SYSTEM.format(p=p)]
            if sid_f.exists():
                cmd += ["--resume", sid_f.read_text().strip()]
            proc = subprocess.Popen(cmd, cwd=PROJECTS / p, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace")
            _running[p] = proc
        log_msg(p, role="user", text=message, context=context)
        text, result, reload, started = "", "", False, False
        try:
            proc.stdin.write(prompt)
            proc.stdin.close()
            for line in proc.stdout:
                try:
                    e = json.loads(line)
                except ValueError:
                    continue
                if e.get("session_id"):
                    sid_f.write_text(e["session_id"])
                t = e.get("type")
                if t == "stream_event":
                    ev = e.get("event", {})
                    if ev.get("type") == "message_start" and started and not text.endswith("\n\n"):
                        text += "\n\n"
                        emit(t="text", v="\n\n")
                    d = ev.get("delta", {})
                    if ev.get("type") == "content_block_delta" and d.get("type") == "text_delta":
                        started = True
                        text += d["text"]
                        emit(t="text", v=d["text"])
                elif t == "assistant":
                    for b in e.get("message", {}).get("content", []):
                        if b.get("type") == "tool_use":
                            cmd = (b.get("input") or {}).get("command", "")
                            if b.get("name") == "Bash" and ("build.py" in cmd or "presets.py" in cmd):
                                reload = True
                            emit(t="tool", v=tool_line(b))
                elif t == "result":
                    result = e.get("result") or ""
                    if e.get("is_error"):
                        emit(t="error", v=result or "Claude stopped with an error")
            proc.wait()
            if proc.returncode and not text and not result:
                err = proc.stderr.read().strip()[-500:]
                emit(t="error", v=err or f"claude exited with code {proc.returncode}")
        finally:
            with _lock:
                _running.pop(p, None)
            log_msg(p, role="assistant", text=text.strip() or result)
            emit(t="done", reload=reload, result=result)

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
    print(f"serving out/ at {url}  (Ctrl+C to stop)" + ("" if CLAUDE else "  [chat off: `claude` not on PATH]"))
    threading.Thread(target=warm_thumbs, daemon=True).start()     # thumbnails ready before you look
    if "-n" not in argv:
        webbrowser.open(url)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    sys.exit(main(sys.argv))
