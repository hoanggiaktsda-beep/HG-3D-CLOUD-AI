# Định dạng SCENE.JSON chuẩn HG3D v1.0

Ví dụ: `examples/living_room.json`, `examples/product_console.json`.

- `schema_version`: bắt buộc `"1.0"`.
- `project`: tên dự án không trống.
- `units`: bắt buộc `"mm"`.
- `source_images`: mảng đường dẫn ảnh nếu có, ghi kèm trong phiếu yêu cầu.
- `objects`: danh sách có ít nhất một đối tượng với `id` duy nhất, `kind`, `center_mm`, `size_mm`, `material`, `confidence`, `source_note`, tùy chọn `rotation_deg`, `color_rgb`, `dimensions_tolerance_mm`.
- `lights`: mảng đèn `id`, `position_mm`, `power_w`, tùy chọn `diameter_mm`.
- `cameras`: mảng `id`, `position_mm`, `target_mm`, tùy chọn `lens_mm`.

`kind` được hỗ trợ ở schema: `box`, `cylinder`, `sphere`, `sofa`, `armchair`, `coffee_table`, `cabinet`, `bed`, `wall`, `floor`, `ceiling`, `door`, `window`, `panel`, `shelf`, `rug`, `column`. Trong mã hiện tại, tường/ô cửa chỉ là hộp cơ bản, CHƯA boolean tường và cửa thật. Sofa, giường, tủ chỉ là mockup thông số, CHƯA là asset thiết kế cụ thể.

`confidence`:

- `confirmed`: có bằng chứng trực tiếp hoặc kích thước do người dùng chỉ định; ghi rõ trong `source_note`.
- `inferred`: suy ra từ bố cục, chưa đo xác thực.
- `needs_confirmation`: mâu thuẫn hoặc thiếu dữ liệu quan trọng.

Không tự động nâng `inferred` lên `confirmed`. Với sản phẩm mạo danh thương hiệu/nội thất, nếu không có ảnh đối chiếu đủ góc thì không ghi model chính hãng đã được tái dựng chính xác.

Kích thước được so sánh phải lấy từ mesh thực tế trong file Blender (gồm rotation, modifier) bằng script đo độc lập trước nghiệm thu; gói khởi tạo mới xác minh schema.
