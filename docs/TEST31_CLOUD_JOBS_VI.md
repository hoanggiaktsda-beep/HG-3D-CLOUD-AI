# TEST 31 — nhận việc và vận hành Blender trên GitHub Actions

TEST 31 kiểm thử vận hành công việc, **không lặp lại TEST 30**. TEST 30 giữ
**CẦN XÁC NHẬN**. Không thay đổi 18 vai trò, viewer, backend riêng tư hoặc
workflow TEST 30. Không render, không nhận ảnh khách hàng hoặc gọi API trả phí.

[Kết quả kiểm thử và hai lượt Actions thực tế](TEST31_RESULTS_VI.md).

## Cách nhận và chạy công việc

- Thêm yêu cầu mới tại `jobs/public/<job_id>/v0001.json`, commit/push lên main:
  Actions tự nhận các file mới trong đúng khoảng commit push.
- Mỗi lần tối đa 5 yêu cầu, xử lý tuần tự, không bỏ công việc sau lỗi Blender/QA.
- Không sửa/xóa yêu cầu cũ. Phiên bản tiếp theo là file `v0002.json`,
  `parent_revision: 1`; ghi SHA-256 yêu cầu và phiên bản cha.
- Các batch có thể chạy song song; không cam kết thứ tự hoàn tất giữa các run.
  Parent là lịch sử yêu cầu, không yêu cầu phiên bản trước phải dựng xong.
  Revision nhận số nguyên 1–100.
- Chạy lại: Actions → TEST 31 → Run workflow → `request_id=console-job/v0002`.
  Hoặc Re-run jobs để có `run_attempt` mới. Quyền GitHub của người vận hành
  bảo vệ thao tác; không đặt token trong JavaScript, không mở API mới.

Ví dụ hợp đồng chỉ cho mẫu công khai:

```json
{"schema_version":1,"job_id":"console-job","revision":1,"parent_revision":0,"sample":"console-demo"}
```

Chỉ nhận `console-demo` và mẫu âm `qa-failure-demo` từ catalog đóng. Không
chấp nhận URL, đường dẫn, nội dung ảnh, Python hoặc kích thước khách hàng.
`examples/product_console.json` đã công khai trong dự án là **mẫu tham số**,
không phải mô hình AI tự nhận diện ảnh. Checksum mẫu được khóa; thay mẫu phải
được kiểm tra và cập nhật catalog. Yêu cầu phải khớp blob Git của commit chạy.

## Tiến độ, phiên bản và kết quả

Mỗi công việc: `QUEUED → BUILDING → VERIFYING → PUBLISHING → NEEDS_REVIEW`,
hoặc `FAILED`. Ghi tiến độ 0/20/65/90/100%, timestamp UTC, lỗi có mã, log Blender,
`state.json` nguyên tử và nhật ký `events.jsonl`. Trạng thái trong hàng chờ
trước khi runner khởi động do GitHub Actions hiển thị, chưa có ledger worker.

Phiên bản gồm revision yêu cầu + commit + GitHub run ID + run attempt. Hai
revision/lượt chạy không ghi đè nhau. Cùng lượt đã hoàn tất được đọc lại và
kiểm checksum, không dựng lại. Lượt đang dở không được coi thành công: chạy
lại bằng attempt mới. Không dùng concurrency group vì GitHub chỉ giữ một
pending run mỗi group và có thể hủy các yêu cầu chờ trước đó.

Theo dõi trực tiếp qua log Actions; tải artifact xem `index.html`,
`REPORT_TEST31_VI.md`, `batch.json`, state và events từng phiên bản. Đọc trạng
thái và kiểm lại checksum cục bộ:

```sh
python scripts/cloud_job_status31.py <thu-muc-artifact-da-giai-nen>
```

Chỉ công việc vượt kiểm định có thư mục `published/` gồm BLEND, GLB, scene JSON,
QA và manifest SHA-256. Workspace chưa kiểm định nằm **ngoài** thư mục upload.
Mở lại BLEND để đo mesh theo spec, nhập lại GLB và so đỉnh world-space hai
chiều; kiểm cả header GLB. Thành công kỹ thuật vẫn giữ NEEDS_REVIEW, không
nghiệm thu thiết kế hoặc nâng TEST 30 thành đạt.

## Kiểm thử và xử lý lỗi

Bộ TEST 31 kiểm tra hợp đồng/mẫu cho phép, chặn symlink/đường dẫn/parent thiếu,
không sửa yêu cầu cũ, giới hạn batch, tiến độ, timeout và kill process group,
attempt bị gián đoạn, version/retry không ghi đè, sửa file bị phát hiện qua
checksum, Blender và GLB thật. Các fixture giao thức được tách khỏi kết quả
thực thi thật.

Mẫu âm dựng console thật rồi đưa **kỳ vọng QA cố ý sai 100 mm** cho verifier.
Mesh thật phải bị đo sai lệch và trả `QA_FAILED`; không giả mã thoát hoặc
phản hồi Blender. Batch chỉ đạt bài thử âm khi thất bại đúng QA, không xuất
model vào `published/`, và công việc tốt tiếp theo vẫn chạy. Trạng thái công
việc âm vẫn là FAILED dù kỳ vọng thử nghiệm đã được đáp ứng.

Các mã lỗi gồm QA_FAILED, WORKER_TIMEOUT, BLENDER_UNAVAILABLE, BLENDER_EXIT,
GLB_INVALID, QA_REPORT_INVALID, ARTIFACT_INTEGRITY_FAILED. Không tự lặp vô hạn;
retry bằng run attempt mới, giữ nguyên bằng chứng lượt trước. Workflow có
timeout 12 phút, từng subprocess tối đa 120 giây, runner Ubuntu tiêu chuẩn
trên repository công khai, quyền contents:read, artifact giữ một ngày.

## Giới hạn thực tế

Đây là hàng đợi theo sự kiện push/dispatch của GitHub, **không phải backend
24/7 nhận ảnh từ website**. Chưa kết nối website hoặc dữ liệu riêng tư. Không
có tự retry vô hạn, SLA, ưu tiên công việc, storage lâu dài hay cơ chế resume
giữa các bước Blender. Run bị hủy/kill cứng có thể chưa kịp upload ledger;
trạng thái GitHub (cancelled/timed out) là nguồn theo dõi lượt đó, tuyệt đối
không coi là thành công. Rerun tạo attempt mới từ đầu. Artifact hết hạn sau
một ngày, cần tải về nếu muốn giữ lâu hơn; Git giữ yêu cầu và lịch sử mã nguồn.

Workflow: `.github/workflows/test31-cloud-jobs.yml`. Chỉ upload dữ liệu mẫu cố
định và log an toàn, không upload workspace, token, bộ nhớ model hoặc thư mục
`.private`. Không phát hành website. Không dùng việc TEST 31 vận hành đạt để
khẳng định TEST 30 đã lắp ráp được ghế.
