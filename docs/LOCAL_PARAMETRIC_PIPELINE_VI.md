# Mục 01 · Bộ mô-đun dựng hình 3D trên website — v1

## Kết quả người dùng

Tại \`https://hoanggiaktsda-beep.github.io/HG-3D-CLOUD-AI/#create-model\`:

1. Chọn ảnh PNG/JPEG/WebP trên thiết bị (tối đa 8 ảnh và giới hạn dung lượng như trước). Việc xác minh ảnh tự động xảy ra tại trình duyệt, không tải lên máy chủ.
2. Nhập kích thước **Dài (X), Sâu (Y), Cao (Z)** tính bằng mm; tích chọn xác nhận đây là số đo được người dùng cung cấp. Nếu không có số đo, quy trình dừng tại \`CẦN XÁC NHẬN\`, không dựng hình bằng kích thước bịa.
3. Chọn **Khối bao theo kích thước** để dựng 1 hình hộp với bounding box được xác nhận, hoặc chọn **Console/Bàn/Tủ** để dựng cấu tạo minh họa. Các kích thước vật thể tham số thuộc giả định toán học, KHÔNG phải cấu tạo đã nhận diện từ ảnh.
4. Mô-đun tự chạy sau khi nguồn và số đo đã hợp lệ, hiển thị mô hình **ngay trong KHÔNG GIAN 3D chính**, với các góc camera, kích thước tính từ mesh thật, số lượng bộ phận và báo cáo \`CẦN XÁC NHẬN\`.
5. Có thể chỉnh các mesh trong ChatGPT Studio (vị trí, góc xoay, tỷ lệ, xóa), đồng bộ khung xem chính; tải **GLB bản nháp** và **FBX nhị phân bản nháp** trực tiếp từ trình duyệt.

## Mô-đun thực tế

| Mô-đun | Phạm vi |
| --- | --- |
| 01 Nhận ảnh | Kiểm MIME/chữ ký ảnh/giải mã/kích thước pixel; dữ liệu chỉ nằm tại trình duyệt |
| 02 Kiểm số đo | Yêu cầu 3 kích thước do người dùng xác nhận, đơn vị mm |
| 03 Dựng hình | Tạo mesh \`BoxGeometry\` tham số dựa trên số đo, không dựng theo pixel/ảnh |
| 04 Xem và chỉnh 3D | Đồng bộ cùng khung xem mẫu; góc nhìn, kích thước mesh, chỉnh bộ phận |
| 05 Kiểm định | Đo bbox, đếm mesh, giữ tình trạng \`CẦN XÁC NHẬN\`; không xác thực giống ảnh |
| 06 Xuất định dạng | \`GLTFExporter\` → GLB, \`@comfyorg/fbx-exporter-three\` → FBX nhị phân |

## Giới hạn bắt buộc

- Không có API ChatGPT, backend bảo mật hay worker nhận ảnh riêng: **không có suy luận AI tự động từ ảnh khi tải lên**. Không dùng tên 18 chuyên gia để giả lập hoạt động inference; các mô-đun trên là xử lý cục bộ chạy thật.
- Một ảnh không cung cấp kích thước metric/chi tiết mặt khuất một cách xác thực; tạo hình hộp bao hoặc dựng cấu tạo minh họa cần số đo và sự chấp thuận của người dùng.
- File FBX/GLB được tải về bằng thao tác người dùng. **Không sinh BLEND**, không có model CAD chính xác để sản xuất, không lưu trữ project lâu dài hoặc ảnh vào GitHub, không phí API.
- Gói FBX \`@comfyorg/fbx-exporter-three@1.0.2\` và \`fflate@0.8.2\` có giấy phép MIT; \`three@0.180.0\` MIT. Thư viện được đóng gói chỉ từ package khóa phiên bản; kiểm định import FBX trong Three.js. Cần nhập thử trên Blender/3ds Max thực tế trước khi dùng trong công việc quan trọng.
- Mọi kết quả phải được người dùng xác nhận hình học, vật liệu, cấu tạo, chiều sâu trước khi chuyển sang chế tác.

## Kiểm thử

- \`npm ci --prefix viewer --ignore-scripts --no-audit --no-fund\`
- \`npm run build --prefix viewer\`
- \`python scripts/serve_pages_preview.py --port 8792\`
- \`HG_VIEWER_URL=http://127.0.0.1:8792/HG-3D-CLOUD-AI/ python -m unittest discover -s viewer/tests -v\`

Kiểm tra hồi quy gốc, mô-đun tự chạy khi có số đo; chặn khi thiếu chứng cứ; file tải về có chữ ký FBX binary và GLB, kiểm nhập FBX bằng Three.js \`FBXLoader\`. Kiểm trên Chromium giả lập không thay thế Safari/iPhone/iPad hoặc import bằng Blender/3ds Max thật.
