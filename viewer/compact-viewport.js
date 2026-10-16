// Compact workspace: hide optional inspector without deleting its editing controls.
const root=document.getElementById('chatgpt-studio');
const inspector=document.getElementById('hg-inspector-collapsible');
const close=document.getElementById('hg-inspector-close');
const open=document.getElementById('hg-inspector-open');
function toggle(show){
 if(!root||!inspector)return;
 root.classList.toggle('hg-inspector-hidden',!show);
 inspector.hidden=!show;
 open.hidden=show;
 // Three.js viewport resize follows normal window resize listeners.
 requestAnimationFrame(()=>window.dispatchEvent(new Event('resize')));
}
close?.addEventListener('click',()=>toggle(false));
open?.addEventListener('click',()=>toggle(true));
toggle(false);
