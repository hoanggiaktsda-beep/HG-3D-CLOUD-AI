# Hoàn thiện sản phẩm — tiếp nối nghiệm thu tổng thể

Không mở chuỗi TEST đánh số mới. Giữ Director + 17 trách nhiệm chuyên gia và TEST 30 CẦN XÁC NHẬN. Chưa công bố hệ thống sử dụng thực tế.

## Luồng mẫu công khai

Website có mục riêng cho ba nguồn OpenDesk đã khóa SHA-256. Người dùng mở workflow trên GitHub và dùng xác thực do GitHub quản lý để bấm Run workflow. Pages không được giữ PAT/token; chưa có nút dispatch API trực tiếp không qua GitHub. Ảnh khách hàng chọn ở mục TẠO MÔ HÌNH 3D không được gửi tới workflow.

Workflow chạy Qwen2-VL-2B thật trước OCR độc lập, chỉ dựng dữ liệu vượt cổng chứng cứ. Có thể chỉ có tấm rời; mẫu thiếu chứng cứ giữ BLOCKED. Không dùng phản hồi AI giả, kết quả mẫu tham số hoặc fixture để công bố nhận diện thành công.

Bộ đóng gói chỉ chấp nhận đúng ba PDF công khai và revision Qwen cố định; kiểm ảnh SHA, trạng thái inference và QA mở lại BLEND/nhập GLB. Chỉ xuất release metadata, phản hồi AI/OCR, GLB/BLEND và QA của tấm ghế đã kiểm định. Build website tiếp tục khóa nguồn, hash, tên và dung lượng file. Không đưa weights, `.private`, bản vẽ khách hàng hoặc thư mục outputs vào website.

Kết quả được lưu tại `viewer/public-demo/` để các lần cập nhật viewer sau không mất mẫu thật. UI đọc trạng thái lượt đã hoàn tất, không giả tiến độ; muốn xem việc đang chạy phải mở GitHub Actions. Kết quả AI không cache bởi PWA. GLB được kiểm SHA-256 trước khi mở; mọi output vẫn CẦN XÁC NHẬN. Giữ ghi công AtFAB / Filson and Rohrbacher, CC BY-NC-SA 3.0, chỉ thử phi thương mại.

## Nhiều hình chiếu và lắp ráp

`hgcloud/multiview.py` và `scripts/review_assembly.py` hợp nhất điểm đối ứng metric từ top/front/side cùng hệ tọa độ đã xác minh. Cần ít nhất ba điểm không thẳng hàng, đúng nhãn cấu kiện và khung tọa độ, annotation có nguồn ảnh/hash. Bộ giải kiểm tọa độ trùng giữa các hình chiếu, tìm phép quay/tịnh tiến rigid và đối chiếu bbox từng hình chiếu qua verifier hiện có. Không đổi tỷ lệ, không phản xạ hoặc tự bù điểm thiếu.

CLI: `python scripts/review_assembly.py cut_layout.json reviewed-plan.json NEW-report.json`. File output phải mới. Mỗi placement dùng `anchor_ids`, `local_anchors_mm`, ba `views`; trong từng view có `anchors_mm` theo cùng ID, `metric_frame_id`, `bbox_mm`, hash ảnh/tài liệu, trạng thái confirmed và chú thích người kiểm tra. Xem fixture trong `tests/test_multiview.py` cho cấu trúc, **không coi fixture là dữ liệu nhận diện ảnh thật**.

Đã kiểm tra toán học bằng dữ liệu tổng hợp có xoay; thiếu/mâu thuẫn hình chiếu, sai tài liệu/hash hoặc chưa duyệt đều chặn. Chưa có ánh xạ nhãn–điểm từ Qwen đủ tốt trên ghế thực, nên chưa tuyên bố lắp ráp tự động hoàn chỉnh hoặc nâng TEST 30. Không tự dựng lỗ/chốt/chi tiết khuất.

## Thiết kế dữ liệu khách hàng riêng

Backend hiện chỉ phục vụ loopback, có bearer auth, ownership, quota, kiểm ảnh, SQLite claim và file quyền 0700/0600. Worker mở BLEND, nhập GLB và ghi checksum từng artifact; API kiểm lại hash/size khi tải, file bị đổi/symlink bị chặn. Đây là bảo vệ cục bộ đã kiểm thử, chưa phải nghiệm thu triển khai Internet.

Phương án triển khai khả thi khi được cấp máy chủ:

1. Một máy Linux cloud có HTTPS, RAM đủ model/Blender và ổ đĩa bền vững; reverse proxy chỉ mở ứng dụng cùng origin, API không nhận CORS tùy ý. Pages chỉ giữ demo công khai.
2. Đăng nhập qua OIDC hoặc session ngắn hạn Secure/HttpOnly/SameSite. Không đặt bearer cố định vào bundle công khai; rotation/revoke, rate limit và nhật ký không ghi token. Chưa triển khai hoặc kiểm thử lớp này.
3. Lưu ảnh/JSON/model theo owner/job/version, ngoài checkout và web root. Volume mã hóa, key ở secret của máy chủ; backup mã hóa, chính sách xóa và quota phải được duyệt. Không dùng Git hoặc public Artifacts làm storage khách hàng.
4. API chỉ cấp việc cho worker riêng, không chuyển ảnh riêng sang Actions công khai. SQLite bền vững phù hợp một máy/single worker; scale nhiều máy cần queue/database riêng. AI disabled cho tới khi connector được kiểm chứng trên dữ liệu được cấp quyền.
5. Chỉ mở Internet sau kiểm thử TLS/auth/ownership, token lifecycle, upload traversal/bomb, file integrity, giới hạn tài nguyên, mất điện/restart, backup/restore và kiểm tra thiết bị thật.

Không tự đăng ký VPS, cloud storage, GPU hoặc dịch vụ có phí. GitHub Free đủ chạy mẫu batch công khai trên standard Linux runner; không cung cấp máy chủ API riêng luôn bật, storage khách hàng bền vững và cầu nối xác thực web miễn phí đã được kiểm chứng. Private Actions có quota và khả năng phát sinh phí nếu vượt; không tự chuyển khách hàng vào đó. Chưa có hạ tầng riêng hoặc thông tin đăng nhập sẵn có trong môi trường.

## Kiểm chứng và trạng thái phát hành

Đang cập nhật sau lượt chạy thực; không đánh dấu thành công trước khi AI, Blender, đóng gói và website đã được kiểm tra. Chromium emulation không phải thiết bị iPhone/iPad/macOS thật.
