# HG 3D CLOUD AI — Giao diện một màn hình

## Phạm vi đã được xác nhận

Chỉ hiển thị màn hình **Ảnh của bạn. Mô hình của bạn.** theo ảnh tham chiếu ngày 16/10/2026:

- Nhãn HOANGGIA / 3D WORKSPACE và tiêu đề chính.
- Khung chọn/kéo-thả/dán ảnh, số lượng và thumbnail của ảnh đã chọn.
- Hai lựa chọn Giữ đúng hình dáng hoặc Tách bộ phận (thực sự bổ sung hướng dẫn vào lệnh ChatGPT).
- Nút Chuẩn bị lệnh phân tích ảnh và Xưởng chỉnh sửa 3D.
- Bảng bên phải với 4 bước, trạng thái thực và cảnh báo AI chưa nối.
- Dòng tiến trình và liên kết mở bộ dựng kích thước (chỉ khi người dùng chủ động).

Tất cả khu vực còn lại được **ẩn bằng CSS** trên màn hình mặc định: sidebar, header cũ, thanh menu dưới, thư viện mẫu công khai, trình xem mẫu, khu vực công việc chưa kết nối, các biểu mẫu và bảng kiểm định kỹ thuật. Không xóa HTML nguyên gốc hoặc JS vì chúng chứa các ID và engine mà phần 3D đang dùng.

## Nút thao tác vẫn hoạt động

1. Chọn ảnh → ảnh được xác minh cục bộ và hiển thị trong hero, không tải lên GitHub.
2. Chuẩn bị lệnh phân tích → mở khung lệnh dạng thu gọn **trong cùng màn hình**, có sao chép lệnh, sao chép ảnh tùy quyền trình duyệt và mở ChatGPT.
3. Xưởng chỉnh sửa 3D → chuyển sang chế độ xem *chỉ editor*, còn toàn bộ bảng cũ không xuất hiện. Có nút quay về màn hình gốc.
4. Khi đã có JSON/GLB hợp lệ, editor cho chỉnh bộ phận và xuất FBX/GLB nháp như trước. Bấm bước Xem 3D khi chưa có mô hình riêng → thông báo chưa có, **không tự lấy mô hình mẫu làm kết quả của ảnh**.
5. Liên kết dựng khối theo số đo vẫn mở một chế độ tập trung nếu người dùng chủ động sử dụng.

Các chế độ điều hướng có đường dẫn băm \`#create-model\` (mặc định), \`#chatgpt-studio\` (editor), \`#sample-viewer\` (viewer) và \`#hg-modules\` (dựng hình tham số). Sidebar và các phần cũ chỉ tồn tại trong mã nguồn; không hiển thị tự động.

## Giữ nguyên bộ não

Giữ tất cả tệp \`viewer/app.js\`, \`viewer/chatgpt-studio.js\`, \`viewer/local-modules.js\`, \`viewer/create-model.js\`, \`viewer/photo-handoff.js\`, \`viewer/public-demo.js\`, \`viewer/model-service.js\` và các file Python/Blender, QA, workflows. Mã kết nối API ChatGPT tự động hoặc worker riêng **chưa có**, không tuyên bố đang phân tích ảnh bằng AI. Không phát sinh phí, không yêu cầu thẻ, không thay kho mã HOANGGIA AI khác.

## Kiểm thử

- Kiểm thử mặc định chỉ có một khu vực 3D Workspace xuất hiện (không còn hàng loạt bảng và sidebar).
- Kiểm thử trạng thái ảnh, lệnh ChatGPT nổi trên cùng màn hình, chuyển chế độ editor và quay lại.
- Kiểm thử điều hướng trên smartphone/touch, không tràn chiều ngang.
- Giữ nguyên các bài kiểm tra bộ não và xuất GLB/FBX cũ thông qua việc **tạm bỏ lớp giao diện tối giản trong bài thử**, không xóa mã hay bỏ kiểm tra.
- Kiểm tra công khai GitHub Pages sau khi build/deploy/verify; không coi kiểm thử trình duyệt giả lập là xác nhận Safari thật.

## Lưu ý cho lần phát triển sau

UI là một lớp hiển thị tối giản bên trên phần code đã có. Khi cần thêm bộ não/hình học mới, bổ sung ngay sau 4 bước trong một luồng duy nhất, không đưa tất cả bảng cũ ra màn hình mặc định.
