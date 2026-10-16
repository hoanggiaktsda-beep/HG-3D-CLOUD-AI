// Single-screen HOANGGIA 3D Workspace.
// Previous brain modules, viewers, tests and export paths remain loaded, hidden until requested.
// This controls presentation only: never claims that GitHub Pages runs AI inference.
const $=id=>document.getElementById(id);
const body=document.body,flow=$('hg-minimal-prompt-panel'),prompt=$('hg-minimal-prompt'),flowStatus=$('hg-minimal-prompt-status');
const MODES=['hg-show-editor','hg-show-viewer','hg-show-modules'];
const state={mode:'launch',promptShown:false};
window.hgMinimalWorkspace=state;

function setMode(mode){
 if(!body.classList.contains('hg-minimal-ui'))return;
 MODES.forEach(cls=>body.classList.remove(cls));
 state.mode=mode;
 if(mode==='editor')body.classList.add('hg-show-editor');
 else if(mode==='viewer')body.classList.add('hg-show-viewer');
 else if(mode==='modules')body.classList.add('hg-show-modules');
 if(mode!=='launch')window.requestAnimationFrame(()=>window.dispatchEvent(new Event('resize')));
}

function route(){
 const hash=decodeURIComponent(location.hash.slice(1));
 if(hash==='chatgpt-studio')setMode('editor');
 else if(hash==='sample-viewer')setMode('viewer');
 else if(hash==='hg-modules')setMode('modules');
 else setMode('launch');
}
window.addEventListener('hashchange',route);
route();

function showPrompt(){
 if(!body.classList.contains('hg-minimal-ui'))return;
 const value=$('cgpt-prompt').value;
 if(!value.trim()){
  flow.hidden=true;
  flowStatus.textContent='Chưa có lệnh; chọn ảnh và yêu cầu phân tích trước.';
  return;
 }
 prompt.value=value;
 flow.hidden=false;
 state.promptShown=true;
 flowStatus.textContent='Lệnh đã chuẩn bị. Ảnh chưa được gửi cho ChatGPT.';
 flow.scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth',block:'nearest'});
}

document.addEventListener('hg3d:promptprepared',showPrompt);
$('hg-close-prompt').addEventListener('click',()=>{
 flow.hidden=true;state.promptShown=false;
 $('hg-launch-analyze').focus();
});
$('hg-minimal-copy-prompt').addEventListener('click',async()=>{
 if(!prompt.value.trim())return;
 try{
  await navigator.clipboard.writeText(prompt.value);
  flowStatus.textContent='Đã sao chép lệnh. Mở ChatGPT và đính kèm ảnh nguồn để tiếp tục.';
 }catch{
  prompt.focus();prompt.select();
  flowStatus.textContent='Hãy sao chép phần văn bản đã được chọn (Ctrl+C hoặc Sao chép).';
 }
});
$('hg-minimal-copy-image').addEventListener('click',()=>{
 $('hg-photo-copy-image').click();
 flowStatus.textContent='Đang yêu cầu quyền sao chép ảnh. Nếu trình duyệt từ chối, hãy tự đính kèm ảnh gốc trong ChatGPT.';
});

document.addEventListener('hg3d:imagesvalidated',event=>{
 if((event.detail?.count||0)>0||!$('source-images').files.length){
  // Never present a prompt for the previous customer's image with a newly selected image.
  flow.hidden=true;prompt.value='';state.promptShown=false;
 }
});
// The existing "step 02" is a handoff, not a second visible page.
document.querySelectorAll('a[href="#hg-photo-workflow"]').forEach(link=>{
 link.addEventListener('click',event=>{
  if(!body.classList.contains('hg-minimal-ui'))return;
  event.preventDefault();
  if(!$('hg-launch-analyze').disabled)$('hg-launch-analyze').click();
  else $('hg-launch-upload-status').textContent='Vui lòng chọn ảnh trước. Website chưa tự gửi ảnh đi hoặc chạy AI.';
 });
});
// The sample model must never be suggested as the newly uploaded image.
document.querySelectorAll('.hg-inspector-steps a[href="#sample-viewer"]').forEach(link=>{
 link.addEventListener('click',event=>{
  if(!body.classList.contains('hg-minimal-ui'))return;
  if(window.hgViewer?.displayMode!=='local_draft'){
    event.preventDefault();
    $('hg-launch-upload-status').textContent='Chưa có mô hình tạo từ ảnh để xem hoặc xuất. Hãy dùng ChatGPT phân tích ảnh và nhập JSON/GLB trước.';
  }
 });
});
