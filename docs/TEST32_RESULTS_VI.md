# TEST 32 — giao diện đa kích thước và PWA

Trạng thái: **đã triển khai và kiểm tra website thật thành công**, trong phạm vi viewer mẫu công khai và trình duyệt Chromium. Chưa nghiệm thu thiết bị thật hoặc AI từ ảnh.

## Phạm vi và bằng chứng

Director giữ nguyên mô hình 18 vai trò; không đổi mã nhận diện hoặc dữ liệu TEST 30. TEST 30 vẫn **CẦN XÁC NHẬN**, không chạy lại.

| Yêu cầu | Quyết định |
|---|---|
| Giữ nguyên | Viewer GLB, 18 vai trò, trạng thái TEST 30 |
| Được thay đổi | Responsive, PWA, tải mẫu BLEND, liên kết Actions, kiểm thử và triển khai Pages |
| Kích thước chắc chắn | Mẫu tổng hợp: 1800 × 450 × 850 mm, không phải số đo từ ảnh khách hàng |
| Chưa chắc chắn | Liên kết, chi tiết khuất, nghiệm thu cấu tạo của mẫu |
| Yêu cầu thêm dữ liệu | Backend riêng và AI được cấp quyền trước khi gửi ảnh thật |

BLEND được nhập từ GLB mẫu công khai, lưu và mở lại bằng Blender 4.3.2: 8 mesh; kích thước thực 1800,000072 × 449,999988 × 849,999964 mm. Không render. File BLEND là mesh chỉnh sửa được, không phục hồi lịch sử tham số gốc. SHA-256 khóa trong `viewer/public-assets.json`; build chỉ đóng gói danh sách tài nguyên công khai.

## Ma trận nền tảng

Tất cả thử nghiệm dùng Chromium headless trên Linux, phần mềm WebGL SwiftShader. Đây là giả lập kích thước, user agent và đầu vào; **không phải thiết bị thật, Safari, Windows hoặc macOS thật**.

| Cấu hình | Kiểm tra |
|---|---|
| iPhone 320 × 568, 390 × 844 | Không tràn ngang, camera, nút zoom, chọn ảnh, yêu cầu, GLB/BLEND; cảm ứng 390 × 844 |
| iPad 820 × 1180, 1180 × 820 | Responsive, góc camera, xoay một ngón và zoom hai ngón; tải file ở cấu hình dọc |
| Windows 1366 × 768 | Giả lập màn hình/UA, camera, zoom, yêu cầu, GLB/BLEND |
| macOS 1440 × 900 | Giả lập màn hình/UA, camera, zoom, yêu cầu, GLB/BLEND |

Tải GLB/BLEND được bắt bằng sự kiện download thực và so SHA-256 với mẫu. Đổi chiều màn hình không gây tràn ngang. Kiểm thử desktop 1440 × 1000 bổ sung chuột xoay và năm góc camera. Việc lưu file vào ứng dụng Tệp iOS, cài màn hình chính, trackpad và Safari thật vẫn chưa kiểm chứng.

## PWA và bảo mật

Manifest có scope/start URL tương đối, icon 192/512 và chế độ standalone. Chỉ hiện nút cài nếu trình duyệt phát sự kiện cài thật; iOS có hướng dẫn thao tác thủ công. Service worker chỉ cache danh sách tài nguyên mẫu công khai tại phạm vi `/HG-3D-CLOUD-AI/`. Không cache POST, API, URL truy vấn, blob ảnh, bản nháp hoặc BLEND. BLEND cần mạng. Cập nhật áp dụng khi đóng tab cũ.

Kiểm thử bật ngoại tuyến và tải lại trang vẫn đo GLB/hiển thị mẫu; ảnh chọn và yêu cầu không tồn tại sau reload. Không lưu localStorage/sessionStorage, không gửi ảnh hoặc tạo công việc. CSP chặn script bên ngoài, `unsafe-eval`, form submit và object; importmap dùng SHA-256. Không đóng gói khóa hoặc local backend client. Báo cáo có nội dung HTML độc hại được hiển thị dạng văn bản, không tự nghiệm thu.

## Cloud Worker và phần chưa hoạt động

Link trên website mở workflow TEST 31 công khai trong GitHub, nơi có trạng thái và Artifacts thật; đăng nhập do GitHub quản lý, không có token trong JavaScript. Artifact có thời hạn lưu, không phải kho lâu dài. Đây không phải cầu nối gửi ảnh từ website. Không chạy thêm công việc AI hoặc TEST 30 để minh họa tiến độ.

Ảnh chọn và yêu cầu chỉ là bản nháp cục bộ. Gửi ảnh, AI tự đọc ảnh, tiến độ công việc mới, dựng lại và nhận GLB/BLEND từ ảnh vẫn **CHƯA KẾT NỐI**. Không giả lập nhận diện hay công việc thành công. Viewer/QA và file tải xuống là mẫu công khai, không phải kết quả ảnh vừa chọn.

## Kiểm thử và triển khai

**19/19 kiểm thử viewer cục bộ đạt**, không bỏ qua kiểm thử (55,558 giây). Bộ kiểm thử gồm responsive, xoay/zoom, ảnh cục bộ, đầu vào sai, chống chèn HTML, lỗi GLB/QA, tải file đúng checksum, ngoại tuyến, bảo mật cache, build lặp lại và hợp đồng workflow. Đã sửa bộ chờ kiểm thử để tương thích CSP không cho `eval`; giữ nguyên CSP.

Mã phát hành: commit `ff9c3cc7abf2458163c3322b2372da564c4e32df`, đã push vào `main` của đúng HG-3D-CLOUD-AI.

[Run 38703733909](https://github.com/hoanggiaktsda-beep/HG-3D-CLOUD-AI/actions/runs/38703733909) **Success**, tổng 3 phút 19 giây:

| Job | Kết quả thực |
|---|---|
| build | Success; kiểm thử viewer đạt trước upload, 1 phút 52 giây |
| deploy | Success; triển khai Pages, 35 giây |
| verify | Success; kiểm tra HTTPS website thật, 40 giây |

Website: **https://hoanggiaktsda-beep.github.io/HG-3D-CLOUD-AI/**.

Bước `Verify live Pages bytes, GLB/BLEND downloads and offline viewer` đã thành công trên runner GitHub: kiểm SHA-256 21 tài nguyên được liệt kê trong manifest, mở Chromium ở 390 × 844, xác nhận chiều cao 850 mm, đổi sang mặt bằng, tải GLB/BLEND thực và so toàn bộ bytes, chờ service worker rồi ngắt mạng và reload GLB thành công. Đây là kiểm tra website đã triển khai, không phải chỉ localhost. Chưa tải gói artifact cloud về Codex; trạng thái từng bước được kiểm tra trên trang Actions công khai.

Artifact Pages `github-pages`: 545 KB; SHA-256 `844742225b7190cab9b9ac44c36acff2e3e6fd80cf9489dc398ceb401926652c`. Chỉ có 22 file tĩnh công khai (bao gồm build-manifest), không có ảnh đầu vào khách hàng.

Workflow `.github/workflows/deploy-pages.yml` yêu cầu build + toàn bộ kiểm thử viewer đạt trước khi upload duy nhất `viewer/dist`. Job sau deploy kiểm tra website HTTPS thật: SHA-256 từng tài nguyên, tải file thực, camera, trạng thái ngắt kết nối và reload ngoại tuyến. Mạng Codex chặn tên miền GitHub Pages (403) ngay cả sau thử nâng quyền và cấp quyền mạng; xác minh live được giao runner Actions, không thay bằng localhost.

Không chỉnh sửa repository khác; không API trả phí, không render, không đưa dữ liệu khách hàng lên Pages/Actions.
