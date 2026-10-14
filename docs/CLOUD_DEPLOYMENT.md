# Đưa HG 3D CLOUD AI ra cloud (chưa triển khai)

Lưu ý: Project hiện đang dùng `Máy tính này` trong Codex. Đây là thư mục cục bộ; máy Windows tắt thì quy trình dựng bằng Blender trên máy đó cũng dừng. Codex không phải máy chủ chạy liên tục theo mặc định.

Để đạt **người dùng ra ngoài, máy tắt, vẫn dựng trên server** phải có:

1. Nơi chạy Blender headless riêng biệt (worker container/máy chủ Linux hoặc Windows), đủ CPU/RAM/đĩa; không tự tạo tài khoản trả phí.
2. Bộ nhận tác vụ nhận ảnh và chỉ thị; hàng đợi, định mức timeouts, retry; file lên xuống qua object storage có TTL.
3. Quy trình phân tích ảnh có thực (model vision/đọc bản vẽ), kết quả scene được kiểm tra nguồn.
4. Worker tự build, kiểm thử file, lưu artifacts và QA; giao diện mobile đã đăng nhập (không public dữ liệu nội thất), có chức năng duyệt/đặt câu hỏi.
5. Giới hạn kích thước upload, kiểm tra file độc hại, không thực thi code do user upload, quản trị secrets, log tối giản, kiểm soát quyền xoá/lưu.
6. Backup/phiên bản và đánh giá chi phí trước khi kích hoạt.

Gói này **KHÔNG** được mô tả là có remote dashboard hoặc cloud service đã chạy. `qa_report.html` là báo cáo HTML xem offline được nếu chép lên điện thoại, không phải URL trực tuyến.

Tạo file native `.max` không thể thực hiện bằng cách đổi đuôi GLB. Cần 3ds Max chạy trong môi trường Windows được cấp phép hoặc nhập định dạng trung gian vào 3ds Max sau.
