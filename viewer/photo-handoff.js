// Photo-first ChatGPT handoff for GitHub Pages.
// Files stay on-device. No images/prompts transmitted by the site.
const $=id=>document.getElementById(id);
const status=$('hg-photo-analysis-state'),description=$('hg-photo-guidance');
const source=$('source-images'),output=$('hg-photo-reference');
const refImg=$('hg-photo-reference-image'),refStatus=$('hg-photo-reference-status');
const copyPromptButton=$('hg-photo-copy-prompt'),copyImageButton=$('hg-photo-copy-image');
const handoff={verifiedImages:0,prepared:false,imported:false,imageCopied:false};
window.hgPhotoHandoff=handoff;
function tell(text){description.textContent=text;}
function verifiedFiles(){
 if(!source.files?.length || !$('image-status').textContent.includes('ảnh đang xem trên thiết bị'))return [];
 return [...source.files];
}
function updateReference(){
 const list=verifiedFiles(),src=$('image-previews').querySelector('img');
 if(list.length&&src){
  output.hidden=false;
  refImg.src=src.src;
  refImg.alt='Ảnh nguồn: '+list[0].name;
  refStatus.textContent='CHƯA PHÂN TÍCH · CHỈ LÀ ẢNH THAM CHIẾU';
 }else{
  output.hidden=true;
  refImg.removeAttribute('src');
 }
}
function resetForPhoto(count){
 const list=verifiedFiles();
 handoff.verifiedImages=count||0;handoff.prepared=false;handoff.imported=false;handoff.imageCopied=false;
 status.textContent=list.length?'ĐÃ NHẬN ẢNH · CHƯA NHẬN DIỆN':'CHƯA CÓ ẢNH';
 copyPromptButton.disabled=!list.length;
 copyImageButton.disabled=!list.length;
 updateReference();
 if(list.length){
  tell('Đã kiểm tra '+list.length+' ảnh trên thiết bị. Website CHƯA phân tích hình dạng; không tự tạo mẫu bàn bốn chân. Bước tiếp: sao chép lệnh → mở ChatGPT → tự đính kèm ảnh.');
  // Existing 3D from a previous photo must never be misrepresented as the new upload.
  window.hgChatGPTStudio?.clearForNewSource?.();
  window.hgViewer?.clearForNewSource?.();
 }else{
  tell('Chọn ảnh, sau đó dùng ChatGPT để phân tích hình dáng và mô tả cấu tạo. Trang không tự gửi ảnh đi.');
  // Clear stale reference/analysis metadata when the user removes a source.
 }
}
source.addEventListener('change',()=>{
 status.textContent='ĐANG KIỂM TRA ẢNH';
 copyPromptButton.disabled=true;copyImageButton.disabled=true;
});
document.addEventListener('hg3d:imagesvalidated',event=>resetForPhoto(event.detail?.count||0));
document.addEventListener('hg3d:sceneimported',event=>{
 handoff.imported=true;
 status.textContent='ĐÃ NHẬN JSON · CẦN ĐỐI CHIẾU VỚI ẢNH';
 if(!output.hidden)refStatus.textContent='CẦN ĐỐI CHIẾU ẢNH ↔ MÔ HÌNH 3D';
 tell('Đã nhận '+(event.detail?.objectCount||0)+' bộ phận trong JSON do người dùng dán. Chưa có kiểm định tự động độ giống ảnh; hãy so sánh và chỉnh trong khung 3D.');
});
copyPromptButton.addEventListener('click',()=>{
 if(!verifiedFiles().length){tell('Cần có ảnh đã xác minh trước khi tạo lệnh phân tích.');return;}
 // The original button creates the real full prompt and writes it on explicit user activation.
 $('cgpt-copy').click();
 handoff.prepared=true;
 status.textContent='LỆNH ĐÃ CHUẨN BỊ · CHƯA GỬI ẢNH';
 tell('Sao chép lệnh (nếu trình duyệt cho phép), sau đó mở ChatGPT. Dán lệnh và chọn tải ảnh vào cuộc trò chuyện. Ảnh vẫn chưa rời khỏi trang này.');
});
copyImageButton.addEventListener('click',async()=>{
 const f=verifiedFiles()[0],img=$('image-previews').querySelector('img');
 if(!f||!img){tell('Chưa có ảnh hợp lệ để sao chép.');return;}
 if(!navigator.clipboard?.write || typeof ClipboardItem==='undefined'){
  tell('Trình duyệt này không hỗ trợ sao chép ảnh trực tiếp. Hãy đính kèm ảnh gốc trong ChatGPT từ thư viện/thiết bị.');
  return;
 }
 try{
  const max=2048,ratio=Math.min(1,max/Math.max(img.naturalWidth,img.naturalHeight));
  const canvas=document.createElement('canvas');
  canvas.width=Math.max(1,Math.round(img.naturalWidth*ratio));
  canvas.height=Math.max(1,Math.round(img.naturalHeight*ratio));
  const ctx=canvas.getContext('2d',{alpha:false});
  if(!ctx)throw Error('Không tạo được ảnh PNG.');
  ctx.drawImage(img,0,0,canvas.width,canvas.height);
  const blob=await new Promise((resolve,reject)=>canvas.toBlob(b=>b?resolve(b):reject(Error('Không mã hóa được PNG.')),'image/png'));
  await navigator.clipboard.write([new ClipboardItem({'image/png':blob})]);
  handoff.imageCopied=true;
  tell('Đã sao chép ảnh đầu tiên ('+canvas.width+' × '+canvas.height+'). Quay về ChatGPT và DÁN ảnh vào ô trò chuyện. Nếu có nhiều ảnh, đính kèm các ảnh còn lại thủ công.');
 }catch(error){
  tell('Chưa sao chép được ảnh ('+String(error.message||'trình duyệt không cấp quyền').slice(0,90)+'). Hãy tải ảnh gốc vào ChatGPT bằng nút đính kèm.');
 }
});
copyPromptButton.disabled=true;
copyImageButton.disabled=true;
tell('Chọn ảnh để bắt đầu phân tích với ChatGPT. Không có kết nối API tự động.');
