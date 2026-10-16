# Hoàn thiện sản phẩm — tiếp nối nghiệm thu tổng thể

Không mở chuỗi TEST đánh số mới. Giữ Director + 17 trách nhiệm chuyên gia và TEST 30 CẦN XÁC NHẬN. Chưa công bố hệ thống sử dụng thực tế.

## Luồng mẫu công khai

Website có mục riêng cho ba nguồn OpenDesk đã khóa SHA-256. Chủ repository hoặc người có quyền write mở workflow trên GitHub và dùng xác thực do GitHub quản lý để bấm Run workflow. Người xem công khai chỉ xem/tải kết quả; không có quyền gửi việc như khách hàng. Pages không được giữ PAT/token; chưa có nút dispatch API trực tiếp không qua GitHub. Ảnh khách hàng chọn ở mục TẠO MÔ HÌNH 3D không được gửi tới workflow.

Workflow chạy Qwen2-VL-2B thật trước OCR độc lập, chỉ dựng dữ liệu vượt cổng chứng cứ. Có thể chỉ có tấm rời; mẫu thiếu chứng cứ giữ BLOCKED. Không dùng phản hồi AI giả, kết quả mẫu tham số hoặc fixture để công bố nhận diện thành công.

Bộ đóng gói chỉ chấp nhận đúng ba PDF công khai và revision Qwen cố định; kiểm ảnh SHA, trạng thái inference và QA mở lại BLEND/nhập GLB. Chỉ xuất release metadata, phản hồi AI/OCR, GLB/BLEND và QA của tấm ghế đã kiểm định. Build website tiếp tục khóa nguồn, hash, tên và dung lượng file. Không đưa weights, `.private`, bản vẽ khách hàng hoặc thư mục outputs vào website.

Kết quả được lưu tại `viewer/public-demo/` để các lần cập nhật viewer sau không mất mẫu thật. UI đọc trạng thái lượt đã hoàn tất, không giả tiến độ; muốn xem việc đang chạy phải mở GitHub Actions. Kết quả AI không cache bởi PWA. GLB được kiểm SHA-256 trước khi mở; mọi output vẫn CẦN XÁC NHẬN. Giữ ghi công AtFAB / Filson and Rohrbacher, CC BY-NC-SA 3.0, chỉ thử phi thương mại.

## Nhiều hình chiếu và lắp ráp

`hgcloud/multiview.py` và `scripts/review_assembly.py` hợp nhất điểm đối ứng metric từ top/front/side cùng hệ tọa độ đã xác minh. Cần ít nhất ba điểm không thẳng hàng, đúng nhãn cấu kiện và khung tọa độ, annotation có nguồn ảnh/hash. Bộ giải kiểm tọa độ trùng giữa các hình chiếu, tìm phép quay/tịnh tiến rigid và đối chiếu bbox từng hình chiếu qua verifier hiện có. Không đổi tỷ lệ, không phản xạ hoặc tự bù điểm thiếu.

CLI: `python scripts/review_assembly.py cut_layout.json reviewed-plan.json NEW-report.json`. File output phải mới. Mỗi placement dùng `anchor_ids`, `local_anchors_mm`, ba `views`; trong từng view có `anchors_mm` theo cùng ID, `metric_frame_id`, `bbox_mm`, hash ảnh/tài liệu, trạng thái confirmed và chú thích người kiểm tra. Xem fixture trong `tests/test_multiview.py` cho cấu trúc, **không coi fixture là dữ liệu nhận diện ảnh thật**.

Đã kiểm tra toán học bằng dữ liệu tổng hợp có xoay; thiếu/mâu thuẫn hình chiếu, sai tài liệu/hash hoặc chưa duyệt đều chặn. Chưa có ánh xạ nhãn–điểm từ Qwen đủ tốt trên ghế thực, nên chưa tuyên bố lắp ráp tự động hoàn chỉnh hoặc nâng TEST 30. Không tự dựng lỗ/chốt/chi tiết khuất.

## Thiết kế dữ liệu khách hàng riêng

Backend hiện chỉ phục vụ loopback, có bearer auth, ownership, quota, kiểm ảnh, SQLite claim và file quyền 0700/0600. Worker mở BLEND, nhập GLB và ghi checksum từng artifact; API kiểm lại hash/size khi tải, file bị đổi/symlink bị chặn. Đây là bảo vệ cục bộ đã kiểm thử, chưa phải nghiệm thu triển khai Internet. Công việc cũ chưa có receipt checksum sẽ bị chặn tải; cần dựng revision mới, không tự tin cậy hoặc cấp hash lại cho file cũ.

Phương án triển khai khả thi khi được cấp máy chủ:

1. Một máy Linux cloud có HTTPS, RAM đủ model/Blender và ổ đĩa bền vững; reverse proxy chỉ mở ứng dụng cùng origin, API không nhận CORS tùy ý. Pages chỉ giữ demo công khai.
2. Đăng nhập qua OIDC hoặc session ngắn hạn Secure/HttpOnly/SameSite. Không đặt bearer cố định vào bundle công khai; rotation/revoke, rate limit và nhật ký không ghi token. Chưa triển khai hoặc kiểm thử lớp này.
3. Lưu ảnh/JSON/model theo owner/job/version, ngoài checkout và web root. Volume mã hóa, key ở secret của máy chủ; backup mã hóa, chính sách xóa và quota phải được duyệt. Không dùng Git hoặc public Artifacts làm storage khách hàng.
4. API chỉ cấp việc cho worker riêng, không chuyển ảnh riêng sang Actions công khai. SQLite bền vững phù hợp một máy/single worker; scale nhiều máy cần queue/database riêng. AI disabled cho tới khi connector được kiểm chứng trên dữ liệu được cấp quyền.
5. Chỉ mở Internet sau kiểm thử TLS/auth/ownership, token lifecycle, upload traversal/bomb, file integrity, giới hạn tài nguyên, mất điện/restart, backup/restore và kiểm tra thiết bị thật.

Không tự đăng ký VPS, cloud storage, GPU hoặc dịch vụ có phí. GitHub Free đủ chạy mẫu batch công khai trên standard Linux runner; không cung cấp máy chủ API riêng luôn bật, storage khách hàng bền vững và cầu nối xác thực web miễn phí đã được kiểm chứng. Private Actions có quota và khả năng phát sinh phí nếu vượt; không tự chuyển khách hàng vào đó. Chưa có hạ tầng riêng hoặc thông tin đăng nhập sẵn có trong môi trường.

## Kiểm chứng và trạng thái phát hành

Ngày 16/10/2026: [workflow mẫu công khai 38856340988](https://github.com/hoanggiaktsda-beep/HG-3D-CLOUD-AI/actions/runs/38856340988) **Success**, 12 phút 10 giây kể cả thời gian chờ. Infer 6 phút 13 giây; publish 2 phút; deploy 12 giây; verify HTTPS 1 phút 1 giây.

- Qwen/OCR chạy thật trên ba bản vẽ: chair sinh 20 tấm rời; desk/table bị chặn vì thiếu chứng cứ. Không dựng sản phẩm lắp ráp hoặc lỗ khoan chưa biết.
- Bộ đóng gói đã kiểm nguồn và QA thật. Kết quả được bot lưu tại commit `73d9ded505156f16d8d256e6dc02df0729b6d214`, gồm GLB/BLEND, QA, phản hồi gốc và receipt. Gói public-ai-release 844 KB, SHA-256 `6fcd4e6c2a65fcbc772721e974dec0516800146f5f960284eae54cc89acca824`.
- Kiểm tra trước phát hành và sau HTTPS đều mở đúng 20 mesh theo run ID, so checksum tài nguyên, tải GLB/BLEND thật và so bytes ở viewport 390/820/1440. Website: [mẫu AI công khai](https://hoanggiaktsda-beep.github.io/HG-3D-CLOUD-AI/#public-demo).
- [Lượt triển khai giao diện thông thường 38856743892](https://github.com/hoanggiaktsda-beep/HG-3D-CLOUD-AI/actions/runs/38856743892) cũng Success, kiểm website HTTPS và giữ nguyên release AI mới nhất nhờ checkout main trong nhóm triển khai tuần tự.
- Codex lấy chính file mới qua Git, mở lại BLEND bằng Blender 4.3.2 và nhập GLB; 20 mesh kín, metadata nguồn/giấy phép, điểm mesh round-trip trùng nhau trong lượt kiểm tra (0 mm sai lệch điểm lưu). Đây không phải độ chính xác so bản vẽ. Sai lệch mesh–JSON trong worker 0,000120147 mm; bất định nguồn raster khoảng 1,521622 mm; IoU sơ đồ cắt 0,9978925343, không phải độ giống sản phẩm đã lắp.
- Hồi quy cục bộ **89/89 lõi**, không skip, và **21/21 viewer** với snapshot AI thật. Bài xác minh trình duyệt riêng cũng tải/xem đúng release thật ở ba viewport. Các fixture toán học/replay trong unit test không được coi là AI thành công.
- Lượt chạy được khởi động bằng Git push để tự kiểm chứng. Link từ website mở workflow GitHub đúng; bước đăng nhập/bấm Run workflow bằng tài khoản người dùng chưa được thao tác trong Codex. Chưa có API website dispatch trực tiếp; không tuyên bố luồng tải ảnh tùy ý đã nối.
- Chromium Linux với kích thước màn hình giả lập không phải iPhone/iPad/Windows/macOS thật. Cài PWA và lưu file trong Tệp iOS vẫn chưa được kiểm chứng trên thiết bị thật.

Kết luận: **mẫu công khai dùng được trong phạm vi đã nêu; chưa sẵn sàng xử lý khách hàng thực tế**. Backend Internet, AI cho ảnh tùy ý/riêng tư, storage cloud và lắp ráp tự động vẫn chưa kết nối/nghiệm thu. TEST 30 giữ CẦN XÁC NHẬN, 18 vai trò không thay đổi. Không render, không gọi API trả phí, không sửa repository khác.

**Một thao tác tiếp theo để mở phần khách hàng:** cấp một máy chủ Linux riêng có HTTPS và ổ đĩa bền vững qua cấu hình môi trường (máy chủ đã có hoặc được cấp miễn phí; không tự thuê/đăng ký). Nếu chạy Qwen tại đó cần tài nguyên tương đương runner đã thử, khoảng 4 CPU/16 GB RAM. Khi chưa có hạ tầng này, tiếp tục chỉ dùng mẫu công khai; không chuyển bản vẽ riêng lên GitHub public. Cấp máy chủ chưa đồng nghĩa được mở Internet ngay: phải kiểm chứng auth/storage và chuỗi riêng tư trước.
