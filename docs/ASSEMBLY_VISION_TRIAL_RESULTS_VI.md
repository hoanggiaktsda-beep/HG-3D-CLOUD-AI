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

Không render, không thay đổi website hoặc 18 vai trò, không dùng dữ liệu khách
hàng, không gọi API trả phí. Chưa nghiệm thu sản phẩm lắp ráp hoặc độ chính xác
gia công. Bán kính dao, đường kính khoan, ánh xạ tên tấm và vị trí lắp thiếu dữ
liệu vẫn CẦN XÁC NHẬN.
