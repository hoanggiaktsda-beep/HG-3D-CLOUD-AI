# Kiểm định từng tấm từ bản vẽ raster

`hgcloud/raster_profile.py` tách đường bao đen khép kín, lỗ kín và ký hiệu khoan đỏ trong vùng ảnh do người kiểm tra chọn. Không đọc DXF hay mô hình có sẵn. Không hiểu mọi bản vẽ; ảnh có đường hở, chồng nét hoặc nhiều bộ phận trong ROI cần người kiểm tra lại.

Ký hiệu khoan đỏ chỉ cung cấp vị trí trên tấm. Kích thước ký hiệu không được dùng làm đường kính khoan. Diameter chưa biết → CẦN XÁC NHẬN, lưu empty marker và extras trong BLEND/GLB; chưa cắt lỗ vật lý. Các đường cong/relief biểu diễn bởi contour pixel, không suy ra bán kính dao chính xác từ dấu đỏ hoặc góc bo. Không tự bevel với bán kính không có chứng cứ.

`scripts/blender_profile_build.py` dựng bản thử AtFAB gồm bốn tấm bên và mặt ghế từ evidence JSON. Đây là builder thử nghiệm cho cấu trúc này, không phải bộ lắp ráp nội thất tổng quát. Chiều rộng/chiều cao/độ dày có số đo từ ảnh; vị trí lắp, contour, tai và lỗ vuông là suy luận theo ảnh. Giữ nhãn NEEDS_REVIEW. Ghi công AtFAB / Filson and Rohrbacher, CC BY-NC-SA 3.0 đối với chuyển thể thử nghiệm này.

Lệnh từ root repository (output mới):

```sh
python3 outputs/detail-upgrade/extract.py
blender -b -t 2 --python-exit-code 1 --python scripts/blender_profile_build.py -- outputs/detail-upgrade/profile_evidence.json outputs/detail-upgrade/NEW-BUILD
python3 -m unittest discover -s tests -v
```

Evidence thử nghiệm tại outputs là kết quả cục bộ, chưa nằm trong checkout Git trên máy mới. Muốn dùng builder ở máy mới cần ảnh nguồn có quyền sử dụng và evidence theo schema của script. Không đưa ảnh riêng tư hoặc output vào Git mặc định.

Kiểm tra trên từng mesh: local bbox ba trục, thickness, ma trận vị trí/hướng, manifold edges, mặt suy biến, thể tích, lỗ trung tâm bằng ray cast. So bbox world từng đối tượng sau import GLB; giữ markers UNKNOWN trong GLB. Tolerance 0.1 mm là kiểm tra giữ dữ liệu qua build/export, không phải độ chính xác đọc ảnh (ảnh có sai số lượng tử khoảng một pixel, tương ứng vài mm).

Kiểm thử chống tái phát dùng fixture hình học tổng hợp để kiểm tra thuật toán, không chứng minh AI đọc ảnh thật. Có cố ý đưa panel về tâm và bỏ Boolean lỗ trung tâm; cả hai phải bị chặn trước khi lưu BLEND. Kiểm tra không đổi ký hiệu đỏ thành đường kính lỗ; đường hở bị từ chối; contour giữ các khoét và phần mỏng.

Viewport là chụp cửa sổ Blender SOLID bằng X11, không gọi render.render hoặc render.opengl. Đối chiếu mặt bằng, đứng, cạnh bằng projection bounds từng object, ảnh viewport và ảnh bản vẽ. Tài liệu nguồn không có các hình chiếu đã lắp chuẩn hóa/camera chuẩn, nên chưa báo PASS độ giống hay IoU độc lập. Chưa đo interference/clearance hoặc xác nhận dùng sản xuất; không tự phê duyệt bản dựng.
