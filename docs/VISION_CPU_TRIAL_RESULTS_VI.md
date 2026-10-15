# Kết quả thử AI thị giác CPU thật — 15/10/2026

**Chưa đạt tự dựng 3D từ ảnh.** Đã chạy mô hình thật, không dùng replay/fixture
để chứng minh nhận diện. Việc workflow hoàn tất không phải nghiệm thu chất lượng AI.

## Mã và mô hình

- Workflow: `.github/workflows/vision-cpu-trial.yml`.
- Suy luận: `hgcloud/local_vision.py`; thử công khai: `scripts/public_vision_trial.py`.
- CLI offline: `scripts/local_vision.py`.
- SmolVLM-256M-Instruct: commit `7e3e67edbbed1bf9888184d9df282b700a323964`,
  513.028.808 byte trọng số, Apache-2.0.
- DETR ResNet-50: commit đã thực thi `1d5f47bd3bdd2c4bbfa585418ffe6da5028b4c0b`,
  166.587.896 byte trọng số, Apache-2.0.
- Không API key, GPU, render, dịch vụ đăng ký hay API trả phí. Mô hình chạy CPU trên
  runner GitHub công khai tiêu chuẩn, giới hạn 20 phút, tuần tự, artifact giữ 1 ngày.
- Giữ nguyên Director + 17 chuyên gia. Đây là 18 trách nhiệm kiểm tra, không giả vờ
  18 mô hình độc lập đã thực thi.

## Bằng chứng và lỗi được sửa

Lượt đầu: https://github.com/hoanggiaktsda-beep/HG-3D-CLOUD-AI/actions/runs/38677430759

5 ảnh được suy luận thật, thời gian toàn run 7 phút 21 giây. SmolVLM có mô tả sai
hoặc không có chứng cứ (ví dụ đoán vật liệu kim loại trên hình nét). Ba phản hồi chép
cấu trúc hộp mẫu nhưng kích thước đều null; hai phản hồi không đúng JSON. Các phản hồi
rỗng không chứng minh nhận diện hình học. Đã bỏ ví dụ hộp trong prompt và thêm kiểm
thử buộc loại phản hồi không có chứng cứ metric, không coi JSON đúng cú pháp là đạt.

Lượt có DETR: https://github.com/hoanggiaktsda-beep/HG-3D-CLOUD-AI/actions/runs/38678385266

GitHub Success, 6 phút; cả hai mô hình thật được tải và chạy. Artifact
`hg-public-vision-38678385266-1`, 6,59 MB, SHA-256:
`310718894d859e77bd9c2467f8ba6403c53b0c5172342bb2c0324ec44e032e4d`.

| Đầu vào công khai | Vùng DETR trên ngưỡng 0,7 | JSON metric dùng được | Dựng tự động |
|---|---:|---:|---|
| Phối cảnh nét AtFAB, cắt bỏ nhãn | 0 | 0 | Chặn |
| Bản vẽ kích thước AtFAB | 0 | 0 | Chặn |
| Ảnh gia đình trong phòng, Fonds Trutat, public domain | 7 ứng viên | 0 | Chặn |
| Ảnh trong category Chairs, CC BY-SA 4.0 | 0 | 0 | Chặn |
| Bản vẽ nhà Harris Homes 1920, public domain | 0 | 0 | Chặn |

7 vùng là dự đoán gồm người, ghế, giường và điện thoại; **không phải 7 vật thể đã
xác nhận đúng**. Ảnh category Chairs chưa được tuyển chọn và xác nhận đại diện cho
ảnh sản phẩm nội thất điển hình. Bộ thử này chưa đủ để công bố độ chính xác trên
ảnh nội thất hiện đại, ảnh sản phẩm hoặc layout khách hàng.

Đã kiểm tra trạng thái từng bước, annotation do runner tạo, tên/kích thước/digest
artifact thực trên GitHub. Không tuyên bố đã tải artifact về Codex: API log/download
bị môi trường chặn. Người dùng đăng nhập GitHub để tải nguồn, JSON và báo cáo đầy đủ.

## Chức năng đã hoạt động

- Tải và kiểm tra giấy phép mô hình công khai, resolve commit trước tải, ghi SHA-256,
  chỉ dùng safetensors, không thực thi mã tùy ý từ repository mô hình.
- Nhận PNG/JPEG bốn loại đầu vào theo intake cũ, kiểm tra nguồn bằng SHA-256.
- Suy luận VLM thật, lưu nguyên caption/phản hồi với trạng thái chưa xác minh.
- Suy luận detector thật, xuất `image_geometry.json` với bbox pixel, nhãn/điểm ứng viên;
  không biến pixel thành mm. Tâm/kích thước 3D còn null và scene_ready=false.
- Kiểm tra schema, giá trị hữu hạn/dương, bbox trong ảnh, id và cổng duyệt độc lập.
- Đối chiếu số đo với OCR sau suy luận; không truyền reference vào model.
  Khi không có dự đoán hợp lệ, ghi NOT_COMPARABLE, không ghi sai số bằng 0.
- Giữ số đo/vị trí AI ở needs_confirmation; không chuyển chi tiết khuất trong caption
  sang hình học. Cổng compile_scene/Blender chặn dữ liệu chưa được duyệt.
- 56/56 kiểm thử Python cục bộ đạt, không skip, bao gồm hồi quy UI/backend/Blender
  hiện có và 7 kiểm thử cổng thị giác. Các JSON fixture trong test chỉ kiểm tra hợp đồng,
  không là chứng cứ nhận diện ảnh.

Lượt kiểm tra cuối của bộ nhỏ, commit `7e4dfba`:
https://github.com/hoanggiaktsda-beep/HG-3D-CLOUD-AI/actions/runs/38678665542

GitHub Success; 7 phút 13 giây thực thi job (9 phút 59 giây gồm xếp hàng).
Đã kiểm tra cả 5 JSON ứng viên đều có source_sha256 đúng định dạng và vẫn chặn dựng;
kết quả 0/0/7/0/0 vùng DETR như bảng trên. Artifact `hg-public-vision-38678665542-1`,
6,59 MB, SHA-256:
`db4045e915af2976c27226fb4c7d1ebff82de1ea7050f6b6c8fe8bdcf97683b3`.

## Còn thiếu

Chưa có đề xuất hình học metric đạt yêu cầu trên bộ 5 ảnh của các mô hình nhỏ. Không có BLEND/GLB mới sinh
từ AI trong bài thử này, và không dùng bản dựng cũ để thay thế. Blender Cloud Worker
đã hoạt động ở giai đoạn trước vẫn cần scene/observations được kiểm chứng độc lập.

Chưa tự gắn kích thước vào đúng vật thể/hình chiếu; chưa xác định chiều sâu từ ảnh
đơn; chưa tách tường/phòng của layout, tách cấu kiện, tái dựng mặt cong, bo/thoát dao
hoặc cấu tạo khuất. Chưa có benchmark tuyển chọn và gán nhãn đủ tốt để đo độ đúng.
SmolVLM nhỏ hiện chưa đủ năng lực tuân thủ schema hình học này. DETR là detector ảnh
thông thường, không phải bộ đọc CAD/layout hoặc bộ dựng mô hình 3D.

Chưa nối AI vào API/website. Giao diện hiện có giữ nguyên; không công khai backend,
không gửi dữ liệu khách hàng tới workflow hoặc repository công khai.

## Thử mô hình 2B trong cùng giới hạn miễn phí

Workflow bổ sung: `.github/workflows/vision-large-cpu-trial.yml`.
Mô hình Qwen/Qwen2-VL-2B-Instruct, Apache-2.0, commit
`895c3a49bc3fa70a340399125c650a463535e71c`, 4.418.050.768 byte safetensors.
Lượng tử hóa động int8 phần Linear ngôn ngữ, encoder ảnh/embedding float32; CPU bốn
luồng, giới hạn 20 phút. Không GPU/API. Trọng số không nằm trong artifact/repository.

Lượt đầu: https://github.com/hoanggiaktsda-beep/HG-3D-CLOUD-AI/actions/runs/38679485435

GitHub Success, 4 phút 10 giây. Cả trang đầy đủ và crop chữ được chọn có giám sát
đều đọc được câu “15 inch tall × 9.5 inch square” qua phản hồi thực của mô hình.
Đây là hai ảnh của **cùng một bản vẽ**, không phải hai ca thiết kế độc lập.
Mô hình chưa tuân thủ schema JSON; không dựng 3D từ phản hồi đó. Artifact
`hg-public-large-vision-38679485435-1`, 2,27 MB, SHA-256:
`3b5f3e3cb001c3b7f86512622f7e2e8d3f0947de4d6262daf00161431fcf8f9e`.

Đã thêm parser có kiểm soát cho chính văn bản model đọc, không điền từ OCR/gold JSON,
không dùng lại phản hồi cũ làm bằng chứng cho lượt suy luận mới. Các số đo vẫn là
ứng viên needs_confirmation, không có gán đối tượng/tâm 3D/bbox số đo được nghiệm thu.
Toàn bộ 60/60 kiểm thử Python cục bộ đạt; bốn kiểm thử mới xác minh đổi đơn vị, số đọc
mâu thuẫn/thiếu, không tự bù chiều sâu và không tự duyệt kể cả khi khớp OCR.

### Kết quả cuối đã kiểm chứng, commit e056723

https://github.com/hoanggiaktsda-beep/HG-3D-CLOUD-AI/actions/runs/38680149403

GitHub Success, 4 phút 36 giây; thực thi job 4 phút 33 giây. Bước kiểm thử 11 ca
cổng hình học/parser, suy luận thật và upload artifact đều thành công.

| Ảnh đưa vào AI | JSON số đo ứng viên x/y/z (mm) | Sai lệch số đọc so với OCR độc lập | Được dựng? |
|---|---|---|---|
| Trang bản vẽ đầy đủ | 241,3 / 241,3 / 381 | 0 / 0 / 0 mm | Không, cần xác nhận |
| Crop chữ được chọn có giám sát | 241,3 / 241,3 / 381 | 0 / 0 / 0 mm | Không, cần xác nhận |

**AI trả văn bản; parser chuyển văn bản đó thành JSON. AI chưa tự trả đúng schema
hình học.** Chiều sâu lấy từ quan hệ “square” trong câu model đọc được, không tự
lấy chiều sâu từ ảnh phối cảnh. Mọi giá trị vẫn needs_confirmation.
Không cấp OCR tham chiếu, đáp án hoặc JSON kích thước gốc cho model; so sánh chỉ
thực hiện sau suy luận và sau bước trích candidates.

Sai lệch 0 ở đây chỉ là **hai nguồn đọc số khớp nhau**, không phải sai số Blender,
độ giống 3D hoặc xác nhận gán số đo vào đúng vật thể. Chưa có bbox chính xác của nhãn,
object_assignment còn CẦN XÁC NHẬN, center_mm=null, scene_ready=false và build_allowed=false.
Không sinh BLEND/GLB, không tự nghiệm thu. Chưa chứng minh tổng quát hóa sang bản vẽ khác.

Artifact: `hg-public-large-vision-38680149403-1`, 2,27 MB, lưu 1 ngày; SHA-256:
`fe647a8688bb501e519c3747d25a69fd6fb78abf9765fcde440614bc583fc510`.
Trong `full-drawing/` và `dimension-crop/` có:

- `dimension_candidates.json`: câu AI đã đọc, mã băm ảnh, đơn vị và ứng viên theo trục.
- `analysis.json`: phản hồi model gốc, provenance thật, kết quả đối chiếu và lý do chặn.
- `intake.json`, ảnh nguồn và `reference-ocr.txt` để kiểm tra lại.

Root artifact có `model_provenance.json`, PDF/PNG công khai, `experiment.json` và
`REPORT_VI.md`. Không chứa trọng số hoặc dữ liệu khách hàng. Đã kiểm tra trên trang run
trạng thái thật, số đo trong annotation, artifact và digest; giới hạn download từ Codex
như phần bằng chứng phía trên vẫn giữ nguyên.

## Hướng miễn phí phù hợp

Dùng OCR và bbox như đề xuất để người kiểm tra đối chiếu nguồn rồi mới chuyển sang
compiler và worker Blender thật. Tuyển chọn ảnh/bản vẽ công khai có giấy phép, số đo
rõ và nhãn kiểm định trước khi mở rộng đánh giá các mô hình CPU với giới hạn thời gian.
Không bật dựng tự động chỉ vì model lớn hơn hoặc JSON hợp lệ; phải chứng minh độ đúng
trên bài thử độc lập. Chưa đề xuất mở dịch vụ có phí hoặc đưa dữ liệu riêng tư vào Actions.
