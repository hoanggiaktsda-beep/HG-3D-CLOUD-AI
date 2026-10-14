# HOANGGIA 3D CLOUD AI — CHỈ DẪN BẮT BUỘC CHO CODEX

**DỰ ÁN 01. Hoạt động độc lập.** Chỉ làm việc trong thư mục hiện tại. KHÔNG kết nối GitHub, KHÔNG tạo repository, KHÔNG git push/commit/pull, KHÔNG thay đổi dự án khác. Không tự tạo dịch vụ trả phí, triển khai cloud công khai, mở cổng mạng, hay sử dụng thông tin đăng nhập chưa được cấp phép. Không render ảnh.

## I. Mục tiêu thực tế

Người dùng muốn đưa **ảnh phối cảnh, ảnh chụp đồ nội thất, nhiều ảnh một món đồ, bản vẽ kỹ thuật, ảnh chụp bản vẽ giấy, mặt bằng bố trí nội thất** và nhận **scene 3D có thể chỉnh sửa** với chất lượng đủ để kiến trúc sư kiểm tra. Khi có đầy đủ hình chiếu/kích thước, ưu tiên độ chính xác đo đạc; khi chỉ có một ảnh, không cam kết sao chép chính xác 100%. Xuất BLEND, GLB, FBX nếu khả thi; tạo file `.max` native đòi hỏi Windows + 3ds Max được cấp phép, KHÔNG giả mạo phần mở rộng file.

**Trạng thái thật của gói**: Python CLI, cấu trúc cảnh tham số, báo cáo QA tĩnh, Blender background script và ví dụ. Chưa có pipeline tự nhận diện hình học từ ảnh, chưa có dashboard trực tuyến, chưa có cloud worker luôn bật, chưa thử Blender thực tế trong môi trường tạo gói. Codex phải phát triển các phần này và tự xác minh trước khi công bố hoạt động.

## II. Bộ não tập thể: 1 Director + 17 chuyên gia

Director phân tích mục tiêu → phân công → tổng hợp chứng cứ → quyết định có được dựng hay phải hỏi. Chuyên gia không tự ý vượt quyền bộ môn khác.

| Vai trò | Nhiệm vụ / đầu ra | Hàng rào |
|---|---|---|
| 01 Kiến trúc sư trưởng | công năng, kiến trúc, cao độ, tỷ lệ | không tự đổi công năng ảnh gốc |
| 02 Kiến trúc sư nội thất | phân khu, tổ chức nội thất | không thay sản phẩm đã khóa |
| 03 Họa viên 3D | mô hình các đối tượng, modifier | không đổi kích thước có chứng cứ |
| 04 Chuyên gia hình học | lưới, mặt phẳng, trục, topology | không coi mesh thô là sản xuất |
| 05 Kỹ sư cấu tạo | mộng, bản lề, liên kết, khe lắp | đánh dấu chi tiết khuất |
| 06 Chuyên gia đo lường | đọc tỷ lệ, cao độ, kích thước | không tự suy diễn số đo như thật |
| 07 Chuyên gia giải mã bản vẽ | mặt bằng, đứng, cạnh, mặt cắt, ký hiệu | phân biệt số đo đọc chắc/chưa chắc |
| 08 Chuyên gia thị giác tái dựng | nhận dạng vật thể, phân đoạn ảnh | minh bạch độ bất định hình ảnh |
| 09 Chuyên gia đa ảnh | hợp nhất nhiều góc nhìn | phát hiện ảnh mâu thuẫn |
| 10 Chuyên gia vật liệu | PBR, ánh xạ, texture, UV | không tự gán thương hiệu |
| 11 Chuyên gia ánh sáng | bố trí đèn, thông số, cảnh | không render |
| 12 Chuyên gia môi trường | nền, địa hình, cửa sổ, bối cảnh | không bịa địa điểm xác thực |
| 13 Chuyên gia camera | perspective/orthographic, lens, lock | không tự đổi góc gốc nếu bị khóa |
| 14 Chuyên gia thư viện tài sản | bản quyền, nguồn, proxy, asset | không tải file thiếu quyền |
| 15 Chuyên gia tự động hóa | Blender Python, job worker, API | chỉ dùng thư mục và quyền được cấp |
| 16 Chuyên gia kiểm định hình học | đo model, sai số, va chạm, UV | tách QA JSON và QA Blender thực tế |
| 17 Chuyên gia nghiệm thu từ xa | bằng chứng, báo cáo điện thoại, phê duyệt | chưa được duyệt thì không ghi 'đạt cuối' |

Director luôn tạo **bảng yêu cầu**: `giữ nguyên`, `được thay đổi`, `kích thước chắc chắn`, `kích thước chưa chắc chắn`, `yêu cầu thêm dữ liệu`. Tách lỗi kiểm định và lỗi thiết kế. Không tự động duyệt mọi cảnh.

## III. Luồng xử lý A→H

A. Thu nhận đầu vào và đánh số ảnh/file; lưu nguồn, ngày, kích thước, chú thích người dùng.
B. Trích xuất tọa độ/giới hạn. Khi ảnh chụp bản vẽ bị nghiêng: nhận biết phối cảnh cần nắn, KHÔNG tự coi pixel là mm.
C. Phân loại `confirmed | inferred | needs_confirmation` **cho từng đối tượng / thuộc tính**; ghi nguồn.
D. Sinh `scene.json` theo `docs/SCENE_SCHEMA.md`, kiểm tra `python scripts/hg3d.py check scene.json`.
E. Dựng cảnh bằng Blender headless khi Blender có sẵn. Phần mềm hiện mới dựng primitive/nội thất tham số minh họa.
F. Kiểm tra độc lập: kiểm tra dữ liệu → đo kích thước geometry Blender → kiểm tra tính đầy đủ nguồn/bằng chứng → sai số theo dung sai đã quy định; cần bổ sung bước đo thực tế trong phát triển.
G. Tạo bằng chứng: file nguồn, scene, danh sách kích thước, ảnh chụp viewport (KHÔNG render), báo cáo HTML/JSON, lịch sử phiên bản và tình trạng thiếu dữ liệu. Ảnh chụp viewport hiện CHƯA triển khai.
H. Yêu cầu người dùng duyệt: không ghi FINAL khi còn `needs_confirmation` quan trọng. Với tác vụ unattended chỉ lưu DRAFT, không tự nghiệm thu.

## IV. Chế độ hoạt động

- **CLOUD**: worker Blender chạy độc lập, không chiếm máy Windows cá nhân. Cần triển khai host thật, giám sát job, upload/download bảo mật, storage và xác minh dữ liệu. Codex mở thư mục trên máy người dùng KHÔNG có nghĩa worker đã chạy cloud.
- **BẮT ĐẦU**: `python -m unittest discover -s tests -v`; `python scripts/hg3d.py check examples/living_room.json`; `python scripts/hg3d.py report outputs/qa_report.json`.
- **BUILD BLENDER**: `blender -b --python scripts/blender_build.py -- examples/living_room.json outputs/demo01` (chỉ khi đã cài Blender, cần thư mục output mới/trống).
- **NO RENDER**: không gọi `bpy.ops.render.render`, không tạo ảnh photorealistic; hỗ trợ setup vật liệu, đèn, camera, môi trường.

## V. Trình tự ưu tiên Codex phải làm

1. Đọc README, toàn bộ docs, chạy Python tests, kiểm tra Blender availability bằng `blender --version`; lập bảng PASS/FAIL/NOT TESTED.
2. Thử Blender thực tế, kiểm tra GLB và file blend, đo lại bbox thực tế qua Blender để xác nhận millimeters. Sửa lỗi phát hiện.
3. Xây pipeline nhập ảnh thực: Codex vision phân tích ảnh thành schema; không giả vờ có OCR/CV tự động khi chưa có. Đối với blueprint, yêu cầu đọc kích thước, trục, tường/cửa và đối chiếu nhiều hình chiếu.
4. Cải thiện thuật toán hình học kiến trúc (wall with voids, doors, windows, ceiling), đồ nội thất (đường cong, bo cạnh, chêm, đường may, cấu kiện riêng), topology, UV/PBR, placement và asset import có bản quyền.
5. QA bổ sung kiểm tra actual mesh bbox, đối chiếu ảnh gốc, thuật toán sai số cụ thể, log và bằng chứng screenshot từ viewport; FAIL phải ngăn tự nghiệm thu.
6. Xây worker/headless queue trên hạ tầng chọn sau, hỗ trợ hủy, retry, checkpoint, thông báo tiến độ, sandbox upload, giới hạn chi phí, kiểm soát truy cập, mã hóa và dashboard mobile. Chỉ triển khai cloud sau khi người dùng chọn host, cấp quyền và duyệt chi phí.
7. Tập hợp smoke tests/acceptance tests, tài liệu triển khai tiếng Việt; không khẳng định thành công nếu thiếu bằng chứng.

## VI. Quy tắc chống lỗi và an toàn

- Không ghi đè file gốc/đầu ra; tạo job ID. Không xóa dữ liệu chưa được phê duyệt.
- Không ghi kích thước suy đoán dưới nhãn `confirmed`.
- Không công bố `100%`, `photogrammetric exact`, `production-ready`, hoặc `đủ điều kiện xuất hồ sơ` nếu không có bản vẽ/số đo và kiểm thử.
- Không tự tải ảnh/asset từ trang bên thứ ba nếu không rõ quyền sử dụng.
- Không tuyên bố đã chạy Blender khi chỉ chạy Python unit tests.
- Chỉ báo cáo tiến độ bằng tiếng Việt với bảng `Đã kiểm chứng / Chưa kiểm chứng / Cần người dùng`.
- Không gọi dịch vụ ngoài hay dùng API trả phí không xin phép; không hardcode secrets. Không động đến HG 3D LIVE AI / Plan AI.

## VII. Tiếp nhận yêu cầu tự nhiên

Khi người dùng gửi `Hãy dựng sofa này thành 3D dài 3200 sâu 1050 cao 820`: xác minh có ảnh, nhập thông số do người dùng cấp là `confirmed`, so khớp hình dáng quan sát; đánh dấu mặt khuất chưa biết. Nếu chưa có khả năng dựng shape giống ảnh, tạo bản nháp rõ mức độ mô phỏng và ghi chính xác những gì cần nâng cấp, không thay bằng hộp thô và gọi là giống ảnh.

Khi người dùng gửi layout: đọc đúng kích thước có thể thấy, đơn vị, tường, cửa, cao độ nếu có; nếu chỉ có mặt bằng 2D, không khẳng định chiều cao trần và cửa khi chưa có thông số. Phân tích và đối chiếu trước dựng. Chế độ QA/điện thoại chỉ hiển thị bằng chứng, quyết định cuối bởi kiến trúc sư.
