# TẠO MÔ HÌNH 3D — trạng thái kết nối thật

Giao diện mới giữ viewer mẫu và thêm chọn ảnh thiết bị, loại ảnh, nội dung yêu cầu và kích thước người dùng xác nhận. Ảnh PNG/JPEG/WebP được kiểm tra signature và giải mã, hiển thị qua blob URL trên trình duyệt. Tối đa 8 ảnh, 20 MB/ảnh, tổng 60 MB, 25 megapixel/ảnh. HEIC/HEIF chưa hỗ trợ; iPhone cần xuất JPEG. Chưa upload ảnh tới máy chủ. Không lưu ảnh/yêu cầu vào localStorage/sessionStorage hay repository. Rời trang/bỏ ảnh thu hồi blob URL; đóng phiên mất bản nháp.

`viewer/model-service.js` định nghĩa các thao tác createJob, getJob, requestRevision, getArtifacts và capabilities. Tất cả thao tác công việc hiện trả BackendUnavailableError; không gọi mạng, không sinh job ID, progress, artifacts hoặc phản hồi AI giả. Không có cờ frontend để bật gửi ảnh khi chưa kết nối dịch vụ thật. Các nút gửi/dựng lại bị khóa; nội dung yêu cầu chỉ là bản nháp cục bộ, chưa được gửi hoặc thực hiện.

Giao diện phải luôn nói CHƯA KẾT NỐI khi chưa có đầy đủ backend xác thực, AI thị giác được cấp quyền, worker Blender và storage riêng. Các bước tiến độ đều CHƯA THỰC HIỆN, chưa có báo cáo hay GLB từ ảnh chọn. Viewer mẫu và báo cáo mẫu bên trên không phải kết quả ảnh người dùng.

## Hợp đồng tích hợp cần hoàn thiện trước khi mở chức năng

Không có backend hoạt động trong bản phát hành này. API dự kiến (chưa triển khai):

- GET /capabilities: ready từng dịch vụ, không gửi secrets cho browser.
- POST /jobs: multipart ảnh đã cấp quyền, input_type, instruction, user-confirmed measurements; tạo job riêng theo người dùng và checksum nguồn.
- GET /jobs/{id}: trạng thái thật, stage, progress nếu đo được (có thể null), lỗi và mục cần xác nhận. Backend phải kiểm tra ownership.
- POST /jobs/{id}/revisions: chỉ thị sửa, base_version; tạo version mới, không ghi đè file gốc. Trạng thái thực, không phần trăm giả.
- GET /jobs/{id}/artifacts: URL riêng có thời hạn cho BLEND/GLB/QA, không URL GitHub công khai; trả về sau build/verification thật.

Luồng worker cần nối với intake/vision schema và Blender hiện có: nhận ảnh → AI thật với provenance → confirmed/inferred/needs_confirmation theo từng thuộc tính → chặn khi thiếu dữ liệu → job Blender không render → đo từng object → QA → artifact riêng → viewer. Không tự chuyển đề xuất của AI thành confirmed. Giữ Director + 17 chuyên gia; không giả vờ 18 agent đã chạy. Backend phải xác thực, phân quyền, giới hạn file, kiểm tra định dạng và lưu riêng; metadata người dùng gửi không được tự chứng nhận dữ liệu.

GitHub Pages chỉ là static viewer, không chạy Python/Blender. Chưa kết nối API/model có phí và không thuê máy. Phương án tiếp theo không gọi API trả phí là backend/Blender chạy trên máy người dùng đã có, với kiểm soát truy cập được duyệt và Codex phân tích ảnh có giám sát. Tự động AI độc lập vẫn cần model phù hợp và kiểm thử thực. Không bật dịch vụ trả phí hoặc gửi ảnh ra ngoài chỉ để biến trạng thái kết nối thành xanh.

## Kiểm thử và đóng gói

Bộ browser kiểm tra xem ảnh hợp lệ cục bộ, từ chối file giả/không hỗ trợ/quá nhiều, xóa ảnh, mọi job operation bị từ chối, không phát sinh request khi chọn ảnh/soạn yêu cầu, không lưu storage, bố cục ba kích thước màn hình và viewer mẫu vẫn đúng số đo. Fixture chỉ kiểm tra UI; không dùng làm bằng chứng AI nhận diện hay dựng thành công từ ảnh.

Build allowlist thêm đúng create-model.js/model-service.js, tổng 16 file. Chỉ hai mẫu tổng hợp trong public-assets.json được phép đi vào artifact. Không đưa ảnh được chọn, bản vẽ khách hàng, outputs, BLEND hoặc dữ liệu private vào build hoặc Git. Chỉ publish UI đã kiểm thử; không quảng bá backend chưa hoạt động. Safari/iOS thật chưa kiểm chứng.
