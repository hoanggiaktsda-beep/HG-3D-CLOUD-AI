import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';
const root=path.dirname(fileURLToPath(import.meta.url)),out=path.join(root,'dist');
const sha=b=>createHash('sha256').update(b).digest('hex');
const manifest=JSON.parse(fs.readFileSync(path.join(root,'public-assets.json')));
if(manifest.release_scope!=='synthetic_public_sample_only')throw Error('Public release scope required');
if(!Array.isArray(manifest.assets)||JSON.stringify(manifest.assets.map(a=>a.path).sort())!==JSON.stringify(['assets/sample-qa.json','assets/sample.glb']))throw Error('Both public sample hashes required');
for(const a of manifest.assets){
 if(!['assets/sample.glb','assets/sample-qa.json'].includes(a.path)||sha(fs.readFileSync(path.join(root,a.path)))!==a.sha256)throw Error('Public sample changed without review');
}
const glb=fs.readFileSync(path.join(root,'assets/sample.glb'));
if(glb.readUInt32LE(0)!==0x46546c67||glb.readUInt32LE(4)!==2||glb.readUInt32LE(8)!==glb.length||glb.readUInt32LE(16)!==0x4e4f534a)throw Error('Invalid GLB');
const json=JSON.parse(glb.subarray(20,20+glb.readUInt32LE(12)).toString().trim());
if([...(json.buffers||[]),...(json.images||[])].some(v=>v.uri))throw Error('External GLB resource not allowed');
const copy={ 'app.js':'app.js','style.css':'style.css','PUBLIC_SAMPLE.md':'PUBLIC_SAMPLE.md','assets/sample.glb':'assets/sample.glb','assets/sample-qa.json':'assets/sample-qa.json',
 'node_modules/three/build/three.module.js':'vendor/three/three.module.js','node_modules/three/build/three.core.js':'vendor/three/three.core.js',
 'node_modules/three/examples/jsm/controls/OrbitControls.js':'vendor/three/addons/controls/OrbitControls.js',
 'node_modules/three/examples/jsm/loaders/GLTFLoader.js':'vendor/three/addons/loaders/GLTFLoader.js',
 'node_modules/three/examples/jsm/utils/BufferGeometryUtils.js':'vendor/three/addons/utils/BufferGeometryUtils.js','node_modules/three/LICENSE':'vendor/three/LICENSE'};
const files=[...Object.values(copy),'index.html','.nojekyll','build-manifest.json'].sort();
if(fs.existsSync(out)){
 const p=path.join(out,'build-manifest.json');if(!fs.existsSync(p)||JSON.parse(fs.readFileSync(p)).owner!=='hg-static-viewer-build')throw Error('Unknown dist; refuse overwrite');
 const walk=dir=>fs.readdirSync(dir,{withFileTypes:true}).flatMap(v=>v.isDirectory()?walk(path.join(dir,v.name)):[path.relative(out,path.join(dir,v.name)).split(path.sep).join('/')]);
 if(walk(out).some(p=>!files.includes(p)))throw Error('Unexpected dist files; refuse delete');
}
const tmp=fs.mkdtempSync(path.join(root,'.build-'));
try{
 for(const [from,to] of Object.entries(copy)){const p=path.join(tmp,to);fs.mkdirSync(path.dirname(p),{recursive:true});fs.copyFileSync(path.join(root,from),p);}
 const html=fs.readFileSync(path.join(root,'index.html'),'utf8').replace('./node_modules/three/build/three.module.js','./vendor/three/three.module.js').replace('./node_modules/three/examples/jsm/','./vendor/three/addons/');
 if(html.includes('node_modules')||html.includes('<base'))throw Error('Unexpected module path');
 fs.writeFileSync(path.join(tmp,'index.html'),html);fs.writeFileSync(path.join(tmp,'.nojekyll'),'');
 fs.writeFileSync(path.join(tmp,'build-manifest.json'),JSON.stringify({owner:'hg-static-viewer-build',base_path:'/HG-3D-CLOUD-AI/',public_data:'Synthetic sample only; no customer data',files:files.filter(p=>p!=='build-manifest.json').map(p=>({path:p,sha256:sha(fs.readFileSync(path.join(tmp,p)))}))},null,2));
 if(fs.existsSync(out))fs.rmSync(out,{recursive:true});fs.renameSync(tmp,out);console.log('Built static site: '+out+' at /HG-3D-CLOUD-AI/');
}catch(e){fs.rmSync(tmp,{recursive:true,force:true});throw e;}
