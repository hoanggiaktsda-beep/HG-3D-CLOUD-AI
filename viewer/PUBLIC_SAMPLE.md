# Tài nguyên công khai đã rà soát — TEST 32

GLB console 1800 × 450 × 850 mm và QA JSON là mẫu tổng hợp của dự án, không chứa dữ liệu khách hàng. BLEND là mesh chỉnh sửa được nhập từ chính GLB này bằng scripts/export_public_viewer_blend.py, đo lại 8 mesh trong Blender 4.3.2 và mở lại file; không phải scene tham số gốc. Sai số tổng thể dưới 0,001 mm; cấu tạo vẫn CẦN XÁC NHẬN.

public-assets.json khóa SHA-256 đúng ba file mẫu. Website chỉ đóng gói danh sách cho phép trong build.mjs, không sao chép outputs, inputs, ảnh khách hàng, khóa hoặc local-client.js. Hai icon HG do dự án tạo. Three.js kèm giấy phép MIT.

PWA chỉ cache danh sách tài nguyên công khai ở phạm vi /HG-3D-CLOUD-AI/. Không cache file ảnh chọn, yêu cầu, POST, URL truy vấn, API hay BLEND. Tải BLEND cần mạng. Không lưu bản nháp vào localStorage, IndexedDB hoặc Cache Storage. Cập nhật PWA sau khi đóng các tab cũ.

Link Cloud Worker dẫn tới GitHub Actions công khai và đăng nhập do GitHub quản lý. Không có token trong JavaScript, không gửi ảnh cho Actions, không tạo công việc từ website. Dịch vụ ảnh riêng và AI vẫn CHƯA KẾT NỐI. TEST 30 giữ CẦN XÁC NHẬN; 18 vai trò không thay đổi.
