# Lộ trình triển khai cho Codex theo tiêu chuẩn hoàn chỉnh

## P0 — Có thể kiểm chứng ngay

- Test Python; kiểm tra schema, evidence, QA HTML; thử dựng Blender thật nếu môi trường có Blender.
- Mở GLB trong viewer thực và BLEND trong Blender. Đo độ dài từng đối tượng, không chỉ so JSON.

## P1 — Dựng mặt bằng và bản vẽ kỹ thuật

- Parser mặt bằng, tọa độ/chiều dày tường, cửa, trần, dầm/cột, phòng; đối chiếu kích thước chuỗi.
- Tường boolean cho ô cửa, cửa sổ/cánh cửa thực, floor, ceiling, skirting, moulding; tách layer rõ ràng.
- Đọc ảnh bản vẽ dưới vai trò vision, kiểm tra vùng OCR chưa rõ, phát hiện nghịch lý hình chiếu.

## P2 — Dựng sản phẩm có bản sắc thiết kế

- Shape từ curve/mesh, profile sweep, subdivision, chamfer, topology sạch, UV đúng tỷ lệ.
- Sofa/ghế armchair/bàn trà/tủ/giường: hình khối, tỷ lệ, tay tựa, đệm, chân, đường may, cấu tạo; không gọi primitive là sản phẩm chính hãng.
- Cho phép nhiều ảnh tham chiếu sản phẩm, locking camera/architecture và đặt model tùy theo người dùng.

## P3 — Kiểm định độc lập và báo cáo từ xa

- World-space geometry bbox, đối chiếu spec theo dung sai, cảnh báo overlap không mong muốn, normal, loose faces, missing textures.
- Chụp screenshot viewport không render: phối cảnh, plan, 4 mặt đứng, detail, so sánh với ảnh gốc; ghi chú sai lệch và nguồn.
- Báo cáo HTML tối ưu iPhone và quyền phê duyệt; các job thiếu bằng chứng chỉ là DRAFT.

## P4 — Cloud unattended có bảo mật

- Thiết kế API và worker persistent, queue, artifact storage, cloud login, nhận ảnh từ điện thoại, khả năng theo dõi/hủy job.
- Duyệt hạ tầng, giá thành và quyền truy cập trước khi triển khai. Codex không tự được coi là cloud host.

## P5 — Hiệu năng và sản xuất

- Benchmark số lượng đối tượng và thời gian dựng, giới hạn RAM, resilience, checkpoint, automatic resume.
- Bộ cảnh chuẩn vàng có số đo được xác minh; tỷ lệ PASS có evidence, không chỉ tự nhận đúng.
