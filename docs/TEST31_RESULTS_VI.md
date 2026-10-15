# TEST 31 — kết quả chạy thực tế

**Đạt phạm vi thử nghiệm vận hành công việc mẫu công khai.** Không phải backend
nhận ảnh khách hàng, không phải chứng minh AI dựng ảnh hoặc lắp ráp thành công.
TEST 30 giữ **CẦN XÁC NHẬN** và không được chạy lại trong bài thử này.

## Kiểm chứng cục bộ

**7/7 kiểm thử TEST 31 đạt**, không bỏ qua kiểm thử. Chạy duy nhất
`python -m unittest discover -s tests -p test_cloud_jobs31.py -v`, không chạy
lại suite hay workflow TEST 30. Có Blender thật: dựng, đo BLEND, nhập lại GLB,
phiên bản/retry không ghi đè, lỗi QA, phát hiện file/manifest hỏng; kèm kiểm
thử hợp đồng, dispatch, trạng thái, timeout process và attempt bị gián đoạn.

Batch cục bộ nhận bốn yêu cầu từ Git diff và khớp blob commit. Ba công việc
có kết quả; một mẫu âm bị chặn QA. Công cụ status kiểm checksum ba bộ kết quả:
đều đúng. Không dùng phản hồi Blender giả để báo dựng thành công.

## Lượt nhận việc tự động trên GitHub Actions

[Run 38701147200](https://github.com/hoanggiaktsda-beep/HG-3D-CLOUD-AI/actions/runs/38701147200),
commit `49bffc6`, sự kiện **push**, **Success**, 1 phút 8 giây. Các bước cài
công cụ miễn phí, kiểm thử TEST 31, nhận/xử lý yêu cầu và upload đều thành công.

| Yêu cầu | Kết quả công việc thật | File được công bố |
|---|---|---|
| console-job / v0001 | NEEDS_REVIEW, 100% | BLEND, GLB, QA, scene, checksum |
| console-job / v0002 | NEEDS_REVIEW, 100%, thư mục khác v0001 | BLEND, GLB, QA, scene, checksum |
| negative-qa / v0001 | FAILED, QA_FAILED, dừng ở 65% | Chỉ trạng thái/log/QA lỗi, không model |
| z-after-failure / v0001 | NEEDS_REVIEW, 100%, chạy sau công việc lỗi | BLEND, GLB, QA, scene, checksum |

Mẫu âm dựng model thật nhưng kỳ vọng đo cố ý sai 100 mm; verifier thực tế
phát hiện sai lệch. FAILED là trạng thái thật của công việc đó, không được
đổi thành thành công để làm xanh báo cáo. Batch đạt vì bài thử âm phải thất
bại đúng và công việc tiếp theo vẫn hoàn thành.

Artifact **hg-test31-public-38701147200-1**, **345 KB**, SHA-256
`f18193bf0292efb14949bd39f547bc1483748c18a93079f1ec791f1c0da81c42`.
Tải từ mục Artifacts của run; giải nén rồi mở `index.html`. Ví dụ kết quả v2:
`console-job/r0002-49bffc6a9c61-38701147200-a1/published/hg_scene.blend`
và `hg_scene.glb`. `batch.json`, `state.json`, `events.jsonl` ghi nhận tiến
độ/phiên bản; `manifest.json` cho từng bộ file. Artifact giữ một ngày.

Đã xác minh trạng thái, từng bước, annotations bốn công việc và thông tin
artifact công khai trên GitHub. Chưa tải artifact cloud về Codex để mở thủ
công; phần mở lại BLEND/nhập lại GLB do worker thật thực hiện và là điều kiện
trước khi công bố model. Cục bộ đã chạy cùng worker và kiểm lại checksum.

## Giới hạn còn lại

- Chỉ nhận công việc bằng Git push hoặc workflow_dispatch với mẫu cho phép;
  chưa kết nối website/backend upload và chưa xử lý dữ liệu riêng tư.
- Mô hình là demo tham số đã công khai, không phải nhận diện ảnh hoặc kết quả
  TEST 30. NEEDS_REVIEW không phải nghiệm thu thiết kế.
- Retry bằng attempt mới đã thử cục bộ; chưa trực tiếp bấm Re-run trên GitHub.
  Không có auto retry vô hạn hoặc resume giữa các bước Blender.
- Git giữ lịch sử yêu cầu/mã; artifact không phải storage model lâu dài.
  Với run bị hủy/timeout cứng, xem trạng thái GitHub; có thể chưa upload ledger.
- Không bảo đảm thứ tự hoàn tất giữa các workflow run song song. Mỗi batch
  giữ thứ tự các yêu cầu đã chọn và mỗi version có thư mục riêng.

[Hợp đồng, cách gửi việc và giới hạn](TEST31_CLOUD_JOBS_VI.md).
Workflow: `.github/workflows/test31-cloud-jobs.yml`. Giữ nguyên 18 vai trò,
viewer và TEST 30; không render, không API trả phí, không sửa repository khác.
