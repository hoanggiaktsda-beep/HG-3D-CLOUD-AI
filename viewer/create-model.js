import { modelService } from './model-service.js';
const input = document.querySelector('#source-images');
const previews = document.querySelector('#image-previews');
const status = document.querySelector('#image-status');
let urls = [], selectionVersion = 0;
const limits = { files: 8, bytes: 20 * 1024 * 1024, total: 60 * 1024 * 1024, pixels: 25_000_000 };
function clear() {
  for (const url of urls) URL.revokeObjectURL(url);
  urls = []; previews.replaceChildren();
}
function message(value) { status.textContent = value; }
async function selected() {
  const version = ++selectionVersion;
  clear();
  const files = [...input.files];
  if (!files.length) { message('Chưa chọn ảnh.'); return; }
  if (files.length > limits.files || files.reduce((n, f) => n + f.size, 0) > limits.total) {
    input.value = ''; message('Tối đa 8 ảnh, tổng dung lượng tối đa 60 MB.'); return;
  }
  const pending = [];
  try {
    for (const file of files) {
      if (!['image/png', 'image/jpeg', 'image/webp'].includes(file.type) || !file.size || file.size > limits.bytes) throw new Error('Chỉ nhận PNG, JPEG, WebP; tối đa 20 MB mỗi ảnh. HEIC/HEIF cần xuất sang JPEG trước.');
      const header = new Uint8Array(await file.slice(0, 12).arrayBuffer());
      const matches = file.type === 'image/png' ? [137,80,78,71,13,10,26,10].every((v,i) => header[i] === v)
        : file.type === 'image/jpeg' ? header[0] === 255 && header[1] === 216 && header[2] === 255
        : String.fromCharCode(...header.slice(0,4)) === 'RIFF' && String.fromCharCode(...header.slice(8,12)) === 'WEBP';
      if (!matches) throw new Error('Định dạng thật của file không khớp PNG/JPEG/WebP.');
      if (version !== selectionVersion) { pending.forEach(URL.revokeObjectURL); return; }
      const url = URL.createObjectURL(file); pending.push(url);
      const image = new Image(); image.src = url;
      try { await image.decode(); } catch { throw new Error('Có file không đọc được như ảnh hợp lệ.'); }
      if (image.naturalWidth * image.naturalHeight > limits.pixels) throw new Error('Mỗi ảnh tối đa 25 megapixel.');
      if (version !== selectionVersion) { pending.forEach(URL.revokeObjectURL); return; }
      image.alt = 'Ảnh đã chọn: ' + file.name;
      const figure = document.createElement('figure');
      const caption = document.createElement('figcaption'); caption.textContent = file.name;
      figure.append(image, caption); previews.append(figure);
    }
    urls = pending;
    message(`${files.length} ảnh đang xem trên thiết bị. Chưa tải lên máy chủ, chưa phân tích AI.`);
  } catch (error) {
    pending.forEach(URL.revokeObjectURL);
    if (version !== selectionVersion) return;
    clear(); input.value = ''; message(error.message);
  }
}
input.addEventListener('change', selected);
document.querySelector('#clear-images').addEventListener('click', () => {
  ++selectionVersion; input.value = ''; clear(); message('Đã bỏ ảnh khỏi phiên xem. Chưa gửi dữ liệu đi.');
});
window.addEventListener('pagehide', () => { ++selectionVersion; clear(); });
document.querySelector('#model-request').addEventListener('submit', event => event.preventDefault());
const connected = modelService.capabilities();
// No runtime toggle or mock can unlock uploads while the required services are absent.
for (const id of ['create-job', 'rebuild-job']) document.getElementById(id).disabled = true;
document.querySelector('#connection-state').textContent = connected.connected ? 'CẦN KIỂM TRA KẾT NỐI' : 'CHƯA KẾT NỐI';
