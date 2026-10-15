# GitHub Pages — workflow triển khai mẫu

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

## Kích hoạt trong GitHub (không cần trả phí)

Workflow đã đặt tại `.github/workflows/deploy-pages.yml`, chỉ upload `viewer/dist`. Chạy khi viewer/workflow thay đổi trên main hoặc qua workflow_dispatch. Không upload cả repository, không chạy Python/Blender. Bộ 18 vai trò giữ nguyên trong mã nguồn; website chỉ xem GLB mẫu và QA.

1. Mở repository HG-3D-CLOUD-AI trên GitHub → Settings → Pages.
2. Trong Build and deployment, chọn Source = GitHub Actions.
3. Mở Actions → Deploy HG sample viewer to Pages. Nếu lần chạy do push đã lỗi vì Pages chưa cấu hình, dùng Re-run all jobs hoặc Run workflow với nhánh main.
4. Chờ cả build và deploy xanh. URL do job deploy/github-pages cung cấp là URL cần kiểm tra, không tự coi việc push workflow là website đã hoạt động.
5. Mở URL đó, kiểm tra GLB, số đo 1800 × 450 × 850, xoay/zoom, góc camera và trạng thái CẦN XÁC NHẬN. Kiểm tra thêm Safari/iPhone/iPad thật.

Repository đã được quan sát hiển thị Public. Chỉ dùng Pages miễn phí, không bật thanh toán hay nâng gói. Không đổi visibility. Workflow dùng GitHub-hosted runner cho repository công khai; không dùng API AI hoặc hạ tầng trả phí.

Trong phiên triển khai, GitHub API từ môi trường Codex trả Forbidden khi đọc Pages; cấu hình Source và kết quả deployment chưa xác minh được bằng API. Không báo website hoạt động trước khi xác minh workflow thành công và truy cập trang. Giữ ghi nhận này cho tới khi có bằng chứng mới.

## Tương thích và giới hạn

Đã kiểm tra Chromium desktop và touch ở kích thước iPhone 390×844, iPad 820×1180/1180×820, trên artifact thực ở đường dẫn project. Safari/iOS thật chưa được kiểm chứng. Giao diện dùng ES modules/import maps/WebGL2, cần Safari/iOS hiện đại (import maps từ Safari 16.4); không hứa hỗ trợ các phiên bản cũ. Sau khi được phép kích hoạt cần kiểm tra iPhone/iPad thật qua HTTPS của Pages. URL Pages hoạt động chưa được xác minh trong phiên này.

Không tạo ảnh render. WebGL hiển thị 3D tương tác là chức năng viewer. Chuẩn bị/build/test cục bộ không dùng API trả phí, không thực hiện deployment.

Trong lần chuẩn bị này, trang repository GitHub hiển thị nhãn Public. Chưa thay đổi hoặc kiểm chứng cấu hình Pages, workflow triển khai hay URL production.
