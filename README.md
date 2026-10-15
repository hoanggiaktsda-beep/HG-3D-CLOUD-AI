# HOANGGIA 3D CLOUD AI — MASTER CODEX

**Dự án 01 — bộ não kiến trúc & nội thất Cloud 3D, dùng riêng trong Codex.** Không cần GitHub và không đụng tới 3ds Max trên Windows của người dùng.

## Dùng nhanh (người dùng)

1. Giải nén **nội dung** file ZIP trực tiếp vào thư mục đã chọn cho dự án Codex: `Documents/HG-3D-CLOUD-AI`. Không để lồng thêm thư mục con nếu muốn AGENTS.md ở ngay thư mục gốc.
2. Quay lại Codex → `HG 3D CLOUD AI` → ô nhập lệnh: **“Hãy đọc AGENTS.md và README.md, chạy kiểm thử, kiểm tra Blender rồi bắt đầu triển khai theo lộ trình; không dùng GitHub.”**
3. Để thử phần đã có: `python -m unittest discover -s tests -v` → `python scripts/hg3d.py check examples/living_room.json` → `python scripts/hg3d.py report outputs/qa_report.json`.
4. Nếu Blender được cài trong môi trường làm việc, thử dựng scene: `blender -b --python scripts/blender_build.py -- examples/living_room.json outputs/demo01` (output mới, không ghi đè). File dự kiến `hg_scene.blend`, `hg_scene.glb`, `qa_report.json`, `qa_report.html`.

**Không có Blender?** Chạy Python unit tests vẫn được; Blender build không thể chạy cho đến khi cài Blender trong runtime tương ứng. Không mặc định Codex là máy chủ cloud 24/7.

## Có gì trong bản này?

- `AGENTS.md`: chỉ dẫn Codex — quy trình, 1 Director + 17 bộ phận, quy tắc bảo mật, QA và lộ trình.
- `docs/`: tiêu chuẩn kiến trúc, đầu vào, schema, quy tắc dựng, kiểm định, cloud và yêu cầu nghiệm thu.
- `hgcloud/`: kiểm tra JSON scene, quản lý job độc lập và xuất báo cáo HTML chạy trên trình duyệt điện thoại (offline).
- `scripts/blender_build.py`: dựng cơ bản bằng Blender/Python **không render** với layer collection, vật liệu, đèn, camera.
- `examples/`: phòng khách tham số, console, mẫu yêu cầu ảnh.
- `tests/`: unit tests Python không phụ thuộc Blender.

## Phân biệt năng lực đã có / còn thiếu

| Chức năng | Trạng thái khởi tạo |
|---|---|
| Kiểm định cấu trúc JSON, đơn vị mm, đánh dấu xác nhận/suy luận | Có mã chạy, có test Python |
| Lưu job riêng không ghi đè, báo cáo HTML tĩnh | Có mã chạy, có test Python |
| Blender procedural basic shapes, vật liệu, camera, đèn | Có mã; **chưa kiểm thử Blender thật ở đây** |
| AI trực tiếp hiểu ảnh → tạo mô hình chi tiết chính xác | **Chưa hoàn thiện**; phải phát triển và đánh giá |
| Bản vẽ layout → kiến trúc đầy đủ, cửa/cột/trần | **Chưa hoàn thiện** |
| Geometry verification trong file BLEND & so sánh ảnh | **Chưa hoàn thiện** |
| Cloud worker chạy khi máy cá nhân tắt + giao diện iPhone trực tuyến | **Chưa triển khai hạ tầng** |
| Render | **Bị cấm theo yêu cầu** |

## Thông số kiến trúc

Đơn vị mm khi biểu diễn JSON, tọa độ Blender chuyển sang m (`mm / 1000`). Hệ trục: X ngang, Y sâu, Z cao; `center_mm` là tâm bbox, `size_mm` ba chiều. `confidence` phân biệt rõ `confirmed`, `inferred`, `needs_confirmation` kèm bằng chứng. Thiếu dữ liệu phải hiện `NEEDS_REVIEW`.

## Hạn chế

Một ảnh 2D không chứa đủ mọi mặt và dữ kiện để tự dựng đúng 100%. Gói này là nền tảng có mã nguồn, bộ não và kiểm thử, **chưa phải hệ thống nhận ảnh và dựng chi tiết không cần giám sát**. Với dự án CLOUD, đầu ra native `.max` cần môi trường 3ds Max hợp lệ; nên xuất BLEND/GLB/FBX rồi chuyển nếu cần.

## Nhập ảnh có chứng cứ (cục bộ)

Xem [IMAGE_PIPELINE.md](docs/IMAGE_PIPELINE.md) cho CLI nhận ảnh/OCR, observations theo từng trục và kiểm định mesh Blender. Nhận diện hình học tự động từ ảnh chưa được kết nối; output hiện là envelope có chứng cứ, không tự tạo chi tiết khuất.

Giao diện AI thị giác và pipeline replay: `scripts/vision_pipeline.py`; chưa kết nối model thật, mọi gọi live bị chặn. Xem tài liệu IMAGE_PIPELINE để chạy mẫu end-to-end không chi phí.

## Xem GLB trong trình duyệt (thử nghiệm)

Giao diện mẫu tại `viewer/`: xoay/zoom cảm ứng, góc camera, kích thước mesh và QA. Xem [hướng dẫn chạy và giới hạn kiểm thử](docs/GLB_VIEWER.md). Chỉ chạy loopback, chưa Publish; trạng thái cấu tạo luôn CẦN XÁC NHẬN.

Chuẩn bị website tĩnh cho đường dẫn `/HG-3D-CLOUD-AI/`: [hướng dẫn GitHub Pages](docs/GITHUB_PAGES_PREPARATION.md). Workflow triển khai tại `.github/workflows/deploy-pages.yml`; cần Source = GitHub Actions. Chỉ báo website hoạt động sau khi kiểm chứng deployment.

## TẠO MÔ HÌNH 3D — CHƯA KẾT NỐI

Có chọn và xem ảnh cục bộ, soạn yêu cầu; chưa upload, phân tích AI hay tạo job. Các nút gửi/dựng lại khóa tới khi có backend thật. Xem [trạng thái và hợp đồng tích hợp](docs/CREATE_MODEL_CONNECTION.md). Viewer mẫu giữ nguyên, không dùng kết quả mẫu để giả nhận diện ảnh người dùng.
