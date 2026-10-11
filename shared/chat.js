/* Project chat panel - injected by serve.py into every viewer page.
   Talks to a Claude Code session running in projects/<name>/ (one ongoing
   conversation per project). "Point" mode: click the model to attach the
   part + exact spot to the next message. Pages expose window.__viewer
   (scene, camera, canvas, meshes(), info(), optional toFile(), reload()). */
(function () {
  "use strict";
  const me = document.currentScript;
  let project = (me && me.dataset.project) || "";
  const V = () => window.__viewer || null;

  const css = `
  #cc-btn{position:fixed;right:18px;bottom:18px;z-index:9998;padding:10px 16px;border-radius:22px;border:0;
    background:#2a8a7e;color:#fff;font:600 14px system-ui,sans-serif;cursor:pointer;box-shadow:0 4px 16px rgba(0,0,0,.4)}
  #cc{position:fixed;top:0;right:0;bottom:0;width:min(420px,100vw);z-index:9999;display:none;flex-direction:column;
    background:#122028;color:#dfe9ee;font:14px/1.45 system-ui,sans-serif;box-shadow:-6px 0 24px rgba(0,0,0,.45)}
  #cc.open{display:flex}
  #cc header{display:flex;gap:6px;align-items:center;padding:10px;border-bottom:1px solid #24414e}
  #cc header select{flex:1;min-width:0}
  #cc select,#cc button,#cc textarea{font:inherit;color:inherit;background:#1b3340;border:1px solid #2c4a58;border-radius:6px;padding:5px 8px}
  #cc button{cursor:pointer} #cc button:hover{background:#24414e}
  #cc button.on{background:#2a8a7e;border-color:#2a8a7e}
  #cc-log{flex:1;overflow:auto;padding:10px 12px}
  .cc-m{margin:0 0 12px;white-space:pre-wrap;word-wrap:break-word}
  .cc-u{background:#1f3a47;border-radius:8px;padding:8px 10px}
  .cc-a code{background:#0d171d;padding:1px 4px;border-radius:4px}
  .cc-a pre{background:#0d171d;padding:8px;border-radius:6px;overflow:auto;white-space:pre}
  .cc-t{color:#8fa6b1;font-size:12px;margin:-6px 0 8px}
  .cc-ctx{color:#8fa6b1;font-size:12px;margin-top:4px}
  #cc-chips{display:flex;flex-wrap:wrap;gap:6px;padding:0 10px}
  .cc-chip{background:#2a5468;border-radius:12px;padding:3px 8px;font-size:12px}
  .cc-chip b{cursor:pointer;margin-left:6px}
  #cc-foot{display:flex;gap:6px;padding:10px;align-items:flex-end}
  #cc-foot textarea{flex:1;resize:none;height:64px}
  #cc-hint{color:#8fa6b1;font-size:12px;padding:0 10px 6px}
  `;
  document.head.insertAdjacentHTML("beforeend", `<style>${css}</style>`);
  document.body.insertAdjacentHTML("beforeend", `
    <button id="cc-btn">Chat</button>
    <div id="cc">
      <header>
        <select id="cc-proj" title="Project"></select>
        <button id="cc-pick" title="Click the model to attach that spot to your message">Point</button>
        <button id="cc-new" title="Start a fresh conversation for this project">New</button>
        <button id="cc-x" title="Close">&times;</button>
      </header>
      <div id="cc-log"></div>
      <div id="cc-chips"></div>
      <div id="cc-hint"></div>
      <div id="cc-foot"><textarea id="cc-in" placeholder="Message... (Enter to send, Shift+Enter new line)"></textarea>
        <button id="cc-send">Send</button></div>
    </div>`);
  const $ = id => document.getElementById(id);
  const panel = $("cc"), log = $("cc-log"), input = $("cc-in"), chipsEl = $("cc-chips"), hint = $("cc-hint");
  let chips = [], picking = false, busy = false, markers = [];

  const store = (k, v) => { try { v === undefined ? sessionStorage.removeItem(k) : sessionStorage.setItem(k, v); } catch (e) {} };
  const recall = k => { try { return sessionStorage.getItem(k); } catch (e) { return null; } };

  /* ---------- rendering ---------- */
  const esc = s => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  function md(s) {
    const parts = esc(s).split(/```(?:\w+)?\n?/);
    return parts.map((p, i) => i % 2 ? `<pre>${p}</pre>` :
      p.replace(/`([^`]+)`/g, "<code>$1</code>").replace(/\*\*([^*]+)\*\*/g, "<b>$1</b>")).join("");
  }
  function add(cls, html) {
    const d = document.createElement("div"); d.className = "cc-m " + cls; d.innerHTML = html;
    log.append(d); log.scrollTop = log.scrollHeight; return d;
  }
  function addUser(text, ctx) {
    const n = (ctx && ctx.picks && ctx.picks.length) || 0;
    add("cc-u", esc(text) + (n ? `<div class="cc-ctx">+ ${n} picked point${n > 1 ? "s" : ""}</div>` : ""));
  }
  function addTool(t) { const d = document.createElement("div"); d.className = "cc-t"; d.textContent = "▸ " + t; log.append(d); log.scrollTop = log.scrollHeight; }

  /* ---------- projects + history ---------- */
  async function loadProjects() {
    const list = await fetch("/api/projects").then(r => r.json());
    const fromView = (V() && V().info().project) || "";
    project = project || fromView || recall("cc.project") || list[0] || "";
    $("cc-proj").innerHTML = list.map(p => `<option ${p === project ? "selected" : ""}>${p}</option>`).join("");
  }
  async function loadHistory() {
    log.innerHTML = "";
    if (!project) return;
    const r = await fetch("/api/chat/history?project=" + encodeURIComponent(project)).then(r => r.json());
    const h = r.messages || [];
    if (!h.length) add("cc-a", `<span style="color:#8fa6b1">Chat about <b>${esc(project)}</b>. Claude works in that project's folder and can edit, build and test it. Use <b>Point</b> to click the model and attach that spot.</span>`);
    h.forEach(m => m.role === "user" ? addUser(m.text, m.context) : add("cc-a", md(m.text)));
    if (r.running) addTool("still working on the last message...");
  }
  $("cc-proj").onchange = async e => { project = e.target.value; store("cc.project", project); await loadHistory(); };

  /* ---------- picking ---------- */
  function setHint() {
    hint.textContent = picking ? "Click the model to attach a spot (drag still rotates)." : "";
    $("cc-pick").classList.toggle("on", picking);
  }
  $("cc-pick").onclick = () => { picking = !picking; setHint(); };
  function renderChips() {
    chipsEl.innerHTML = chips.map((c, i) => `<span class="cc-chip">${esc(c.label)}<b data-i="${i}">&times;</b></span>`).join("");
    chipsEl.querySelectorAll("b").forEach(b => b.onclick = () => {
      const i = +b.dataset.i; const m = markers[i]; if (m && V()) V().scene.remove(m);
      chips.splice(i, 1); markers.splice(i, 1); renderChips();
    });
  }
  let down = null;
  document.addEventListener("pointerdown", e => { down = {x: e.clientX, y: e.clientY}; }, true);
  document.addEventListener("pointerup", e => {
    const v = V();
    if (!picking || !v || !down || e.target !== v.canvas) return;
    if (Math.hypot(e.clientX - down.x, e.clientY - down.y) > 4) return;        // was a drag
    const T = v.THREE, r = v.canvas.getBoundingClientRect();
    const ndc = new T.Vector2(((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1);
    const ray = new T.Raycaster(); ray.setFromCamera(ndc, v.camera);
    const hit = ray.intersectObjects(v.meshes(), false)[0];
    if (!hit) return;
    const p = [hit.point.x, hit.point.y, hit.point.z];
    const fp = (v.toFile ? v.toFile(p) : p).map(x => +x.toFixed(2));
    const n = hit.face ? hit.face.normal.clone().transformDirection(hit.object.matrixWorld) : null;
    const info = v.info();
    const sub = v.meshes().length > 1 ? v.meshes().indexOf(hit.object) : null;
    chips.push({label: `${info.variant || info.file || "part"} @ (${fp.map(x => x.toFixed(1)).join(", ")})`,
                part: info.variant || info.file, sub_body: sub, point_mm: fp,
                surface_normal: n ? [n.x, n.y, n.z].map(x => +x.toFixed(3)) : null});
    const s = new T.Mesh(new T.SphereGeometry(Math.max(1.2, (v.camera.position.distanceTo(hit.point)) / 150), 16, 12),
                         new T.MeshBasicMaterial({color: 0xff7a45, depthTest: false}));
    s.position.copy(hit.point); s.renderOrder = 999; v.scene.add(s); markers.push(s);
    renderChips();
  }, true);

  /* ---------- sending ---------- */
  async function send() {
    const text = input.value.trim();
    if (!text || busy || !project) return;
    const v = V();
    const ctx = {view: v ? v.info() : null, coordinates: v && v.coords, picks: chips.map(({label, ...c}) => c)};
    addUser(text, ctx); input.value = "";
    chips = []; markers.forEach(m => v && v.scene.remove(m)); markers = []; renderChips();
    busy = true; $("cc-send").disabled = true;
    const out = add("cc-a", "…"); let txt = "", reload = false;
    try {
      const r = await fetch("/api/chat", {method: "POST", headers: {"Content-Type": "application/json"},
                                          body: JSON.stringify({project, message: text, context: ctx})});
      const rd = r.body.getReader(), dec = new TextDecoder(); let buf = "";
      for (;;) {
        const {value, done} = await rd.read(); if (done) break;
        buf += dec.decode(value, {stream: true});
        let i; while ((i = buf.indexOf("\n")) >= 0) {
          const line = buf.slice(0, i); buf = buf.slice(i + 1); if (!line) continue;
          const ev = JSON.parse(line);
          if (ev.t === "text") { txt += ev.v; out.innerHTML = md(txt); log.scrollTop = log.scrollHeight; }
          else if (ev.t === "tool") { if (!txt) out.remove(); addTool(ev.v); if (!txt) log.append(out); }
          else if (ev.t === "error") { txt += "\n\n⚠ " + ev.v; out.innerHTML = md(txt); }
          else if (ev.t === "done") { reload = ev.reload; if (!txt && ev.result) out.innerHTML = md(ev.result); }
        }
      }
    } catch (e) { out.innerHTML = md(txt + "\n\n⚠ " + e); }
    busy = false; $("cc-send").disabled = false;
    if (reload) { addTool("rebuilt - reloading the view"); setTimeout(() => {
      store("cc.open", "1"); (V() && V().reload) ? V().reload() : location.reload(); }, 600); }
  }
  $("cc-send").onclick = send;
  input.addEventListener("keydown", e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } });
  $("cc-new").onclick = async () => {
    if (!project || busy) return;
    await fetch("/api/chat/new", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({project})});
    await loadHistory();
  };

  /* ---------- open / close ---------- */
  function open(on) { panel.classList.toggle("open", on); $("cc-btn").style.display = on ? "none" : ""; store("cc.open", on ? "1" : undefined); }
  $("cc-btn").onclick = async () => { open(true); await loadProjects(); await loadHistory(); input.focus(); };
  $("cc-x").onclick = () => { open(false); picking = false; setHint(); };
  if (recall("cc.open")) $("cc-btn").onclick();
})();
