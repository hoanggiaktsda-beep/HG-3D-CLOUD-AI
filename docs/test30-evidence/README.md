# TEST 30 — bằng chứng công khai, CHƯA LẮP RÁP HOÀN CHỈNH

BLEND/GLB ở đây là **20 tấm rời tại vị trí sơ đồ cắt**, không phải ghế đã lắp.
Không dùng bộ file này để nghiệm thu lắp ráp hoặc gia công. Tất cả vị trí lắp,
ánh xạ tên tấm, khe hở và liên kết còn CẦN XÁC NHẬN. Không có dữ liệu khách hàng.

- [BLEND](source_parts_review.blend) và [GLB](source_parts_review.glb).
- [Kiểm định từng bộ phận và từng cặp](assembly-qa-local.json).
- [Kết quả hai nguồn công khai](test30-local.json).
- [Trang 3 có các hình chiếu nguồn](orthographic_source.png) và
  [bảng quan sát/nhãn OCR](assembly-plan-observations.json). Nhãn rộng là
  khoảng giá trị, chưa xác định biến thể; chương trình chưa đăng ký được
  các hình chiếu này vào từng contour. Không nói tài liệu AtFAB thiếu hình chiếu.
- Viewport GUI thực, không render: [mặt bằng](viewport_top.png),
  [mặt trước](viewport_front.png), [mặt cạnh](viewport_side.png),
  [phối cảnh](viewport_perspective.png). Các góc này xem **tấm rời**, không phải
  đối chiếu hình chiếu sản phẩm lắp ráp với bản vẽ chưa có.
- [SHA-256 và kích thước file](manifest.json).

Nguồn mô hình phái sinh: **AtFAB / Filson and Rohrbacher, Five To Thirty Minute
Chair, ©2013**. [PDF gốc công khai](https://raw.githubusercontent.com/opendesk/design-playground/gh-pages/OD-51381-5-To-30-Minute-Chair-1.0.0/OD-51381-Assembly-Guide.pdf),
SHA-256 `e295e6496d2b5dc314175afc678bf7b0aa61d984dc52b7d53e50c4d602441445`.
Giấy phép ghi trên trang 7 PDF: [CC BY-NC-SA 3.0](https://creativecommons.org/licenses/by-nc-sa/3.0/).
Các mô hình và ảnh phái sinh trong thư mục này được chia sẻ theo cùng giấy phép,
chỉ sử dụng phi thương mại, giữ ghi công và điều kiện chia sẻ tương tự.

Thay đổi so với nguồn: phân đoạn đường cắt từ ảnh raster, đùn theo chiều dày
danh nghĩa OCR, giữ sơ đồ cắt; không lấy CAD gốc, không tự lắp ghế, không thêm
lỗ khoan vật lý hoặc chi tiết khuất. Đã mở lại BLEND và nhập lại GLB bằng
Blender 4.3.2. Sai số nội bộ dưới 0,1 mm không có nghĩa dung sai ảnh dưới 0,1 mm.
