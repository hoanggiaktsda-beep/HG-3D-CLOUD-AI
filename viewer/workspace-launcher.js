// HOANGGIA 3D WORKSPACE — public static image-first launcher.
// Every image stays in the browser until the user intentionally sends it elsewhere.
const $=id=>document.getElementById(id);
const drop=$('hg-upload-drop'),source=$('source-images');
const empty=$('hg-upload-empty'),loaded=$('hg-upload-loaded');
const preview=$('hg-launch-preview'),fileName=$('hg-launch-filename');
const count=$('hg-launch-filecount'),status=$('hg-launch-upload-status');
const analyze=$('hg-launch-analyze');
const stageSource=$('hg-stage-source'),stageAnalysis=$('hg-stage-analysis');
const stageModel=$('hg-stage-model'),stageExport=$('hg-stage-export');
const state={verified:0,dragged:false,priorities:['shape','parts'],priority:'shape'};
window.hgWorkspaceLauncher=state;
const checkedPriority=()=>document.querySelector('input[name="hg-model-priority"]:checked')?.value||'shape';
function showStatus(text){status.textContent=text;}
function setSource(files){
 if(!files||!files.length){showStatus('Không có ảnh hợp lệ được chọn.');return;}
 const dt=new DataTransfer();
 for(const file of [...files].slice(0,9))dt.items.add(file);
 source.files=dt.files;
 source.dispatchEvent(new Event('change',{bubbles:true}));
 showStatus('Đang kiểm tra ảnh trên thiết bị...');
}
function updateFromValidated(countNumber){
 const approved=Number(countNumber)>0 && $('image-status').textContent.includes('ảnh đang xem trên thiết bị');
 const files=approved?[...source.files]:[];
 state.verified=files.length;
 analyze.disabled=!files.length;
 if(files.length){
  const first=$('image-previews').querySelector('img');
  if(!first){showStatus('Đang chuẩn bị hình thu nhỏ.');return;}
  preview.src=first.src;
  fileName.textContent=files[0].name.slice(0,180);
  count.textContent=files.length+' ảnh nguồn · đang ở thiết bị';
  loaded.hidden=false;empty.hidden=true;
  stageSource.textContent='Đã nhận '+files.length+' ảnh';
  stageAnalysis.textContent='Chưa phân tích · cần gửi ChatGPT';
  stageModel.textContent='Chưa có mô hình từ ảnh';
  stageExport.textContent='Chưa có file kết quả từ ảnh';
  showStatus('Ảnh đã được kiểm tra. Bấm “Chuẩn bị lệnh phân tích ảnh” để sử dụng ChatGPT; không tự dựng mô hình mẫu.');
 }else{
  loaded.hidden=true;empty.hidden=false;preview.removeAttribute('src');
  stageSource.textContent='Chưa chọn ảnh nguồn';
  stageAnalysis.textContent='Đính kèm ảnh thủ công';
  stageModel.textContent='Đợi JSON/GLB hợp lệ';
  stageExport.textContent='Có file khi đã dựng hình học';
  showStatus('Chọn ảnh hoặc kéo thả ảnh vào ô lớn để bắt đầu. Không có kết nối AI tự động.');
 }
}
drop.addEventListener('click',()=>source.click());
drop.addEventListener('keydown',event=>{
 if(event.key==='Enter'||event.key===' '){event.preventDefault();source.click();}
});
for(const name of ['dragenter','dragover']){
 drop.addEventListener(name,event=>{
  event.preventDefault();event.dataTransfer.dropEffect='copy';
  drop.classList.add('is-dragging');state.dragged=true;
 });
}
drop.addEventListener('dragleave',event=>{
 if(!drop.contains(event.relatedTarget)){drop.classList.remove('is-dragging');state.dragged=false;}
});
drop.addEventListener('drop',event=>{
 event.preventDefault();drop.classList.remove('is-dragging');state.dragged=false;
 const files=[...(event.dataTransfer?.files||[])];
 if(!files.length){showStatus('Vui lòng thả ảnh PNG, JPEG hoặc WebP, không thả liên kết.');return;}
 if(files.length>8){showStatus('Tối đa 8 ảnh; hãy chọn lại.');return;}
 setSource(files);
});
drop.addEventListener('paste',event=>{
 const clipboard=[...(event.clipboardData?.files||[])];
 if(!clipboard.length)return;
 event.preventDefault();
 if(clipboard.length>8){showStatus('Tối đa 8 ảnh; hãy chọn lại.');return;}
 setSource(clipboard);
});
document.addEventListener('hg3d:imagesvalidated',event=>updateFromValidated(event.detail?.count||0));
source.addEventListener('change',()=>{if(source.files.length){analyze.disabled=true;showStatus('Đang kiểm tra ảnh...');}});
for(const radio of document.querySelectorAll('input[name="hg-model-priority"]')){
 radio.addEventListener('change',()=>{state.priority=checkedPriority();});
}
analyze.addEventListener('click',()=>{
 if(!state.verified){showStatus('Hãy tải ảnh thành công trước khi bắt đầu.');return;}
 // Delegates to existing checked manual handoff. No direct model API or fake progress.
 $('hg-photo-copy-prompt').click();
 stageAnalysis.textContent='Lệnh đã chuẩn bị · người dùng gửi ảnh';
 showStatus('Đã chuẩn bị lệnh theo chế độ đã chọn. Mở ChatGPT ở bước 02 và đính kèm ảnh trước khi gửi.');
 const el=$('hg-photo-workflow');el.scrollIntoView({behavior:window.matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth',block:'center'});
});
document.addEventListener('hg3d:sceneimported',event=>{
 stageModel.textContent=(event.detail?.objectCount||0)+' bộ phận trong mô hình nháp';
 stageExport.textContent='Sẵn sàng tải GLB/FBX nháp';
});
const localInfo=$('cgpt-result-note');
if(localInfo){
 const observer=new MutationObserver(()=>{
  if(window.hgChatGPTStudio?.ready){
   stageModel.textContent=(window.hgChatGPTStudio.objects||0)+' bộ phận · cần đối chiếu';
   stageExport.textContent='GLB/FBX nháp trên thiết bị';
  }
 });
 observer.observe(localInfo,{childList:true,subtree:true,characterData:true});
 window.addEventListener('pagehide',()=>observer.disconnect());
}
updateFromValidated(0);
