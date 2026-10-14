# Quy trình ảnh → scene 3D (mục tiêu triển khai trong Codex)

## Nhóm đầu vào

1. Ảnh 1 vật thể (sofa, bàn, cabinet, console, giường, ghế); 2. ảnh phối cảnh không gian; 3. ảnh chụp bản vẽ kỹ thuật; 4. bản vẽ layout nội thất; 5. nhiều ảnh góc khác nhau.

## Các bước cho Codex

- Kiểm tra có ảnh đính kèm, file có đọc được không, người dùng có chú thích hay kích thước không.
- Lấy thông tin thật từ ảnh, tách từng đối tượng với vai trò và quan hệ tương đối. Không suy kích thước tuyệt đối chỉ từ pixel khi không có vật chuẩn/cỡ thực.
- Tách dữ liệu `QUAN SÁT`, `XÁC NHẬN TỪ KÍCH THƯỚC`, `SUY LUẬN`, `CẦN XÁC NHẬN`.
- Ảnh bản vẽ: ưu tiên dimension strings, chain-dimension consistency, tỷ lệ; nếu giấy bị nghiêng thì coi số đo đọc được là dữ kiện, không coi ảnh đã rectified nếu chưa kiểm.
- Layout: xác định trục, chiều dài rộng, tường, cột, cửa, đồ nội thất, cao độ; khi không có mặt đứng/section thì ghi chưa xác minh chiều cao/chi tiết đứng.
- Kiểm tra tương quan các hình chiếu; nếu xung đột thì không tự chọn tùy tiện.
- Tạo JSON scene theo SCENE_SCHEMA.md, giữ vị trí, góc nhìn và tỷ lệ; nội thất đóng vai trò placeholder khi chưa đủ ảnh để dựng chính xác.
- Không ghi 'đã tự dựng giống 100%' nếu chỉ tạo primitives.
- Dựng, đối chiếu kích thước thực, chụp bằng chứng viewport (không render), xuất file và QA.

## Ví dụ lệnh của người dùng

"Hãy dựng chiếc console trong ảnh. Dài 1800, sâu 450, cao 900. Giữ đúng tỷ lệ; những phần không thấy hãy đánh dấu để tôi duyệt. Xuất GLB và BLEND; không render."

"Dựng layout trong ảnh thành mô hình 3D. Sử dụng kích thước ghi trên bản vẽ; chưa có chiều cao trần thì hỏi trước hoặc tạo DRAFT với giả định công khai."

## Nhiệm vụ phát triển còn thiếu

Giai đoạn đầu: cho Codex có khả năng nhìn ảnh và tạo JSON scene một cách tường minh. Sau đó phát triển suy ra hình học, kỹ thuật polygon/curve, kết hợp nhiều ảnh, OCR có kiểm định và bộ model khác khi được cấp quyền. Tách pipeline trích xuất ảnh với pipeline dựng — hai bước phải kiểm định độc lập. Không có ảnh mà tuyên bố đã phân tích ảnh là FAIL.
