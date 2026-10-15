# Backend Python riêng tư — thử nghiệm cục bộ

Có API FastAPI với bearer token riêng từng user, SQLite lưu hàng đợi, worker Blender thật và artifact riêng. Không chạy trong GitHub Pages, không mở public API, không CORS công khai, không dịch vụ/AI trả phí. AGENTS.md và 18 vai trò không thay đổi.

## Chạy trong HG-3D-CLOUD-AI

Cài requirements-backend.txt trong môi trường Python riêng nếu chưa có dependencies; môi trường Codex hiện đã có. Cần Blender trên PATH.

```sh
python3 scripts/backend.py init
python3 scripts/backend.py api --port 8770
# Terminal khác:
python3 scripts/backend.py worker
```

init tạo token ngẫu nhiên trong `.private/backend-credentials.json` bằng exclusive-create, mode 0600; không in giá trị ra terminal. Không gửi token trong chat, không commit file. API chỉ bind 127.0.0.1, không có tùy chọn host công khai. Private root `.private/backend` mode 0700, DB 0600. Launcher/worker umask 077. File private, log, ảnh và outputs không nằm trong viewer/dist. Root .gitignore bỏ qua .private và pycache.

Mỗi request dùng Authorization: Bearer <token>. Không dùng token trong URL, cookie hoặc frontend Pages. Credentials chỉ do operator cấp qua file riêng; đây chưa phải hệ thống đăng ký tài khoản/MFA. Khởi động lại API để áp dụng đổi/thu hồi token. Chưa có TLS vì chỉ chạy loopback. Không public dịch vụ này trước khi review bổ sung.

## API đã chạy

- GET /capabilities: auth bắt buộc; AI tự động false, mode supervised, 18 vai trò. connected false vì chưa có AI tự động được cấp quyền.
- POST /jobs: multipart `image`, `input_type`, `instruction`; tối đa 20 MiB, PNG/JPEG/WebP có format thực hợp lệ, tối đa 25 MP. Tên file client không dùng làm đường dẫn. Trả WAITING_ANALYSIS, chưa có hình học.
- GET /jobs, GET /jobs/{id}: chỉ công việc của user đã xác thực. progress null khi không có số đo tiến độ thật; không phần trăm giả.
- GET /jobs/{id}/source: lấy ảnh riêng để kiểm tra có giám sát, ownership bắt buộc.
- POST /jobs/{id}/observations: JSON quan sát theo schema hiện có. Chặn thiếu số đo/evidence, tối đa 100 object, tọa độ/kích thước giới hạn 100 m. Chỉ WAITING_ANALYSIS được gửi; scene hợp lệ mới QUEUED. Không cho gửi mã Python hay đường dẫn script.
- POST /jobs/{id}/revisions: instruction mới tạo job ID khác với ảnh snapshot và parent_job. Phải phân tích lại, không tự tái sử dụng quan sát cũ, không ghi đè kết quả gốc.
- GET /jobs/{id}/artifacts/{glb|blend|qa|html}: ownership bắt buộc; chỉ trả khi worker hoàn thành và đo đạt. Không có public/signed URL trong phiên này; download phải dùng bearer token. Trả attachment/no-store.

Mọi route kiểm tra auth trước parse body. Giới hạn body được kiểm tra header và số byte thực. SQLite BEGIN IMMEDIATE bảo đảm một job chỉ được một worker claim. Tối đa 20 job active/user, kiểm tra quota trong transaction. Worker file lock chỉ cho một daemon, stale RUNNING khi restart chuyển INTERRUPTED, không giả thành công; tạo revision để thử lại. Worker timeout 120 s mỗi Blender command, kill process group khi hết hạn, dùng 2 threads, không shell/user code. Kết quả luôn NEEDS_REVIEW, không APPROVED. FAILED/partial không được download qua API.

## AI thị giác

`hgcloud/backend/vision_adapter.py` định nghĩa protocol/configuration boundary, mặc định DisabledVisionProvider; provider lạ bị từ chối, không gửi ảnh ra mạng. Chưa có model hoặc transport được cấp quyền/cài vào pipeline. Thử nghiệm dùng Codex xem ảnh thật rồi gửi observations có chứng cứ qua API, không replay fixture để giả nhận diện. Nhãn verified_by là khai báo người xem ảnh, không phải chữ ký độc lập; không được coi user tự khai là nghiệm thu chuyên môn.

## Thử nghiệm thực tế

Đã gửi source-3.png từ bản vẽ công khai AtFAB Rotational Stools (Filson and Rohrbacher, OpenDesk, CC BY-NC-SA 3.0) qua loopback HTTP. Không dùng model/DXF có sẵn. Ảnh ghi cao 15 inch, cạnh 9.5 inch; Codex xem ảnh và chuyển sang 381/241.3 mm. Sau đó authenticated observations → queue SQLite → tiến trình Blender thật → verify mesh → download private BLEND/GLB/QA.

Bản thử API chỉ dựng envelope để kiểm tra plumbing; chưa dựng lại các khoét/chốt của ghế. QA luôn nêu giới hạn và NEEDS_REVIEW. Bản ghế chi tiết từ thử nghiệm trước vẫn là pipeline riêng, chưa được nối tự động vào endpoint này. Kết quả/credentials cục bộ tại .private, không đưa lên Pages. Báo cáo thử nghiệm phi bí mật ở outputs/backend-real-trial/report.json.

## Kiểm thử và phần chưa sẵn sàng public

```sh
python3 -m unittest discover -s tests -v
```

Kiểm tra 401/404 ownership, credentials lỗi/trùng, fake image/path traversal filename, thiếu kích thước, submit lặp, SQLite claim đồng thời, restart store, worker thật, private downloads, revision, worker lỗi không lộ partial, quota và no-CORS. Các kiểm thử thuật toán dùng fixture synthetic được phân biệt với lần HTTP thực dùng bản vẽ công khai.

Chưa có AI tự động, OAuth/session lifecycle, audit log chống sửa, retention/disk quota toàn hệ thống, antivirus, cách ly Blender bằng container/OS sandbox, rate-limit proxy hay public TLS. Tiến trình Blender chạy bằng user backend, không tuyên bố đã sandbox toàn diện. Chưa có frontend authenticated nối trực tiếp backend; Pages vẫn CHƯA KẾT NỐI đúng thực tế. Cần threat review và hạ tầng riêng được cấp quyền trước khi mở Internet. Không đăng ký dịch vụ có phí.
