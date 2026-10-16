# HOANGGIA 3D WORKSPACE — giao diện tạo 3D từ ảnh

## Ý tưởng lấy cảm hứng từ Tripo Studio

Nghiên cứu trải nghiệm người dùng tại \`https://studio.tripo3d.ai/\` và tài liệu của nhà phát triển Tripo Studio. Các bài học áp dụng ở mức **bố cục và luồng sử dụng phổ biến**, không sao chép thương hiệu, mã nguồn, ảnh/đồ họa hoặc thuật toán độc quyền:

- Điều hướng giống phần mềm làm việc 3D, giao diện tối có điểm nhấn vàng của HOANGGIA AI.
- Khung tải ảnh lớn ở giữa ngay khi mở trang, có thao tác **chọn / kéo thả / dán ảnh** (tệp chỉ nằm trong trình duyệt). Giữ các bước giới hạn 8 ảnh, mỗi ảnh ≤20MB và tổng ≤60MB như phần kiểm định có sẵn.
- Hai chế độ thiết kế: **Giữ đúng hình dáng** (hình khối/tỷ lệ) và **Tách bộ phận** (mesh chỉnh sửa được). Lựa chọn thực sự đưa vào lệnh yêu cầu ChatGPT ở \`viewer/chatgpt-studio.js\`.
- Bảng trạng thái thông minh: ảnh đã nhận, lệnh ChatGPT đã chuẩn bị, mô hình JSON/GLB đã nhập và tùy chọn GLB/FBX.
- Các lối tắt: \`#hg-launch\` tạo từ ảnh, \`#create-model\` biểu mẫu nguồn, \`#chatgpt-studio\` chỉnh mesh, \`#sample-viewer\` viewer, \`#public-demo\` mẫu công khai.

## Luồng sử dụng (miễn phí, không yêu cầu máy chủ)

1. Tại màn hình đầu **Tạo từ ảnh**, nhấn ô giữa (hoặc kéo thả/dán ảnh).
2. Sau khi hệ thống kiểm tra file tại trình duyệt, ảnh hiển thị ngay trong vùng giữa; chương trình **không gọi AI khi vừa nhận ảnh**.
3. Chọn **Giữ đúng hình dáng** hoặc **Tách bộ phận** để bổ sung hướng dẫn hình học có ý nghĩa vào prompt.
4. Bấm **Chuẩn bị lệnh phân tích ảnh**: tạo/copy prompt và chuyển tới hướng dẫn gửi ảnh. Mở ChatGPT và tự đính kèm ảnh để AI phân tích.
5. Trở về **Xưởng chỉnh sửa 3D**, dán JSON ChatGPT cung cấp nếu đủ chứng cứ số đo hoặc nhập GLB; so sánh ảnh nguồn, chỉnh mesh, tải GLB/FBX nháp.

Nếu ảnh thiếu kích thước metric hoặc góc khuất, ChatGPT phải trả \`objects=[]\` và nêu phần cần xác nhận. Không được dựng bàn/sofa/tủ giả theo mẫu khi người dùng đưa ảnh mới.

## Giới hạn

- Đây là **giao diện và công cụ xử lý tại trình duyệt**, không phải hệ backend AI của Tripo. Không có image-to-3D học sâu, retopology tự động, texturing PBR, rigging, DCC Bridge hoặc gọi ChatGPT bằng session của người dùng.
- Web tĩnh không thể dùng tài khoản đăng nhập ChatGPT của người dùng để xử lý ảnh ở nền. Không có API key hay dịch vụ trả phí, nên phải gửi ảnh thủ công qua ChatGPT.
- FBX nhị phân và GLB được xuất từ mesh JSON/GLB đã có; không phải mô hình được đảm bảo giống ảnh hay mô hình đã nghiệm thu.
- Không lưu trữ ảnh khách hàng trên GitHub, không thêm mạng ngoài, không chỉnh các repository HOANGGIA AI khác.

## Kiểm thử

Tệp \`viewer/tests/test_workspace_launcher.py\` kiểm thử vùng bấm mở chọn tệp thật, kéo thả file tại trình duyệt, đồng bộ trạng thái nguồn, thay đổi prompt đúng hai chế độ và bố cục không tràn ở màn hình 320/390/820px. Bộ kiểm thử hồi quy giữ viewer, QA, FBX/GLB và ảnh không được tự suy luận sai.
