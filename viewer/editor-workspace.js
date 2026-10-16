// 3D AI | HOANGGIA AI — Tripo-inspired editor shell connected to the EXISTING Three.js editor.
// No model-generation API, hidden model uploads, AI mock progress, or additional export engines.
const $=id=>document.getElementById(id);
const root=$('chatgpt-studio');
const core=()=>window.hgChatGPTStudio;
const modes={
 image:['Ảnh nguồn','Xem và thay đổi ảnh sản phẩm đã được kiểm tra'],
 model:['Dựng mô hình','Tạo yêu cầu cho ChatGPT / mở JSON hoặc GLB có sẵn'],
 parts:['Bộ phận','Chọn mesh thật và chỉnh sửa trong Thuộc tính'],
 material:['Vật liệu','Màu đơn sắc, lưới và sàn hiển thị'],
 export:['Xuất file','Tải GLB / FBX nhị phân từ mô hình đang mở']
};
const state={tool:'model',inspector:'properties',mobilePanel:'settings'};
window.hgEditorWorkspace=state;
function setTool(tool){
 if(!Object.hasOwn(modes,tool))return false;
 state.tool=tool;root.dataset.wsTool=tool;
 state.mobilePanel=tool==='parts'?'inspector':'settings';root.dataset.wsMobilePanel=state.mobilePanel;
 for(const button of root.querySelectorAll('[data-ws-tool]'))button.setAttribute('aria-pressed',String(button.dataset.wsTool===tool));
 $('hg-ws-tool-name').textContent=modes[tool][0];
 $('hg-ws-tool-subtitle').textContent=modes[tool][1];
 if(tool==='parts')setInspector('assets');
 if(tool==='material')state.mobilePanel='settings';
 root.dataset.wsMobilePanel=state.mobilePanel;
 refresh();
 return true;
}
function setInspector(which){
 if(!['assets','properties'].includes(which))return;
 state.inspector=which;
 state.mobilePanel='inspector';root.dataset.wsMobilePanel='inspector';
 $('hg-ws-assets-panel').hidden=which!=='assets';
 $('hg-ws-properties-panel').hidden=which!=='properties';
 for(const [mode,id] of [['assets','hg-ws-assets-tab'],['properties','hg-ws-properties-tab']]){
  const btn=$(id);btn.setAttribute('aria-selected',String(mode===which));
  btn.tabIndex=mode===which?0:-1;
 }
}
function makeButton(text,click,selected=false){
 const b=document.createElement('button');b.type='button';b.textContent=text;
 b.className='hg-ws-mesh-row'+(selected?' is-selected':'');
 b.addEventListener('click',click);return b;
}
function refreshSources(){
 const verified=window.hgPhotoHandoff?.verifiedImages>0;
 const files=verified?[...($('source-images').files||[])]:[];
 const src=$('image-previews').querySelector('img'),img=$('hg-ws-source-image');
 if(files.length&&src){
  img.src=src.src;img.hidden=false;
  $('hg-ws-source-empty').hidden=true;
  $('hg-ws-source-info').textContent=files.length+' ảnh đã chọn · chưa có AI tự phân tích ảnh trên web.';
 }else{
  img.removeAttribute('src');img.hidden=true;
  $('hg-ws-source-empty').hidden=false;
  $('hg-ws-source-info').textContent='Chưa có ảnh nguồn. Có thể mở GLB hoặc nhập JSON được kiểm tra.';
 }
 const list=$('hg-ws-source-assets');list.replaceChildren();
 if(!files.length){list.textContent='Chưa có ảnh nguồn.';return;}
 for(const file of files.slice(0,8)){
  const item=document.createElement('div');item.className='hg-ws-file-row';
  const name=document.createElement('span');name.textContent='▧ '+file.name.slice(0,100);
  const meta=document.createElement('small');meta.textContent=(file.size/1024/1024).toFixed(1)+' MB';
  item.append(name,meta);list.append(item);
 }
}
function refresh(){
 const engine=core();
 const parts=engine?.getParts?.()||[],selected=engine?.getSelectedPart?.()||null;
 const ready=Boolean(engine?.ready&&parts.length);
 for(const id of ['hg-ws-top-glb','hg-ws-top-fbx','hg-ws-panel-glb','hg-ws-panel-fbx'])$(id).disabled=!ready;
 $('hg-ws-project-state').textContent=ready?parts.length+' bộ phận · BẢN NHÁP · CẦN XÁC NHẬN':'Chưa có mô hình · Dữ liệu trên thiết bị';
 $('hg-ws-project-name').textContent=ready?String(engine.origin||'Mô hình cục bộ').slice(0,64):'Dự án chưa đặt tên';
 $('hg-ws-asset-count').textContent=String(parts.length);
 const container=$('hg-ws-mesh-assets');container.replaceChildren();
 if(!parts.length){container.textContent='Chưa có mô hình từ JSON / GLB.';}
 for(const mesh of parts){
  const button=makeButton((mesh.visible?'◈ ':'○ ')+(mesh.name||'Bộ phận '+(mesh.index+1)),()=>{
    engine.selectPart(mesh.index);setInspector('properties');
  },selected?.index===mesh.index);
  button.setAttribute('aria-label','Chọn bộ phận '+mesh.name);
  container.append(button);
 }
 if(selected){
  $('hg-ws-part-name').value=selected.name||'';
  $('hg-ws-part-visible').checked=selected.visible;
  $('hg-ws-part-color').value=/^#[0-9a-fA-F]{6}$/.test(selected.color)?selected.color:'#948773';
 }else{
  $('hg-ws-part-name').value='';
  $('hg-ws-part-visible').checked=false;
  $('hg-ws-part-color').value='#948773';
 }
 for(const id of ['hg-ws-part-name','hg-ws-part-visible','hg-ws-part-color','hg-ws-apply-appearance'])$(id).disabled=!ready||!selected;
 refreshSources();
}
function forward(id){
 const engine=core();
 if(!engine?.ready||!engine.getParts?.().length){$('cgpt-feedback').textContent='Chưa có mô hình thực để xuất. Hãy mở GLB hoặc nhập JSON có hình học trước.';return;}
 $(id).click();
}
for(const button of root.querySelectorAll('[data-ws-tool]'))button.addEventListener('click',()=>setTool(button.dataset.wsTool));
$('hg-ws-assets-tab').addEventListener('click',()=>setInspector('assets'));
$('hg-ws-properties-tab').addEventListener('click',()=>setInspector('properties'));
$('hg-ws-open-assets').addEventListener('click',()=>setInspector('assets'));
$('hg-ws-material-properties').addEventListener('click',()=>setInspector('properties'));
$('hg-ws-change-image').addEventListener('click',()=>$('source-images').click());
$('hg-ws-import-glb').addEventListener('click',()=>$('cgpt-glb-file').click());
for(const [from,to] of [['hg-ws-top-glb','cgpt-export-glb'],['hg-ws-top-fbx','cgpt-export-fbx'],
                        ['hg-ws-panel-glb','cgpt-export-glb'],['hg-ws-panel-fbx','cgpt-export-fbx']]){
 $(from).addEventListener('click',()=>forward(to));
}
$('hg-ws-apply-appearance').addEventListener('click',()=>{
 try{
  core().setAppearance({name:$('hg-ws-part-name').value,color:$('hg-ws-part-color').value,visible:$('hg-ws-part-visible').checked});
 }catch(error){$('cgpt-feedback').textContent=error.message;}
});
$('hg-ws-wireframe').addEventListener('change',event=>core()?.setWireframe?.(event.target.checked));
$('hg-ws-grid').addEventListener('change',event=>core()?.setGrid?.(event.target.checked));
for(const b of root.querySelectorAll('[data-ws-view]')){
 b.addEventListener('click',()=>{
  if(!core()?.setCameraView?.(b.dataset.wsView)){
   $('cgpt-feedback').textContent='Chưa có mô hình để đổi góc xem.';
   return;
  }
  for(const other of root.querySelectorAll('[data-ws-view]'))
   other.setAttribute('aria-pressed',String(other===b));
 });
}
$('hg-ws-reset-view').addEventListener('click',()=>{
 $('cgpt-recenter').click();
 for(const b of root.querySelectorAll('[data-ws-view]'))b.setAttribute('aria-pressed',String(b.dataset.wsView==='perspective'));
});
// Reuse the existing evidence-aware ChatGPT job builder rather than implementing another.
for(const [visibleId,engineId] of [
 ['hg-ws-input-kind','input-type'],
 ['hg-ws-instruction','model-instruction'],
 ['hg-ws-measurements','confirmed-measurements']
]){
 const visible=$(visibleId),original=$(engineId);
 visible.value=original.value;
 visible.addEventListener('input',()=>{original.value=visible.value;original.dispatchEvent(new Event('input',{bubbles:true}));});
 visible.addEventListener('change',()=>{original.value=visible.value;original.dispatchEvent(new Event('change',{bubbles:true}));});
}
document.addEventListener('hg3d:editorchange',event=>{
 if(event.detail?.reason==='model'){
  core()?.setWireframe?.($('hg-ws-wireframe').checked);
  core()?.setGrid?.($('hg-ws-grid').checked);
 }
 refresh();
});
document.addEventListener('hg3d:imagesvalidated',refresh);
document.addEventListener('hg3d:sceneimported',refresh);
window.addEventListener('hashchange',()=>{
 if(location.hash==='#chatgpt-studio')requestAnimationFrame(()=>{
  window.dispatchEvent(new Event('resize'));refresh();
 });
});
setInspector('properties');
setTool('model');
refresh();
