// Local evidence-gated modeling modules. No AI inference, API, upload or persistence.
const $=id=>document.getElementById(id);
const ui={width:$('hg-width'),depth:$('hg-depth'),height:$('hg-height'),template:$('hg-template'),confirm:$('hg-confirm-dims'),illustration:$('hg-allow-illustration')};
const state={status:'WAITING',runs:0,meshes:0,template:null,errors:[],imageCount:0};
window.hgLocalModules=state;
let lastSignature='',timer;
const show=(id,text)=>{$(id).textContent=text;};
const finite=x=>Number.isFinite(x)&&x>=10&&x<=100000;
function inputState(){
 const photos=[...($('source-images').files||[])];
 const verified=photos.length>0&&$('image-status').textContent.includes('ảnh đang xem trên thiết bị');
 state.imageCount=verified?photos.length:0;
 show('hg-mod-source',verified?('Đã xác minh '+photos.length+' ảnh tại thiết bị'):photos.length?'Đang kiểm tra ảnh':'Chưa có ảnh; có thể dựng theo số đo');
 const values=[ui.width,ui.depth,ui.height].map(field=>Number(field.value));
 const valid=values.every(finite)&&[ui.width,ui.depth,ui.height].every(field=>field.value.trim()!=='');
 const approved=valid&&ui.confirm.checked;
 show('hg-mod-measure',!valid?'Thiếu dài/sâu/cao (mm)':approved?'Đã xác nhận ba số đo':'Chờ người dùng xác nhận');
 return {photos,verified,valid,approved,values};
}
function box(id,name,size,position,color,confidence='inferred'){
 if(!size.every(x=>x>0))throw Error('Cấu kiện có kích thước không hợp lệ');
 return {id,name,shape:'box',size_mm:size.map(x=>Math.round(x*1000)/1000),position_mm:position.map(x=>Math.round(x*1000)/1000),rotation_deg:[0,0,0],color,confidence};
}
function makeParts(width,depth,height,kind){
 const objects=[],wood='#927c69',edge='#766354',legs='#9c8d6c';
 const put=(...p)=>objects.push(box(...p));
 if(kind==='box'){
  put('bounds','Khối bao theo số đo xác nhận',[width,depth,height],[0,0,height/2],wood,'confirmed');
 }else if(kind==='table'){
  if(Math.min(width,depth,height)<100)throw Error('Mẫu Bàn yêu cầu mỗi chiều ít nhất 100 mm.');
  const top=Math.min(32,height*.075),leg=Math.min(70,Math.max(25,Math.min(width,depth)*.07));
  put('top','Mặt bàn minh họa',[width,depth,top],[0,0,height-top/2],wood);
  for(const sx of [-1,1])for(const sy of [-1,1])
   put('leg_'+(sx<0?'L':'R')+(sy<0?'F':'B'),'Chân bàn minh họa',[leg,leg,height-top],[sx*(width-leg)/2,sy*(depth-leg)/2,(height-top)/2],legs);
 }else if(kind==='console'){
  if(Math.min(width,depth,height)<140)throw Error('Mẫu Console yêu cầu mỗi chiều ít nhất 140 mm.');
  const ground=Math.min(height*.16,130),body=height-ground;
  const thick=Math.min(25,Math.max(8,Math.min(width,depth,body)*.035));
  const leg=Math.min(45,Math.max(15,Math.min(width,depth)*.06));
  put('top','Mặt console minh họa',[width,depth,thick],[0,0,height-thick/2],wood);
  put('front','Mặt trước console minh họa',[width-2*thick,thick,body-thick],[0,-(depth-thick)/2,ground+(body-thick)/2],wood);
  put('back','Mặt sau console minh họa',[width-2*thick,thick,body-thick],[0,(depth-thick)/2,ground+(body-thick)/2],edge);
  put('left','Hông trái minh họa',[thick,depth,body-thick],[-(width-thick)/2,0,ground+(body-thick)/2],edge);
  put('right','Hông phải minh họa',[thick,depth,body-thick],[(width-thick)/2,0,ground+(body-thick)/2],edge);
  put('base','Đáy console minh họa',[width-2*thick,depth-2*thick,thick],[0,0,ground+thick/2],wood);
  for(const sx of [-1,1])for(const sy of [-1,1])
   put('foot_'+(sx<0?'L':'R')+(sy<0?'F':'B'),'Chân minh họa',[leg,leg,ground],[sx*(width-leg)/2,sy*(depth-leg)/2,ground/2],legs);
 }else if(kind==='open_tray'){
  if(Math.min(width,depth,height)<180)throw Error('Hộc mở yêu cầu các chiều ít nhất 180 mm.');
  // Open cavity is real geometry: separate four walls + bottom, NEVER a solid top box.
  const legH=Math.min(height*.52,Math.max(100,height*.38));
  const trayH=height-legH;
  const thick=Math.min(28,Math.max(10,Math.min(width,depth)*.038));
  const bottom=Math.min(22,Math.max(10,trayH*.1));
  const leg=Math.min(50,Math.max(18,Math.min(width,depth)*.085));
  if(width<=2*thick||depth<=2*thick||trayH<=bottom)throw Error('Hộc không đủ không gian cho lòng rỗng.');
  put('tray_base','Đáy hộc minh họa',[width-2*thick,depth-2*thick,bottom],[0,0,legH+bottom/2],wood);
  put('tray_front','Thành trước minh họa',[width,thick,trayH],[0,-(depth-thick)/2,legH+trayH/2],wood);
  put('tray_back','Thành sau minh họa',[width,thick,trayH],[0,(depth-thick)/2,legH+trayH/2],wood);
  put('tray_left','Thành trái minh họa',[thick,depth-2*thick,trayH],[-(width-thick)/2,0,legH+trayH/2],edge);
  put('tray_right','Thành phải minh họa',[thick,depth-2*thick,trayH],[(width-thick)/2,0,legH+trayH/2],edge);
  for(const sx of [-1,1])for(const sy of [-1,1])
   put('tray_leg_'+(sx<0?'L':'R')+(sy<0?'F':'B'),'Chân hộc minh họa',[leg,leg,legH],[sx*(width-leg)/2,sy*(depth-leg)/2,legH/2],legs);
 }else if(kind==='chair'){
  if(Math.min(width,depth,height)<250)throw Error('Ghế tựa yêu cầu các chiều ít nhất 250 mm.');
  const seatZ=height*.48,seatT=Math.min(95,height*.1);
  const backT=Math.min(85,depth*.14),leg=Math.min(55,width*.095);
  put('chair_seat','Mặt ngồi minh họa',[width,depth-backT,seatT],[0,-backT/2,seatZ],wood);
  put('chair_back','Lưng tựa minh họa',[width,backT,height-seatZ+seatT/2],[0,(depth-backT)/2,(height+seatZ-seatT/2)/2],edge);
  for(const sx of [-1,1])for(const sy of [-1,1])
   put('chair_leg_'+(sx<0?'L':'R')+(sy<0?'F':'B'),'Chân ghế minh họa',[leg,leg,seatZ-seatT/2],[sx*(width-leg)/2,sy*(depth-leg)/2,(seatZ-seatT/2)/2],legs);
 }else if(kind==='sofa'){
  if(width<600||depth<450||height<400)throw Error('Sofa minh họa cần dài >=600, sâu >=450, cao >=400 mm.');
  const arm=Math.min(180,Math.max(70,width*.09)),baseZ=height*.22;
  const seatZ=height*.49,seatH=Math.min(155,height*.17),backT=Math.min(180,depth*.24);
  put('sofa_base','Bệ sofa minh họa',[width,depth,baseZ],[0,0,baseZ/2],edge);
  put('sofa_seat','Đệm ngồi minh họa',[width-2*arm,depth-backT,seatH],[0,-backT/2,seatZ],wood);
  put('sofa_back','Tựa lưng minh họa',[width-2*arm,backT,height-baseZ],[0,(depth-backT)/2,(height+baseZ)/2],wood);
  for(const sx of [-1,1])
   put('sofa_arm_'+(sx<0?'L':'R'),'Tay vịn minh họa',[arm,depth,height*.62],[sx*(width-arm)/2,0,height*.31],edge);
 }else if(kind==='cabinet'){
  if(Math.min(width,depth,height)<100)throw Error('Mẫu Tủ kệ yêu cầu mỗi chiều ít nhất 100 mm.');
  const thick=Math.min(25,Math.max(7,Math.min(width,depth,height)*.04));
  put('top','Nóc tủ minh họa',[width,depth,thick],[0,0,height-thick/2],wood);
  put('bottom','Đáy tủ minh họa',[width,depth,thick],[0,0,thick/2],wood);
  put('left','Hông trái minh họa',[thick,depth,height-2*thick],[-(width-thick)/2,0,height/2],edge);
  put('right','Hông phải minh họa',[thick,depth,height-2*thick],[(width-thick)/2,0,height/2],edge);
  put('back','Hậu tủ minh họa',[width-2*thick,thick,height-2*thick],[0,(depth-thick)/2,height/2],wood);
 }else throw Error('Loại mô hình chưa hỗ trợ');
 return objects;
}
function build(force=false){
 const input=
const photoStart=$('hg-photo-analysis-start');
photoStart?.addEventListener('click',async()=>{
 const input=inputState();
 if(!input.verified){$('hg-photo-analysis-status').textContent='Hãy tải ảnh nguồn hợp lệ trước khi phân tích.';return;}
 const kind=ui.template.selectedOptions[0]?.textContent||'Sản phẩm nội thất';
 const prompt=[
 'HOANGGIA 3D CLOUD AI — PHÂN TÍCH ẢNH ĐỂ TẠO MÔ HÌNH 3D THAM KHẢO',
 'Hãy quan sát các ảnh tôi đính kèm. Nhận diện đúng sản phẩm, không dùng mẫu bàn/ghế/tủ có sẵn để thay thế.',
 'Loại tham khảo do người dùng chọn: '+kind,
 'Kích thước người dùng nhập (mm): '+input.values.join(' × ')+'. Đã xác nhận: '+(input.approved?'CÓ':'CHƯA')+'. Nếu chưa xác nhận, không được coi là số đo thực.',
 'Liệt kê rõ từng bộ phận quan sát được, hình dáng, lòng rỗng, chân, tay nắm, bề mặt và vị trí tương đối. Không tự thêm chi tiết khuất.',
 'Chỉ dùng các số đo đã xác nhận để đặt kích thước thực. Khi thiếu số đo quan trọng, trả objects=[] và yêu cầu bổ sung; không giả vờ dựng đúng.',
 'Nếu đủ dữ liệu, trả một khối JSON THUẦN duy nhất đúng schema sau để tôi dán vào HG-3D-CLOUD-AI:',
 '{"schema":"hg-chatgpt-scene-v1","unit":"mm","review_status":"NEEDS_REVIEW","objects":[{"id":"part_01","name":"Tên bộ phận quan sát được","shape":"box","size_mm":[500,400,20],"position_mm":[0,0,500],"rotation_deg":[0,0,0],"color":"#806c5c","confidence":"inferred"}],"unknown_details":["Chi tiết cần xác nhận"]}',
 'Các con số trong JSON trên chỉ minh họa cú pháp, KHÔNG được sao chép vào kết quả. Chỉ shape box/cylinder, tối đa 80 bộ phận, vị trí là tâm, trục Z đứng, đơn vị mm.',
 'Đánh dấu XÁC NHẬN / SUY LUẬN / CẦN XÁC NHẬN. Không cam kết giống 100%; kết quả chỉ để kiểm tra ngoại hình sơ bộ.'
 ].join('\n\n');
 try{await navigator.clipboard.writeText(prompt);$('hg-photo-analysis-status').textContent='Đã sao chép lệnh. Mở ChatGPT, dán lệnh cùng ảnh, rồi dán JSON nhận được vào mục Chỉnh sửa với ChatGPT để xem 3D.';}
 catch{$('hg-photo-analysis-status').textContent='Không sao chép tự động được. Hãy dùng mục Tạo yêu cầu cho ChatGPT ở bên dưới.';}
});

inputState();
 // A valid photo is a reference, NOT a shape-recognition input to this parametric engine.
 // Without explicit separate consent, never replace the depicted product with a generic table/cabinet.
 if(input.photos.length&&!input.verified){
  state.status='WAITING_IMAGES';show('hg-engine-result','Ảnh đang được kiểm tra định dạng. Hãy đợi...');return false;
 }
 if(input.verified&&!ui.illustration.checked&&!force){
  state.status='WAITING_PREVIEW_APPROVAL';
  show('hg-mod-geometry','Ảnh chưa phân tích — chờ tạo 3D sơ bộ');
  show('hg-mod-preview','Nhấn TẠO MÔ HÌNH 3D để xem khối tham số tạm thời');
  show('hg-mod-qa','Chưa đối chiếu hình dạng với ảnh');
  show('hg-mod-export','Chưa có mô hình');
  show('hg-engine-result','Ảnh chỉ là tham chiếu. Nhấn TẠO MÔ HÌNH 3D để dựng mẫu tham số theo loại và số đo đang chọn (không phải AI tái dựng từ ảnh).');
  return false;
 }
 // Explicit click on TẠO MÔ HÌNH 3D authorizes a visibly labeled parametric preview.
 // It does not authorize claiming the geometry matches the uploaded photograph.
 if(input.verified&&!ui.illustration.checked&&force)ui.illustration.checked=true;
 if(!input.valid||!input.approved){
  state.status='WAITING_MEASUREMENTS';
  const msg=!input.valid?'Nhập Dài, Sâu, Cao bằng mm rồi xác nhận số đo.':'Đánh dấu xác nhận số đo để dựng mô hình.';
  show('hg-engine-result',msg);
  if(force)show('hg-mod-geometry','Chưa dựng — thiếu chứng cứ');
  return false;
 }
 if(input.photos.length&&!input.verified){
  state.status='WAITING_IMAGES';show('hg-engine-result','Ảnh đang được kiểm tra định dạng. Hãy đợi...');return false;
 }
 const dims=input.values,kind=ui.template.value;
 const signature=[...dims,kind,ui.illustration.checked?'illustration':'noimage',input.photos.map(f=>f.name+':'+f.size).join('|')].join('/');
 if(!force&&signature===lastSignature)return false;
 try{
  const objects=makeParts(...dims,kind);
  const notes=['Không có phân tích thị giác ChatGPT tự động trên website; ảnh nguồn chỉ là tham chiếu.','Chưa đối chiếu hình dạng 3D, cấu tạo khuất, chi tiết gia công hay độ giống với ảnh gốc.'];
  if(kind!=='box')notes.unshift('Các tấm, chân và độ dày là cấu tạo minh họa từ mô hình tham số; không đo từ ảnh.');
  const data={schema:'hg-chatgpt-scene-v1',unit:'mm',review_status:'NEEDS_REVIEW',objects,unknown_details:notes};
  const editor=$('cgpt-scene-json');editor.value=JSON.stringify(data,null,2);
  if(!window.hgChatGPTStudio?.loadParametricDraft?.(data))throw Error('Trình dựng hình 3D không khởi tạo thành công.');
  lastSignature=signature;
  state.status='BUILT_PARAMETRIC_DRAFT';state.runs+=1;state.template=kind;state.meshes=objects.length;state.errors=[];
  show('hg-mod-geometry','Đã dựng '+objects.length+' mesh tham số');
  show('hg-mod-preview','Đã hiển thị mô hình cục bộ');
  show('hg-mod-qa','CẦN XÁC NHẬN hình dạng và cấu tạo');
  show('hg-mod-export','Sẵn sàng GLB và FBX nháp');
  show('hg-engine-result','Đã dựng '+objects.length+' bộ phận 3D THAM KHẢO theo mẫu tham số và số đo. KHÔNG phải tái dựng từ ảnh; hãy xoay, kiểm tra và chỉnh trong KHÔNG GIAN 3D.');
  return true;
 }catch(err){
  state.status='BLOCKED';state.errors=[err.message];
  show('hg-mod-geometry','Không dựng được: '+err.message);
  show('hg-engine-result','CẦN XÁC NHẬN — '+err.message);
  return false;
 }
}
function changed(){clearTimeout(timer);timer=setTimeout(()=>build(false),220);}
for(const f of [ui.width,ui.depth,ui.height,ui.template,ui.confirm,ui.illustration]){
 f.addEventListener('change',changed);
 if(f.type==='number')f.addEventListener('input',changed);
}
$('hg-run-modules').addEventListener('click',()=>build(true));
document.addEventListener('hg3d:imagesvalidated',event=>{
 // Uploading/replacing a photo cancels an earlier permission to show unrelated model templates.
 if(event.detail?.count>0)ui.illustration.checked=false;
 lastSignature='';changed();
});
$('source-images').addEventListener('change',()=>{state.status='VERIFYING_INPUT';show('hg-mod-source','Đang xác minh ảnh tại thiết bị');});
inputState();
