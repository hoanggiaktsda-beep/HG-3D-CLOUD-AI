# GitHub Pages — bản chuẩn bị, chưa kích hoạt

Bản build website nằm ở viewer/dist, root chứa index.html. Khi xuất artifact này vào GitHub Pages của repository HG-3D-CLOUD-AI, nó hoạt động tại `/HG-3D-CLOUD-AI/`. Mọi JS, CSS, GLB, báo cáo và vendor module dùng đường dẫn tương đối; không phụ thuộc root `/` hoặc node_modules. Có .nojekyll và MIT license Three.js. Không CDN/API ngoài ở runtime.

## Build và kiểm tra

Từ root repository:

```sh
cd viewer
npm ci --cache ../tools/npm-viewer-cache --ignore-scripts --no-audit --no-fund
npm run build
cd ..
python3 scripts/serve_pages_preview.py
```

Preview chỉ bind loopback cổng 8766 với tiền tố /HG-3D-CLOUD-AI/. Chạy ở terminal khác:

```sh
HG_VIEWER_URL=http://127.0.0.1:8766/HG-3D-CLOUD-AI/ python3 -m unittest discover -s viewer/tests -v
python3 -m unittest discover -s tests -v
```

Đóng gói allowlist 14 file, có manifest SHA-256, không sao chép repository đệ quy. public-assets.json chỉ định đúng GLB mẫu console tổng hợp và báo cáo mẫu đã công khai trong repository. Build từ chối nếu mẫu bị thay mà chưa cập nhật hash sau kiểm tra quyền công khai. Không có bản vẽ khách hàng, ảnh nguồn, tài liệu AtFAB, dữ liệu upload, secrets, đường dẫn nguồn riêng tư, BLEND hoặc outputs trong website. Giữ nguyên AGENTS.md và 18 vai trò, không thay code dựng hay cấu trúc hiện có.

## Triển khai về sau — CHƯA thực hiện

`viewer/pages-workflow.example.yml` là template KHÔNG HOẠT ĐỘNG, nằm ngoài .github/workflows. Không có workflow mới chạy khi push mã, không gọi GitHub Pages API, không thay settings, không tạo nhánh gh-pages, không đổi visibility và không Publish.

Chỉ khi người dùng cho phép kích hoạt: xác nhận repository công khai và tài khoản đủ điều kiện GitHub Pages miễn phí; không nâng gói hoặc bật thanh toán. Nếu repo riêng tư thì không tự đổi sang public hoặc trả phí. Chuyển template vào .github/workflows, đặt Source = GitHub Actions trong Settings → Pages, rồi chạy workflow_dispatch theo quyết định người dùng. Build artifact là viewer/dist; deploy artifact tại root của project Pages, không publish cả viewer hoặc cả repository. Chưa kiểm chứng workflow triển khai vì chưa chạy trên GitHub.

GitHub Pages không chạy Python/Blender hay bộ 18 vai trò: website chỉ xem mẫu và QA. Core và bộ não giữ trong repository để phát triển. Website luôn CẦN XÁC NHẬN, không có chức năng tự nghiệm thu.

## Tương thích và giới hạn

Đã kiểm tra Chromium desktop và touch ở kích thước iPhone 390×844, iPad 820×1180/1180×820, trên artifact thực ở đường dẫn project. Safari/iOS thật chưa được kiểm chứng. Giao diện dùng ES modules/import maps/WebGL2, cần Safari/iOS hiện đại (import maps từ Safari 16.4); không hứa hỗ trợ các phiên bản cũ. Sau khi được phép kích hoạt cần kiểm tra iPhone/iPad thật qua HTTPS của Pages. Chưa có URL Pages hoạt động.

Không tạo ảnh render. WebGL hiển thị 3D tương tác là chức năng viewer. Chuẩn bị/build/test cục bộ không dùng API trả phí, không thực hiện deployment.

Trong lần chuẩn bị này, trang repository GitHub hiển thị nhãn Public. Chưa thay đổi hoặc kiểm chứng cấu hình Pages, workflow triển khai hay URL production.
