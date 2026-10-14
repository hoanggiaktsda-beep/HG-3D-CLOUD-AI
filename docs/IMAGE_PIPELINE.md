# Nhập ảnh có chứng cứ — phiên bản cục bộ

## Phạm vi thật

Đã có nhận ảnh PNG/JPEG qua Pillow, sao chép nguồn vào job mới, SHA-256, OCR Tesseract với vùng chữ và độ tin cậy. Bốn loại đầu vào: `technical_drawing`, `layout`, `product_photo`, `interior_photo`. OCR chỉ đọc các dòng nhãn rõ `WIDTH/DEPTH/HEIGHT <số> mm|cm|m`; không phải parser dimension chain, OCR tiếng Việt, nắn phối cảnh hoặc nhận dạng CAD.

Không có model thị giác tự động hay API trả phí được kết nối. Codex/người dùng xem ảnh và cung cấp observations theo `tests/fixtures/cabinet_observations.json`. Không được gán kết quả OCR là confirmed chỉ vì confidence cao. Từng trục phải có nguồn, trạng thái; drawing confirmed cần người kiểm tra và bbox vùng số đo. `verified_by` là khai báo người kiểm tra, không phải chữ ký hay tự động chứng minh số đo đúng.

Đối với ảnh sản phẩm/phối cảnh, nhận file và lưu chứng cứ hoạt động; phân đoạn, tái dựng hình học, vật liệu và cấu tạo tự động chưa hoạt động. Không lấy pixel làm mm. Layout thiếu chiều cao sẽ bị chặn. Người kiểm tra có thể nhập từng phần nhìn thấy như một object riêng; hiện chỉ xuất envelope hộp quan sát, không tự dựng cửa/bản lề/mặt sau. Ghi phần khuất vào `unknown_details`. Không khẳng định envelope là sản phẩm hoàn chỉnh.

## Chạy

Cần Python, Pillow, Tesseract (`tesseract` trên PATH), Blender có glTF addon. Môi trường hiện tại đã có các công cụ này; dependency Python được khai báo trong requirements-image.txt. Không gọi dịch vụ mạng.

Từ root HG-3D-CLOUD-AI, dùng các đường dẫn output mới:

```sh
python3 scripts/image_to_scene.py receive tests/fixtures/dimensioned_cabinet.png technical_drawing outputs/image-job-NEW
# Xem ảnh + intake.json; lập observations có chứng cứ, không tự xác nhận OCR.
python3 scripts/image_to_scene.py compile outputs/image-job-NEW/intake.json tests/fixtures/cabinet_observations.json outputs/image-job-NEW/scene.json
blender -b -t 2 --python-exit-code 1 --python scripts/blender_build.py -- outputs/image-job-NEW/scene.json outputs/image-job-NEW/build
blender -b -t 2 --python-exit-code 1 --python scripts/verify_blender.py -- outputs/image-job-NEW/scene.json outputs/image-job-NEW/build
python3 -m unittest discover -s tests -v
```

Verifier mở lại BLEND, đo evaluated mesh vertices, world transform rồi chuyển về trục thiết kế nếu object xoay. Báo cáo JSON/HTML chứa kích thước mong đợi/thực tế, sai lệch kích thước và tâm, tolerance mặc định 1 mm, chứng cứ theo trục và chi tiết chưa biết. Sai lệch vượt tolerance trả mã lỗi và `QA_FAILED`. `PASS` chỉ là khớp specification, không xác nhận giống ảnh hay nghiệm thu. GLB export lỗi phải xem `glb_error`, builder có thể vẫn exit 0.

## Bằng chứng kiểm thử

`tests/fixtures/dimensioned_cabinet.png` là bản vẽ tổng hợp tự tạo để kiểm tra, không phải bản vẽ thực của khách hàng. Số đo 1800 × 450 × 900 mm được đọc bởi OCR, sau đó Codex xem ảnh kiểm tra trước khi tạo observations. Dựng BLEND/GLB tại outputs/image-pipeline-trial/build; không render.

Kiểm thử tự động bao gồm OCR thật, kích thước thiếu, OCR chưa xác nhận, nguồn bị thay đổi, giá trị vô hạn/âm, suy luận không được nâng mức, BLEND đo thật và cố ý đổi specification 10 mm để chứng minh QA phát hiện sai lệch. Test phụ thuộc công cụ sẽ báo skipped nếu công cụ thiếu; không coi skipped là pass.

## Bước tiếp theo

Cần ảnh/bản vẽ thực có quyền sử dụng để đánh giá font, độ nghiêng, chuỗi kích thước và ảnh nhiều góc. Model thị giác tự động cần chọn backend và được cấp phép sử dụng; không yêu cầu gửi API key trong chat. Khi có backend phải kiểm tra schema, độ bất định, gắn số đo vào đúng đối tượng và đối chiếu nguồn độc lập trước build. Chưa có xử lý mặt cong, openings, kết cấu khuất, OCR tổng quát hoặc native .max.

## Giao diện mô hình thị giác và pipeline replay

`hgcloud/vision.py` định nghĩa hợp đồng provider `analyze(request)`, prompt phân tích ảnh, payload ảnh base64 tương thích cấu trúc Chat Completions và JSON observations. `prepare-request` chỉ ghi yêu cầu ra file, không gửi ảnh đi. Không gọi mạng, không chi phí. `ExternalVisionProvider` hiện chặn mọi lời gọi: chưa có backend, khóa API hay chính sách chi phí được cấp quyền. Tính tương thích endpoint/model thật chưa được kiểm chứng.

```sh
python3 scripts/vision_pipeline.py run tests/fixtures/dimensioned_cabinet.png technical_drawing outputs/vision-job-NEW --response-file tests/fixtures/vision_response.json
python3 scripts/vision_pipeline.py prepare-request outputs/vision-job-NEW/intake.json outputs/vision-request-NEW.json --model YOUR_AUTHORIZED_MODEL
```

Replay chỉ đọc phản hồi fixture đã viết trước, **không nhận diện ảnh bằng AI thật**. File `pipeline.json` ghi `offline_replay`, `live_model_executed:false`, trạng thái từng giai đoạn và lỗi BLOCKED/FAILED. Fixture kích thước chỉ được đánh dấu inferred. Output luôn BUILT_NEEDS_REVIEW, không tự phê duyệt. Input AI tự khai confirmed bị hạ xuống needs_confirmation; khai user_measurement bị chặn để người kiểm tra nhập lại từ nguồn độc lập. Thiếu chiều cao/độ sâu chặn build, không tự điền.

Danh sách Director + 17 chuyên gia trong provenance giữ đủ 18 vai trò của AGENTS.md; đây là trách nhiệm rà soát, không giả vờ đã chạy 18 tác nhân AI. AGENTS.md giữ nguyên. Khi kết nối provider thật cần cấp quyền backend và chính sách chi phí, triển khai transport có giới hạn timeout/response, kiểm chứng schema và ảnh thật; không chỉ bật một cờ để tuyên bố AI đã chạy.

Mọi ảnh gửi backend về sau phải được cấp quyền sử dụng; request chuẩn bị chứa ảnh và OCR, không chứa khóa API. Không commit request/ảnh khách hàng hoặc cache/generated outputs mặc định. Ảnh fixture trong tests là ảnh tổng hợp dùng riêng cho kiểm thử.
