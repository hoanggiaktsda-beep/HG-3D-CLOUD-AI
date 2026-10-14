# QA chuyên nghiệp — tiêu chuẩn nghiệm thu

## 4 cổng kiểm tra

**G1 Dữ liệu**: cấu trúc đúng, đơn vị mm, mỗi kích thước có nguồn/dung sai, đầy đủ hình chiếu bắt buộc; không tự tăng độ tin cậy.

**G2 Scene**: thực thi Blender thật, file .blend mở được, export GLB/FBX không lỗi, mesh hợp lệ, đo bbox thực ở world-space, số đối tượng/cấu kiện đúng, khớp topology và tỷ lệ UV, texture không bị thiếu.

**G3 Đối chiếu**: cho phép khóa camera, chụp viewport góc gốc/phụ, so hình với ảnh bằng phương pháp được xác minh, liệt kê khác biệt và chỗ thiếu. Không dùng render, hình viewport chỉ là bằng chứng trực quan.

**G4 Phê duyệt**: báo cáo HTML+JSON, nguồn bản vẽ, kích thước, sai số, trạng thái; mọi chi tiết chưa xác minh hoặc lỗi vượt ngưỡng → chặn trạng thái FINAL.

## Các trạng thái

- `PREPARED`: job/scene hợp lệ, chưa dựng.
- `BUILT`: Blender tạo scene thật và đã xuất file.
- `QA_FAILED`: có lỗi kỹ thuật hoặc sai kích thước.
- `NEEDS_REVIEW`: dữ kiện không đầy đủ; user cần xét.
- `APPROVED`: chỉ do người dùng hoặc quy tắc rõ đã được uỷ quyền, dựa trên bằng chứng G1-G4.

Gói khởi tạo chỉ đánh giá input JSON, có thể xuất BLEND/GLB qua Blender khi môi trường sẵn sàng; chưa có đo bbox, so sánh ảnh, approval thật. Không thể coi `SPEC_VALIDATED` là mô hình hoàn chỉnh.

## Tiêu chuẩn riêng theo loại

- Sofa/ghế: silhouette, tay/tựa/đệm/chân, tỷ lệ và vật liệu, không giả thương hiệu.
- Bàn: top, leg, base, edge, joinery, độ dày/tỷ lệ.
- Tủ: kích thước, số cánh/ngăn, khe hở, vật liệu/veneering, cấu tạo mặt sau.
- Layout: closure of wall loops, kích thước chuỗi, vị trí cửa/column, không cấn nội thất, chiều cao cần có nguồn.
- Phòng/biệt thự: trục/lưới, cốt sàn/trần, openings, thiết bị, vật liệu, camera và môi trường có căn cứ.

Không sử dụng AI tự chấm điểm mơ hồ để báo ‘chuẩn 100%’.
