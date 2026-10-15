# Giao diện kết nối backend loopback

## Chạy

Từ root HG-3D-CLOUD-AI, build viewer rồi khởi động API và worker ở hai terminal:

```sh
npm --prefix viewer ci --cache ../tools/npm-viewer-cache --ignore-scripts --no-audit --no-fund
npm --prefix viewer run build
# Chỉ init lần đầu nếu chưa có file; không ghi đè credential đang dùng.
python3 scripts/backend.py init
python3 scripts/backend.py api --port 8770
python3 scripts/backend.py worker
```

Mở đường dẫn `/local/` trên API loopback cổng 8770. API tự phục vụ bản viewer đã build và thêm local-client/local-style từ allowlist riêng. Hai file local này KHÔNG có trong viewer/dist, không được GitHub Pages xuất bản. Viewer mẫu giữ nguyên; kết quả riêng hiển thị ở khu vực riêng có nhãn CẦN XÁC NHẬN.

Nhập token của mình lấy an toàn từ file credential cục bộ; không gửi token trong chat hoặc sửa token vào JS. Input bị xóa sau khi đăng nhập; token chỉ giữ trong closure RAM, không localStorage/sessionStorage, cookie hay query string. Đăng xuất/rời trang xóa token/kết quả trên UI. Token được gửi dưới Authorization cho đúng origin loopback; không có URL backend tùy ý và không gửi sang Pages. Không dùng screenshot/tracing/network dump chứa token.

1. Xác thực. Backend sẵn sàng nhưng AI tự hiểu ảnh luôn CHƯA KẾT NỐI.
2. Chọn đúng 1 ảnh cho mỗi job (chế độ backend hiện tại), chọn loại và nhập yêu cầu, bấm Gửi.
3. Job WAITING_ANALYSIS. Xem ảnh trực tiếp, kiểm tra chứng cứ từng số đo, chuẩn bị observations theo schema của image pipeline. Không lấy fixture để giả làm kết quả nhận diện ảnh người dùng.
4. Chọn JSON quan sát đã xác minh, đánh dấu đã xem ảnh và kiểm tra chứng cứ. Gửi để xếp hàng. Đây là xác nhận có giám sát của user, không phải chứng minh AI tự động chính xác.
5. Worker Blender thật xử lý. UI poll trạng thái thật, không bịa phần trăm. Kết quả GLB tải có auth vào bộ nhớ để hiển thị; BLEND/GLB/QA tải xuống qua fetch có bearer, không dùng link public.
6. Dựng lại tạo revision mới, giữ bản gốc, yêu cầu gửi lại quan sát được kiểm tra.

API không CORS. Host chỉ localhost/127.0.0.1/::1; POST có Origin phải cùng origin, để hạn chế DNS rebinding/cross-origin. Static `/local/` chỉ phục vụ file allowlist không chứa dữ liệu riêng; mọi API/job/source/artifact vẫn cần auth và ownership. Token frontend phải giữ ở RAM để dùng API, không thể chống user đã bị XSS/extension/máy bị chiếm; chưa được gọi là chuẩn public production.

## Kiểm thử

Có bài kiểm thử Chromium thật tự chạy API subprocess với hai user/token ngẫu nhiên trong .private, chọn ảnh fixture thuật toán, đăng nhập, upload, nộp observations, chạy worker thật, xem mesh, tải BLEND, revision và logout. Không dùng provider fake để chứng minh AI. Kiểm tra 401, 404 ownership, Host giả 403 và không có secret/storage trên DOM. Fixture synthetic dùng để test software; bài thử thủ công bổ sung dùng bản vẽ AtFAB thật và observations có giám sát.

Safari/iPhone/iPad thật chưa kiểm chứng. API chỉ loopback, chưa public. Không thay đổi backend thành dịch vụ Internet trong tác vụ này.

# Máy dựng cloud miễn phí: lựa chọn và giới hạn

Đã đọc tài liệu chính thức qua repository của nhà cung cấp ngày 15/10/2026; không tạo tài khoản/dịch vụ, không bật billing.

## Đề xuất thử tiếp: GitHub-hosted Actions dạng batch trong repository RIÊNG TƯ

Máy dựng do GitHub cấp và chạy trong cloud, không phụ thuộc máy cá nhân. Chỉ phù hợp thử batch nhỏ, không phải máy chủ Python/SQLite luôn bật. Không dùng repository HG công khai để nhận ảnh khách hàng. Chỉ nên thử sau khi user duyệt repository riêng và kiểm tra quota miễn phí thực tế của tài khoản.

- Tài liệu GitHub xác nhận repository private có quota phút/artifact miễn phí tùy gói; phần vượt quota có thể tính tiền. Không giả định một số phút cố định cho mọi tài khoản.
- Phải không có payment method hoặc cấu hình budget hard stop thích hợp; không nâng gói. Tài liệu ghi không có payment method thì vượt quota sẽ bị chặn. Chỉ chọn standard Linux runner, không larger runner.
- Đặt giới hạn của HG: 1 job đồng thời, timeout 10 phút/job, ảnh <=20 MiB, không render/GPU, artifact private giữ tối đa 1 ngày; theo dõi cả dung lượng lẫn phút và dừng trước quota. Đây là giới hạn đề xuất, CHƯA triển khai.
- Giới hạn nền tảng GitHub-hosted job là 6 giờ; job HG tự giới hạn thấp hơn. Runner và ổ đĩa là tạm thời, không dùng SQLite trên runner làm queue/storage bền vững sau khi job kết thúc.
- Không upload artifact khách hàng lên Pages hoặc repo public. Artifact private vẫn cần auth; không dùng PAT trong JavaScript công khai. Có thể vận hành thử qua GitHub UI được xác thực trước, chưa tự động nối website Pages.

Phương án này giải quyết worker cloud theo lô, chưa giải quyết API web luôn bật, auth đa người dùng và lưu trữ bền vững. Cần chọn riêng control-plane/storage có quota dừng cứng và kiểm tra điều khoản hiện hành trước khi triển khai toàn bộ web. Chưa có giải pháp VPS 24/7 + storage bền vững hoàn toàn miễn phí đã được kiểm chứng cho dự án; không cam kết một hệ thống như vậy sẽ miễn phí mãi.

## Không đề xuất mặc định Hugging Face Docker Space cho tài khoản mới yêu cầu 0 phí

Tài liệu HF hiện ghi CPU Basic 2 vCPU/16 GB RAM/50 GB disk tạm thời và không tính phí theo giờ, ngủ sau 48 giờ không hoạt động. Tuy nhiên, chính tài liệu hiện ghi tạo Space compute mới (Docker/Gradio) cần paid plan. Vì vậy không được quảng cáo đây là phương án 0 phí cho tài khoản mới. Static Space miễn phí không chạy được Blender worker. Không đăng ký hay nâng gói trong tác vụ này.

Render free: truy cập tài liệu chính thức từ môi trường bị 403 kể cả thử quyền mạng bổ sung; chưa xác minh quota hiện hành, nên không đưa ra cam kết miễn phí/độ bền dữ liệu cho worker trên dịch vụ đó.

Nguồn:
- https://github.com/github/docs/blob/main/content/billing/concepts/product-billing/github-actions.md
- https://github.com/github/docs/blob/main/data/reusables/billing/default-over-quota-behavior.md
- https://github.com/github/docs/blob/main/content/actions/reference/limits.md
- https://github.com/huggingface/hub-docs/blob/main/docs/hub/spaces-overview.md
- https://github.com/huggingface/hub-docs/blob/main/docs/hub/spaces-gpus.md
