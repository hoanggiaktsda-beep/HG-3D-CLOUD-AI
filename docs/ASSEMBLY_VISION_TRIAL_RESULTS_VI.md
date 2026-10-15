# Kết quả thử nghiệm Qwen + OCR → Blender

## Phương pháp và giới hạn

Chỉ nhận ảnh raster từ ba PDF công khai độc lập; không dùng CAD hay JSON đáp án.
Qwen2-VL-2B-Instruct revision `895c3a49bc3fa70a340399125c650a463535e71c`
chạy CPU thật, lượng tử hóa int8 các lớp Linear ngôn ngữ; OCR Tesseract chạy riêng.
ROI do người phát triển chọn có giám sát. Đây chưa phải tự phân trang và tự chọn
vùng đọc hoàn toàn. Quy trình và giấy phép: [tài liệu tích hợp](QWEN_OCR_BLENDER_INTEGRATION.md).

## Lượt đầu — không xuất mô hình

[Actions 38693016821](https://github.com/hoanggiaktsda-beep/HG-3D-CLOUD-AI/actions/runs/38693016821),
commit `4c91308`, hoàn tất thành công về thực thi; **0/3 mẫu được phép dựng**.

| Mẫu công khai | Bằng chứng thực tế | Kết quả |
|---|---|---|
| zerozero Desk | Qwen không đọc được nhãn bộ phận hữu ích; không có bộ dữ liệu tỷ lệ tấm đầy đủ | Chặn, không BLEND/GLB |
| AtFAB Five To Thirty Minute Chair | AI/OCR cùng đọc 4’×8’, nhãn 18.5 mm và chú giải màu. Riêng bảng số lượng: AI chỉ trả `system`, OCR đọc được bảng | Chặn; không lấy OCR thay cho AI |
| AtFAB One To Several Table | AI/OCR cùng đọc hai tấm, nhãn 18.5 (3/4”) và chú giải; thiếu kích thước tấm được xác nhận | Chặn, không tự giả định cỡ tấm tiêu chuẩn |

Qwen còn mô tả sai/ngắt giữa chừng nhãn bộ phận ở hình tháo lắp ghế. Các mô tả
này không được dùng để tự ánh xạ bộ phận hoặc lắp ráp. Giữ CẦN XÁC NHẬN.

Artifact `hg-public-assembly-38693016821-1`, 15.9 MB, SHA-256
`84d94b1a34c0e0de90a9c91f861db84a4a380ce15ded6ba882abe28b64e1e21c`.
Đã kiểm tra annotations và thông tin artifact công khai của GitHub; chưa tải
artifact về Codex vì đường API tải yêu cầu quyền truy cập không sẵn có.

## Sửa lỗi và kiểm thử

Commit `6bb58f4`: với phản hồi trống/tên vai trò chat, thử đọc lại tối đa một lần
bằng prompt ngắn trên cùng ảnh, trước khi chạy OCR; lưu cả hai phản hồi. Không
thêm đáp án vào prompt hoặc thay bằng phản hồi soạn sẵn. Sau sửa: **66/66** kiểm
thử đạt tại Codex, gồm Blender thật, kiểm tra từng mesh, mở lại BLEND, nhập lại
GLB, đối chiếu đường bao nguồn, bắt sai vị trí và chặn sai/mâu thuẫn bằng chứng.

Thử riêng bộ CV/Blender cục bộ trên ảnh ghế 4800 px đã dựng 20 tấm, hai đường
cắt trong; IoU đường bao nhỏ nhất 0.9978925. Đây là kiểm tra thành phần, **không
phải bằng chứng Qwen nhận diện thành công** và không thay thế lượt chạy AI thật.

## Lượt hai — phát hiện lỗi đọc bảng Markdown

[Actions 38693712111](https://github.com/hoanggiaktsda-beep/HG-3D-CLOUD-AI/actions/runs/38693712111),
commit `6bb58f4`, thực thi thành công trong 7 phút 20 giây; **0/3 mẫu xuất mô hình**.
Qwen đọc được dòng `| Total per File | 20 | 1238 + 54 holes |`, khớp Tesseract,
nhưng parser chỉ nhận văn bản thuần nên chặn. Đây là lỗi xử lý định dạng, không
phải thiếu bằng chứng số lượng ở lượt này. Sửa bằng bỏ ký tự định dạng Markdown,
giữ nguyên số/dấu/đơn vị; thêm kiểm thử chặn số âm và số lượng AI/OCR mâu thuẫn.

Phản hồi mô tả nhãn cấu kiện vẫn sai và model còn tự thêm lời khuyên vào phần
vật liệu. Chỉ các trường số và chú giải có đối chứng OCR mới được sử dụng;
không chuyển phần diễn giải thêm này thành hình học.

Artifact `hg-public-assembly-38693712111-1`, 15.9 MB, SHA-256
`baf6b55ddad8f480f1bab169ce62149e0ba04e59cd766a5def906d95382fa364`.
Đã xác minh qua annotations/trạng thái GitHub; chưa tải artifact về Codex.

## Lượt ba — đã chạy toàn tuyến tới BLEND/GLB thật

[Actions 38694666996](https://github.com/hoanggiaktsda-beep/HG-3D-CLOUD-AI/actions/runs/38694666996),
commit `2dd6a11`, **Success**, thời gian 4 phút 54 giây. Kiểm thử hồi quy Blender
và bước Qwen/OCR/worker/kiểm định/upload đều đạt.

| Mẫu | Kết quả thực tế |
|---|---|
| Desk | BLOCKED_NEEDS_CONFIRMATION, không xuất mô hình |
| Chair | BUILT_UNASSEMBLED_PARTS_NEEDS_REVIEW, xuất BLEND/GLB thật |
| Table | BLOCKED_NEEDS_CONFIRMATION, không xuất mô hình |

Với ghế, Qwen và OCR thống nhất tấm 4’×8’ → 1219,2×2438,4 mm, chiều dày danh
nghĩa 18,5 mm, tổng 20 chi tiết và chú giải đỏ/cyan/xanh lá. OpenCV lấy contour
từ pixel sau khi vượt cổng đối chứng; không dùng CAD hoặc kích thước JSON gốc.
20 tấm tương ứng sơ đồ cắt cho hai ghế, **chưa lắp ráp**.

Worker dựng 20 mesh kín, hai đường cắt trong và 64 marker khoan; không tạo lỗ
khoan vật lý khi thiếu đường kính. Kiểm kích thước/vị trí từng mesh và chiếu
tam giác mesh thực về ảnh nguồn: IoU nhỏ nhất **0,9978925343**. Sai số nội bộ lớn
nhất giữa mesh và JSON **0,00012015 mm**; đây là sai số tính toán, không phải
dung sai thiết kế. Ước lượng hai pixel nguồn khoảng **1,52162 mm**, chưa tính
sai lệch in/scan hoặc đường nét. Không có kích thước dài/rộng độc lập từng tấm
hay hình chiếu đứng/cạnh sản phẩm hoàn chỉnh để nghiệm thu.

BLEND được mở lại và GLB được nhập lại bằng Blender: **PASS**. Đầu ra trong
artifact: `chair/build/cut_layout.blend`, `chair/build/cut_layout.glb`,
`chair/build/part_qa.json`; kèm `chair/cut_layout.json`, `chair/readings.json`,
ảnh nguồn và `REPORT_VI.md`.

Ở lượt này AI đọc được tổng 20 nhưng bỏ cột chiều dài cắt và tổng lỗ. OCR đọc
54 lỗ trong bảng, trong khi CV thấy 64 ký hiệu: số lỗ chưa được AI đối chứng,
không dùng để dựng lỗ hay nghiệm thu. Nhãn bộ phận trong hình tháo lắp vẫn bị
AI đọc sai; ánh xạ tên tấm, vị trí lắp, bán kính bo/dao, đường kính và chiều sâu
lỗ đều **CẦN XÁC NHẬN**. Chưa kiểm chứng ảnh phối cảnh hoặc sản phẩm nội thất
bằng quy trình này. Một mẫu dựng tấm rời thành công không chứng minh tự dựng
hoàn chỉnh nhiều loại đồ nội thất.

Artifact **hg-public-assembly-38694666996-1**, **16.9 MB**, SHA-256
`8bc05bb8e29d6fac6abdf668717f5d4c717b70a1429c04fd2867dab6a8b612c9`,
giữ một ngày theo workflow. Đã kiểm tra trạng thái, annotations kết quả thật
do worker tính và thông tin artifact trên GitHub. Chưa tải artifact về Codex
để mở kiểm tra thủ công lần nữa; không tuyên bố đã thực hiện bước đó.

Không render, không thay đổi website hoặc 18 vai trò, không dùng dữ liệu khách
hàng, không gọi API trả phí. Chưa nghiệm thu sản phẩm lắp ráp hoặc độ chính xác
gia công. Bán kính dao, đường kính khoan, ánh xạ tên tấm và vị trí lắp thiếu dữ
liệu vẫn CẦN XÁC NHẬN.
