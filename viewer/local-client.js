/** Served ONLY by the loopback Python app, never copied into the Pages artifact. */
import './create-model.js';
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
let token = '', job = null, polling = null, generation = 0, renderer = null, controls = null, observer = null, shownJob = null;
const panel = document.createElement('section'); panel.className = 'card local-panel';
panel.innerHTML = `<h2>Backend cục bộ · chế độ có giám sát</h2><p>AI tự hiểu ảnh: <strong>CHƯA KẾT NỐI</strong>. Chỉ dựng sau khi gửi quan sát đã xác minh.</p><label for="local-token">Token cá nhân (chỉ giữ trong bộ nhớ)</label><input id="local-token" type="password" autocomplete="off"><button id="local-login" type="button">Xác thực</button><button id="local-logout" type="button">Đăng xuất</button><p id="local-status" role="status">Chưa xác thực.</p><label for="verified-observations">JSON quan sát đã kiểm tra từ ảnh (tối đa 512 KB)</label><input id="verified-observations" type="file" accept="application/json,.json"><label><input id="reviewed-check" type="checkbox"> Tôi đã xem ảnh và kiểm tra chứng cứ, phân biệt số đo xác nhận/suy luận</label><button id="submit-observations" type="button" disabled>Gửi dữ liệu đã xác minh</button><button id="refresh-job" type="button" disabled>Cập nhật công việc</button><div id="private-downloads"></div><div id="private-result" hidden><h3>Kết quả riêng tư · CẦN XÁC NHẬN</h3><div id="private-canvas"></div><p id="private-dimensions"></p><pre id="private-qa"></pre></div>`;
document.querySelector('#create-model').prepend(panel);
const el = id => document.getElementById(id);
const status = value => { el('local-status').textContent = value; };
const base = new URL('../', location.href);
function resetPrivate() {
  generation++; clearTimeout(polling); polling = null; job = null;
  renderer?.setAnimationLoop(null); controls?.dispose(); renderer?.dispose(); observer?.disconnect(); renderer = null; controls = null; observer = null; shownJob = null;
  el('private-canvas').replaceChildren(); el('private-downloads').replaceChildren(); el('private-result').hidden = true;
  el('private-qa').textContent = ''; el('private-dimensions').textContent = '';
  el('submit-observations').disabled = true; el('refresh-job').disabled = true; el('rebuild-job').disabled = true;
}
function logout(message = 'Đã đăng xuất, đã xóa token và kết quả khỏi giao diện.') {
  resetPrivate(); token = ''; el('local-token').value = '';
  el('create-job').disabled = true; el('connection-state').textContent = 'CHƯA XÁC THỰC · AI CHƯA KẾT NỐI'; status(message);
}
async function api(path, options = {}) {
  if (!token) throw new Error('Cần xác thực.');
  const current = token;
  const response = await fetch(new URL(path, base), { ...options, headers: { ...options.headers, Authorization: `Bearer ${current}` }, cache: 'no-store', credentials: 'omit', redirect: 'error' });
  if (response.status === 401) { logout('Token không hợp lệ hoặc đã hết quyền.'); throw new Error('Chưa xác thực.'); }
  if (!response.ok) throw new Error(`API trả lỗi ${response.status}; chưa có kết quả thành công.`);
  if (current !== token) throw new Error('Phiên xác thực đã thay đổi.');
  return response;
}
async function displayArtifacts(id, version) {
  if (shownJob === id) return;
  shownJob = id;
  const [glbResponse, qaResponse] = await Promise.all([api(`jobs/${id}/artifacts/glb`), api(`jobs/${id}/artifacts/qa`)]);
  const [buffer, qa] = await Promise.all([glbResponse.arrayBuffer(), qaResponse.json()]);
  if (version !== generation) return;
  const gltf = await new GLTFLoader().parseAsync(buffer, '');
  if (version !== generation) return;
  const scene = new THREE.Scene(); scene.background = new THREE.Color('#1b211d');
  gltf.scene.rotation.x = Math.PI / 2; scene.add(gltf.scene); gltf.scene.updateMatrixWorld(true);
  const box = new THREE.Box3().setFromObject(gltf.scene), size = box.getSize(new THREE.Vector3()), center = box.getCenter(new THREE.Vector3());
  scene.add(new THREE.HemisphereLight(0xffffff, 0x464a3d, 4));
  const camera = new THREE.PerspectiveCamera(40, 1, 0.001, 100); camera.up.set(0, 0, 1);
  camera.position.copy(center).add(new THREE.Vector3(1, -1.5, 1).multiplyScalar(size.length() * 1.8));
  renderer = new THREE.WebGLRenderer({ antialias: true }); renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  el('private-canvas').replaceChildren(renderer.domElement); el('private-result').hidden = false;
  controls = new OrbitControls(camera, renderer.domElement); controls.target.copy(center); controls.update();
  const resize = () => { if (!renderer) return; const w = el('private-canvas').clientWidth; renderer.setSize(w, 340); camera.aspect = w / 340; camera.updateProjectionMatrix(); };
  resize(); observer = new ResizeObserver(resize); observer.observe(el('private-canvas'));
  renderer.setAnimationLoop(() => { controls?.update(); renderer?.render(scene, camera); });
  el('private-dimensions').textContent = size.toArray().map(v => (v * 1000).toFixed(2)).join(' × ') + ' mm';
  el('private-qa').textContent = JSON.stringify({ status: 'NEEDS_REVIEW', geometry_status: qa.geometry_status, automatic_vision_executed: qa.automatic_vision_executed, measurements: qa.geometry_measurements }, null, 2);
  el('private-downloads').replaceChildren();
  for (const kind of ['glb', 'blend', 'qa']) {
    const button = document.createElement('button'); button.type = 'button'; button.textContent = `Tải ${kind.toUpperCase()} riêng tư`;
    button.onclick = async () => { try { const response = await api(`jobs/${id}/artifacts/${kind}`); const blob = await response.blob(); if (version !== generation) return; const url = URL.createObjectURL(blob); const a = document.createElement('a'); a.href = url; a.download = `${id}.${kind === 'qa' ? 'json' : kind}`; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000); } catch (e) { status(e.message); } };
    el('private-downloads').append(button);
  }
}
async function refresh() {
  if (!job) return;
  const id = job.id, version = generation;
  const latest = await (await api(`jobs/${id}`)).json();
  if (version !== generation) return;
  job = latest;
  el('job-state').textContent = `Công việc ${job.id}: ${job.state}. Tiến độ: ${job.progress === null ? 'chưa có số đo phần trăm' : job.progress}`;
  el('submit-observations').disabled = job.state !== 'WAITING_ANALYSIS';
  el('rebuild-job').disabled = !['NEEDS_REVIEW', 'FAILED', 'INTERRUPTED'].includes(job.state);
  if (job.state === 'NEEDS_REVIEW') { await displayArtifacts(id, version); status('Đã dựng thật, CẦN XÁC NHẬN. AI tự hiểu ảnh vẫn CHƯA KẾT NỐI.'); }
  else if (['QUEUED', 'RUNNING'].includes(job.state)) polling = setTimeout(() => refresh().catch(e => status(e.message)), 1000);
  else status(`Trạng thái thật: ${job.state}. ${job.error || ''}`);
}
el('local-login').onclick = async () => {
  const candidate = el('local-token').value.trim(); logout('Đang xác thực…'); token = candidate;
  try { const capabilities = await (await api('capabilities')).json(); if (!capabilities.authenticated) throw new Error('Chưa xác thực.'); el('create-job').disabled = false; el('create-job').textContent = 'Gửi 1 ảnh tới backend cục bộ'; el('connection-state').textContent = 'BACKEND CỤC BỘ · AI CHƯA KẾT NỐI'; status('Đã xác thực. Ảnh chỉ gửi tới backend loopback này khi bạn bấm Gửi.'); }
  catch (e) { logout(e.message); }
};
el('local-logout').onclick = () => logout();
el('model-request').addEventListener('submit', async event => {
  event.preventDefault(); if (!token) return;
  try {
    const files = el('source-images').files; if (files.length !== 1) throw new Error('Chế độ backend hiện nhận đúng 1 ảnh/job.');
    resetPrivate(); const form = new FormData(); form.append('image', files[0]); form.append('input_type', el('input-type').value); form.append('instruction', el('model-instruction').value);
    job = await (await api('jobs', { method: 'POST', body: form })).json(); el('refresh-job').disabled = false; await refresh();
  } catch (e) { status(e.message); }
});
el('submit-observations').onclick = async () => {
  try { if (!job || !el('reviewed-check').checked) throw new Error('Cần xác nhận đã kiểm tra chứng cứ.'); const file = el('verified-observations').files[0]; if (!file || file.size > 512000) throw new Error('Chọn JSON đã xác minh, tối đa 512 KB.'); const body = JSON.parse(await file.text()); await api(`jobs/${job.id}/observations`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }); await refresh(); }
  catch (e) { status(e.message); }
};
el('refresh-job').onclick = () => refresh().catch(e => status(e.message));
el('rebuild-job').onclick = async () => {
  try { if (!job) return; const id = job.id; const instruction = el('model-instruction').value.trim(); if (!instruction) throw new Error('Nhập yêu cầu chỉnh sửa.'); const next = await (await api(`jobs/${id}/revisions`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ instruction }) })).json(); resetPrivate(); job = next; el('refresh-job').disabled = false; await refresh(); }
  catch (e) { status(e.message); }
};
window.addEventListener('pagehide', () => logout());
