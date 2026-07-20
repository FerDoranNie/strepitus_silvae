"""Interactive Three.js viewers for detected taxa."""

from __future__ import annotations

import json
from typing import Any

import streamlit.components.v1 as components


# Add URLs here only after verifying that the asset depicts the exact taxon and
# that its license permits this use. Unknown species deliberately use a default.
CURATED_GLB_MODELS: dict[str, str] = {}


def curated_model_url(scientific_name: str) -> str | None:
    """Return an explicitly reviewed species model, never an unverified search result."""
    return CURATED_GLB_MODELS.get(scientific_name.casefold())


def infer_visual_group(scientific_name: str, common_name: str) -> str:
    """Choose a cautious generic silhouette when no curated model exists."""
    text = f"{scientific_name} {common_name}".casefold()
    if any(word in text for word in (
        "bird", "ave", "hawk", "eagle", "owl", "parrot", "duck", "turkey", "blackbird",
        "pato", "ganso", "cisne", "garza", "pelícano", "colibrí", "gorrión",
    )):
        return "ave"
    if any(word in text for word in ("snake", "serpent", "lizard", "iguana", "turtle", "crocod", "reptil", "víbora")):
        return "reptil"
    if any(word in text for word in ("frog", "toad", "salamander", "rana", "sapo")):
        return "anfibio"
    return "mamífero"


def visual_group_for_renderer(renderer_id: str | None, scientific_name: str, common_name: str) -> str:
    """Keep broad UI labels separate from the more specific model factory."""
    if renderer_id == "bird_waterfowl":
        return "ave acuática"
    if renderer_id == "bird_passerine":
        return "ave paseriforme"
    if renderer_id and renderer_id.startswith("bird_"):
        return "ave"
    return infer_visual_group(scientific_name, common_name)


def _safe_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False).replace("</", "<\\/")


def render_species_model(scientific_name: str, common_name: str, renderer_id: str | None = None) -> tuple[str, bool]:
    """Render a navigable stylized 3D specimen and report whether it is curated."""
    model_url = curated_model_url(scientific_name)
    visual_group = visual_group_for_renderer(renderer_id, scientific_name, common_name)
    data = _safe_json({
        "group": visual_group,
        "renderer_id": renderer_id,
        "name": common_name or scientific_name,
        "scientific_name": scientific_name,
        "model_url": model_url,
    })
    components.html(
        f"""
<div id="species-viewer" style="height:410px;position:relative;overflow:hidden;border-radius:12px;background:linear-gradient(#173928,#091b13)">
  <div id="loading" style="position:absolute;inset:0;display:grid;place-items:center;color:#f1efe8;font:14px Inter,Arial,sans-serif;z-index:2">Preparando espécimen 3D…</div>
  <div id="label" style="position:absolute;left:12px;top:12px;padding:8px 10px;border-radius:8px;background:rgba(6,18,12,.8);color:#f1efe8;font:12px Inter,Arial,sans-serif;z-index:1"></div>
  <div style="position:absolute;right:12px;bottom:12px;padding:7px 9px;border-radius:8px;background:rgba(6,18,12,.8);color:#f1efe8;font:11px Inter,Arial,sans-serif;z-index:1">Arrastra para rotar · rueda para acercar</div>
</div>
<script type="importmap">{{"imports": {{"three": "https://cdn.jsdelivr.net/npm/three@0.180.0/build/three.module.js"}}}}</script>
<script>
  const loadingMessage = document.getElementById('loading');
  window.addEventListener('error', () => {{ loadingMessage.textContent = 'No fue posible cargar el visor 3D. Recarga la página.'; }}, true);
  window.addEventListener('unhandledrejection', () => {{ loadingMessage.textContent = 'No fue posible iniciar el visor 3D. Recarga la página.'; }});
</script>
<script type="module">
  import * as THREE from 'three';
  import {{ OrbitControls }} from 'https://cdn.jsdelivr.net/npm/three@0.180.0/examples/jsm/controls/OrbitControls.js';
  const data = {data};
  const root = document.getElementById('species-viewer');
  document.getElementById('label').textContent = `Representación estilizada: ${{data.group}}`;
  const scene = new THREE.Scene();
  scene.fog = new THREE.Fog('#10281b', 12, 35);
  const camera = new THREE.PerspectiveCamera(42, root.clientWidth / root.clientHeight, .1, 100);
  camera.position.set(7, 4.8, 8);
  const renderer = new THREE.WebGLRenderer({{antialias:true, alpha:true}});
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2)); renderer.setSize(root.clientWidth, root.clientHeight);
  renderer.shadowMap.enabled = true; root.appendChild(renderer.domElement);
  scene.add(new THREE.HemisphereLight('#d8f5d8', '#102318', 2.4));
  const light = new THREE.DirectionalLight('#fff2cb', 2.5); light.position.set(5, 8, 5); light.castShadow = true; scene.add(light);
  const controls = new OrbitControls(camera, renderer.domElement); controls.enableDamping = true; controls.target.set(0, 1.25, 0); controls.minDistance = 4; controls.maxDistance = 20;
  const ground = new THREE.Mesh(new THREE.CircleGeometry(4.6, 48), new THREE.MeshStandardMaterial({{color:'#315d31', roughness:1}})); ground.rotation.x = -Math.PI / 2; ground.receiveShadow = true; scene.add(ground);
  const body = new THREE.MeshStandardMaterial({{color:'#c98b4c', roughness:.83}}), dark = new THREE.MeshStandardMaterial({{color:'#53351e', roughness:.9}}), accent = new THREE.MeshStandardMaterial({{color:'#e9d4a6', roughness:.75}});
  function mesh(geometry, material, position, scale=[1,1,1], rotation=[0,0,0]) {{ const object = new THREE.Mesh(geometry, material); object.position.set(...position); object.scale.set(...scale); object.rotation.set(...rotation); object.castShadow=true; scene.add(object); return object; }}
  function mammal() {{
    mesh(new THREE.SphereGeometry(1, 28, 20), body, [0,1.45,0], [1.45,.8,.72]); mesh(new THREE.SphereGeometry(.62,24,18), body, [1.2,1.8,0], [.9,.9,.85]);
    mesh(new THREE.ConeGeometry(.28,.7,4), dark, [1.65,1.75,0], [1,1,1], [0,0,Math.PI/2]);
    [[-.7,.7],[-.7,-.7],[.65,.62],[.65,-.62]].forEach(([x,z]) => mesh(new THREE.CylinderGeometry(.11,.15,1.25,8), dark, [x,.65,z]));
    mesh(new THREE.ConeGeometry(.18,.85,10), dark, [-1.5,1.45,0], [1,1,1], [0,0,-Math.PI/2]);
    mesh(new THREE.SphereGeometry(.2,16,12), accent, [1.55,2.05,.5]); mesh(new THREE.SphereGeometry(.2,16,12), accent, [1.55,2.05,-.5]);
  }}
  function bird() {{
    mesh(new THREE.SphereGeometry(1,28,20), body, [0,1.75,0], [.85,1.35,.72]); mesh(new THREE.SphereGeometry(.52,24,18), body, [0,3,0], [.9,.9,.9]);
    mesh(new THREE.ConeGeometry(.25,.75,4), accent, [0,2.95,.65], [1,1,1], [Math.PI/2,0,0]);
    mesh(new THREE.ConeGeometry(.8,1.8,12), dark, [0,1.75,-.65], [1,.75,1], [-Math.PI/2,0,0]);
    [[-.85,1.9,0],[.85,1.9,0]].forEach(([x,y,z]) => mesh(new THREE.SphereGeometry(.72,20,16), dark, [x,y,z], [.35,1,.25], [0,0,x > 0 ? -.55:.55]));
    [[-.23,0],[.23,0]].forEach(([x,z]) => mesh(new THREE.CylinderGeometry(.045,.045,1.2,6), dark, [x,.6,z]));
  }}
  function waterfowl() {{
    // Stylized from the supplied side-view: a low diving-duck silhouette,
    // pale cheek patch, yellow eye, and broad blue-grey bill.
    const plumage = new THREE.MeshStandardMaterial({{color:'#1e2926', roughness:.68}});
    const chest = new THREE.MeshStandardMaterial({{color:'#303a35', roughness:.78}});
    const wing = new THREE.MeshStandardMaterial({{color:'#151d1a', roughness:.73}});
    const cheek = new THREE.MeshStandardMaterial({{color:'#d9d4bd', roughness:.82}});
    const bill = new THREE.MeshStandardMaterial({{color:'#778f94', roughness:.46, metalness:.05}});
    const iris = new THREE.MeshPhysicalMaterial({{color:'#e8c653', roughness:.18, clearcoat:.45}});
    const water = new THREE.Mesh(new THREE.CircleGeometry(4.45, 56), new THREE.MeshPhysicalMaterial({{color:'#1b6268', roughness:.31, metalness:.04, clearcoat:.25, transparent:true, opacity:.82}}));
    water.rotation.x = -Math.PI / 2; water.position.y=.018; water.receiveShadow=true; scene.add(water);
    mesh(new THREE.SphereGeometry(1,32,22), plumage, [-.15,1.23,0], [1.58,.74,.74]);
    mesh(new THREE.SphereGeometry(1,28,20), chest, [.65,1.34,0], [.74,.78,.69]);
    mesh(new THREE.SphereGeometry(1,28,20), plumage, [1.16,1.75,0], [.56,.64,.58]);
    mesh(new THREE.SphereGeometry(.72,26,18), wing, [-.38,1.36,.48], [1.1,.47,.15], [0,.16,-.12]);
    mesh(new THREE.SphereGeometry(.72,26,18), wing, [-.38,1.36,-.48], [1.1,.47,.15], [0,.16,.12]);
    mesh(new THREE.ConeGeometry(.48,1.15,12), plumage, [-1.48,1.26,0], [.72,.48,.7], [0,0,-Math.PI/2]);
    mesh(new THREE.BoxGeometry(.62,.2,.48), bill, [1.62,1.76,0]);
    mesh(new THREE.SphereGeometry(.22,18,14), cheek, [1.08,1.76,.48], [1,.78,.25]);
    mesh(new THREE.SphereGeometry(.22,18,14), cheek, [1.08,1.76,-.48], [1,.78,.25]);
    [[1.38,1.93,.48],[1.38,1.93,-.48]].forEach(([x,y,z]) => mesh(new THREE.SphereGeometry(.09,16,12), iris,[x,y,z]));
    [[-.32,.2],[.2,.2]].forEach(([x,z]) => mesh(new THREE.CylinderGeometry(.05,.065,.52,8), dark,[x,.42,z]));
  }}
  function passerine() {{
    // Perching-songbird archetype: compact body, pointed bill, long tail,
    // folded wings and grasping feet visibly attached to a branch.
    const isVermilionFlycatcher = String(data.scientific_name || '').toLowerCase() === 'pyrocephalus rubinus';
    const plumage = new THREE.MeshStandardMaterial({{color:isVermilionFlycatcher ? '#d94332' : '#8c4a35', roughness:.72}});
    const wing = new THREE.MeshStandardMaterial({{color:'#3b302d', roughness:.78}});
    const throat = new THREE.MeshStandardMaterial({{color:isVermilionFlycatcher ? '#eb5b47' : '#d7a88d', roughness:.82}});
    const bill = new THREE.MeshStandardMaterial({{color:'#25272a', roughness:.42}});
    const eye = new THREE.MeshPhysicalMaterial({{color:'#0d0d0d', roughness:.13, clearcoat:.6}});
    const branch = new THREE.Mesh(new THREE.CylinderGeometry(.105,.15,5.2,10), new THREE.MeshStandardMaterial({{color:'#6d4328', roughness:.94}}));
    branch.rotation.z=Math.PI/2; branch.position.set(0,.67,0); branch.castShadow=true; branch.receiveShadow=true; scene.add(branch);
    mesh(new THREE.SphereGeometry(1,28,20), plumage, [0,1.62,0], [.72,.92,.62]);
    mesh(new THREE.SphereGeometry(.58,26,18), plumage, [.55,2.27,0], [.82,.9,.82]);
    mesh(new THREE.SphereGeometry(.56,22,16), throat, [.48,1.89,.44], [.72,.98,.16]);
    mesh(new THREE.ConeGeometry(.14,.6,8), bill, [1.08,2.25,0], [1,1,1], [0,0,-Math.PI/2]);
    [[.77,2.42,.43],[.77,2.42,-.43]].forEach(([x,y,z]) => mesh(new THREE.SphereGeometry(.075,14,10), eye,[x,y,z]));
    mesh(new THREE.SphereGeometry(.68,22,16), wing, [-.22,1.66,.48], [.8,1.18,.16], [0,.16,.15]);
    mesh(new THREE.SphereGeometry(.68,22,16), wing, [-.22,1.66,-.48], [.8,1.18,.16], [0,.16,-.15]);
    mesh(new THREE.ConeGeometry(.3,1.48,10), wing, [-.82,1.51,0], [.62,.48,.66], [0,0,-Math.PI/2]);
    [[-.12,.22], [.18,.22]].forEach(([x,z]) => {{
      mesh(new THREE.CylinderGeometry(.035,.045,.67,8), bill,[x,.97,z]);
      mesh(new THREE.TorusGeometry(.1,.018,6,10,Math.PI), bill,[x,.7,z],[1,1,1],[Math.PI/2,0,0]);
    }});
  }}
  function reptile() {{
    for (let i=0;i<9;i+=1) {{ const x=-2.4+i*.58, y=.72+Math.sin(i*.65)*.13; mesh(new THREE.SphereGeometry(.62,20,14), body, [x,y,Math.sin(i*.65)*.38], [1.2,.55,.62]); }}
    mesh(new THREE.ConeGeometry(.55,1.25,6), dark, [2.65,.75,-.22], [1,.7,1], [0,0,-Math.PI/2]);
  }}
  function amphibian() {{ mesh(new THREE.SphereGeometry(1,28,20), body,[0,1.05,0],[1.25,.6,.9]); [[-.9,.45],[.9,.45],[-.9,-.45],[.9,-.45]].forEach(([x,z])=>mesh(new THREE.SphereGeometry(.38,18,12),dark,[x,.65,z],[1.6,.35,.55])); mesh(new THREE.SphereGeometry(.35,18,12),accent,[.55,1.4,.45]); mesh(new THREE.SphereGeometry(.35,18,12),accent,[.55,1.4,-.45]); }}
  (data.renderer_id === 'bird_waterfowl' ? waterfowl : data.renderer_id === 'bird_passerine' ? passerine : ({{'ave':bird,'reptil':reptile,'anfibio':amphibian,'mamífero':mammal}}[data.group] || mammal))();
  function resize() {{ camera.aspect=root.clientWidth/root.clientHeight; camera.updateProjectionMatrix(); renderer.setSize(root.clientWidth,root.clientHeight); }}
  new ResizeObserver(resize).observe(root);
  function animate() {{ requestAnimationFrame(animate); controls.update(); renderer.render(scene,camera); }}
  document.getElementById('loading').remove(); animate();
</script>
        """,
        height=420,
        scrolling=False,
    )
    return visual_group, bool(model_url)
