# AI thị giác cục bộ bằng CPU — thử nghiệm, chưa nghiệm thu

Mô hình ứng viên: HuggingFaceTB/SmolVLM-256M-Instruct, Apache-2.0, không cần API key.
Chạy Transformers/PyTorch CPU, safetensors, `trust_remote_code=False`, tải theo commit
đã resolve và ghi revision/hash trọng số vào báo cáo. Không gửi ảnh tới API AI.
Không dùng replay làm chứng cứ nhận diện. Không đổi 18 vai trò; một mô hình thực thi,
18 trách nhiệm rà soát vẫn giữ nguyên, không giả vờ có 18 AI đã chạy.

Workflow `.github/workflows/vision-cpu-trial.yml` dùng runner CPU tiêu chuẩn của repo
công khai, tối đa 20 phút, một công việc đồng thời, artifact giữ 1 ngày. Không lịch
chạy, GPU, dịch vụ đăng ký hay API trả phí. Không upload trọng số/cache. Chỉ dùng
nguồn mẫu công khai do script cố định chọn; không có input file/URL tùy ý từ khách.
Nếu đổi repo riêng tư/runner cần đánh giá lại giới hạn miễn phí của GitHub.

`scripts/public_vision_trial.py` tải PDF AtFAB đã khóa checksum, lấy phối cảnh không
chứa nhãn và bản vẽ kích thước. Phối cảnh này là hình nét, không gọi là ảnh chụp.
Script thử thêm ảnh nội thất, sản phẩm và layout từ Wikimedia Commons với giấy phép
cho phép sử dụng rõ ràng; nguồn/giấy phép/tác giả được ghi `public_sources.json`.
Nguồn không tải được ghi SOURCE_UNAVAILABLE, không thay bằng fixture để tuyên bố đạt.
Vùng ảnh phối cảnh được chọn có giám sát; mô hình tự sinh mô tả/JSON từ pixel,
không được cấp sẵn tên vật thể hoặc số đo OCR trong prompt. OCR lưu riêng để đối chiếu.

Luồng:

1. Nhận PNG/JPEG, loại ảnh, SHA-256 và OCR ứng viên theo intake hiện có.
2. Mô hình thật đọc ảnh, sinh mô tả và đề xuất JSON; lưu nguyên phản hồi, token và thời gian.
3. Kiểm tra schema, hữu hạn/dương, đủ ba trục hoặc null, bbox trong ảnh và id không trùng.
4. Tất cả kích thước/vị trí AI tự đề xuất thành needs_confirmation. Không tự gán confirmed,
   không tạo kích thước từ pixel nếu không có tỷ lệ, không tự dựng phần khuất.
5. JSON hợp lệ là ANALYZED_NEEDS_REVIEW; JSON sai là BLOCKED_INVALID_GEOMETRY.
   Cả hai đều không cho dựng tự động. Người kiểm tra phải đối chiếu với ảnh gốc,
   sửa observations và ghi bằng chứng trước khi dùng compile_scene/Blender Worker.
6. Chỉ sau bước duyệt độc lập mới xuất BLEND/GLB và kiểm định bằng worker đã có.
   Chưa nối chế độ này vào API/website; trạng thái backend thị giác cũ vẫn chưa kết nối.

Phân biệt: workflow thực thi thành công không có nghĩa AI đọc đúng hoặc mô hình 3D giống
ảnh. Caption sai, thiếu số đo, JSON bị cắt hoặc không đúng schema phải được báo nguyên trạng.
Không tạo GLB dự phòng từ số liệu cũ để chứng minh model thị giác mới thành công.

Cục bộ, với trọng số đã tải và dependencies CPU:

```bash
python scripts/image_to_scene.py receive path/to/authorized.png product_photo outputs/new-intake
python scripts/local_vision.py outputs/new-intake/intake.json path/to/model-snapshot path/to/model_provenance.json outputs/new-analysis.json
python -m unittest discover -s tests -p test_local_vision.py -v
```

CLI suy luận chỉ đọc trọng số cục bộ, không tải lên đâu. Không sử dụng CLI này trong
workflow công khai để phân tích dữ liệu riêng tư. Bài test dùng JSON cố định chỉ kiểm tra
cổng an toàn, không là bằng chứng nhận diện. Hiệu quả ảnh phối cảnh, layout phức tạp,
chi tiết sản xuất, liên kết khuất và tái dựng metric chính xác chưa được mặc định xác nhận.
