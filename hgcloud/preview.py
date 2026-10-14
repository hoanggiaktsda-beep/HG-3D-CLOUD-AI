"""Offline mobile-friendly report HTML — not a live cloud dashboard."""
import html, json
from pathlib import Path

def build_html(report_path, dest):
    report=json.loads(Path(report_path).read_text(encoding='utf-8'))
    status=html.escape(report['status']); project=html.escape(report['project'])
    cards=''.join(f'<li><strong>{html.escape(item["id"])}</strong> — {html.escape(item["status"])}: {html.escape(item["reason"])}</li>' for item in report['review_items'])
    page=f'''<!doctype html><html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>HG 3D QA</title><style>body{{font:16px system-ui;margin:auto;padding:20px;max-width:780px;background:#101216;color:#fafafa}}.panel{{background:#22262d;border-radius:15px;padding:18px;margin:14px 0}}li{{margin:12px 0}}.muted{{color:#bbc4cf}}</style></head><body><h1>HG 3D CLOUD AI</h1><p class="muted">Báo cáo kiểm tra thông số — không thay thế nghiệm thu file 3D.</p><div class="panel"><h2>{project}</h2><p>Trạng thái: <strong>{status}</strong></p><p>Đối tượng: {report['objects']} · Xác nhận: {report['confirmed']} · Suy luận: {report['inferred']}</p></div><div class="panel"><h3>Các điểm cần kiểm tra</h3><ul>{cards or '<li>Không có mục cần xem trong JSON; chưa phải xác nhận hình học.</li>'}</ul></div><div class="panel"><h3>Giới hạn</h3><ul>{''.join('<li>'+html.escape(x)+'</li>' for x in report['limits'])}</ul></div></body></html>'''
    p=Path(dest); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(page,encoding='utf-8'); return p
