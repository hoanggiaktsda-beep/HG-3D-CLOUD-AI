# Câu lệnh đầu tiên trong Codex

Dán vào ô chat trong dự án `HG 3D CLOUD AI`:

> Hãy đọc AGENTS.md, README.md và tất cả docs. Đây là dự án độc lập, không kết nối GitHub hay dự án khác. Chạy kiểm thử Python, kiểm tra Blender có sẵn không, sau đó thử dựng file BLEND/GLB từ examples/living_room.json. Không render. Hãy liệt kê phần nào đã thực thi và phần nào chưa; ưu tiên kết nối pipeline tiếp nhận ảnh và mặt bằng bản vẽ thành JSON có bằng chứng, rồi mở rộng dựng hình. Không tự nhận giống ảnh 100%, không tự tạo dịch vụ trả phí.

## Lệnh kiểm thử

```sh
python -m unittest discover -s tests -v
python scripts/hg3d.py check examples/living_room.json
python scripts/hg3d.py report outputs/qa_report.json
```

Nếu môi trường có Blender:

```sh
blender --version
blender -b --python scripts/blender_build.py -- examples/living_room.json outputs/demo01
```

Đừng chạy lại vào cùng `outputs/demo01` khi đã có file; chọn tên mới `outputs/demo02` để không ghi đè.

## Nếu ZIP bị giải nén sai

Mở thư mục nguồn trong File Explorer. `AGENTS.md`, `README.md`, `hgcloud/`, `scripts/`, `docs/` phải ở ngang hàng ngay trong `HG-3D-CLOUD-AI`. Không để `HG-3D-CLOUD-AI/HG_3D_CLOUD_AI_MASTER_CODEX/AGENTS.md` trừ khi thay thư mục gốc trong Codex.
