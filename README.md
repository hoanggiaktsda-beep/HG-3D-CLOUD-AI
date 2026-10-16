# HG 3D CLOUD AI

Dự án thử nghiệm dựng và kiểm định 3D có giám sát. Giữ Director + 17 chuyên gia theo [AGENTS.md](AGENTS.md). **Chưa sẵn sàng sử dụng thực tế như hệ thống tự nhận ảnh và dựng hoàn chỉnh.** Không render.

## Giao diện HOANGGIA STUDIO

Bản website HG 3D CLOUD AI dùng cùng hệ nhận diện với [HOANGGIA STUDIO](https://hoanggiaktsda-beep.github.io/hoanggia-studio/#home): monogram HA, sidebar desktop, thanh điều hướng dưới trên điện thoại, sắc tối/xanh than/vàng champagne, breadcrumb và nút Home. Giao diện độc lập, chỉ thay đổi repository này; toàn bộ viewer, kiểm định và trình chỉnh GLB giữ nguyên logic.

## Mục 01 — Nhận ảnh đúng, không dựng nhầm mô hình mẫu

Đã khắc phục tình huống tải ảnh bàn trà khối hộp thấp/hốc lõm mà hệ thống lại hiển thị bàn 4 chân: **vừa chọn ảnh nguồn mới, website xóa bản nháp cũ và báo CHỜ PHÂN TÍCH ẢNH; tuyệt đối không tự dựng mẫu theo ảnh**. Mẫu tham số chỉ chạy khi không có ảnh, hoặc người dùng chủ động tích thêm ô **Chỉ dựng mẫu minh họa, KHÔNG theo ảnh đã tải lên**. Nút sao chép lệnh / sao chép ảnh / mở ChatGPT / dán JSON giúp tạo vòng làm việc từ ảnh gốc, có ảnh tham chiếu cạnh khung 3D để đối chiếu. Không có API hay 18 AI chạy tự động từ thao tác tải ảnh. [Xem hướng dẫn và giới hạn](docs/PHOTO_CHATGPT_HANDOFF_VI.md).

## Mục 01 — Bộ mô-đun dựng 3D trực tiếp từ số đo

Tại [Tạo mô hình 3D](https://hoanggiaktsda-beep.github.io/HG-3D-CLOUD-AI/#create-model), khi người dùng nhập **ba kích thước được xác nhận**, mô-đun tự tạo hình học ở **khung KHÔNG GIAN 3D chính**, cập nhật thống kê mesh/kích thước/điểm chưa biết và cho xuất **GLB/FBX bản nháp** ngay trên thiết bị. Có thể chọn khối bao an toàn hoặc mẫu bàn, console, tủ kệ; các tấm/chân của mẫu là **giả định minh họa do người dùng chủ động chọn**, không nhận diện tự động qua ảnh. Tải ảnh sẽ kích hoạt kiểm tra định dạng, nhưng **mô-đun tham số KHÔNG tự dựng một bàn/tủ mẫu dựa trên ảnh** nếu người dùng chưa bật quyền tạo mẫu minh họa riêng. Hệ thống cũng **từ chối bịa kích thước** nếu chưa có số đo xác nhận. Không đăng ảnh hay mô hình lên máy chủ.

FBX nhị phân dùng gói mã nguồn mở MIT \`@comfyorg/fbx-exporter-three\`, GLB dùng Three.js. File có nhãn NEEDS_REVIEW, không phải hồ sơ thi công. Tương thích phụ thuộc phần mềm nhập và phải kiểm chứng với Blender/3ds Max trên thiết bị thật. Mọi giới hạn ChatGPT-only vẫn như cũ: **không có AI tự đọc ảnh khi upload** vì không có API/worker riêng, không có 18 mô hình AI thật chạy trong trình duyệt. [Chi tiết phạm vi](docs/LOCAL_PARAMETRIC_PIPELINE_VI.md).

## Chỉnh sửa 3D cùng ChatGPT trên website (không cần Codex)

[**Mở công cụ ChatGPT Studio**](https://hoanggiaktsda-beep.github.io/HG-3D-CLOUD-AI/#create-model): chọn ảnh trên thiết bị → tự tạo lệnh ChatGPT và đính kèm thủ công → dán JSON hình học ChatGPT trả về → xem/chỉnh mô hình cục bộ bằng Three.js → tải GLB **bản nháp**. Có thể nhập GLB có sẵn để chỉnh vị trí, góc xoay và tỷ lệ. Không lưu ảnh khách hàng, không yêu cầu API key, không dùng server riêng, không phát sinh chi phí API tự động. **Không kết nối ChatGPT tự động**, không xuất BLEND từ trình duyệt, không khẳng định tái dựng chính xác từ một ảnh. Xem [hướng dẫn chi tiết](docs/CHATGPT_BROWSER_STUDIO_VI.md).

## Giai đoạn hoàn thiện sản phẩm

[Mẫu AI công khai trên website](https://hoanggiaktsda-beep.github.io/HG-3D-CLOUD-AI/#public-demo) đã có kết quả Qwen/OCR → Blender thật, GLB/BLEND và QA. Chạy lại qua workflow GitHub được xác thực dành cho người có quyền write; không có token trên website. Mẫu hiện là tấm rời, chưa lắp ráp; ảnh khách hàng không được gửi vào workflow công khai. [Phạm vi đã kiểm chứng và phương án backend riêng](docs/PRODUCT_COMPLETION_VI.md).

## Trạng thái đã có bằng chứng

- [Viewer mẫu công khai](https://hoanggiaktsda-beep.github.io/HG-3D-CLOUD-AI/): xoay/zoom, kích thước mesh, QA, GLB/BLEND và PWA. [TEST 32](docs/TEST32_RESULTS_VI.md) đã triển khai và kiểm tra website thật. Kiểm thử dùng Chromium giả lập, chưa thiết bị thật/Safari.
- [Cloud Worker](docs/GITHUB_ACTIONS_WORKER.md) chạy Blender trên GitHub-hosted Actions, không cần máy cá nhân chạy Blender. Chỉ nhận dữ liệu mẫu công khai, không phải backend website luôn bật.
- [Qwen + OCR](docs/ASSEMBLY_VISION_TRIAL_RESULTS_VI.md) đã chạy mô hình thật trên ba bản vẽ công khai. Lượt đã ghi nhận dựng được tấm rời của ghế; không phải sản phẩm lắp ráp hoàn chỉnh. Các mẫu thiếu bằng chứng bị chặn.
- [Backend cục bộ](docs/PRIVATE_BACKEND.md): bearer auth, phân quyền, hàng đợi SQLite, Blender và tải kết quả riêng tư. Chưa công khai API; AI tự động và kết nối nhận ảnh từ Pages vẫn **CHƯA KẾT NỐI**.
- [TEST 31](docs/TEST31_RESULTS_VI.md): nhận yêu cầu mẫu, tiến độ thật, phiên bản và xử lý lỗi qua Actions. Artifacts có thời hạn, không phải storage bền vững.
- [TEST 30](docs/TEST30_ASSEMBLY_VI.md): **CẦN XÁC NHẬN**. Chưa chứng minh lắp ráp đúng kỹ thuật; không tự nâng trạng thái.

[Báo cáo nghiệm thu TEST 33](docs/TEST33_ACCEPTANCE_VI.md): 84/84 kiểm thử lõi và 19/19 viewer đạt, Qwen/OCR chạy thật nhưng chỉ có tấm rời. Kết luận tổng thể **CHƯA ĐẠT** điều kiện sử dụng thực tế. Kết quả kiểm thử mã không thay thế nghiệm thu AI, hình học, cấu tạo hay bảo mật vận hành.

## Phát triển và kiểm thử

Chỉ làm việc trong repository này. Tuân thủ yêu cầu người dùng về quyền GitHub; không đưa ảnh/bản vẽ khách hàng lên repository hoặc workflow công khai. Dữ liệu backend nằm trong `.private/`, không commit.

```sh
python -m unittest discover -s tests -v
python scripts/hg3d.py check examples/living_room.json
blender -b -t 2 --python-exit-code 1 --python scripts/blender_build.py -- examples/living_room.json outputs/new-public-demo
blender -b -t 2 --python-exit-code 1 --python scripts/verify_blender.py -- examples/living_room.json outputs/new-public-demo
```

Thư mục đầu ra Blender phải mới/trống. Các bài tích hợp cần Blender, Tesseract, Pillow, NumPy/OpenCV, FastAPI/httpx, Playwright và Chromium; xem các file `requirements*.txt`, `viewer/requirements-test.txt` và workflow TEST 33. Thiếu công cụ phải ghi rõ skip/fail, không coi kiểm thử chưa chạy là đạt.

```sh
npm ci --prefix viewer --ignore-scripts --no-audit --no-fund
npm run build --prefix viewer
python scripts/serve_pages_preview.py --port 8792
# Trong terminal khác:
HG_VIEWER_URL=http://127.0.0.1:8792/HG-3D-CLOUD-AI/ python -m unittest discover -s viewer/tests -v
```

Backend riêng: [hướng dẫn API](docs/PRIVATE_BACKEND.md), [giao diện loopback và giới hạn cloud miễn phí](docs/LOCAL_UI_AND_FREE_CLOUD.md). Mã local không được đóng gói vào Pages. Không đặt token vào JavaScript công khai.

## Dữ liệu dựng hình và nghiệm thu

JSON dùng mm, Blender dùng m; trục X ngang, Y sâu, Z cao. Từng thuộc tính có `confirmed`, `inferred` hoặc `needs_confirmation` kèm chứng cứ. [Schema](docs/SCENE_SCHEMA.md), [nhập ảnh](docs/IMAGE_PIPELINE.md), [cổng QA](docs/QA_ACCEPTANCE.md), [tích hợp Qwen/OCR](docs/QWEN_OCR_BLENDER_INTEGRATION.md).

Replay/fixture chỉ kiểm thử phần mềm, không phải chứng cứ AI nhận diện thành công. Box/envelope và đồ nội thất tham số không phải mô hình sản xuất; không tự tạo lỗ khoan, liên kết hay chi tiết khuất. BLEND giữ scene chỉnh sửa; GLB không bảo đảm giữ layer/collection Blender, đèn Area, hoặc mọi thông số vật liệu/camera. Cần kiểm tra từng định dạng thực tế.

Một ảnh không xác định đầy đủ chiều sâu, vật liệu, mặt khuất hoặc cấu tạo. Layout 2D không tự xác nhận chiều cao. Không tuyên bố độ giống 100%, nghiệm thu cuối hoặc sử dụng sản xuất khi còn thiếu dữ liệu.

GitHub Pages chỉ phục vụ mẫu tĩnh công khai. Actions miễn phí được dùng trong phạm vi runner tiêu chuẩn và repository công khai; không phải máy chủ 24/7. Không nâng gói, dùng GPU/runner trả phí hoặc công bố dữ liệu riêng. Nguồn OpenDesk/AtFAB phải giữ ghi công và giấy phép; dữ liệu BY-NC không được tự coi là thư viện thương mại.
