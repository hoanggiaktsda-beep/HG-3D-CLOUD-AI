# Thử nghiệm ảnh thật trực tiếp trong Codex

## Khả năng hiện có

Codex có thể xem ảnh đính kèm trong chat và ảnh trên máy qua view_image. Đây là phân tích tương tác bởi trợ lý Codex, không phải một model/API thị giác chạy độc lập trong Python. Máy hiện có Pillow, Tesseract và Blender; chưa có model thị giác cục bộ hoặc backend API được cấu hình. Không gọi API trả phí, không tải model hay triển khai website trong chế độ này.

Chưa có ảnh thật của người dùng trong lần chuẩn bị này. Các kiểm thử fixture/replay chỉ xác minh phần mềm; không chứng minh nhận diện ảnh thật thành công.

## Quy trình

1. Người dùng gửi ảnh trực tiếp trong Codex. Ưu tiên bản vẽ có số đo rõ và đơn vị; thêm mặt đứng/cạnh nếu có. Với ảnh sản phẩm, cung cấp kích thước đã đo và nhiều góc. Không yêu cầu gửi khóa API.
2. Codex lưu ảnh đã cung cấp vào inputs với tên mới, không ghi đè. Đối với file Sediment dùng download_file, sau đó sao chép vào repository; ảnh đã có workspace_path thì đọc file sẵn. Mọi kết quả của dự án nằm trong HG-3D-CLOUD-AI.
3. Codex xem ảnh thật qua khả năng thị giác của phiên chat. Đọc số đo, vị trí, phần nhìn thấy; lập bảng giữ nguyên/được thay đổi/số đo chắc chắn/chưa chắc/yêu cầu thêm dữ liệu. Giữ Director + 17 vai trò của AGENTS.md. Không coi OCR hay replay là bằng chứng đã hiểu ảnh.
4. Chạy receive vào output mới để lưu ảnh nguồn, hash và OCR khi thích hợp. Viết observations JSON theo cấu trúc tests/fixtures/cabinet_observations.json, nhưng nội dung phải lấy từ ảnh thật vừa xem, không sao chép số đo fixture. Từng trục ghi source_note, confidence và bbox_px vùng số đo. confirmed từ bản vẽ cần verified_by ghi người/trợ lý thực sự xem vùng đó. Số đo do người dùng trực tiếp cung cấp dùng basis user_measurement. Không tự dùng nhãn này cho số do model suy ra.
5. Ghi chi tiết khuất vào unknown_details. Mặt bằng không có chiều cao thì bỏ trục z hoặc để null; compiler sẽ chặn build. Khi không có thước/đơn vị/số đo, không chuyển pixel thành mm. Chỉ build kích thước inferred nếu đã ghi rõ cơ sở suy luận; unresolved vẫn chặn.
6. Compile scene rồi build bằng Blender và chạy verifier. Với hình học chưa đủ dữ liệu, hiện chỉ dựng observed_envelope dạng hộp. Không giả vờ hộp là sofa/tủ chi tiết. Các phần nhìn thấy có thể tách thành nhiều object; hình cong, tường có ô cửa và cấu tạo nâng cao chưa tự tái dựng.
7. Báo cáo đúng số đo mesh, sai số, chi tiết chưa biết và giới hạn đối chiếu ảnh. Đầu ra BLEND/GLB vẫn là DRAFT/NEEDS_REVIEW; không tự nghiệm thu. Không render.

## Lệnh dùng sau khi đã nhận ảnh thật

Từ /workspace/HG-3D-CLOUD-AI; thay IMAGE, JOB và OBSERVATIONS bằng đường dẫn thật mới tạo:

```sh
python3 scripts/image_to_scene.py receive IMAGE technical_drawing JOB
# Codex xem ảnh thật rồi viết OBSERVATIONS; không chạy ReplayProvider.
python3 scripts/image_to_scene.py compile JOB/intake.json OBSERVATIONS JOB/scene.json
blender -b -t 2 --python-exit-code 1 --python scripts/blender_build.py -- JOB/scene.json JOB/build
blender -b -t 2 --python-exit-code 1 --python scripts/verify_blender.py -- JOB/scene.json JOB/build
```

Chọn input_type phù hợp: technical_drawing, layout, product_photo hoặc interior_photo. Compiler phải có nguồn ảnh khớp SHA-256. Cần kiểm tra glb_created và glb_error trong qa_report.json vì builder có thể bắt lỗi export và vẫn exit 0. Kết quả gồm hg_scene.blend, hg_scene.glb, qa_report.json và qa_report.html.

Không dùng scripts/vision_pipeline.py run --response-file trong thử nghiệm nhận diện ảnh thật: đó là replay fixture. Không commit ảnh riêng tư, request chứa ảnh hay file output tự động.

## Phương án không dùng API trả phí

Ưu tiên khả năng xem ảnh sẵn có trong Codex để thử có giám sát; không thêm lời gọi dịch vụ ngoài. Tesseract miễn phí hỗ trợ số đo nhưng không hiểu hình học. Nếu cần tự động chạy ngoài phiên Codex, phải chọn model thị giác mã nguồn mở có license phù hợp và kiểm tra CPU/GPU/RAM, độ chính xác, tải model và nguồn checksum trước; hiện chưa cài hay kiểm chứng phương án đó. Không tuyên bố bản thân model miễn phí đồng nghĩa hạ tầng vận hành không có chi phí.
