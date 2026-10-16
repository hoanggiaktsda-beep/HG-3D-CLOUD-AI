import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';
const root=path.dirname(fileURLToPath(import.meta.url)),out=path.join(root,'dist');
const sha=b=>createHash('sha256').update(b).digest('hex');
const manifest=JSON.parse(fs.readFileSync(path.join(root,'public-assets.json')));
if(manifest.release_scope!=='synthetic_public_sample_only')throw Error('Public release scope required');
if(!Array.isArray(manifest.assets)||JSON.stringify(manifest.assets.map(a=>a.path).sort())!==JSON.stringify(['assets/sample-qa.json','assets/sample.blend','assets/sample.glb']))throw Error('All reviewed public sample hashes required');
for(const a of manifest.assets){
 if(!['assets/sample.glb','assets/sample-qa.json','assets/sample.blend'].includes(a.path)||sha(fs.readFileSync(path.join(root,a.path)))!==a.sha256)throw Error('Public sample changed without review');
}
const glb=fs.readFileSync(path.join(root,'assets/sample.glb'));
if(glb.readUInt32LE(0)!==0x46546c67||glb.readUInt32LE(4)!==2||glb.readUInt32LE(8)!==glb.length||glb.readUInt32LE(16)!==0x4e4f534a)throw Error('Invalid GLB');
const json=JSON.parse(glb.subarray(20,20+glb.readUInt32LE(12)).toString().trim());
if([...(json.buffers||[]),...(json.images||[])].some(v=>v.uri))throw Error('External GLB resource not allowed');
if(fs.readFileSync(path.join(root,'assets/sample.blend')).subarray(0,7).toString()!=='BLENDER')throw Error('Invalid BLEND');
const copy={ 'public-demo.js':'public-demo.js', 'pwa.js':'pwa.js','studio-theme.js':'studio-theme.js','studio-theme.css':'studio-theme.css','assets/hoanggia-icon.svg':'assets/hoanggia-icon.svg','manifest.webmanifest':'manifest.webmanifest','icons/icon-192.png':'icons/icon-192.png','icons/icon-512.png':'icons/icon-512.png','assets/sample.blend':'assets/sample.blend', 'create-model.js':'create-model.js','chatgpt-studio.js':'chatgpt-studio.js','local-modules.js':'local-modules.js','photo-handoff.js':'photo-handoff.js','workspace-launcher.js':'workspace-launcher.js','minimal-shell.js':'minimal-shell.js','editor-workspace.js':'editor-workspace.js','model-service.js':'model-service.js','app.js':'app.js','style.css':'style.css','PUBLIC_SAMPLE.md':'PUBLIC_SAMPLE.md','assets/sample.glb':'assets/sample.glb','assets/sample-qa.json':'assets/sample-qa.json',
 'node_modules/three/build/three.module.js':'vendor/three/three.module.js','node_modules/three/build/three.core.js':'vendor/three/three.core.js',
 'node_modules/three/examples/jsm/controls/OrbitControls.js':'vendor/three/addons/controls/OrbitControls.js',
 'node_modules/three/examples/jsm/loaders/GLTFLoader.js':'vendor/three/addons/loaders/GLTFLoader.js',
 'node_modules/three/examples/jsm/loaders/FBXLoader.js':'vendor/three/addons/loaders/FBXLoader.js',
 'node_modules/three/examples/jsm/libs/fflate.module.js':'vendor/three/addons/libs/fflate.module.js',
 'node_modules/three/examples/jsm/curves/NURBSCurve.js':'vendor/three/addons/curves/NURBSCurve.js',
 'node_modules/three/examples/jsm/curves/NURBSUtils.js':'vendor/three/addons/curves/NURBSUtils.js',
 'node_modules/fflate/esm/browser.js':'vendor/fflate/esm/browser.js',
 'node_modules/three/examples/jsm/exporters/GLTFExporter.js':'vendor/three/addons/exporters/GLTFExporter.js',
 'node_modules/three/examples/jsm/utils/BufferGeometryUtils.js':'vendor/three/addons/utils/BufferGeometryUtils.js','node_modules/three/LICENSE':'vendor/three/LICENSE'};
// Optional release produced only by the fixed public Qwen workflow.
const publicNames=['public-demo/readings.json','public-demo/chair.glb','public-demo/chair.blend','public-demo/chair-qa.json'];
const releasePath=path.join(root,'public-demo/release.json');
if(fs.existsSync(releasePath)){
 if(fs.lstatSync(releasePath).isSymbolicLink())throw Error('Unsafe public release');
 const release=JSON.parse(fs.readFileSync(releasePath));
 const known={desk:['6ebbf999eae55082711585656d5476873baa3745861af496b0bce8ef33a5759e','OD-51380-Desk-1.1.0/OD-51380'],chair:['e295e6496d2b5dc314175afc678bf7b0aa61d984dc52b7d53e50c4d602441445','OD-51381-5-To-30-Minute-Chair-1.0.0/OD-51381'],table:['97775bcc2b30a768d18170d49118afbd9020181c45cafd7013ddbf2925fc0d6a','OD-51383-One-To-Several-Table-1.0.0/OD-51383']};
 if(release.scope!=='fixed_public_qwen_catalog_only'||release.final_approved!==false||release.private_upload_connected!==false||!/^\d+$/.test(release.run_id)||!/^[a-f0-9]{40}$/.test(release.commit)||release.model_revision!=='895c3a49bc3fa70a340399125c650a463535e71c'||release.roles?.length!==18)throw Error('Unverified public release');
 if(release.cases?.length!==3||new Set(release.cases.map(c=>c.id)).size!==3)throw Error('Public catalog mismatch');
 for(const c of release.cases){const k=known[c.id];if((c.id!=='chair'&&c.status==='BUILT_UNASSEMBLED_PARTS_NEEDS_REVIEW')||!k||c.source.original_geometry_json_used!==false||c.source.sha256!==k[0]||c.source.url!=='https://raw.githubusercontent.com/opendesk/design-playground/gh-pages/'+k[1]+'-Assembly-Guide.pdf'||c.source.answers_supplied_to_model!==false||c.assembly_allowed!==false||!['BLOCKED_NEEDS_CONFIRMATION','BUILT_UNASSEMBLED_PARTS_NEEDS_REVIEW'].includes(c.status))throw Error('Unapproved public source');}
 const expected=release.cases.some(c=>c.id==='chair'&&c.status==='BUILT_UNASSEMBLED_PARTS_NEEDS_REVIEW')?publicNames:['public-demo/readings.json'];
 if(!Array.isArray(release.files)||JSON.stringify(release.files.map(f=>f.path).sort())!==JSON.stringify([...expected].sort()))throw Error('Public file allowlist mismatch');
 for(const f of release.files){const p=path.join(root,f.path);if(fs.lstatSync(p).isSymbolicLink()||fs.statSync(p).size>25*1024*1024||fs.statSync(p).size!==f.bytes||sha(fs.readFileSync(p))!==f.sha256)throw Error('Public result changed without matching receipt');copy[f.path]=f.path;}
 copy['public-demo/release.json']='public-demo/release.json';
}
// Vendor only published FBX library JavaScript and its MIT license; never copy arbitrary assets.
const packageDist=path.join(root,'node_modules/@comfyorg/fbx-exporter-three/dist');
if(!fs.existsSync(packageDist))throw Error('Missing @comfyorg/fbx-exporter-three package; npm ci required');
function includeFBX(dir){
 for(const item of fs.readdirSync(dir,{withFileTypes:true})){
  const full=path.join(dir,item.name);
  if(item.isSymbolicLink())throw Error('Symlink forbidden in FBX vendor package');
  if(item.isDirectory())includeFBX(full);
  else if(item.isFile()&&item.name.endsWith('.js')){
    const rel=path.relative(packageDist,full).split(path.sep).join('/');
    copy[path.relative(root,full).split(path.sep).join('/')]='vendor/fbx-exporter/'+rel;
  }
 }
}
includeFBX(packageDist);
if(!Object.values(copy).includes('vendor/fbx-exporter/index.js'))throw Error('Missing published FBX entrypoint');
for(const [from,to] of [
 ['node_modules/@comfyorg/fbx-exporter-three/LICENSE','vendor/fbx-exporter/LICENSE'],
 ['node_modules/fflate/LICENSE','vendor/fflate/LICENSE']
]){if(!fs.existsSync(path.join(root,from)))throw Error('Missing third-party license: '+from);copy[from]=to;}
const files=[...Object.values(copy),'index.html','.nojekyll','service-worker.js','build-manifest.json'].sort();
if(fs.existsSync(out)){
 const p=path.join(out,'build-manifest.json');if(!fs.existsSync(p)||JSON.parse(fs.readFileSync(p)).owner!=='hg-static-viewer-build')throw Error('Unknown dist; refuse overwrite');
 const walk=dir=>fs.readdirSync(dir,{withFileTypes:true}).flatMap(v=>v.isDirectory()?walk(path.join(dir,v.name)):[path.relative(out,path.join(dir,v.name)).split(path.sep).join('/')]);
 if(walk(out).some(p=>!files.includes(p)&&!publicNames.includes(p)&&p!=='public-demo/release.json'))throw Error('Unexpected dist files; refuse delete');
}
const tmp=fs.mkdtempSync(path.join(root,'.build-'));
try{
 for(const [from,to] of Object.entries(copy)){const p=path.join(tmp,to);fs.mkdirSync(path.dirname(p),{recursive:true});fs.copyFileSync(path.join(root,from),p);}
 let html=fs.readFileSync(path.join(root,'index.html'),'utf8').replace('./node_modules/three/build/three.module.js','./vendor/three/three.module.js').replace('./node_modules/three/examples/jsm/','./vendor/three/addons/').replace('./node_modules/@comfyorg/fbx-exporter-three/dist/','./vendor/fbx-exporter/').replace('./node_modules/fflate/esm/browser.js','./vendor/fflate/esm/browser.js');
 if(html.includes('node_modules')||html.includes('<base'))throw Error('Unexpected module path');
 const importmap=html.match(/<script type="importmap">([\s\S]*?)<\/script>/)[1];
 const scriptHash=createHash('sha256').update(importmap).digest('base64');
 const csp=`default-src 'none'; script-src 'self' 'sha256-${scriptHash}'; style-src 'self'; img-src 'self' blob: data:; connect-src 'self'; worker-src 'self'; manifest-src 'self'; base-uri 'none'; form-action 'none'; object-src 'none'`;
 html=html.replace('<meta charset="UTF-8">',`<meta charset="UTF-8"><meta http-equiv="Content-Security-Policy" content="${csp}"><meta name="referrer" content="no-referrer">`);
 fs.writeFileSync(path.join(tmp,'index.html'),html);fs.writeFileSync(path.join(tmp,'.nojekyll'),'');
 const cached=files.filter(p=>!p.startsWith('public-demo/')&&!['service-worker.js','build-manifest.json','assets/sample.blend','.nojekyll','PUBLIC_SAMPLE.md'].includes(p));
 const version=sha(cached.map(p=>p+sha(fs.readFileSync(path.join(tmp,p)))).join(''));
 const sw=`// Generated allowlist: public resources only; no uploads, APIs, query strings or private drafts.
const PREFIX='hg-public-viewer-', CACHE=PREFIX+'${version}';
const urls=${JSON.stringify(cached)}.map(p=>new URL(p,self.registration.scope).href);
const root=self.registration.scope;
self.addEventListener('install',event=>event.waitUntil(caches.open(CACHE).then(cache=>cache.addAll(urls))));
self.addEventListener('activate',event=>event.waitUntil(Promise.all([caches.keys().then(keys=>Promise.all(keys.filter(k=>k.startsWith(PREFIX)&&k!==CACHE).map(k=>caches.delete(k)))),self.clients.claim()])));
self.addEventListener('fetch',event=>{
 if(event.request.method!=='GET')return;
 const key=event.request.url===root?new URL('index.html',root).href:event.request.url;
 if(!urls.includes(key))return;
 event.respondWith(caches.open(CACHE).then(cache=>cache.match(key)).then(hit=>hit||fetch(event.request)));
});
`;
 fs.writeFileSync(path.join(tmp,'service-worker.js'),sw);
 fs.writeFileSync(path.join(tmp,'build-manifest.json'),JSON.stringify({owner:'hg-static-viewer-build',base_path:'/HG-3D-CLOUD-AI/',public_data:'Reviewed synthetic sample and optional fixed public Qwen catalog only; no customer data',files:files.filter(p=>p!=='build-manifest.json').map(p=>({path:p,sha256:sha(fs.readFileSync(path.join(tmp,p)))}))},null,2));
 if(fs.existsSync(out))fs.rmSync(out,{recursive:true});fs.renameSync(tmp,out);console.log('Built static site: '+out+' at /HG-3D-CLOUD-AI/');
}catch(e){fs.rmSync(tmp,{recursive:true,force:true});throw e;}
