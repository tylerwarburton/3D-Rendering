/* Project chat panel - injected by serve.py into every viewer page.
   Talks to a Claude Code session running in projects/<name>/ (one ongoing
   conversation per project). "Point" mode: click the model to attach the
   part, exact spot and the whole face around it (F1, F2...) to the next message. Pages expose window.__viewer
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
  .cc-f{color:#0d171d;font-weight:700;border-radius:4px;padding:0 4px;cursor:pointer}
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
      tagFaces(p.replace(/`([^`]+)`/g, "<code>$1</code>").replace(/\*\*([^*]+)\*\*/g, "<b>$1</b>"))).join("");
  }
  function add(cls, html) {
    const d = document.createElement("div"); d.className = "cc-m " + cls; d.innerHTML = html;
    log.append(d); log.scrollTop = log.scrollHeight; return d;
  }
  function addUser(text, ctx) {
    const picks = (ctx && ctx.picks) || [], n = picks.length;
    const named = picks.filter(p => p.face).map(p => `${p.face.id} ${esc(p.face.name)}`).join(", ");
    add("cc-u", tagFaces(esc(text) + (n ? `<div class="cc-ctx">+ ${named || n + " picked point" + (n > 1 ? "s" : "")}</div>` : "")));
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
    hint.textContent = picking ? "Hover to see a face, click to attach it (+ that exact spot) as F1, F2... Click more faces to add them; click one again to drop it." : "";
    $("cc-pick").classList.toggle("on", picking);
  }
  $("cc-pick").onclick = () => { picking = !picking; setHint(); if (!picking) clearHover(); };
  function renderChips() {
    chipsEl.innerHTML = chips.map((c, i) => `<span class="cc-chip"${c.color ? ` style="border-left:4px solid ${hex(c.color)}"` : ""}>${esc(c.label)}<b data-i="${i}">&times;</b></span>`).join("");
    chipsEl.querySelectorAll("b").forEach(b => b.onclick = () => unpick(+b.dataset.i));
  }
  function unpick(i) {
    const m = markers[i]; if (m && V()) V().scene.remove(m);
    const f = chips[i].face && faces[chips[i].face.id]; if (f && V()) { V().scene.remove(f.overlay); delete faces[f.info.id]; }
    chips.splice(i, 1); markers.splice(i, 1); renderChips();
  }
  /* ---------- faces: a click selects the whole flat (or smoothly curved) surface ----------
     Triangles are welded by position, then grown from the clicked one: coplanar
     neighbours for a flat face, else gently-bending ones (cylinders, fillets).
     Each face gets an id (F1, F2...), a colour and a description for Claude. */
  const COLORS = [0xff7a45, 0x48d6ff, 0xb48cff, 0x7ee081, 0xffd54a, 0xff6fae];
  const faces = {};                                    // id -> {overlay, info, color}
  const hex = c => "#" + c.toString(16).padStart(6, "0");

  function adjacency(g) {
    if (g.userData.ccAdj) return g.userData.ccAdj;
    const pos = g.attributes.position.array, idx = g.index ? g.index.array : null;
    const nt = (idx ? idx.length : pos.length / 3) / 3, corner = i => idx ? idx[i] : i;
    const weld = new Map(), vid = new Int32Array(nt * 3);
    for (let i = 0; i < nt * 3; i++) {
      const j = corner(i) * 3;
      const k = Math.round(pos[j] * 1e3) + "," + Math.round(pos[j + 1] * 1e3) + "," + Math.round(pos[j + 2] * 1e3);
      let id = weld.get(k); if (id === undefined) weld.set(k, id = weld.size); vid[i] = id;
    }
    const nv = weld.size, edges = new Map(), nb = new Int32Array(nt * 3).fill(-1);
    const nrm = new Float32Array(nt * 3), area = new Float32Array(nt);
    for (let t = 0; t < nt; t++) {
      const a = corner(t * 3) * 3, b = corner(t * 3 + 1) * 3, c = corner(t * 3 + 2) * 3;
      const ux = pos[b] - pos[a], uy = pos[b + 1] - pos[a + 1], uz = pos[b + 2] - pos[a + 2];
      const vx = pos[c] - pos[a], vy = pos[c + 1] - pos[a + 1], vz = pos[c + 2] - pos[a + 2];
      let nx = uy * vz - uz * vy, ny = uz * vx - ux * vz, nz = ux * vy - uy * vx;
      const l = Math.hypot(nx, ny, nz) || 1; area[t] = l / 2;
      nrm[t * 3] = nx / l; nrm[t * 3 + 1] = ny / l; nrm[t * 3 + 2] = nz / l;
      for (let e = 0; e < 3; e++) {
        const p = vid[t * 3 + e], q = vid[t * 3 + (e + 1) % 3], key = Math.min(p, q) * nv + Math.max(p, q);
        const o = edges.get(key);
        if (o === undefined) edges.set(key, t * 3 + e);
        else { nb[t * 3 + e] = Math.floor(o / 3); nb[o] = t; }
      }
    }
    return g.userData.ccAdj = {nt, nb, nrm, area, corner};
  }

  function grow(A, seed, ok) {
    const seen = new Uint8Array(A.nt), out = [seed], dot = (s, t) =>
      A.nrm[s * 3] * A.nrm[t * 3] + A.nrm[s * 3 + 1] * A.nrm[t * 3 + 1] + A.nrm[s * 3 + 2] * A.nrm[t * 3 + 2];
    seen[seed] = 1;
    for (let i = 0; i < out.length; i++)
      for (let e = 0; e < 3; e++) {
        const n = A.nb[out[i] * 3 + e];
        if (n >= 0 && !seen[n] && ok(dot(n, out[i]), dot(n, seed))) { seen[n] = 1; out.push(n); }
      }
    return out;
  }

  function sideName(n) {                               // file frame: +Z up, +Y back, +X right
    const a = [Math.abs(n[0]), Math.abs(n[1]), Math.abs(n[2])], i = a.indexOf(Math.max(...a)), s = n[i] >= 0;
    const word = [s ? "right" : "left", s ? "back" : "front", s ? "top" : "bottom"][i];
    return (a[i] > 0.97 ? word : "sloped " + word) + " (" + (s ? "+" : "-") + "XYZ"[i] + ")";
  }

  // The face (triangle list) around a raycast hit.
  function regionOf(hit) {
    const A = adjacency(hit.object.geometry);
    const flat = grow(A, hit.faceIndex, (_, s) => s > 0.9994);             // within 2 deg of the clicked plane
    const tris = flat.length >= 4 ? flat : grow(A, hit.faceIndex, (n, s) => n > 0.978 && s > 0.5);  // 12 / 60 deg
    return {obj: hit.object, A, tris, flat: tris === flat, has: new Set(tris)};
  }
  function overlayOf(v, R, color, opacity) {
    const T = v.THREE, pos = R.obj.geometry.attributes.position, w = new T.Vector3();
    const verts = new Float32Array(R.tris.length * 9);
    R.tris.forEach((t, k) => { for (let e = 0; e < 3; e++) {
      w.fromBufferAttribute(pos, R.A.corner(t * 3 + e)).applyMatrix4(R.obj.matrixWorld); verts.set([w.x, w.y, w.z], k * 9 + e * 3); } });
    const og = new T.BufferGeometry(); og.setAttribute("position", new T.BufferAttribute(verts, 3));
    const o = new T.Mesh(og, new T.MeshBasicMaterial({color, transparent: true, opacity, side: T.DoubleSide,
      depthWrite: false, polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2}));
    o.renderOrder = 998; v.scene.add(o); return o;
  }

  // Select the face under a raycast hit: highlight it and describe it in file coordinates.
  function faceAt(v, hit, R) {
    R = R || regionOf(hit);
    const T = v.THREE, obj = R.obj, A = R.A, tris = R.tris;
    const pos = obj.geometry.attributes.position, w = new T.Vector3(), W = obj.matrixWorld;
    const F = p => (v.toFile ? v.toFile([p.x, p.y, p.z]) : [p.x, p.y, p.z]);
    const lo = [1e9, 1e9, 1e9], hi = [-1e9, -1e9, -1e9];
    const c = [0, 0, 0], nl = new T.Vector3(), M = [0, 0, 0, 0, 0, 0, 0, 0, 0]; let area = 0;
    tris.forEach((t, k) => {
      const tc = [0, 0, 0];
      for (let e = 0; e < 3; e++) {
        w.fromBufferAttribute(pos, A.corner(t * 3 + e)).applyMatrix4(W);
        F(w).forEach((x, i) => { lo[i] = Math.min(lo[i], x); hi[i] = Math.max(hi[i], x); tc[i] += x / 3; });
      }
      tc.forEach((x, i) => c[i] += x * A.area[t]); area += A.area[t];
      nl.x += A.nrm[t * 3] * A.area[t]; nl.y += A.nrm[t * 3 + 1] * A.area[t]; nl.z += A.nrm[t * 3 + 2] * A.area[t];
      for (let i = 0; i < 9; i++) M[i] += A.nrm[t * 3 + (i / 3 | 0)] * A.nrm[t * 3 + i % 3] * A.area[t];
    });
    c.forEach((x, i) => c[i] = x / area);
    // directions into the file frame: map a short step through the same transforms as the points
    const c0 = new T.Vector3().fromBufferAttribute(pos, A.corner(tris[0] * 3)).applyMatrix4(W), a0 = F(c0);
    const toFile = d => { const n = F(c0.clone().add(d.clone().transformDirection(W))).map((x, i) => x - a0[i]);
                          const l = Math.hypot(...n) || 1; return n.map(x => +(x / l).toFixed(3)); };
    const spread = nl.length() / area, normal = toFile(nl.normalize()), kind = R.flat ? "flat" : "curved";
    let side = sideName(normal), axis = null;
    if (kind === "curved" && spread < 0.7) {           // wraps round (bore, boss, fillet): name it by its axis,
      const tr = M[0] + M[4] + M[8], ax = new T.Vector3(1, 0.7, 0.3);   // the direction its normals avoid
      for (let k = 0; k < 40; k++) ax.set(tr * ax.x - (M[0] * ax.x + M[1] * ax.y + M[2] * ax.z),
        tr * ax.y - (M[3] * ax.x + M[4] * ax.y + M[5] * ax.z), tr * ax.z - (M[6] * ax.x + M[7] * ax.y + M[8] * ax.z)).normalize();
      const a = axis = toFile(ax), m = a.map(Math.abs), i = m.indexOf(Math.max(...m));
      side = m[i] > 0.97 ? `around the ${"XYZ"[i]} axis` : `around axis (${a.join(", ")})`;
    }
    const custom = v.surfaceName ? v.surfaceName(c, new T.Vector3(...normal)) : null;
    const id = "F" + (+(recall("cc.faceSeq") || 0) + 1); store("cc.faceSeq", id.slice(1));
    const color = COLORS[(+id.slice(1) - 1) % COLORS.length];
    const r2 = x => +x.toFixed(2), size = hi.map((x, i) => x - lo[i]).filter(x => x > 0.05).map(x => x.toFixed(0));
    const info = {id, name: (custom && !/_surface$/.test(custom) ? custom + " - " : "") + kind + " " + side + " face",
                  kind, normal, area_mm2: +area.toFixed(1), centroid_mm: c.map(r2), bounds_mm: [lo.map(r2), hi.map(r2)],
                  triangles: tris.length, sub_body: v.meshes().length > 1 ? v.meshes().indexOf(obj) : null};
    if (axis) info.axis = axis;
    if (kind === "flat") info.plane_offset_mm = r2(normal.reduce((s, x, i) => s + x * c[i], 0));   // normal . p = offset
    info.label = `${id} · ${info.name} · ${size.join(" × ")} mm`;
    faces[id] = {overlay: overlayOf(v, R, color, 0.55), info, color, region: R};
    return faces[id];
  }
  window.__faceAt = (hit, v) => faceAt(v || V(), hit);     // the configurator's "Name surface" uses this too

  // Face ids in messages ("F2") become coloured tags; clicking one toggles its highlight.
  function tagFaces(html) {
    return html.replace(/\bF(\d+)\b/g, (m) => faces[m] ? `<span class="cc-f" data-f="${m}" style="background:${hex(faces[m].color)}">${m}</span>` : m);
  }
  log.addEventListener("click", e => {
    const f = e.target.dataset && faces[e.target.dataset.f]; if (!f) return;
    const sc = V() && V().scene; if (!sc) return;
    f.overlay.parent ? sc.remove(f.overlay) : sc.add(f.overlay);
  });

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
    // clicking a face that is already picked un-picks it
    const again = chips.findIndex(c => { const f = c.face && faces[c.face.id];
      return f && f.region.obj === hit.object && f.region.has.has(hit.faceIndex); });
    if (again >= 0) { unpick(again); return; }
    const p = [hit.point.x, hit.point.y, hit.point.z];
    const fp = (v.toFile ? v.toFile(p) : p).map(x => +x.toFixed(2));
    const n = hit.face ? hit.face.normal.clone() : null;
    const info = v.info();
    const sub = v.meshes().length > 1 ? v.meshes().indexOf(hit.object) : null;
    const face = hit.faceIndex != null ? faceAt(v, hit, hover && hover.R.has.has(hit.faceIndex) && hover.R.obj === hit.object ? hover.R : null) : null;
    clearHover();
    const surface = face ? face.info.name : v.surfaceName && n ? v.surfaceName(fp, n) : null;
    chips.push({label: face ? face.info.label : `${surface || info.variant || info.file || "part"} @ (${fp.map(x => x.toFixed(1)).join(", ")})`,
                color: face && face.color,
                part: info.variant || info.file, sub_body: sub, point_mm: fp,
                surface_name: surface, face: face ? (({label, ...f}) => f)(face.info) : null,
                surface_normal: n ? [n.x, n.y, n.z].map(x => +x.toFixed(3)) : null});
    const s = new T.Mesh(new T.SphereGeometry(Math.max(1.2, (v.camera.position.distanceTo(hit.point)) / 150), 16, 12),
                         new T.MeshBasicMaterial({color: 0xff7a45, depthTest: false}));
    s.position.copy(hit.point); s.renderOrder = 999; v.scene.add(s); markers.push(s);
    renderChips();
  }, true);

  // While picking, the face under the pointer glows cyan before you click it.
  let hover = null, hoverBusy = false;
  function clearHover() { if (hover) { hover.o.parent && hover.o.parent.remove(hover.o); hover.o.geometry.dispose(); hover = null; } }
  document.addEventListener("pointermove", e => {
    const v = V();
    if (!picking || !v || e.target !== v.canvas || e.buttons) { clearHover(); return; }
    if (hoverBusy) return;
    hoverBusy = true;
    requestAnimationFrame(() => {
      hoverBusy = false;
      const T = v.THREE, r = v.canvas.getBoundingClientRect(), ray = new T.Raycaster();
      ray.setFromCamera(new T.Vector2(((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1), v.camera);
      const hit = ray.intersectObjects(v.meshes(), false)[0];
      if (!hit || hit.faceIndex == null) return clearHover();
      if (hover && hover.R.obj === hit.object && hover.R.has.has(hit.faceIndex)) return;   // same face
      clearHover();
      const R = regionOf(hit);
      hover = {R, o: overlayOf(v, R, 0x00e5ff, 0.4)};
    });
  }, true);

  /* ---------- sending ---------- */
  async function send() {
    const text = input.value.trim();
    if (!text || busy || !project) return;
    const v = V();
    const ctx = {view: v ? v.info() : null, coordinates: v && v.coords, picks: chips.map(({label, color, ...c}) => c)};
    addUser(text, ctx); input.value = "";
    // faces stay known (their tags in the chat re-highlight them) but leave the view
    chips.forEach(c => c.face && faces[c.face.id] && v && v.scene.remove(faces[c.face.id].overlay));
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
