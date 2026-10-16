# TEST 33 — nghiệm thu tổng thể HG 3D CLOUD AI

Ngày đánh giá: **16/10/2026 (Asia/Saigon)**. Báo cáo đánh giá chức năng, không tự nghiệm thu thiết kế hoặc điều kiện sản xuất.

**Kết luận tổng thể: CHƯA ĐẠT điều kiện sử dụng thực tế như hệ thống tự nhận ảnh → dựng sản phẩm 3D hoàn chỉnh.** Các thành phần có khả năng chạy thật nhưng còn thiếu kết nối website–AI–Worker riêng, lắp ráp theo bằng chứng, bảo mật vận hành và thiết bị thật. TEST 30 giữ **CẦN XÁC NHẬN**.

## Phạm vi và phương pháp

Rà soát mã, tài liệu, lịch sử Git và kiểm thử chức năng được xây dựng tới TEST 32. Repository không có sổ nghiệm thu riêng đánh số đủ TEST 01–29; không tự gán số hoặc xác nhận các bài thử không có hồ sơ. Đánh giá theo từng năng lực thực tế, có liên kết nguồn cũ và lượt kiểm chứng TEST 33.

| Yêu cầu Director | Quyết định |
|---|---|
| Giữ nguyên | 18 trách nhiệm chuyên gia, viewer đã triển khai, TEST 30 CẦN XÁC NHẬN |
| Được thay đổi | Sửa lỗi có ca tái hiện, kiểm thử, workflow nghiệm thu và tài liệu |
| Kích thước chắc chắn | Số đo mẫu do tác giả quy định; số đọc OCR ghi riêng với nguồn và điều kiện |
| Chưa chắc chắn | Pose lắp ráp, lỗ khoan, liên kết khuất, bán kính dao, độ giống vật liệu/ánh sáng/ảnh |
| Cần thêm dữ liệu | Hình chiếu–bộ phận được gán đúng, dịch vụ riêng có xác thực, kiểm thử thiết bị thật |

**ĐẠT** chỉ áp dụng phạm vi ghi trong dòng tương ứng. **ĐẠT MỘT PHẦN** nghĩa là có bằng chứng một số bước/mẫu nhưng chưa đáp ứng toàn yêu cầu. **CHƯA ĐẠT** nghĩa là thiếu chức năng hoặc chưa có bằng chứng đạt. Không dùng số bài test xanh để nâng trạng thái hệ thống.

## Kiểm chứng TEST 33

**Cục bộ: 84/84 kiểm thử lõi đạt**, không skip, 86,876 giây; **19/19 kiểm thử viewer đạt**, 50,258 giây. Kiểm thử lõi bao gồm backend auth/ownership, browser loopback, Blender thật, hồi quy sofa/giường, cổng AI/OCR, giới hạn workflow và ca lỗi. Sau sửa kiểm kê vật liệu, kiểm thử Blender tương ứng tiếp tục đạt. Fixture/replay chỉ là bằng chứng phần mềm.

Lượt đầu [38840384459](https://github.com/hoanggiaktsda-beep/HG-3D-CLOUD-AI/actions/runs/38840384459), commit `d099d06`: kiểm thử lõi và OCR/Blender đạt, bước inventory lỗi nên các job tiếp theo không chạy. Đã tái hiện lỗi inventory tính cả datablock vật liệu không gán lên mesh và sửa phạm vi kiểm tra, thêm ca hồi quy giữ nguyên kiểm tra PBR cho các bề mặt thực. Không che lượt thất bại hoặc coi job bị bỏ qua là đạt.

Lượt cuối [38840914648](https://github.com/hoanggiaktsda-beep/HG-3D-CLOUD-AI/actions/runs/38840914648), commit `7f19a81`, **Success**, tổng **9 phút 23 giây**:

| Job trên runner GitHub | Kết quả thực |
|---|---|
| core-and-ocr | Success, 2 phút 31 giây; 84/84 test, không skip; OCR → BLEND/GLB và inventory Blender 4.0.2 |
| live-vision | Success, 6 phút 47 giây; Qwen thật + OCR độc lập, cổng chứng cứ, Blender và QA |
| viewer-and-live-pages | Success, 1 phút 43 giây; 19 test viewer và kiểm tra HTTPS website đã triển khai |

Website [HG 3D CLOUD AI](https://hoanggiaktsda-beep.github.io/HG-3D-CLOUD-AI/) được kiểm từ runner: checksum 21 tài nguyên, tải GLB/BLEND thật và so bytes, camera, upload vẫn khóa, reload ngoại tuyến. Đây là website thật, không chỉ localhost. Truy cập trực tiếp tên miền Pages từ Codex bị proxy 403; yêu cầu thử nâng quyền bị hủy, không dùng đường vòng. Website giữ nguyên bản TEST 32, không triển khai lại giao diện trong TEST 33.

Đã đọc trạng thái từng bước, annotations giá trị thật và digest Artifacts trên trang GitHub công khai. **Chưa tải Artifacts cloud về Codex để mở thủ công**; việc mở BLEND/nhập GLB trong cloud là verifier thực thi và điều kiện pipeline, kiểm tra cục bộ cũng dùng Blender thật. [Bản ghi annotations và checksum](test33-evidence/cloud-public-notices.json) lưu nguồn đọc; không dùng dữ liệu soạn sẵn làm suy luận mới.

Workflow mới: `.github/workflows/test33-acceptance.yml`, chỉ repository HG công khai, runner `ubuntu-24.04` tiêu chuẩn, quyền `contents: read`, timeout 15/20/10 phút, Artifacts một ngày, không nhận ảnh/URL/command tùy ý, không upload `.private` hoặc model cache.

### Lỗi được tái hiện và sửa

1. **Giường sai chiều sâu:** mẫu 2000 × 2200 × 900 mm có mesh sâu 2210,999966 mm do đầu giường vượt khối bao. Đưa mép sau đầu giường về giới hạn thiết kế; hồi quy dựng, mở BLEND và nhập GLB kiểm tra giường cùng sofa/armchair xoay. Sofa 950 mm được giữ đúng.
2. **Camera/đèn nhận giá trị sai:** schema trước sửa chấp nhận lens 0, âm, NaN/Infinity và đường kính đèn 0/âm/NaN/Infinity. Nay lens hữu hạn 1–5000 mm, đường kính đèn hữu hạn dương; có kiểm thử từ chối trước Blender.
3. **GLB hỏng vẫn được backend cho tải:** ca âm chạy export Blender thật rồi cố ý làm hỏng GLB vẫn ra NEEDS_REVIEW trước sửa. Worker nay mở BLEND và nhập lại GLB, so hình học hai chiều bằng verifier hiện có trước khi công bố. Ca hỏng chuyển FAILED và API chặn download; ca hợp lệ vẫn chạy thật. Đây là tiêm lỗi kiểm thử, không dùng AI hay kết quả dựng giả.
4. **Kiểm thử UI backend không tương thích CSP:** lệnh chờ cũ dùng eval bị CSP chặn. Đổi sang predicate hàm; giữ nguyên CSP, không bật unsafe-eval. Chọn Chromium hệ thống nếu có, nếu không dùng binary Playwright đã cài.
5. **Tài liệu trạng thái cũ:** README và hướng dẫn viewer/kết nối được cập nhật để phân biệt backend loopback đã có với backend website chưa nối; Pages/PWA/BLEND mẫu đã phát hành. Không sửa AGENTS.md hoặc danh sách 18 vai trò.

### Kiểm tra scene thật, không render

Dựng lại `examples/living_room.json`, mở BLEND và nhập GLB bằng Blender 4.3.2. Inventory: **20 mesh**, **6 vật liệu có Principled BSDF**, mesh kín có thể tích dương, có UV layer và collection. Kiểm tra đèn Area **320 W**, kích thước **1700,000048 mm** và camera **35 mm** hướng tới target (dot hướng **0,99999998**). Đây là scene tham số công khai, không phải nhận diện ảnh.

GLB nhập lại có **20 mesh và 1 camera**, nhưng **không có đèn Area hoặc collection Blender** trong mẫu này. Lens camera nhập lại là 41,481476 mm; glTF dùng FOV/quy ước sensor nên không coi số lens khác là kết luận camera sai, nhưng chưa xác minh khớp góc ảnh gốc. World có sẵn trong BLEND, không có môi trường/HDRI từ ảnh được xác nhận. Không render để đánh giá thẩm mỹ; không gọi vật liệu PBR cơ bản là tái dựng đúng sản phẩm.

### Ảnh công khai → OCR → Blender

Chạy mới `scripts/cloud_worker_sample.py` tại Codex. Nguồn AtFAB Rotational Stools từ OpenDesk, SHA-256 PDF `e7ab9a6da6e9d5639cbf99f9b69f5b522f5782ee1730be0836b765f2623fed65`, CC BY-NC-SA 3.0, AtFAB / Filson and Rohrbacher 2013; chỉ thử phi thương mại. PDF được raster thành PNG; nhận diện không đọc vector/CAD/JSON kích thước có sẵn.

Tesseract đọc 241,3 × 241,3 × 381 mm, dày danh nghĩa 18,5 mm. Mesh đo thực **241,300046 × 241,300017 × 380,999982 mm**; sai lệch số học lớn nhất **0,00004645 mm**. Năm mesh được kiểm độ dày/vị trí/manifold/thể tích/lỗ giữa; mở lại BLEND và nhập lại GLB thật. 16 ký hiệu khoan giữ marker, không tạo đường kính khoan chưa biết.

Đây là **OCR + contour với ROI chọn có giám sát và bố trí suy luận**, không phải AI tự hiểu ảnh. Sai số mesh nhỏ chỉ chứng minh dựng theo số đọc; không chứng minh ảnh gốc hoặc cấu tạo chính xác tới mức đó. Không dùng kết quả này để tự nghiệm thu hoặc nâng TEST 30.


### Qwen + OCR → Blender trên ba bản vẽ công khai

Lượt TEST 33 mới dùng Qwen2-VL-2B revision `895c3a49bc3fa70a340399125c650a463535e71c`, CPU int8, trọng số safetensors, không API trả phí/khóa API. Script `public_assembly_trial.py` đưa PNG/crop vào model trước, rồi mới chạy OCR độc lập; không truyền đáp án, CAD hay JSON hình học gốc. ROI/trang được chọn có giám sát; đây là đánh giá lại ba mẫu đã biết của dự án, không phải benchmark mù mới.

| Nguồn công khai | Kết quả mới |
|---|---|
| zerozero Desk, CC BY 4.0 | BLOCKED_NEEDS_CONFIRMATION, thiếu cut_context, không có BLEND/GLB |
| AtFAB Five To Thirty Minute Chair, CC BY-NC-SA 3.0 | BUILT_UNASSEMBLED_PARTS_NEEDS_REVIEW, BLEND/GLB chứa 20 tấm rời |
| AtFAB One To Several Table, CC BY-NC-SA 3.0 | BLOCKED_NEEDS_CONFIRMATION, thiếu material evidence, không có BLEND/GLB |

Ghế: AI/OCR đối chứng cỡ tấm 1219,2 × 2438,4 mm, chiều dày danh nghĩa 18,5 mm, tổng 20 tấm và chú giải màu. OpenCV trích contour sau cổng này; Blender dựng 20 mesh và hai đường cắt trong. BLEND mở lại và GLB nhập lại **PASS**. IoU chiếu về sơ đồ cắt nhỏ nhất **0,9978925343**; sai số mesh so JSON lớn nhất **0,000120147 mm**; bất định nguồn hai pixel khoảng **1,521622 mm**, chưa gồm sai lệch in/scan. IoU sơ đồ cắt không là độ giống sản phẩm đã lắp.

Có **64 marker khoan** nhưng bảng ghi **54 lỗ**; không tạo lỗ vật lý, không tự giải mâu thuẫn. Tên cấu kiện, pose lắp, bán kính dao và đường kính lỗ vẫn CẦN XÁC NHẬN. `front_side_comparison=NOT_PROVIDED` chỉ nói lượt thử này chưa đưa hình chiếu vào pipeline; PDF có hình chiếu/số đo ở trang 3 như TEST 30 đã đính chính. **0/3 mẫu có sản phẩm lắp ráp được nghiệm thu.** Không suy ra tỷ lệ nhận diện tổng quát từ ba ca.

Artifacts lưu một ngày trong run:

- `test33-core-public-38840914648-1`: **2,17 MB**, SHA-256 `364000cc9b21e5a60973e4ec46c8df60ebaa689fed74d4c00daad93a42f87454`; gồm summary test, mẫu OCR/BLEND/GLB và inventory.
- `test33-live-vision-public-38840914648-1`: **16,9 MB**, SHA-256 `baaeb22f3626906b7333c61dbd8e7ded3ef78c408bd52deaad0cd7ac36fdf01f`. Kết quả ghế tại `chair/build/cut_layout.blend`, `cut_layout.glb`, `part_qa.json`; kèm nguồn công khai và phản hồi Qwen/OCR thật. Không chứa trọng số hoặc dữ liệu khách hàng.

## Ma trận chức năng

| Chức năng | Phân loại | Bằng chứng và giới hạn |
|---|---|---|
| Nhận ảnh và kiểm tra định dạng/dung lượng | ĐẠT | PNG/JPEG/WebP, kiểm signature/giải mã và giới hạn; HEIC chưa hỗ trợ |
| OCR số đo từ bản vẽ | ĐẠT MỘT PHẦN | Tesseract thật; cần ROI/chọn trang, đối chiếu nhãn và đơn vị |
| Qwen2-VL-2B đọc ảnh | ĐẠT MỘT PHẦN | Có lượt suy luận thật; chưa tự gán đầy đủ số đo–vật thể–pose |
| Phối cảnh/ảnh sản phẩm → 3D metric đầy đủ | CHƯA ĐẠT | Chưa có benchmark đạt trên ảnh sản phẩm/nội thất thực đa dạng |
| Layout → kiến trúc đầy đủ | CHƯA ĐẠT | Chưa tự xác định tường, cửa, trần và cao độ đủ chứng cứ |
| Đối chiếu AI/OCR và chặn dữ liệu mâu thuẫn | ĐẠT | Cổng bằng chứng và ca âm; không tự lấy OCR thay AI để báo thành công |
| JSON và phân biệt confirmed/inferred/needs_confirmation | ĐẠT | Nguồn, hash, từng trục; đề xuất model không tự xác nhận |
| Tự hợp nhất mặt bằng/đứng/cạnh | CHƯA ĐẠT | Chưa suy ra pose từng cấu kiện đã kiểm chứng |
| Blender tham số và envelope | ĐẠT MỘT PHẦN | Dựng thật, giữ khối bao; không phải tái dựng chi tiết sản phẩm |
| Contour tấm, chi tiết mỏng, đường cắt trong | ĐẠT MỘT PHẦN | Mẫu công khai; tỷ lệ pixel/ROI có giám sát, chưa tổng quát |
| Lỗ chốt, khoan, liên kết và bán kính gia công | CHƯA ĐẠT | Thiếu số đo giữ CẦN XÁC NHẬN; marker không phải lỗ vật lý |
| Sản phẩm lắp ráp đúng kỹ thuật | CHƯA ĐẠT | TEST 30 chưa giải được pose/quan hệ đủ bằng chứng |
| Đo kích thước/vị trí từng mesh | ĐẠT | Đo Blender thật, so nguồn JSON; không đồng nghĩa JSON đúng bản vẽ |
| Va chạm, khe hở, độ dày lắp ráp | ĐẠT MỘT PHẦN | Có bộ kiểm tra và ca tổng hợp, chưa đủ pose ghế thật để nghiệm thu |
| Vật liệu, PBR và UV | ĐẠT MỘT PHẦN | Có slot/giá trị cơ bản; chưa kiểm chất lượng UV/texture hoặc giống sản phẩm |
| Ánh sáng | ĐẠT MỘT PHẦN | BLEND giữ đèn/giá trị; GLB mẫu mất đèn Area; chưa đối chiếu ảnh |
| Môi trường/bối cảnh từ ảnh | CHƯA ĐẠT | World mặc định không phải môi trường được tái dựng |
| Camera và góc nhìn | ĐẠT MỘT PHẦN | Pose/lens BLEND, camera viewer có thật; chưa khớp camera ảnh nguồn |
| Layer/collection | ĐẠT MỘT PHẦN | Có collection BLEND; không bảo toàn collection Blender trong GLB |
| Lưu và mở lại BLEND/GLB | ĐẠT | Kiểm kỹ thuật trên mẫu; backend nay nhập lại GLB trước tải |
| Dựng độc lập trên GitHub-hosted Actions | ĐẠT | Runner cloud chạy Blender; không cần Blender ở máy cá nhân, không phải server 24/7 |
| Nhận việc/tiến độ/phiên bản/lỗi | ĐẠT MỘT PHẦN | TEST 31 batch công khai và backend loopback; chưa quản lý việc riêng qua website |
| Backend auth và phân quyền file | ĐẠT MỘT PHẦN | Loopback kiểm 401/404/ownership/Host/Origin/quota; chưa nghiệm thu bảo mật Internet |
| Lưu trữ riêng bền vững và API Internet | CHƯA ĐẠT | Chưa triển khai; chưa TLS/rotation/rate limit/backup/retention vận hành được nghiệm thu |
| Website xem mẫu, xoay/zoom/QA | ĐẠT | Chromium thật, giả lập màn hình/cảm ứng; website chỉ mẫu công khai |
| PWA ngoại tuyến | ĐẠT MỘT PHẦN | Cache allowlist mẫu, reload ngoại tuyến; cài thực trên iOS/macOS chưa kiểm chứng |
| iPhone/iPad/Windows/macOS thật | CHƯA ĐẠT | Chỉ Chromium Linux giả lập, không Safari/thiết bị thật |
| Tải GLB/BLEND/báo cáo | ĐẠT | GLB/BLEND download thực và so bytes; QA JSON đọc qua HTTP, chưa thử lưu vào Tệp iOS |
| Ảnh khách hàng không lên Pages/Actions | ĐẠT | Build allowlist, upload website khóa, workflow mới không nhận ảnh tùy ý; phạm vi mã thử nghiệm |
| Website → AI → Worker → kết quả riêng | CHƯA ĐẠT | CHƯA KẾT NỐI, không dùng job/progress/model giả |
| Giới hạn miễn phí | ĐẠT MỘT PHẦN | Runner tiêu chuẩn public, không dịch vụ trả phí; chưa truy cập billing/quota tài khoản thực |
| 18 vai trò và báo cáo có giám sát | ĐẠT | Giữ danh sách 18, không giả vờ 18 model chạy; không tự nghiệm thu |

## Rà soát theo 18 trách nhiệm chuyên gia

| Trách nhiệm | Kết luận kiểm tra |
|---|---|
| Director | Không phê duyệt tổng thể; lập ma trận và phân biệt bằng chứng |
| Kiến trúc sư trưởng | Layout/cao độ chưa đủ để dựng kiến trúc hoàn chỉnh |
| Kiến trúc sư nội thất | Chưa chứng minh giữ đúng sản phẩm từ ảnh đa dạng |
| Họa viên 3D | Mesh/BLEND/GLB chạy thật; sửa đầu giường vượt khối bao |
| Chuyên gia hình học | Kiểm kích thước, topology và round-trip; không đồng nhất bbox với hình dáng |
| Kỹ sư cấu tạo | Lắp ráp, lỗ/chốt và khe hở chưa nghiệm thu; TEST 30 giữ nguyên |
| Chuyên gia đo lường | Tách sai số dựng theo JSON với sai số ảnh/OCR và dung sai gia công |
| Chuyên gia giải mã bản vẽ | Chưa tự hợp nhất số đo và ba hình chiếu thành pose |
| Chuyên gia thị giác tái dựng | Chỉ công nhận suy luận thật có provenance; replay không là chứng cứ AI |
| Chuyên gia đa ảnh | Chưa có thử nghiệm đạt hợp nhất nhiều ảnh sản phẩm |
| Chuyên gia vật liệu | PBR cơ bản có thật; nhận diện vật liệu/UV/texture chưa đạt đầy đủ |
| Chuyên gia ánh sáng | Kiểm scene, không render; đèn Area không được giữ trong GLB mẫu |
| Chuyên gia môi trường | World mặc định chưa xác nhận từ ảnh |
| Chuyên gia camera | Kiểm hướng/lens BLEND và điều khiển viewer; camera ảnh chưa khớp |
| Chuyên gia thư viện tài sản | Chỉ nguồn công khai có hash/giấy phép, AtFAB giữ BY-NC-SA |
| Chuyên gia tự động hóa | Chạy Actions có timeout, quyền đọc, artifact giới hạn; không API riêng công khai |
| Chuyên gia kiểm định hình học | Chặn GLB hỏng, không phát hành kết quả chỉ vì export flag báo có file |
| Chuyên gia nghiệm thu từ xa | Chưa đủ thiết bị thật, bảo mật và chuỗi tự động để công bố sử dụng thực tế |

Đây là 18 trách nhiệm rà soát, không phải tuyên bố 18 mô hình hoặc 18 nhân sự độc lập đã thực thi.

## Giới hạn GitHub Free và bảo vệ dữ liệu

Đọc tài liệu chính thức GitHub ngày 16/10/2026 từ repository `github/docs`:

- [Actions billing](https://github.com/github/docs/blob/main/content/billing/concepts/product-billing/github-actions.md): public repository dùng standard GitHub-hosted runner miễn phí; private có quota và phần vượt có thể tính phí. Larger runner không thuộc giả định miễn phí.
- [Actions limits](https://github.com/github/docs/blob/main/content/actions/reference/limits.md): job GitHub-hosted tối đa 6 giờ; workflow HG chủ động giới hạn thấp hơn. Không xem runner tạm thời là API/queue/storage 24/7.
- [Over quota](https://github.com/github/docs/blob/main/data/reusables/billing/default-over-quota-behavior.md): không có payment method hợp lệ thì chặn vượt quota; có payment method phải kiểm budget. Không truy cập dashboard billing nên không chứng nhận số dư/hóa đơn toàn tài khoản.
- [Pages limits](https://github.com/github/docs/blob/main/content/pages/getting-started-with-github-pages/github-pages-limits.md): site tối đa 1 GB, bandwidth mềm 100 GB/tháng; Pages không phải hosting SaaS thương mại. Gói viewer hiện khoảng 2,8 MB trên đĩa, chỉ demo công khai.

Không bật billing, không đăng ký dịch vụ, không dùng GPU/runner trả phí, không lịch chạy lặp. Không công khai backend hoặc dữ liệu khách hàng. Model weights chỉ ở thư mục tạm, không artifact. Artifacts hết hạn sau một ngày, không dùng làm kho model bền vững. Không thay đổi repository khác và không render.

## Điều kiện còn thiếu trước khi dùng thực tế

1. Đạt bài thử độc lập đủ đa dạng cho AI/OCR, gán đúng đối tượng–hình chiếu–số đo và pose; không chỉ đọc được chữ.
2. Đủ dữ liệu lắp ráp và QA va chạm/khe hở/chi tiết cấu tạo cho sản phẩm thật; giải quyết TEST 30 có bằng chứng.
3. Có backend/storage riêng trên cloud với TLS, auth/ownership, vòng đời token, rate limit, quota, log an toàn, backup và kiểm tra bảo mật thực tế; chưa tự triển khai trong TEST 33.
4. Nối website với dịch vụ đó và thử end-to-end dữ liệu được phép; hiện vẫn CHƯA KẾT NỐI.
5. Kiểm thiết bị thật/Safari, cài PWA, lưu file trên iOS và hiệu năng mô hình lớn.

Không chuyển kết quả kiểm thử mã xanh thành thông báo hệ thống đã hoàn thiện.
