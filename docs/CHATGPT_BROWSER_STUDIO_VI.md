# HG 3D CLOUD AI — Chế độ ChatGPT, không dùng Codex hoặc máy chủ riêng

## Công cụ được bổ sung

Trang `#create-model` sử dụng HTML/JavaScript tĩnh tại GitHub Pages.

- Chọn và kiểm tra ảnh PNG/JPEG/WebP tại thiết bị (giới hạn hiện có: 8 ảnh, 20 MB/ảnh và tổng 60 MB). Ảnh không tự gửi sang GitHub, OpenAI hoặc máy chủ bất kỳ.
- Nhập yêu cầu và số đo xác nhận. **Tạo lệnh** hoặc **Tải JSON công việc** (gồm prompt, danh sách tên ảnh và loại đầu vào; **không chứa dữ liệu ảnh**).
- **Mở ChatGPT** trong tab mới; người dùng sao chép lệnh và đính kèm ảnh bằng giao diện ChatGPT. Đây không phải tích hợp tài khoản hay API OpenAI. Không có AI tự đọc ảnh trên website, không tính phí API tự động.
- Khi ChatGPT cung cấp JSON cấu trúc `hg-chatgpt-scene-v1`, sao chép vào website để dựng hình khối cục bộ bằng Three.js. Có thể nhập JSON từ tệp, hoặc nhập GLB 2.0 không có tham chiếu tài nguyên ngoài và dưới 30 MB.
- Chọn mesh, sửa tọa độ tâm X/Y/Z (mm), xoay trục đứng, thay tỷ lệ đồng nhất, xóa bộ phận, xem mô hình 360 độ và tải **GLB nháp**. Mọi chỉnh sửa chỉ tồn tại trong phiên trang web, không lưu tự động.
- Không hỗ trợ tạo BLEND trong trình duyệt; GLB có thể mở trên Blender/3ds Max qua trình nhập phù hợp. Đầu ra có nhãn **CẦN XÁC NHẬN**, không tự phê duyệt hoặc xem là tài liệu sản xuất.

## Quy trình ngắn

1. Mở `#create-model`, chọn ảnh ở mục đầu vào và điền yêu cầu/kích thước đã có.
2. Cuộn tới **XƯỞNG CHỈNH SỬA MÔ HÌNH 3D**, nhấn **Tạo lệnh từ yêu cầu**, sau đó **Sao chép lệnh → Mở ChatGPT**.
3. Đính kèm ảnh trực tiếp vào cuộc trò chuyện ChatGPT nếu tự nguyện đồng ý chia sẻ. Nhận phân tích và JSON do ChatGPT tạo ra.
4. Dán JSON vào ô **Nhận mô hình ChatGPT trả về**, nhấn **Xem 3D từ JSON**. Chỉnh bộ phận tại chỗ và tải GLB nháp.

## Dạng JSON mẫu minh họa (KHÔNG phải kết quả nhận diện ảnh)

```json
{
  "schema": "hg-chatgpt-scene-v1",
  "unit": "mm",
  "review_status": "NEEDS_REVIEW",
  "objects": [
    {
      "id": "panel_01",
      "name": "Vách thử nghiệm",
      "shape": "box",
      "size_mm": [1000, 25, 800],
      "position_mm": [0, 0, 400],
      "rotation_deg": [0, 0, 0],
      "color": "#8a735c",
      "confidence": "inferred"
    }
  ],
  "unknown_details": ["Chưa xác nhận tỉ lệ, vật liệu và bộ phận khuất"]
}
```

**Quan trọng:** Khi không có kích thước xác nhận, ChatGPT nên trả `objects: []` và nêu rõ dữ liệu thiếu thay vì tạo kích thước giả. Ví dụ trên chỉ để hiểu định dạng. Bộ dựng không kiểm tra độ giống ảnh; việc có GLB không đồng nghĩa chính xác.

## Bảo mật và khả năng vận hành

- GitHub Pages CSP `connect-src 'self'`: không có API gọi OpenAI, không có khóa API trong JavaScript.
- Tệp ảnh và mô hình nhập là đối tượng trong bộ nhớ trình duyệt. Tạo lệnh và file JSON công việc chủ động theo yêu cầu người dùng. Bản sao lệnh trong clipboard và tệp tải xuống chịu chính sách của thiết bị; có thể chứa tên ảnh/ghi chú.
- PWA chỉ cache các asset công khai cố định của trang, không cache ảnh do người dùng chọn, mô hình nhập hoặc mô hình xuất. Khi đóng trang, các thay đổi chưa tải về sẽ mất.
- ChatGPT là công cụ bên ngoài: phải tự đính kèm ảnh; không thể tự động truyền dữ liệu giữa GitHub Pages và ChatGPT bằng phiên đăng nhập. Dịch vụ ChatGPT có các giới hạn riêng theo tài khoản.
- Không render quang thực, không thay các hệ thống Qwen/OCR/Blender công khai đang có; các bài thử trước giữ trạng thái và TEST 30 vẫn **CẦN XÁC NHẬN**.
- Three.js chỉ dựng hình học tham số đơn giản (hộp/trụ) và cho phép biến đổi mesh. Chưa hỗ trợ dựng nội thất phức tạp hoàn toàn tự động, Boolean, CAD/BLEND, tự đo vật liệu/ánh sáng, hay kiểm định cấu tạo từ một ảnh.

## Kiểm thử

Chạy `npm ci` và `npm run build` trong thư mục `viewer/`. Sau đó khởi động server nội bộ bằng `python3 ../scripts/serve_viewer.py`. Kiểm thử bằng `python3 -m unittest discover -s viewer/tests -v` từ gốc repository, gồm trình duyệt thực Chromium. Safari trên iPhone/iPad cần xác minh trên thiết bị thật.
