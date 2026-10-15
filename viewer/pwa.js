// Only reviewed public assets are cached; never persist image selections or requests.
const status = document.querySelector('#pwa-status');
const button = document.querySelector('#install-app');
let prompt;
window.addEventListener('beforeinstallprompt', event => {
  event.preventDefault(); prompt = event; button.hidden = false;
});
button.addEventListener('click', async () => {
  if (!prompt) return;
  await prompt.prompt(); await prompt.userChoice;
  prompt = undefined; button.hidden = true;
});
if ('serviceWorker' in navigator && window.isSecureContext) {
  navigator.serviceWorker.register('./service-worker.js', {scope:'./', updateViaCache:'none'})
    .then(async registration => {
      await navigator.serviceWorker.ready;
      status.textContent = 'PWA sẵn sàng · chỉ lưu mẫu công khai để xem ngoại tuyến. Cập nhật mới có hiệu lực sau khi đóng các tab cũ.';
      registration.update().catch(() => {});
    }).catch(() => { status.textContent = 'Chưa bật ngoại tuyến. Cần kết nối mạng để xem mẫu.'; });
} else status.textContent = 'Trình duyệt chưa hỗ trợ PWA hoặc kết nối chưa an toàn.';
