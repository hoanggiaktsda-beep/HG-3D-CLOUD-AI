# HOANGGIA 3D AI — kết nối TripoSR miễn phí (thử nghiệm cục bộ)

## Trạng thái chính xác

- Website GitHub Pages **không** chạy TripoSR, không cung cấp GPU hay máy chủ AI miễn phí.
- Đã thêm nút **AI TẠO 3D TỪ ẢNH → Kiểm tra TripoSR → TẠO 3D TỪ ẢNH** vào xưởng chỉnh sửa.
- Bộ kết nối scripts/triposr_local_bridge.py chạy **chỉ trên 127.0.0.1:8787**, nhận đúng một ảnh sau khi người dùng tích xác nhận, gọi **TripoSR chính thức** rồi trả tệp GLB nhị phân cho xưởng Three.js.
- Phần mềm và trọng số TripoSR dùng giấy phép MIT (nguồn chính thức: https://github.com/VAST-AI-Research/TripoSR). Không cần khóa API hoặc đăng ký dịch vụ trả phí. **Chi phí GPU/điện/phần cứng không bằng 0.**
- Chưa có kết quả suy luận GPU TripoSR được xác minh trong CI: CI chỉ kiểm thử HTTP, bảo mật và giao diện bằng bộ dựng giả **chỉ trong bài kiểm thử**. Chưa được phép tuyên bố tái dựng chính xác sản phẩm hoặc đạt chuẩn CAD.

## Cài trên Windows (PowerShell) hoặc Linux

1. Cài Python tương thích TripoSR (khuyến nghị bắt đầu với Python 3.10) và Git. Với NVIDIA, cần trình điều khiển GPU và bản PyTorch/CUDA phù hợp. GPU khoảng 6 GB VRAM theo README chính thức. CPU có thể chạy nhưng rất chậm, thậm chí không đủ RAM.
2. Mở terminal trong thư mục **HG-3D-CLOUD-AI** (thư mục có scripts/, viewer/).
3. Tải mã nguồn chính thức **vào thư mục riêng, không commit**:

       git clone https://github.com/VAST-AI-Research/TripoSR.git .private/TripoSR

4. Tạo môi trường Python riêng. Trên Windows PowerShell:

       py -3.10 -m venv .private\triposr-venv
       .private\triposr-venv\Scripts\python.exe -m pip install --upgrade pip setuptools

   Trên Linux:

       python3.10 -m venv .private/triposr-venv
       .private/triposr-venv/bin/python -m pip install --upgrade pip setuptools

5. Cài **PyTorch phù hợp phần cứng** theo https://pytorch.org/get-started/locally/ trước, rồi cài phụ thuộc của TripoSR:

   Windows:

       .private\triposr-venv\Scripts\python.exe -m pip install -r .private\TripoSR\requirements.txt

   Linux:

       .private/triposr-venv/bin/python -m pip install -r .private/TripoSR/requirements.txt

   Nếu torchmcubes, xatlas, rembg hoặc PyTorch lỗi, phải giải quyết theo hướng dẫn dự án gốc; đây không phải phần mềm một-click và không cam kết mọi máy đều tương thích.

6. Chạy bộ kết nối, dùng **đúng Python vừa cài TripoSR**. Ví dụ Windows:

       py -3.10 scripts\triposr_local_bridge.py --triposr-dir .private\TripoSR --python .private\triposr-venv\Scripts\python.exe

   Linux:

       python3 scripts/triposr_local_bridge.py --triposr-dir .private/TripoSR --python .private/triposr-venv/bin/python

7. Mở http://127.0.0.1:8787/health **trên cùng máy tính**. Nếu engine_found là true, website có thể thử gọi TripoSR; điều đó **chưa chứng minh** GPU hoặc model đã chạy thành công. Mô hình trọng số có thể được tải từ Hugging Face khi suy luận lần đầu.
8. Mở https://hoanggiaktsda-beep.github.io/HG-3D-CLOUD-AI/#chatgpt-studio trên **chính máy tính đang chạy bộ kết nối**. Chọn Ảnh → một ảnh PNG/JPEG/WebP → Model → Kiểm tra TripoSR → tích đồng ý → TẠO 3D TỪ ẢNH. Chờ GLB mở trong xưởng, sau đó có thể chỉnh mesh và xuất GLB/FBX.

**Trình duyệt**: GitHub Pages dùng HTTPS và bộ xử lý cục bộ dùng HTTP loopback. Chromium có hỗ trợ truy cập địa chỉ loopback đáng tin cậy nhưng có thể hỏi quyền truy cập mạng nội bộ; Safari hoặc chính sách trình duyệt có thể chặn. Khi bị chặn, xem lỗi Console và thử trên Chrome/Edge ở chính máy chạy TripoSR. Không mở cổng 8787 ra Internet.

## iPhone và mạng LAN

127.0.0.1 trên iPhone là **chính iPhone**, không phải máy tính Windows. Vì vậy **không thể** tạo ảnh→3D trên iPhone thông qua bridge này khi AI chạy trên PC khác. Xưởng xem/chỉnh GLB và dựng tham số vẫn dùng được trên iPhone.

Để dùng iPhone gửi ảnh tới GPU trên PC cần một dịch vụ HTTPS có xác thực, quản lý quyền, giới hạn truy cập, bảo vệ ảnh, CORS/PNA và cấu hình mạng. **Chưa triển khai**; không mở API cục bộ công khai hoặc tự tạo dịch vụ có phí.

## Giới hạn và quyền riêng tư

- Ảnh chỉ gửi khi bấm **TẠO 3D TỪ ẢNH** và đã xác nhận; chỉ gửi tới http://127.0.0.1:8787, không gửi đến GitHub/Tripo API. TripoSR có thể tự tải **trọng số mô hình** từ Hugging Face nếu máy chưa có.
- Bridge chỉ lắng nghe 127.0.0.1, từ chối Host/Origin lạ, kiểm tra MIME và dấu hiệu định dạng, giới hạn 20 MB ảnh, 30 MB GLB, không lưu ảnh hoặc kết quả sau khi trả về; mỗi lần chỉ chạy một tác vụ.
- Một ảnh chỉ tạo ước lượng 3D: mặt khuất, tỷ lệ thực, kích thước mm, chi tiết cơ khí và chất lượng lưới chưa được xác minh. **Không tự động xuất hồ sơ kỹ thuật**.
- Lần chạy đầu có thể mất nhiều phút. Nếu GPU không đủ bộ nhớ, TripoSR có thể lỗi; kiểm tra cửa sổ terminal.
- Các bài kiểm thử tự động **không tải model nặng và không chạy GPU thật**. Phải thử trực tiếp trên máy chồng trước khi tuyên bố tính năng AI hoạt động hoàn chỉnh.

## Kiểm thử kỹ thuật

    python3 -m unittest viewer.tests.test_triposr_bridge -v

Kiểm tra CORS/Origin, từ chối ảnh không hợp lệ, chỉ chạy một job, GLB thật từ fixture **trong test**, và xóa dữ liệu tạm. Không dùng mẫu fixture để đánh tráo kết quả suy luận TripoSR.
