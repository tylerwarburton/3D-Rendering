// Realistic mode for the configurator: path traces what is on screen (three-gpu-pathtracer).
// The configurator runs three r128; this module copies its visible meshes into a modern
// three scene on an overlay canvas, follows its camera, and sharpens while you hold still.
// The copy is a snapshot - call start() again after the scene changes.
import * as T from 'three';
import {WebGLPathTracer, GradientEquirectTexture} from 'three-gpu-pathtracer';

let S = null;                                   // {renderer, pt, scene, cam, canvas, raf, src}

const lin = c => Math.pow(c, 2.2);              // r128 drew vertex colours as-is (no colour management)

function copyGeometry(g0){
  const g = new T.BufferGeometry();
  for(const k of ['position', 'normal', 'color', 'uv']){
    const a = g0.attributes[k];
    if(!a) continue;
    const arr = new a.array.constructor(a.array);
    if(k === 'color') for(let i = 0; i < arr.length; i++) arr[i] = lin(arr[i]);
    g.setAttribute(k, new T.BufferAttribute(arr, a.itemSize, a.normalized));
  }
  if(g0.index) g.setIndex(new T.BufferAttribute(new g0.index.array.constructor(g0.index.array), 1));
  if(!g.attributes.normal) g.computeVertexNormals();
  return g;
}

function copyMaterial(m, part, plastic){
  if(part) return new T.MeshPhysicalMaterial({color: new T.Color(plastic.color), roughness: plastic.glossy ? .12 : .45,
    clearcoat: plastic.glossy ? .6 : .1, clearcoatRoughness: .4, side: T.DoubleSide});
  const o = {color: new T.Color(m.color ? m.color.getHex() : 0xffffff), vertexColors: !!m.vertexColors, side: m.side,
             transparent: !!m.transparent, opacity: m.opacity ?? 1,
             roughness: m.roughness ?? 1, metalness: m.metalness ?? 0};
  if(m.map && m.map.image){                     // gauge faces etc.: canvas textures, lit from within
    o.map = o.emissiveMap = new T.CanvasTexture(m.map.image);
    o.map.colorSpace = T.SRGBColorSpace; o.emissive = new T.Color(0xffffff); o.emissiveIntensity = .7;
  }
  if(m.emissive && m.emissive.getHex()) o.emissive = new T.Color(m.emissive.getHex());
  return new T.MeshStandardMaterial(o);
}

function mirror(v, plastic){
  const src = v.scene, parts = v.meshes(), sc = new T.Scene(), box = new T.Box3();
  src.updateMatrixWorld(true);
  src.traverseVisible(o => {
    if(!o.isMesh || !o.geometry.attributes.position) return;
    const mat = Array.isArray(o.material) ? o.material[0] : o.material;
    if(mat.side === 1 && !parts.includes(o)) return;          // the section's back-face fill
    const m = new T.Mesh(copyGeometry(o.geometry), copyMaterial(mat, parts.includes(o), plastic));
    m.matrixAutoUpdate = false; m.matrix.fromArray(o.matrixWorld.elements);
    sc.add(m);
    if(parts.includes(o)) box.expandByObject(m);
  });
  sc.updateMatrixWorld(true);
  if(box.isEmpty()) box.setFromObject(sc);
  const env = new GradientEquirectTexture();
  env.topColor.set(0xeef4f8); env.bottomColor.set(0x1a2830); env.update();
  sc.environment = env; sc.environmentIntensity = .9;
  sc.background = new T.Color(src.background ? src.background.getHex() : 0x0f1d25);
  const c = box.getCenter(new T.Vector3()), R = box.getSize(new T.Vector3()).length() / 2;
  const key = new T.RectAreaLight(0xffffff, 6, R * 2.5, R * 2.5);
  key.position.set(c.x + R * 2.2, c.y - R * 2.6, c.z + R * 3.2); key.lookAt(c);
  sc.add(key);
  return sc;
}

function syncCamera(){
  const a = S.src.camera, b = S.cam;
  const r = S.src.canvas.getBoundingClientRect();
  if(r.width !== S.w || r.height !== S.h){
    S.w = r.width; S.h = r.height; S.renderer.setSize(r.width, r.height, false);
  }
  const key = a.matrixWorld.elements.join() + a.fov + a.aspect;
  if(key === S.camKey) return;
  S.camKey = key;
  b.position.copy(a.position); b.quaternion.copy(a.quaternion); b.up.copy(a.up);
  b.fov = a.fov; b.aspect = a.aspect; b.near = a.near; b.far = a.far; b.updateProjectionMatrix();
  b.updateMatrixWorld(); S.pt.updateCamera();
}

export function start(v, plastic, onSample){
  stop();
  const canvas = document.createElement('canvas');
  canvas.style.cssText = 'position:absolute;inset:0;width:100%;height:100%;pointer-events:none';
  v.canvas.after(canvas);                       // above the 3D view, under the overlays and buttons
  const renderer = new T.WebGLRenderer({canvas, antialias: true, preserveDrawingBuffer: true});
  renderer.toneMapping = T.ACESFilmicToneMapping;
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  const pt = new WebGLPathTracer(renderer);
  const phone = devicePixelRatio > 1.5;
  pt.tiles.set(phone ? 2 : 1, phone ? 2 : 1); pt.renderScale = phone ? .6 : 1; pt.minSamples = 1; pt.filterGlossyFactor = .5;
  const cam = new T.PerspectiveCamera();
  S = {renderer, pt, cam, canvas, src: v, w: 0, h: 0, camKey: ''};
  const scene = mirror(v, plastic);
  S.scene = scene;
  syncCamera();
  pt.setScene(scene, cam);
  (function loop(){
    if(!S || S.canvas !== canvas) return;
    S.raf = requestAnimationFrame(loop);
    syncCamera();
    pt.renderSample();
    onSample && onSample(pt.isCompiling ? -1 : Math.floor(pt.samples));
  })();
}

export function stop(){
  if(!S) return;
  cancelAnimationFrame(S.raf);
  S.scene.traverse(o => { if(o.isMesh){ o.geometry.dispose(); o.material.dispose(); } });
  S.pt.dispose && S.pt.dispose();
  S.renderer.dispose(); S.canvas.remove();
  S = null;
}

export const active = () => !!S;
