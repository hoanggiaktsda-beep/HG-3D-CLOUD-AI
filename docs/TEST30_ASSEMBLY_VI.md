# TEST 30 — lắp ráp dựa trên bằng chứng

**CHƯA ĐẠT mục tiêu mô hình ghế lắp ráp hoàn chỉnh. Chưa chuyển TEST 31.**
Đã bổ sung và kiểm thử bộ giải/worker, nhưng tài liệu hiện có chưa xác minh
được ánh xạ contour sang cấu kiện, tọa độ, hướng/góc lắp và khe lắp. Không tự
bịa các giá trị này để tạo một ghế có vẻ hoàn chỉnh.

**Đính chính kiểm tra nguồn:** lượt đầu ở commit `c5aa1bb` chỉ xét trang 4–7
và kết luận thiếu hình chiếu quá sớm. **Trang 3 có mặt bằng, đứng/trước/sau,
mặt cạnh và kích thước.** Bản sửa kiểm tra đủ 7 trang, OCR riêng nhãn xoay và
ghi nhận các hình chiếu có sẵn. Lỗi chương trình chưa hợp nhất/đăng ký được
hình chiếu không được báo thành lỗi thiếu bản vẽ của người dùng.

## Kết quả tại Codex

**73/73 kiểm thử đạt, không bỏ qua kiểm thử.** Bảy kiểm thử mới bao gồm:
giải chuyển động cứng từ điểm đối ứng; chặn điểm thẳng hàng, đổi tỷ lệ/phản
chiếu; chặn sai ảnh, thiếu/mâu thuẫn hình chiếu; không coi thứ tự lắp là tọa
độ; Blender thật bắt giao khối nằm lọt; khoảng cách 5 mm trên fixture; xoay
tấm 90° và kiểm lại chiều dày/hướng sau xuất. Fixture tổng hợp chỉ kiểm tra
thuật toán/worker, không chứng minh nhận diện hoặc lắp ghế từ ảnh thành công.
Kiểm thử chống tái phát bắt việc bỏ trang tài liệu, và không biến khoảng kích
thước OCR thành một giá trị cố định tùy ý.

Hai nguồn PDF công khai được kiểm tra trực tiếp bằng ảnh và OCR thật:

| Nguồn | Dữ liệu có | Kết quả |
|---|---|---|
| AtFAB Five To Thirty Minute Chair — nguồn đã dùng ở lượt trước | Đủ 7 trang; mặt bằng/đứng/cạnh ở trang 3; sơ đồ cắt, nhãn A–F, bảng số lượng, hướng dẫn lắp | 20 tấm được xuất; chưa đăng ký/ánh xạ được pose từng tấm đủ kiểm chứng |
| Jose Pacheco Slim Chair — nguồn độc lập mới cho TEST 30 | Hai trang hình tháo lắp | Không có kích thước/chiều dày xác minh; không tạo mesh tùy ý |

Nguồn Slim Chair: [PDF](https://raw.githubusercontent.com/opendesk/design-playground/gh-pages/OD-55134-Slim-Chair-1.1.0/OD-55134-Assembly-Guide.pdf),
SHA-256 `9930aaaac970f386fb516d48f0a190b069ef65c4fd36b091765d4d38800f54b0`.
LICENSE nguồn CC BY 4.0; thử nghiệm phi thương mại và tôn trọng watermark PDF.
Nguồn AtFAB và giấy phép: [bộ bằng chứng](test30-evidence/README.md).

TEST 30 dùng OCR/CV thật và kiểm tra ảnh có hỗ trợ Codex; **không chạy một lượt
Qwen mới, không mô phỏng phản hồi Qwen**. Lượt Qwen thật trước đó đã ghi tại
[báo cáo cũ](ASSEMBLY_VISION_TRIAL_RESULTS_VI.md). Chưa tự động suy ra vị trí
lắp từ ảnh phối cảnh hoặc hình tháo lắp.

OCR đọc bảng A Seat Back ×1, B Seat ×1, C Sides ×2, D Front Legs ×1,
E Back Legs ×1, F Feet ×4. Đọc được “Slot part B into part D”, “Fit side parts
C, then part E”, “Add parts A & F”. Đây là quan hệ/thứ tự phi số đo; các vị
trí và hướng vẫn null. Không coi tổng số chi tiết đúng là ánh xạ từng contour
đúng. Không dùng gợi ý chế tạo chung về chốt để tự tạo đường kính/chiều sâu
khoan cho chiếc ghế này.

OCR nhãn trang 3 sau xoay crop 270° đọc chiều sâu **50 cm → 500 mm**, cao tổng
**79,3 cm → 793 mm**, cao mặt ngồi ghi **48,6 cm → 486 mm**. Nhãn rộng là
**50–180 cm → khoảng 500–1800 mm**, không phải một chiều rộng cố định. Đây là
số đo nguồn để đối chiếu, chưa phải sai số một ghế đã lắp. Chưa xác định bản
biến thể chiều rộng nào tương ứng chính xác từng contour trong sơ đồ cắt.

## Kiểm định thực tế và file đã lưu

Mẫu AtFAB có 20 mesh kín, chiều dày danh nghĩa 18,5 mm, hai đường cắt trong.
Sai số nội bộ lớn nhất kích thước/vị trí so JSON khoảng **0,000132 mm**;
độ phân giải hai pixel nguồn khoảng **1,522 mm**, chưa gồm sai lệch nét/in/scan.
IoU đường bao nhỏ nhất khoảng **0,997893**. Kích thước từng tấm suy ra tỷ lệ
ảnh, chưa có nhãn kích thước độc lập từng tấm để chứng minh dung sai gia công.

Kiểm tra **190 cặp trong sơ đồ cắt**, không phát hiện giao khối. Đây **không
phải** kiểm tra 190 cặp trong ghế lắp ráp. Khoảng cách được báo bằng khoảng
cận dưới AABB/cận trên khoảng cách đỉnh–mặt; cực tiểu cạnh–cạnh có thể nhỏ
hơn cận trên. Không ghi một khoảng cách xấp xỉ thành khe hở chính xác hoặc
khe đạt thiết kế. Chưa có khe thiết kế để đối chiếu. Giao khối dùng Boolean
EXACT, ngưỡng nhiễu số 0,01 mm³, bắt được trường hợp khối nằm trong khối mà
chỉ kiểm giao mặt có thể bỏ sót.

Mở lại BLEND và nhập lại GLB: PASS. Ngoài bbox, so khoảng cách hai chiều của
tập đỉnh world-space để bắt thay đổi hình học có thể giữ nguyên bbox.
Đã chụp và xem trực tiếp bốn góc GUI trên
X11, không dùng render hoặc OpenGL render. Góc trước/cạnh cho thấy cạnh của
tấm nằm phẳng; không được gọi là mặt đứng/cạnh ghế đã lắp hoặc coi đã đối
chiếu hình học từng tấm với hình chiếu nguồn ở trang 3.

[Tải BLEND/GLB, ảnh viewport và JSON kiểm định đã lưu](test30-evidence/README.md).
Marker khoan giữ trong nguồn dựng và dữ liệu contour; bản review bỏ các
annotation không phải mesh để không tự gán chúng vào cấu kiện lắp. Không
cắt lỗ vật lý hoặc thêm phụ kiện. OCR bảng 54 lỗ và 64 ký hiệu quan sát còn
mâu thuẫn; không tự sửa số để nghiệm thu.

## Cổng lắp ráp và giới hạn tích hợp

`hgcloud/assembly_constraints.py`: mỗi tấm cần ánh xạ nhãn đã kiểm tra, ít nhất
ba điểm đối ứng 3D không thẳng hàng và annotation metric mặt bằng/đứng/cạnh.
Giải phép quay/tịnh tiến, không tự đổi tỷ lệ. So bbox chiếu với annotation ba
mặt. Thiếu/mâu thuẫn nguồn, đổi SHA ảnh, trộn tài liệu khác hoặc tọa độ không
nhất quán thì chặn.

**Annotation đã duyệt là đầu vào tin cậy của CLI**, không phải bằng chứng tự
thân rằng con người đã duyệt. Hiện chưa có kênh API xác thực cho review này;
không đưa nó lên backend/website hoặc tin cờ `confirmed` do client công khai
gửi. Việc so annotation kiểm tra tính nhất quán, chưa tự kiểm lại mọi con số
annotation bằng OCR. Bộ thử công khai không tạo annotation dương giả để vượt
cổng. Chưa có bộ giải mộng/slot tự ánh xạ từ ảnh thành các điểm đối ứng.

`scripts/blender_assembly_review.py`: chỉ áp dụng pose đủ chứng cứ; giữ tấm
chưa có pose ở vị trí sơ đồ cắt và ghi UNPLACED. Không kiểm va chạm giữa hai
nhóm tọa độ khác nhau. Đo mesh/vị trí/hướng, giao khối/khoảng cách, mở lại BLEND
và GLB; luôn giữ `final_approved=false`, `next_test_allowed=false`.

## Giữ 18 trách nhiệm chuyên gia

Không thay đổi `ROLES`, không tuyên bố đã chạy 18 model độc lập hoặc có 18
người phê duyệt. Director tổng hợp bằng chứng, xác định không đủ điều kiện
nghiệm thu. Các trách nhiệm được áp dụng trong TEST 30 như sau:

| Vai trò | Kiểm tra/giới hạn |
|---|---|
| Director | Bảng giữ nguyên/được thay đổi/số đo chắc/chưa chắc/thiếu dữ liệu; chặn TEST 31 |
| Kiến trúc sư trưởng | Chưa xác minh hình dáng/công năng ghế sau lắp |
| Kiến trúc sư nội thất | Nhãn seat/back/legs từ bảng, chưa gán contour |
| Họa viên 3D | Chỉ dựng tấm có contour và tỷ lệ; không dịch tùy ý |
| Hình học | Phép chuyển động cứng, mesh kín, không đổi tỷ lệ |
| Cấu tạo | Chưa xác minh mộng, khoan và khe lắp |
| Đo lường | Phân biệt nhãn mm danh nghĩa, tỷ lệ raster và sai số tính toán |
| Giải mã bản vẽ | Kiểm đủ trang, phát hiện hình chiếu trang 3 và OCR nhãn xoay |
| Thị giác tái dựng | Kiểm ảnh có giám sát; chưa có pose AI tự động |
| Đa ảnh | Hình chiếu đã có; chương trình chưa hợp nhất được thành pose từng cấu kiện |
| Vật liệu | Không tự gán thương hiệu hoặc đoán độ dày thực |
| Ánh sáng | Không render |
| Môi trường | Không tạo bối cảnh ngoài bằng chứng |
| Camera | Bốn góc viewport GUI thật, không thay cho ảnh nguồn |
| Thư viện tài sản | Nguồn công khai, SHA và ghi công/giấy phép |
| Tự động hóa | CLI/worker/Actions, không mở API công khai |
| Kiểm định hình học | Từng mesh, pose, giao khối và khoảng cách có giới hạn |
| Nghiệm thu từ xa | Giữ CẦN XÁC NHẬN, không tự APPROVED |

## Chạy lại miễn phí

Dùng checkout hiện tại của HG-3D-CLOUD-AI, không tạo worktree hoặc sửa repository
khác. Trong môi trường đã có Blender, Tesseract, Poppler và ImageMagick:

```sh
python -m pip install -r requirements-test30.txt
python -m unittest discover -s tests -v
python scripts/test30_public_trial.py --output outputs/test30-new-job
# Khi có Xvfb/xauth và cần chụp GUI:
xvfb-run -a -s '-screen 0 1440x1000x24 -nolisten tcp' python scripts/test30_public_trial.py --output outputs/test30-new-gui-job --capture-viewport
```

Mỗi lần cần output mới; không ghi đè file nguồn. Workflow
`.github/workflows/test30-assembly-review.yml` chỉ chạy trên đúng repository
công khai, nguồn cố định có SHA, runner Ubuntu tiêu chuẩn, timeout 15 phút,
quyền contents:read, không dùng secret/API trả phí; chỉ upload thư mục thử
công khai trong runner.temp, giữ artifact một ngày. Không publish website,
không render, không đưa bản vẽ khách hàng lên GitHub/Actions.

Trước TEST 31 cần hoàn thiện/kiểm tra: hợp nhất các hình chiếu đã có và đọc ràng buộc
lắp; ánh xạ mỗi tấm với nhãn/phiên bản/số lượng/biến thể chiều rộng; tọa độ và hướng lắp;
thông số khe hở, liên kết và lỗ có chứng cứ. Nếu chưa có, TEST 30 tiếp tục
ở trạng thái **CẦN XÁC NHẬN**, không gọi là đã hoàn thành lắp ráp.

## Xác nhận GitHub Actions sau đính chính

[Run 38698809411](https://github.com/hoanggiaktsda-beep/HG-3D-CLOUD-AI/actions/runs/38698809411),
commit `66c217a`: **Success**, 1 phút 32 giây. Bảy kiểm thử mới, bước đọc toàn
bộ PDF/Blender/chụp GUI và upload artifact đều hoàn tất thành công. Toàn bộ
73 kiểm thử chạy ở Codex; workflow chỉ chạy bảy kiểm thử TEST 30 cùng thử
nghiệm công khai, không tuyên bố chạy đủ 73 trên Actions.

Annotations thực tế ghi: đọc trang 1–7, phát hiện mặt bằng/đứng/cạnh ở trang 3,
OCR giữ đúng khoảng rộng; 20 mesh, **0 pose được phép lắp**, 190 cặp chỉ trong
sơ đồ cắt. Trạng thái **BLOCKED_COMPLETE_ASSEMBLY**, không phải PASS lắp ráp.
Slim Chair độc lập vẫn bị chặn vì nguồn không có kích thước xác minh.

Artifact `hg-test30-public-38698809411-1`, 10.3 MB, SHA-256
`0547ffaf2396612e4b0c2d48daea7bdc417d6dd10e7c7ae5e32e033e8d0d4f0e`,
giữ một ngày. Đã xác minh trạng thái, từng bước và annotations công khai;
chưa tải artifact cloud về Codex. Các BLEND/GLB/viewport lưu trực tiếp trong
repository là bằng chứng của lần chạy cục bộ đã kiểm tra, không giả là file
tải từ Actions. Hai lần chạy dùng cùng nguồn PDF có SHA được khóa.
