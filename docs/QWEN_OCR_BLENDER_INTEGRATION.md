# Qwen + OCR → Blender: thử nghiệm độc lập

Workflow: `.github/workflows/vision-blender-integration.yml`.

Ba nguồn công khai cố định thuộc ba thiết kế khác nhau của OpenDesk: zerozero Desk,
AtFAB Five To Thirty Minute Chair và AtFAB One To Several Table. URL, SHA-256,
tác giả và giấy phép được ghi trong từng artifact. Chỉ thử phi thương mại;
các nguồn AtFAB có điều kiện BY-NC-SA 3.0 trên PDF. Giữ ghi công và giấy phép
khi chia sẻ bản vẽ hoặc mô hình phái sinh.

Qwen2-VL-2B chạy thật trên CPU, revision cố định, chỉ safetensors, không chạy mã
từ model. Đầu vào nhận diện là PNG raster từ PDF, không lấy CAD, đường vector
PDF hoặc JSON kích thước. Crop được chọn có giám sát; đây chưa phải tự đọc toàn
bộ tài liệu. Prompt không chứa kích thước, số lượng hoặc đáp án của thiết kế.
Tesseract chạy độc lập sau model trên đúng crop có cùng SHA-256.
Nếu model trả nội dung rỗng hoặc chỉ tên vai trò chat, thử lại tối đa một lần
trên cùng ảnh với yêu cầu đọc ngắn hơn; lưu nguyên cả hai lần. Không chọn câu
trả lời theo số mong muốn và không đưa OCR vào prompt thử lại.

Bộ kiểm chứng yêu cầu AI và OCR thống nhất kích thước tấm, chiều dày danh nghĩa,
số lượng và chú giải màu trước khi hiệu chỉnh tỷ lệ. OpenCV lấy đường bao từ
pixel; không tuyên bố Qwen đã tự suy ra toàn bộ contour. Khung tấm phải phù hợp
tỷ lệ hai trục. Thiếu hoặc mâu thuẫn dữ liệu thì chặn dựng, giữ CẦN XÁC NHẬN.

BLEND/GLB nếu được tạo chỉ là **các tấm rời tại vị trí sơ đồ cắt**, chưa phải
sản phẩm đã lắp ráp. Tên cấu kiện chỉ là ứng viên; chưa ánh xạ chắc chắn vào từng
tấm. Ký hiệu khoan chỉ là marker, không tự tạo đường kính hoặc lỗ vật lý.
Vị trí lắp, chi tiết khuất, bán kính dao và hình chiếu đứng/cạnh thiếu bằng chứng
đều giữ CẦN XÁC NHẬN. Chiều dày từ nhãn mm là danh nghĩa, không phải đo vật liệu.

Blender dựng mesh thật, kiểm từng đối tượng, mở lại BLEND và nhập lại GLB để đo
kích thước, vị trí và mesh kín. Chiếu tam giác từ mesh thực lên nguồn để đối
chiếu IoU. Sai số nội bộ dựng JSON không thay thế sai số pixel nguồn; IoU hình
chiếu tấm không chứng minh độ giống sản phẩm lắp ráp hay khả năng gia công.

Artifact có `trial.json`, `REPORT_VI.md`, bản đọc AI/OCR, ảnh nguồn, JSON dựng,
log Blender và kiểm định từng bộ phận; các file BLEND/GLB chỉ có khi vượt cổng.
Workflow hoàn tất có thể gồm trường hợp bị chặn hợp lệ: cần đọc `outputs_created`
và trạng thái từng mẫu, không lấy dấu xanh làm bằng chứng mọi mẫu dựng thành công.

Chỉ runner GitHub tiêu chuẩn miễn phí cho repository công khai, timeout 20 phút,
giới hạn tải model 6 GB, artifact giữ một ngày. Không API trả phí, không render,
không kết nối website, không dữ liệu khách hàng, không thay đổi 18 vai trò.
Không tải cache model vào artifact. Kiểm thử giao thức có fixture được đánh dấu;
fixture không được dùng làm bằng chứng nhận diện ảnh thật.
