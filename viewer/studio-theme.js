// HOANGGIA STUDIO navigation semantics. No network access, no local data stored.
const labels={
 'create-model':'TẠO MÔ HÌNH 3D',
 'chatgpt-studio':'XƯỞNG CHATGPT',
 'sample-viewer':'XEM MÔ HÌNH MẪU',
 'public-demo':'THƯ VIỆN KIỂM ĐỊNH'
};
function updateRoute(){
 const id=decodeURIComponent(location.hash.slice(1));
 const active=Object.prototype.hasOwnProperty.call(labels,id)?id:null;
 const crumb=document.getElementById('hg-crumb');
 if(crumb)crumb.textContent=active?labels[active]:'TỔNG QUAN';
 document.querySelectorAll('[data-hg-route]').forEach(link=>{
  if(active&&link.dataset.hgRoute===active)link.setAttribute('aria-current','page');
  else link.removeAttribute('aria-current');
 });
}
window.addEventListener('hashchange',updateRoute);
updateRoute();
