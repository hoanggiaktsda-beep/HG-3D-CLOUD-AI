// Optional FREE TripoSR bridge. No remote API, tracking, tokens or automatic uploads.
// A browser on a phone cannot reach the TripoSR server on a different PC via 127.0.0.1.
const $=id=>document.getElementById(id);
const ENDPOINT='http://127.0.0.1:8787';
const probeButton=$('hg-triposr-check');
const generateButton=$('hg-triposr-generate');
const consent=$('hg-triposr-consent');
const status=$('hg-triposr-status');
const state={connected:false,working:false,requests:0};
window.hgTripoSRLocal=state;
let aborter=null;
function say(message){status.textContent=message;}
function photo(){
 const input=$('source-images');
 if(window.hgPhotoHandoff?.verifiedImages!==1||input.files.length!==1)return null;
 return input.files[0];
}
function update(){
 generateButton.disabled=!state.connected||state.working||!consent.checked||!photo();
 probeButton.disabled=state.working;
}
async function probe(){
 state.connected=false;update();
 say('Đang kiểm tra TripoSR trên chính máy tính này…');
 try{
  const response=await fetch(ENDPOINT+'/health',{
   method:'GET',mode:'cors',cache:'no-store',credentials:'omit',
   signal:AbortSignal.timeout(7000)
  });
  if(!response.ok)throw Error('HTTP '+response.status);
  const info=await response.json();
  if(info.engine!=='TripoSR'||info.local_only!==true)throw Error('Không đúng bộ xử lý');
  if(!info.engine_found){
   say('Đã thấy bộ kết nối, nhưng máy chưa cài mã nguồn TripoSR. Xem hướng dẫn cài đặt bên dưới.');
   return;
  }
  state.connected=true;
  say('Đã thấy TripoSR cục bộ. GPU, trọng số và khả năng dựng chỉ được xác nhận sau khi chạy thành công. Chọn đúng 1 ảnh và đồng ý gửi vào máy này.');
 }catch{
  say('CHƯA KẾT NỐI. Cần chạy TripoSR + bộ kết nối trên máy tính đang mở website. iPhone không thể dùng 127.0.0.1 của PC. Không có ảnh nào được gửi.');
 }finally{update();}
}
async function generate(){
 const selected=photo();
 if(!state.connected||state.working||!consent.checked||!selected){
  say('Chọn đúng 1 ảnh đã kiểm tra, kết nối TripoSR và xác nhận trước khi tạo.');
  return;
 }
 if(selected.size>20*1024*1024||!['image/png','image/jpeg','image/webp'].includes(selected.type)){
  say('Ảnh phải là PNG/JPEG/WebP, tối đa 20 MB.');return;
 }
 const version=++state.requests;
 state.working=true;update();
 aborter=new AbortController();
 say('Đang chạy AI TripoSR THẬT trên máy tính. Lần đầu có thể cần tải trọng số miễn phí và mất nhiều phút; chưa có phần trăm tiến độ xác thực.');
 try{
  const response=await fetch(ENDPOINT+'/v1/generate',{
   method:'POST',mode:'cors',cache:'no-store',credentials:'omit',
   headers:{'Content-Type':selected.type},body:selected,signal:aborter.signal
  });
  if(!response.ok){
   let message='HTTP '+response.status;
   try{const error=await response.json();message=String(error.error||message).slice(0,180);}catch{}
   throw Error(message);
  }
  const buffer=await response.arrayBuffer();
  if(version!==state.requests||$('source-images').files[0]!==selected)return;
  await window.hgChatGPTStudio.importGLBBuffer(buffer,
   'TripoSR · AI từ 1 ảnh · KÍCH THƯỚC CHƯA XÁC NHẬN');
  if(version!==state.requests)return;
  say('Đã tạo và mở GLB AI thật trong xưởng. Có thể xoay, chọn mesh và xuất GLB/FBX. Kích thước, mặt khuất và cấu tạo cần kiểm định trước khi sử dụng.');
  if(matchMedia('(max-width:600px)').matches)
   $('chatgpt-studio').querySelector('.cgpt-scene').scrollIntoView({block:'start',behavior:'smooth'});
 }catch(error){
  if(version!==state.requests)return;
  say(error.name==='AbortError'
   ?'Đã dừng chờ kết quả. Tác vụ trên GPU có thể vẫn đang chạy.'
   :'Chưa tạo được mô hình: '+String(error.message||'Lỗi không xác định').slice(0,190)+'. Kiểm tra cửa sổ chạy TripoSR và cấu hình GPU.');
 }finally{
  if(version===state.requests){state.working=false;aborter=null;update();}
 }
}
probeButton.addEventListener('click',probe);
generateButton.addEventListener('click',generate);
consent.addEventListener('change',update);
document.addEventListener('hg3d:imagesvalidated',()=>{
 state.requests++;
 aborter?.abort();aborter=null;
 state.working=false;consent.checked=false;update();
});
window.addEventListener('pagehide',()=>{state.requests++;aborter?.abort();});
update();
