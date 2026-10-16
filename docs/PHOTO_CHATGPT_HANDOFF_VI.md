# Sửa Mục 01 — Không dựng sai mẫu khi tải ảnh

## Lỗi đã sửa

Trước đây: người dùng tải một ảnh bàn trà thấp có hốc lõm; nếu đã chọn mẫu bàn 4 chân và xác nhận kích thước, thuật toán cục bộ có thể vẽ chiếc bàn 4 chân **mà không hề nhìn ảnh**, khiến người dùng hiểu nhầm hệ thống đã nhận diện ảnh.

Bản sửa tách hẳn hai chế độ:

### A. Dựng **theo ảnh thật** (có ChatGPT tham gia thủ công, không gọi API)

1. Mở \`#create-model\`, chọn ảnh PNG/JPEG/WebP. Website xác thực file cục bộ.
2. Trình xem chính **xóa bản mẫu/bản nháp cũ** và hiện **CHỜ PHÂN TÍCH ẢNH**. Không tự thay bằng bàn 4 chân.
3. Nhấn **01 · Sao chép lệnh phân tích ảnh**. Lệnh yêu cầu ChatGPT nhận diện dáng đồ thật: hình khối, hốc, mặt trên, chân hoặc bệ, thành viền, cấu tạo thấy được; không suy đoán mặt khuất hay dùng mẫu bàn 4 chân.
4. Nhấn **02 · Mở ChatGPT**. Dán lệnh, **đính kèm chính ảnh đã chọn** trong ChatGPT (hoặc quay lại website và thử nút **03 · Sao chép ảnh đầu tiên** để dán ảnh trực tiếp nếu trình duyệt hỗ trợ).
5. Khi ChatGPT nhận ảnh và có số đo được xác nhận, sao chép JSON đúng \`hg-chatgpt-scene-v1\` về website, dán vào **XƯỞNG CHỈNH SỬA MÔ HÌNH 3D** → **Xem 3D từ JSON**.
6. So sánh **ảnh nguồn** bên cạnh mô hình 3D trong khung chỉnh. Chỉnh bộ phận, tải FBX/GLB nháp.

**Chú ý:** Nếu thiếu kích thước tuyệt đối, ChatGPT phải yêu cầu người dùng cung cấp kích thước, KHÔNG bịa ra số đo từ ảnh. Tạo bản nháp chưa có độ tin cậy sản xuất.

### B. Dựng **mẫu tham số không dựa trên ảnh**

Nếu muốn tạo một khối bao, bàn 4 chân, console hay tủ kệ minh họa từ số đo, nhập đủ ba kích thước và đánh dấu đã xác nhận. Khi **có ảnh**, nút/thuật toán dựng mẫu chỉ hoạt động nếu người dùng còn chủ động đánh dấu thêm **Chỉ dựng mẫu minh họa, KHÔNG theo ảnh đã tải lên**. Tích chọn này bị hủy mỗi lần đổi ảnh nguồn.

## Giới hạn kỹ thuật

- **Không có ChatGPT API ở GitHub Pages.** Giao diện đăng nhập ChatGPT không cho phép website bên ngoài tự dùng tài khoản của người dùng để gọi AI. Nút chọn ảnh chỉ xác minh file ở trình duyệt; không tự gửi ảnh sang ChatGPT, không đọc hình ảnh bằng mô hình thị giác.
- Ảnh gốc chỉ có trong bộ nhớ trình duyệt; thao tác sao chép ảnh là tùy chọn, do người dùng chủ động thực hiện, chuyển một bản PNG vào clipboard; không upload qua server.
- JSON do người dùng dán được dựng bằng Three.js, không được trang web xác thực là đến từ ChatGPT hay giống ảnh thật. Hiển thị rõ **CẦN ĐỐI CHIẾU ẢNH ↔ MÔ HÌNH** và **CẦN XÁC NHẬN**.
- Không phát sinh phí AI/API hoặc yêu cầu thẻ; không sử dụng Codex, Render, dịch vụ Linux hay lưu ảnh khách hàng vào GitHub. FBX/GLB là bản nháp thật nhưng tính chính xác hình học cần người dùng kiểm định.

## Bộ kiểm thử

\`viewer/tests/test_photo_handoff.py\` thử đủ 3 tình huống:
- Có số đo và một bàn 4 chân đã dựng, sau đó tải ảnh mới lên ⇒ mô hình cũ bị xóa, trạng thái chờ phân tích; không có tải FBX của ảnh mới.
- Prompt nhận diện hình dạng từ ảnh cụ thể, không gọi API, không tự tạo mô hình.
- Dán một JSON minh họa gồm các tấm viền và đáy lõm ⇒ khung 3D dựng sáu bộ phận, hiển thị ảnh để so sánh và cho tải GLB.

Các bài thử chỉ xác nhận hành vi giao diện/đầu ra theo dữ liệu đã nhập, **không** chứng minh ChatGPT tự phân tích ảnh từ website hoặc dựng sản phẩm đúng theo ảnh.
