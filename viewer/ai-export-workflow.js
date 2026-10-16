// HG-3D-CLOUD-AI: client-side five-step handoff. No image inference or remote uploads.
const $=id=>document.getElementById(id);
const status=$('hg-flow-status'),out=$('hg-flow-output');
const platformNames={chatgpt:'ChatGPT',meshy:'Meshy',tripo:'Tripo',hunyuan:'Hunyuan3D',blender:'Blender',generic:'nền tảng AI 3D khác'};
const formatNames={fbx:'FBX',obj:'OBJ',glb:'GLB',blend:'BLEND',stl:'STL'};
function photos(){return [...($('source-images')?.files||[])].filter(f=>f.type.startsWith('image/'));}
function dims(){
 const ids=['hg-width','hg-depth','hg-height'];
 return ids.map(id=>{const e=$(id);const n=Number(e.value);return e.value.trim()&&Number.isFinite(n)&&n>0&&n<=100000?n:null;});
}
function build(analysisOnly=false){
 const files=photos(),[w,d,h]=dims();
 if(!files.length)throw Error('Vui lòng tải ít nhất một ảnh sản phẩm trước.');
 const type=$('hg-flow-type').selectedOptions[0].textContent;
 const format=formatNames[$('hg-flow-format').value];
 const platform=platformNames[$('hg-flow-platform').value];
 const confirmed=$('hg-confirm-dims').checked;
 const measurements=[w,d,h].map((n,i)=>(['Dài X','Sâu Y','Cao Z'][i])+': '+(n===null?'CHƯA CÓ':n+' mm')).join('; ');
 const preface=[
 'HOANGGIA 3D CLOUD AI — '+(analysisOnly?'PHÂN TÍCH ẢNH NGUỒN':'YÊU CẦU DỰNG MÔ HÌNH 3D THEO ẢNH'),
 'Tôi sẽ đính kèm '+files.length+' ảnh nguồn riêng. Tên ảnh: '+files.map(f=>f.name).join(', ')+'.',
 'BƯỚC 1: Quan sát chính ảnh đính kèm; mô tả loại sản phẩm, hình dáng, số bộ phận, chân, hộc, tay nắm, đường cong, vật liệu và những chi tiết nhìn thấy. Không dùng mẫu 3D mặc định thay sản phẩm.',
 'BƯỚC 2: Phân loại từng đặc điểm thành XÁC NHẬN (quan sát được), SUY LUẬN và CẦN XÁC NHẬN. Nếu không xem được ảnh, phải báo rõ.',
 'BƯỚC 3: Kiểu loại mong muốn: '+type+'. Nếu không khớp ảnh, cảnh báo trước khi dựng.',
 'BƯỚC 4: '+measurements+'. Trạng thái số đo: '+(confirmed?'Người dùng xác nhận':'CHƯA XÁC NHẬN')+'. Không tự biến pixel thành mm hoặc tự bịa kích thước.',
 'Giữ hình học nhìn thấy, tỷ lệ và cấu tạo có bằng chứng; đánh dấu các phần khuất, không tự tạo chi tiết gia công.'
 ];
 if(analysisOnly)return preface.concat('Hãy trả báo cáo nhận diện hình học và các số đo còn thiếu trước khi tạo model.').join('\n\n');
 return preface.concat(
 'BƯỚC 5: Nền tảng đích: '+platform+'. Định dạng mong muốn: '+format+'.',
 $('hg-flow-platform').value==='blender'||$('hg-flow-platform').value==='chatgpt'?
 'Nếu môi trường hỗ trợ tạo mã, hãy cung cấp mã Python cho Blender dựng mesh có tên từng bộ phận, trục Z đứng, đơn vị mm; kiểm tra và xuất '+format+' khi công cụ hỗ trợ. Không tuyên bố đã tạo file nếu chưa thực thi.':
 'Tạo mô hình 3D từ ảnh tham chiếu với hình khối đúng sản phẩm, giữ đúng tỷ lệ, chi tiết quan sát được và không thêm chi tiết không có chứng cứ. Dùng ảnh gốc làm điều kiện tạo hình; kiểm tra định dạng '+format+' có được nền tảng hỗ trợ trước khi xuất.',
 'Đầu ra cần có: danh sách bộ phận, giả định, điểm chưa chắc chắn, phương pháp kiểm tra bằng các góc nhìn, và file '+format+' nếu nền tảng thực sự hỗ trợ. Không cam kết chính xác tuyệt đối từ một ảnh.',
 'Nếu nền tảng không hỗ trợ '+format+', hãy nêu định dạng trung gian khả dụng và bước chuyển đổi; không đổi phần mở rộng file để giả lập.'
 ).join('\n\n');
}
$('hg-flow-analyze').addEventListener('click',async()=>{try{const s=build(true);out.value=s;await navigator.clipboard.writeText(s);status.textContent='Đã sao chép lệnh phân tích. Dán cùng ảnh gốc vào ChatGPT.';}catch(e){status.textContent=e.message;}});
$('hg-flow-generate').addEventListener('click',()=>{try{out.value=build();status.textContent='Đã tổng hợp prompt cho nền tảng đã chọn. Đính kèm ảnh gốc khi gửi prompt.';}catch(e){status.textContent=e.message;}});
$('hg-flow-copy').addEventListener('click',async()=>{if(!out.value)return status.textContent='Hãy tổng hợp prompt trước.';try{await navigator.clipboard.writeText(out.value);status.textContent='Đã sao chép prompt.';}catch{out.focus();out.select();status.textContent='Hãy sao chép văn bản đã chọn thủ công.';}});
$('hg-flow-download').addEventListener('click',()=>{if(!out.value)return status.textContent='Hãy tổng hợp prompt trước.';const url=URL.createObjectURL(new Blob([out.value],{type:'text/plain;charset=utf-8'}));const a=document.createElement('a');a.href=url;a.download='HG-3D-AI-PROMPT.txt';a.click();setTimeout(()=>URL.revokeObjectURL(url),30000);status.textContent='Đã tải prompt dạng văn bản.';});
$('source-images').addEventListener('change',()=>{$('hg-flow-photo').textContent=photos().length?'Đã chọn '+photos().length+' ảnh. Chưa phân tích tự động.':'Chưa chọn ảnh nguồn.';});
