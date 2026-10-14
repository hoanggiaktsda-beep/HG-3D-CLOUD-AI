# Giao diện GLB thử nghiệm — chưa Publish

Viewer tĩnh dành cho xem và rà soát có giám sát. Dữ liệu mẫu là console tổng hợp tự tạo (không phải bản thiết kế/ảnh khách hàng). Không upload, không tài khoản, không backend AI hoặc dịch vụ trả phí, không tự phê duyệt. Không gọi Blender render hoặc tạo ảnh photorealistic; WebGL chỉ dùng để hiển thị mô hình tương tác trong trình duyệt.

## Chạy cục bộ

Từ root HG-3D-CLOUD-AI:

```sh
cd viewer
npm ci --cache ../tools/npm-viewer-cache --ignore-scripts --no-audit --no-fund
npm start
```

Server Python chỉ bind 127.0.0.1, cổng 8765; không mở mạng công khai hay triển khai website. File viewer không chạy đúng bằng file:// do browser module/fetch restrictions. iPhone/iPad thật không truy cập được loopback của máy cloud trực tiếp; chưa cung cấp đường truy cập thiết bị hoặc Publish. Khi có môi trường thử thiết bị được cấp quyền cần kiểm tra lại Safari/iOS thực tế.

Three.js phiên bản cố định 0.180.0, lockfile giữ integrity dependency. Runtime chỉ tải file cùng nguồn; không dùng CDN hay API ngoài. npm install/ci cần registry.npmjs.org một lần để cài dependency, không phải lời gọi AI. Không commit node_modules hoặc browser caches.

## Chức năng

- Orbit xoay quanh mô hình, zoom con lăn hoặc hai ngón, pan; nút phóng to/thu nhỏ và đặt lại.
- Góc phối cảnh, mặt đứng, cạnh, bằng, mặt sau; góc nhìn tự do khi tương tác.
- Đo bbox GLB thực tế và mesh từng object, so kích thước mẫu và tolerance; báo mesh thiếu/sai lệch. GLTF Y-up được chuyển về hệ HG Z-up trước khi đo và đặt camera.
- Hiển thị dữ liệu xác nhận/suy luận riêng với trạng thái cấu tạo. Dù số đo confirmed hay báo cáo ghi APPROVED, giao diện vẫn CẦN XÁC NHẬN và không có nút tự nghiệm thu.
- Báo lỗi tải GLB, báo cáo thiếu/hỏng hoặc mất WebGL context; không coi lỗi là đã đạt. Hiển thị chuỗi bằng textContent để tránh chèn HTML.
- Bố cục responsive, điều khiển tối thiểu 44 px, cảm ứng một/two finger và DPR giới hạn 2.

QA viewer hiện đo bbox, không kiểm tra topology, chốt, relief, texture hay độ giống ảnh. Số đo hiển thị làm tròn; QA giữ giá trị chưa làm tròn. Báo cáo và GLB phải cùng dữ liệu mẫu; đổi assets cần cập nhật report đúng nguồn, không được dùng để tự xác nhận sản xuất.

## Kiểm thử

Sau khi start server, từ root:

```sh
python3 -m unittest discover -s tests -v
python3 -m unittest discover -s viewer/tests -v
```

Browser suite cần Python Playwright và Chromium. Trong môi trường hiện tại có sẵn; test dùng /usr/bin/chromium và software WebGL. Kiểm tra desktop, kích thước iPhone 390×844, iPad 820×1180 và ngang 1180×820, touch orbit/pinch thật qua CDP, camera, zoom, kích thước GLB, lỗi tải, báo cáo không hợp lệ, chèn HTML và không có runtime request bên ngoài.

Mô phỏng Chromium không chứng minh Safari hoặc thiết bị iPhone/iPad thật đã chạy. WebKit Playwright chưa có binary trong môi trường này. Chưa kiểm chứng hiệu năng trên thiết bị thật hoặc GLB lớn. Giao diện không Publish.
