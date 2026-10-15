# HG 3D CLOUD WORKER — mẫu công khai, không render

Workflow: `.github/workflows/cloud-worker.yml`. Chạy thủ công tại GitHub → Actions →
HG 3D CLOUD WORKER → Run workflow, hoặc tự chạy khi mã worker được push vào main.
Chỉ dùng runner Linux CPU tiêu chuẩn của repository công khai; không đăng ký dịch vụ,
không GPU trả phí, không lịch chạy nền. Giới hạn 10 phút, một công việc đồng thời,
artifact tự hết hạn sau 1 ngày. GitHub Actions tiêu chuẩn cho repository công khai
không tính phút sử dụng; cần kiểm tra lại chính sách GitHub nếu đổi repository/runner.

Đầu vào duy nhất được tải là PDF AtFAB Rotational Stools công khai từ OpenDesk,
khóa SHA-256 trong `scripts/cloud_worker_sample.py`; nội dung đổi thì dừng.
PDF chỉ raster bằng Poppler; nhận diện đọc PNG bằng Tesseract và trích biên dạng pixel
ở các vùng ảnh chọn có giám sát. Không đọc DXF, vector PDF hoặc JSON kích thước có sẵn.
Kích thước được đọc OCR trước, kiểm định lại sau; không có số đo dự phòng khi OCR lỗi.
Đây **không phải AI thị giác tự hiểu ảnh**; trạng thái AI vẫn CHƯA KẾT NỐI.

Ghi công: AtFAB / Filson and Rohrbacher, 2013, nguồn OpenDesk design-playground.
Tuân thủ CC BY-NC-SA 3.0 ghi trong trang 6 PDF (giữ điều kiện chặt hơn giấy phép
BY-NC 4.0 ở thư mục nguồn). Bản dựng phái sinh dùng CC BY-NC-SA 3.0, phi thương mại.
Artifact kèm PDF gốc, PNG nguồn trang 3/4/6, chứng cứ OCR và JSON biên dạng từ ảnh.

Artifact `hg-public-blender-RUN_ID-ATTEMPT` chứa:

- `model/detailed_draft.blend`, `model/detailed_draft.glb` dựng thật trong Blender.
- `model/object_qa.json`: đo từng đối tượng, topology, vị trí, lỗ giữa, nhập lại GLB.
- `model/blend_reopen_qa.json`: mở lại BLEND và đo mesh độc lập.
- `REPORT_VI.md`: sai lệch, nguồn, cách nhận diện và các chi tiết CẦN XÁC NHẬN.
- `manifest.json`: kích thước file và SHA-256; log Blender, OCR và nguồn công khai.

PASS kỹ thuật không phải nghiệm thu thiết kế. Độ chính xác dựng theo kích thước
danh nghĩa <0,1 mm không có nghĩa biên dạng ảnh chính xác dưới mm. Khe lắp, đường kính
khoan, bán kính dao/thoát dao chưa xác nhận. 16 ký hiệu khoan chỉ là marker.

Chạy lại cục bộ khi đã có Blender, Tesseract, Poppler và Pillow:

Với Blender gói Ubuntu 24.04, cần thêm `python3-numpy` cho addon xuất GLB.
Không bỏ qua lỗi thiếu NumPy: BLEND lưu được chưa chứng minh GLB xuất thành công.

```bash
python3 -m unittest discover -s tests -p test_cloud_worker.py -v
python3 scripts/cloud_worker_sample.py --output outputs/public-worker-new-run
```

Thư mục đầu ra phải chưa tồn tại. Workflow chỉ upload thư mục mới dành riêng cho mẫu
công khai dưới runner.temp, không upload toàn bộ checkout, outputs hoặc .private.
Không nhận URL/file khách hàng, không khóa API, quyền GITHUB_TOKEN chỉ contents:read,
không public API, không cập nhật Pages và không thay đổi bộ não 18 vai trò.
Đây là worker batch thử nghiệm, chưa là backend nhận ảnh riêng tư từ website.
