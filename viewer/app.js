import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

const viewport = document.querySelector('#viewport');
const text = (id, value) => { document.getElementById(id).textContent = value; };
const format = value => Number(value.toFixed(2)).toLocaleString('vi-VN');
const labels = { perspective: 'Phối cảnh', front: 'Mặt đứng', right: 'Mặt cạnh', top: 'Mặt bằng', back: 'Mặt sau' };
let renderer, camera, controls, center, boxSize, resizeObserver;
const state = { ready: false, currentView: null, camera: null, controls: null, error: null };
window.hgViewer = state;

function setView(name) {
  if (!state.ready) return;
  const directions = { perspective: [1.4, -2, 1.1], front: [0, -1, 0], right: [1, 0, 0], top: [0, -0.001, 1], back: [0, 1, 0] };
  const direction = new THREE.Vector3(...directions[name]).normalize();
  const fov = THREE.MathUtils.degToRad(camera.fov);
  const distance = Math.max(boxSize.x, boxSize.y, boxSize.z) / (2 * Math.tan(fov / 2)) * Math.max(1, 1 / camera.aspect) * 1.45;
  controls.target.copy(center);
  camera.position.copy(center).addScaledVector(direction, distance);
  camera.lookAt(center);
  controls.update();
  state.currentView = name;
  text('active-view', labels[name]);
  document.querySelectorAll('[data-view]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.view === name)));
}

function zoom(factor) {
  if (!state.ready) return;
  const offset = camera.position.clone().sub(controls.target);
  const distance = THREE.MathUtils.clamp(offset.length() * factor, controls.minDistance, controls.maxDistance);
  camera.position.copy(controls.target).add(offset.setLength(distance));
  controls.update();
}

function validateReport(report) {
  if (!Array.isArray(report.design_mm) || report.design_mm.length !== 3 || !report.design_mm.every(v => typeof v === 'number' && Number.isFinite(v) && v > 0)) throw new Error('Báo cáo thiếu kích thước hợp lệ.');
  if (!Number.isFinite(report.tolerance_mm) || report.tolerance_mm < 0) throw new Error('Dung sai không hợp lệ.');
  if (!Array.isArray(report.objects) || !report.objects.length || !Array.isArray(report.unknown_details) || !report.unknown_details.every(v => typeof v === 'string')) throw new Error('Báo cáo thiếu dữ liệu kiểm định.');
  for (const object of report.objects) {
    if (typeof object.id !== 'string' || !Array.isArray(object.dimensions_mm) || object.dimensions_mm.length !== 3 || !object.dimensions_mm.every(v => Number.isFinite(v) && v > 0)) throw new Error('Báo cáo bộ phận không hợp lệ.');
  }
}

async function start() {
  const scene = new THREE.Scene();
  camera = new THREE.PerspectiveCamera(38, 1, 0.01, 100);
  camera.up.set(0, 0, 1);
  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  viewport.appendChild(renderer.domElement);
  renderer.domElement.setAttribute('aria-label', 'Mô hình GLB tương tác: kéo để xoay, hai ngón hoặc con lăn để zoom');
  controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.minDistance = 0.3;
  controls.maxDistance = 20;
  scene.add(new THREE.HemisphereLight(0xf7f0dc, 0x4b5145, 3));
  const light = new THREE.DirectionalLight(0xffffff, 3);
  light.position.set(3, -4, 5); scene.add(light);
  const reportResponse = await fetch('./assets/sample-qa.json');
  if (!reportResponse.ok) throw new Error('Không tải được báo cáo kiểm định.');
  const report = await reportResponse.json();
  validateReport(report);
  const gltf = await new GLTFLoader().loadAsync('./assets/sample.glb');
  // glTF is Y-up; the HG design/QA contract uses X width, Y depth, Z height.
  gltf.scene.rotation.x = Math.PI / 2;
  scene.add(gltf.scene);
  gltf.scene.updateMatrixWorld(true);
  const box = new THREE.Box3().setFromObject(gltf.scene);
  if (box.isEmpty()) throw new Error('GLB không có hình học để kiểm tra.');
  center = box.getCenter(new THREE.Vector3());
  boxSize = box.getSize(new THREE.Vector3());
  const measured = boxSize.toArray().map(v => v * 1000);
  if (!measured.every(v => Number.isFinite(v) && v > 0)) throw new Error('Kích thước GLB không hợp lệ.');
  const errors = measured.map((v, i) => Math.abs(v - report.design_mm[i]));
  ['width', 'depth', 'height'].forEach((id, i) => text(id, format(measured[i])));
  text('measurement-note', 'Đo bounding box GLB trực tiếp, đơn vị mm. Dữ liệu mẫu tổng hợp.');
  text('max-error', `${format(Math.max(...errors))} mm`);
  text('tolerance', `${format(report.tolerance_mm)} mm`);
  text('qa-result', Math.max(...errors) <= report.tolerance_mm ? 'Kích thước khớp' : 'SAI LỆCH');
  const meshes = [];
  gltf.scene.traverse(object => { if (object.isMesh) meshes.push(object); });
  text('mesh-count', String(meshes.length));
  text('object-count', `${report.objects.length} bộ phận · ${meshes.length} mesh`);
  const unknownList = document.querySelector('#unknown-list'); unknownList.replaceChildren();
  for (const value of report.unknown_details.length ? report.unknown_details : ['Chưa có đủ chứng cứ nghiệm thu hình học.']) {
    const item = document.createElement('li'); item.textContent = value; unknownList.appendChild(item);
  }
  const rows = document.querySelector('#object-rows'); rows.replaceChildren();
  for (const object of report.objects) {
    const partMeshes = meshes.filter(mesh => mesh.name === `${object.id}_body` || mesh.name === object.id);
    const partBox = new THREE.Box3();
    partMeshes.forEach(mesh => partBox.union(new THREE.Box3().setFromObject(mesh)));
    const actual = partBox.isEmpty() ? null : partBox.getSize(new THREE.Vector3()).toArray().map(v => v * 1000);
    const mismatch = !actual || actual.some((v, i) => Math.abs(v - object.dimensions_mm[i]) > report.tolerance_mm);
    const row = document.createElement('tr');
    const dataState = object.confidence === 'confirmed' ? 'Số đo xác nhận' : object.confidence === 'inferred' ? 'Suy luận' : 'CẦN XÁC NHẬN';
    for (const value of [object.label || object.id, actual ? actual.map(format).join(' × ') : 'Không tìm thấy mesh', dataState, mismatch ? 'SAI LỆCH · CẦN XÁC NHẬN' : 'CẦN XÁC NHẬN']) {
      const cell = document.createElement('td'); cell.textContent = value; row.appendChild(cell);
    }
    row.lastElementChild.className = 'pending'; rows.appendChild(row);
  }
  const grid = new THREE.GridHelper(5, 20, 0x64705c, 0x3e493b);
  grid.rotation.x = Math.PI / 2; grid.position.z = box.min.z - 0.003; scene.add(grid);
  const resize = () => {
    const rect = viewport.getBoundingClientRect();
    const width=Math.max(1,rect.width),height=Math.max(1,rect.height);
    camera.aspect=width/height;camera.updateProjectionMatrix();renderer.setSize(width,height);
  };
  resizeObserver = new ResizeObserver(resize); resizeObserver.observe(viewport); resize();
  state.ready = true; state.camera = camera; state.controls = controls; state.measured_mm = measured;
  setView('perspective'); document.querySelector('#loading').hidden = true;
  renderer.setAnimationLoop(() => { controls.update(); renderer.render(scene, camera); });

  let localRoot = null;
  // Snapshot only publicly reviewed sample labels, to restore a meaningful viewer when photos are cleared.
  const sampleIds=['width','depth','height','measurement-note','max-error','tolerance','qa-result','mesh-count','object-count'];
  const sampleText=Object.fromEntries(sampleIds.map(id=>[id,document.getElementById(id).textContent]));
  const sampleRows=document.querySelector('#object-rows').cloneNode(true);
  const sampleUnknowns=document.querySelector('#unknown-list').cloneNode(true);
  const sampleOriginCenter=center.clone(),sampleOriginSize=boxSize.clone();
  state.restorePublicSample = () => {
    if(!state.ready)return false;
    if(localRoot){scene.remove(localRoot);localRoot=null;}
    gltf.scene.visible=true;
    center.copy(sampleOriginCenter);boxSize.copy(sampleOriginSize);
    camera.near=.01;camera.far=100;camera.updateProjectionMatrix();
    controls.minDistance=.3;controls.maxDistance=20;
    for(const id of sampleIds)text(id,sampleText[id]);
    document.querySelector('#object-rows').replaceChildren(...[...sampleRows.children].map(x=>x.cloneNode(true)));
    document.querySelector('#unknown-list').replaceChildren(...[...sampleUnknowns.children].map(x=>x.cloneNode(true)));
    document.querySelector('#sample-viewer h1').textContent='Console Luxury';
    document.querySelector('#sample-viewer .subtitle').textContent='Khối bao thiết kế · Gỗ tối màu & chân kim loại';
    document.querySelector('#sample-viewer .review-badge').textContent='● CẦN XÁC NHẬN';
    for(const id of ['hg-download-glb','hg-download-fbx'])document.getElementById(id).hidden=true;
    state.displayMode='public_sample';state.localMeshes=undefined;state.measured_mm=sampleOriginSize.toArray().map(x=>x*1000);
    setView('perspective');
    return true;
  };
  // A freshly selected photo must NEVER be visually associated with the old sample/model.
  state.clearForNewSource = () => {
    if(!state.ready)return false;
    if(localRoot){scene.remove(localRoot);localRoot=null;}
    gltf.scene.visible=false;
    center.set(0,0,0);boxSize.set(1,1,1);
    camera.near=.01;camera.far=100;camera.updateProjectionMatrix();
    controls.minDistance=.1;controls.maxDistance=20;
    ['width','depth','height','max-error','tolerance','mesh-count'].forEach(id=>text(id,'—'));
    text('qa-result','CHƯA PHÂN TÍCH ẢNH');
    text('object-count','Chưa có hình học từ ảnh mới');
    text('measurement-note','Ảnh đã nhận, nhưng hình dáng và kích thước từ ảnh chưa được AI xác nhận. Chưa tạo mô hình theo ảnh.');
    const list=document.querySelector('#unknown-list');list.replaceChildren();
    const li=document.createElement('li');li.textContent='Ảnh vừa chọn chưa được ChatGPT phân tích; không sử dụng lại mô hình mẫu/bản nháp cũ.';list.append(li);
    document.querySelector('#object-rows').replaceChildren();
    document.querySelector('#sample-viewer h1').textContent='CHỜ PHÂN TÍCH ẢNH';
    document.querySelector('#sample-viewer .subtitle').textContent='Ảnh đã nhận ở trình duyệt · chưa tạo mô hình theo ảnh';
    document.querySelector('#sample-viewer .review-badge').textContent='● CHƯA NHẬN DIỆN';
    for(const id of ['hg-download-glb','hg-download-fbx'])document.getElementById(id).hidden=true;
    state.displayMode='awaiting_photo_analysis';state.localMeshes=0;state.measured_mm=null;
    setView('perspective');
    return true;
  };
  // Display local drafts in the SAME viewer as the sample screenshot, without altering public source assets.
  // Three.js editors use Y-up; the original QA viewer uses Z-up.
  state.showLocalDraft = (source, metadata = {}) => {
    if(!state.ready || !source || !source.isObject3D) return false;
    const wrapper = new THREE.Group();
    wrapper.name = 'HG_LOCAL_DRAFT_NEEDS_REVIEW';
    wrapper.rotation.x = Math.PI / 2;
    wrapper.add(source.clone(true));
    wrapper.updateMatrixWorld(true);
    const measuredBox = new THREE.Box3().setFromObject(wrapper);
    if(measuredBox.isEmpty())throw Error('Bản nháp không có hình học');
    const nextSize = measuredBox.getSize(new THREE.Vector3());
    const nextCenter = measuredBox.getCenter(new THREE.Vector3());
    if(!nextSize.toArray().every(x=>Number.isFinite(x)&&x>0))throw Error('Kích thước bản nháp không hợp lệ');
    gltf.scene.visible = false;
    if(localRoot)scene.remove(localRoot);
    localRoot=wrapper;
    scene.add(wrapper);
    center=nextCenter;boxSize=nextSize;
    const scale=Math.max(nextSize.x,nextSize.y,nextSize.z);
    camera.near=Math.max(0.0001,scale/10000);
    camera.far=Math.max(100,scale*50);
    camera.updateProjectionMatrix();
    controls.minDistance=Math.max(.001,scale*.05);
    controls.maxDistance=Math.max(20,scale*35);
    const sizes=nextSize.toArray().map(v=>v*1000);
    ['width','depth','height'].forEach((id,i)=>text(id,format(sizes[i])));
    const parts=[];
    wrapper.traverse(mesh=>{if(mesh.isMesh)parts.push(mesh);});
    text('measurement-note','Đo trực tiếp hình học NHÁP trong trình duyệt, đơn vị mm. Chưa đối chiếu hình dạng với ảnh.');
    text('max-error','Chưa đối chiếu ảnh');
    text('tolerance','Chưa xác định');
    text('qa-result','CẦN XÁC NHẬN');
    text('mesh-count',String(parts.length));
    text('object-count',String(parts.length)+' bộ phận · mô hình nháp');
    const unknownList=document.querySelector('#unknown-list');
    unknownList.replaceChildren();
    const unknowns=Array.isArray(metadata.unknownDetails)?metadata.unknownDetails.slice(0,30):[];
    for(const value of (unknowns.length?unknowns:['Chưa kiểm định cấu tạo và kích thước theo bản vẽ.'])){
      const li=document.createElement('li');li.textContent=String(value).slice(0,400);unknownList.append(li);
    }
    const rows=document.querySelector('#object-rows');rows.replaceChildren();
    for(const mesh of parts.slice(0,80)){
      const bounds=new THREE.Box3().setFromObject(mesh);
      const dimensions=bounds.getSize(new THREE.Vector3()).toArray().map(x=>x*1000);
      const row=document.createElement('tr');
      const cells=[mesh.name||'Bộ phận',dimensions.map(format).join(' × '),'Bản nháp tham số','CẦN XÁC NHẬN'];
      for(const content of cells){const td=document.createElement('td');td.textContent=content;row.append(td);}
      row.lastElementChild.className='pending';rows.append(row);
    }
    document.querySelector('#sample-viewer h1').textContent='MÔ HÌNH 3D · BẢN NHÁP';
    document.querySelector('#sample-viewer .subtitle').textContent=String(metadata.origin||'Dựng trên thiết bị, chưa nghiệm thu');
    document.querySelector('#sample-viewer .review-badge').textContent='● CẦN XÁC NHẬN';
    for(const id of ['hg-download-glb','hg-download-fbx'])document.getElementById(id).hidden=false;
    state.displayMode='local_draft';
    state.measured_mm=sizes;state.localMeshes=parts.length;
    setView('perspective');
    return true;
  };
  controls.addEventListener('start', () => {
    state.currentView = 'free'; text('active-view', 'Góc nhìn tự do');
    document.querySelectorAll('[data-view]').forEach(button => button.setAttribute('aria-pressed', 'false'));
  });
  renderer.domElement.addEventListener('webglcontextlost', event => { event.preventDefault(); fail(new Error('Mất kết nối đồ họa. Hãy tải lại trang.')); });
}

function fail(error) {
  state.ready = false; state.error = error.message;
  renderer?.setAnimationLoop(null); resizeObserver?.disconnect();
  document.querySelector('#loading').hidden = true;
  const alert = document.querySelector('#error'); alert.hidden = false;
  alert.textContent = `Không thể xem mô hình. ${error.message}`;
  text('qa-result', 'CHƯA KIỂM CHỨNG');
}

document.querySelectorAll('[data-view]').forEach(button => button.addEventListener('click', () => setView(button.dataset.view)));
document.querySelector('#zoom-in').addEventListener('click', () => zoom(0.8));
document.querySelector('#zoom-out').addEventListener('click', () => zoom(1.25));
document.querySelector('#reset').addEventListener('click', () => setView('perspective'));
document.querySelector('#hg-download-glb').addEventListener('click',()=>document.querySelector('#cgpt-export-glb').click());
document.querySelector('#hg-download-fbx').addEventListener('click',()=>document.querySelector('#cgpt-export-fbx').click());
start().catch(fail);
