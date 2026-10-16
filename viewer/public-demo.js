// Fixed public catalog only. No auth token, uploads, fake jobs, or customer API.
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
const status=document.querySelector('#public-demo-status'),cards=document.querySelector('#public-demo-cases');
let renderer,controls,observer,model,camera,target,size,generation=0;
window.hgPublicDemo={ready:false};
function reset(){generation++;renderer?.setAnimationLoop(null);controls?.dispose();observer?.disconnect();model?.traverse(o=>{o.geometry?.dispose();if(o.material){for(const m of [].concat(o.material))m.dispose();}});renderer?.dispose();document.querySelector('#public-demo-viewport').replaceChildren();window.hgPublicDemo.ready=false;camera=null;controls=null;renderer=null;observer=null;model=null;}
function cameraView(direction){if(!camera)return;camera.position.copy(target).addScaledVector(new THREE.Vector3(...direction).normalize(),size.length()*Math.max(1,1/camera.aspect)*1.2);controls.target.copy(target);controls.update();}
async function show(record,release){
 reset();const version=generation;status.textContent='Đang kiểm tra và tải kết quả AI công khai…';
 const asset=release.files.find(f=>f.path==='public-demo/chair.glb');
 const response=await fetch('./public-demo/chair.glb?run='+encodeURIComponent(release.run_id),{cache:'no-store',credentials:'omit'});if(!response.ok)throw Error('Không tải được GLB kết quả.');
 const buffer=await response.arrayBuffer();const digest=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',buffer)),b=>b.toString(16).padStart(2,'0')).join('');
 if(digest!==asset.sha256)throw Error('GLB không khớp checksum của lượt chạy.');
 if(version!==generation)return;
 const loaded=await new GLTFLoader().parseAsync(buffer,'');if(version!==generation)return;model=loaded.scene;model.rotation.x=Math.PI/2;model.updateMatrixWorld(true);
 const scene=new THREE.Scene();scene.background=new THREE.Color('#1b211d');scene.add(model,new THREE.HemisphereLight(0xffffff,0x444444,4));
 const box=new THREE.Box3().setFromObject(model);if(box.isEmpty())throw Error('Kết quả không có mesh.');target=box.getCenter(new THREE.Vector3());size=box.getSize(new THREE.Vector3());
 camera=new THREE.PerspectiveCamera(40,1,.001,100);camera.up.set(0,0,1);
 renderer=new THREE.WebGLRenderer({antialias:true});renderer.setPixelRatio(Math.min(devicePixelRatio,2));
 const viewport=document.querySelector('#public-demo-viewport');viewport.append(renderer.domElement);
 controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;
 const resize=()=>{const w=viewport.clientWidth;renderer.setSize(w,360);camera.aspect=w/360;camera.updateProjectionMatrix();};resize();observer=new ResizeObserver(resize);observer.observe(viewport);
 cameraView([0,0.001,1]);renderer.setAnimationLoop(()=>{controls.update();renderer.render(scene,camera);});
 let meshes=0;model.traverse(o=>{if(o.isMesh)meshes++;});window.hgPublicDemo={ready:true,meshes,run_id:release.run_id,measured_mm:size.toArray().map(v=>v*1000)};
 status.textContent=`Kết quả thật của lượt ${release.run_id}: ${meshes} mesh tấm rời · CẦN XÁC NHẬN. Chưa lắp ráp, không phải kết quả ảnh bạn chọn.`;
}
async function refresh(){
 try{
 const response=await fetch('./public-demo/release.json',{cache:'no-store',credentials:'omit'});
 if(response.status===404){status.textContent='Chưa có kết quả AI công khai được phát hành. Theo dõi workflow trên GitHub.';return;}
 if(!response.ok)throw Error('Chưa tải được trạng thái công khai. Cần kết nối mạng.');
 const release=await response.json();
 if(release.scope!=='fixed_public_qwen_catalog_only'||release.final_approved!==false||!Array.isArray(release.cases))throw Error('Metadata kết quả không hợp lệ.');
 cards.replaceChildren();reset();status.textContent=`Bản ghi đã hoàn tất của lượt ${release.run_id}; không phải tiến độ đang chạy. Xem tiến độ thật trên GitHub.`;
 for(const record of release.cases){
  const card=document.createElement('article');card.className='card';
  const title=document.createElement('h3');title.textContent=record.id;
  const state=document.createElement('p');state.textContent=record.status;
  const note=document.createElement('p');note.className='note';note.textContent=record.reason||`${record.parts} tấm rời; ${record.source.license}. ${record.source.author}. CẦN XÁC NHẬN.`;
  card.append(title,state,note);
  if(record.id==='chair'&&record.status==='BUILT_UNASSEMBLED_PARTS_NEEDS_REVIEW'){
   const view=document.createElement('button');view.textContent='Xem kết quả AI 3D';view.onclick=()=>show(record,release).catch(e=>{reset();status.textContent=e.message;});card.append(view);
   const report=document.createElement('p');report.className='note';report.textContent=`IoU đường bao tấm cắt: ${Number(record.min_source_top_iou).toFixed(4)}; bất định nguồn khoảng ${Number(record.source_uncertainty_mm).toFixed(2)} mm. Chưa xác minh lắp ráp, tên tấm, lỗ khoan và bán kính dao.`;card.append(report);
   for(const [label,path] of [['GLB','public-demo/chair.glb'],['BLEND','public-demo/chair.blend'],['QA JSON','public-demo/chair-qa.json']]){const a=document.createElement('a');a.href='./'+path+'?run='+encodeURIComponent(release.run_id);a.download='';a.textContent='Tải '+label;card.append(a);}
  }
  const source=document.createElement('a');const sourceURL=new URL(record.source.url);if(sourceURL.origin!=='https://raw.githubusercontent.com'||!sourceURL.pathname.startsWith('/opendesk/design-playground/'))throw Error('Nguồn không thuộc danh mục công khai.');source.href=sourceURL.href;source.target='_blank';source.rel='noopener noreferrer';source.textContent='Bản vẽ nguồn công khai';card.append(source);cards.append(card);
 }
 }catch(e){status.textContent=e.message||'CHƯA KẾT NỐI kết quả mẫu. Không có kết quả thành công để hiển thị.';}
}
document.querySelector('#refresh-public-demo').onclick=refresh;
document.querySelector('#public-demo-top').onclick=()=>cameraView([0,.001,1]);
document.querySelector('#public-demo-perspective').onclick=()=>cameraView([1,-1,1]);
window.addEventListener('pagehide',reset);refresh();
