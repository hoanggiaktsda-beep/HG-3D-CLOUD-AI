# 3D AI | HOANGGIA AI — Xưởng chỉnh sửa V1

**Tên sản phẩm:** 3D AI · Thành viên của hệ sinh thái HOANGGIA AI  
**Repository:** HG-3D-CLOUD-AI (giữ nguyên để tránh đổi link)  
**Website:** https://hoanggiaktsda-beep.github.io/HG-3D-CLOUD-AI/#create-model  
**Xưởng chỉnh sửa:** https://hoanggiaktsda-beep.github.io/HG-3D-CLOUD-AI/#chatgpt-studio

## Phạm vi triển khai

Màn hình Tạo từ ảnh đã được phê duyệt **được giữ nguyên và vẫn là màn hình mặc định**. Khi người dùng nhấn **Xưởng chỉnh sửa 3D**, chuyển sang giao diện nhiều vùng lấy cảm hứng từ cách bố trí công cụ Tripo Studio nhưng sử dụng toàn bộ thiết kế, màu sắc, nhãn và logic HOANGGIA.

### Bố cục trên PC

1. **Thanh trên:** 3D AI / HOANGGIA AI, trạng thái model thực, trở lại, nhập GLB, xuất GLB/FBX khi có mesh.
2. **Thanh công cụ dọc:** Ảnh, Model, Bộ phận, Vật liệu, Xuất file. Retopo/UV AI chỉ hiện **disabled (chưa nối)**, không tạo tiến độ giả.
3. **Thiết lập trái:** ảnh tham chiếu, phân tích thủ công cùng ChatGPT, nhập JSON chuẩn, nhập GLB, bật wireframe/grid, hướng dẫn chọn mesh, xuất file.
4. **Trung tâm:** chính canvas WebGL Three.js của \`viewer/chatgpt-studio.js\`, không tạo canvas/model thứ hai. Camera phối cảnh, đứng, cạnh, bằng; nhấp mesh trực tiếp để chọn; ảnh nguồn đối chiếu và nhãn CẦN XÁC NHẬN.
5. **Bên phải:** hai tab Tài sản/Thuộc tính. Danh sách bộ phận phản ánh đúng mesh đang có, chọn mesh để chỉnh tên/màu/ẩn hiện, X/Y/Z (mm), góc xoay đứng, tỷ lệ, xóa, reset view.
6. **Thanh trạng thái:** phản hồi thật từ bộ dựng / xuất file và lỗi khi chưa đủ dữ liệu.

### iPad/điện thoại

Thanh công cụ thu thành một hàng cuộn ngang. Viewport vẫn ưu tiên trên cùng; các panel xuất hiện kế tiếp theo chiều dọc, không ép 4 cột gây tràn ngang hoặc giấu nút. Giao diện chỉ hiển thị dữ liệu thật.

## Bộ não được tái sử dụng, KHÔNG thay thế

Các file engine đang dùng:

- \`viewer/chatgpt-studio.js\`: nhận JSON hoặc GLB, tạo mesh thật, chọn bộ phận, thao tác vị trí/xoay/tỷ lệ, màu, xuất GLB và FBX nhị phân.
- \`viewer/app.js\`: khung xem GLB/QA cũ, đồng bộ từ bộ chỉnh sửa.
- \`viewer/photo-handoff.js\` / \`viewer/create-model.js\`: kiểm chứng ảnh tại trình duyệt và chuyển ảnh cho ChatGPT do người dùng chủ động.
- \`viewer/local-modules.js\`: dựng hình tham số theo số đo được xác nhận, **không giả nhận diện ảnh**.
- Bộ Python/Blender/Qwen/OCR/QA ở \`hgcloud/\`, \`scripts/\`, \`.github/workflows/\` được giữ nguyên; không tự kích hoạt các dịch vụ chưa kết nối.
- **Bộ não 18 trách nhiệm:** Director + 17 chuyên gia giữ nguyên theo AGENTS.md. Đây là vai trò điều phối/kiểm chứng, **không phải 18 mô hình AI chạy thật trong browser**.

## Quy trình thực tế

1. Tải ảnh từ màn hình đầu hoặc trong tool Ảnh → kiểm tra và xem ảnh cục bộ.
2. Người dùng ghi mô tả, số đo (mm), tự gửi ảnh vào ChatGPT để phân tích; chưa có API gọi tự động.
3. Nhập JSON \`hg-chatgpt-scene-v1\` đủ chứng cứ, hoặc GLB đã có.
4. Chọn mesh từ canvas hay danh sách Tài sản → chỉnh các thông số trên thuộc tính.
5. Xuất **GLB / FBX nhị phân từ chính mô hình trong trình duyệt**, lưu với nhãn NEEDS_REVIEW.
6. Nếu model chưa tồn tại hoặc thiếu kích thước, không cho tải file và không thay bằng khối hộp giả.

## Giới hạn chưa hoàn thiện

- Chưa có suy luận image-to-3D tự động ở website Pages: web không tự sử dụng tài khoản ChatGPT của người dùng.
- Chưa có Retopo AI, UV AI, tự tách mesh từ ảnh, tạo texture PBR hoặc hệ thống rig AI.
- Chưa có quyền lưu project cloud riêng, chưa có BLEND/MAX trực tiếp từ trình duyệt.
- Chưa có kiểm thử thực tế iOS Safari, Blender/3ds Max 2023 ở máy người dùng hoặc độ giống ảnh nội thất ngoài đời. Dữ liệu source/chỉnh sửa chỉ tồn tại trong phiên trình duyệt; tải file khi cần giữ bản nháp.
- Không sử dụng nền tảng/API tính phí, không yêu cầu thẻ, không commit ảnh khách hàng lên repository công khai.

## Kiểm thử nghiệm thu

- Giao diện 5 vùng hiện khi nhấn Xưởng chỉnh sửa, trang đầu vẫn tối giản.
- Model JSON thật → mesh → đổi màu, tên, ẩn/hiện, vị trí, góc camera.
- Hai tab Tài sản/Thuộc tính chọn đúng cùng một mesh.
- Chưa có model → nút xuất disabled.
- GLB có magic \`glTF\`, FBX có header \`Kaydara FBX Binary\`, không thay đuôi file.
- Không tràn ngang ở 320/390/820 px; kiểm hồi quy tất cả chức năng cũ, build allowlist/CSP/PWA.
- Chỉ công bố triển khai sau PR CI thành công và Pages Build/Deploy/Verify chạy đạt.
