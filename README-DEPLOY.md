# HOANGGIA FURNITURE 3D AI — cấu trúc mới

Ứng dụng tĩnh không phụ thuộc build: index.html, src/style.css, src/app.js.

## Chức năng hiện có
- Giao diện tiếng Việt, responsive, đường dẫn #create-model.
- Chọn và xem trước ảnh ngay trên máy (không upload).
- Cấu hình đồ nội thất, kích thước, mức độ chi tiết, định dạng FBX/OBJ.
- Sinh, sao chép và tải đặc tả dựng 3D.

## Chưa có
- Phân tích hình ảnh bằng AI, tạo mesh 3D, xem 360°, xuất FBX/OBJ thực tế.
- Cần backend hoặc dịch vụ dựng hình tương thích và bước kiểm tra tệp thật trước khi mở các tính năng này.

## GitHub Pages
Settings → Pages → Deploy from a branch → main → /(root) → Save.
Không cần GitHub Actions. Không đưa API key vào frontend.
