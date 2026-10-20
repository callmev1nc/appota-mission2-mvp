# Agent D — Mission 3: kiểm chứng trích dẫn + timeline + khung CR
- 2026-10-20 21:10 · live https://mission2mvp.vercel.app

| Nhóm | Check | Kết luận |
|---|---|---|
| T10 | U01 xem D03#s1: nguyên văn + version 2.0 + visibility | PASS {"accessible": true, "section": {"id": "D03#s1", "policy_key": "annual_entitlement_days", "value": 14, "text": "Định mức |
| T10 | U01 D09#s1 ≡ D99#s9 (không xác nhận sự tồn tại) | PASS {"accessible": false} vs {"accessible": false} |
| T10 | phản hồi từ chối không chứa canary/title D09 | PASS  |
| T10 | U01 xem D05#s1 (đọc được, khác phạm vi) — lộ lý do scope, giá trị | PASS {"accessible": true, "section": {"id": "D05#s1", "policy_key": "annual_entitlement_days", "value": 16, "text": "Định mức |
| T10 | U05 xem D11#s1 (nguồn được chọn) — value khớp dataset | PASS  |
| TIMELINE | U05: 7 row đúng trạng thái + restricted=1 + out_of_scope=4 | PASS {"D10": {"id": "D10", "title": "Đề xuất định mức Công ty An — bản nháp", "version": "99.0-draft", "kind": "draft_policy", "publication_statu |
| TIMELINE | U03 (Công ty Bình): không lộ tài liệu phòng Kinh doanh An | PASS ['D01', 'D05', 'D06'] |
| TIMELINE | U04 (HR): timeline ngang quyền ghi chú | PASS  |
| T12-CR | bản chạy thật KHÔNG chứa hồ sơ kịch bản U90 (chỉ ở khung test) | PASS  |
| T12-CR | CR thêm D90/U90 → ask() trả 21 [D90#s1] KHÔNG sửa lõi engine | PASS {"annual_entitlement_days": 21, "notice_working_days": 3, "request_route": "direct_manager", "eligible": true} |
| T12-CR | engine không biến dịch bộ dữ liệu thật sau khi ask(overlay) | PASS  |
| T12-CR | U01 (khách) vẫn 14 — phạm vi D90 không lan truyền | PASS {"annual_entitlement_days": 14, "notice_working_days": 3, "request_route": "direct_manager", "request_form": "KT-01", "handover_form": "NF-01", "eligible": true} |
| T10-live | GET /api/source U01 D03#s1 → 200 nguyên văn | PASS 200 {"accessible": true, "section": {"id": "D03#s1", "policy_key": "annual_entitleme |
| T10-live | GET /api/source U01 D09#s1 → 404 + rỗng metadata bị chặn | PASS 404 {"error": "section_not_available"} |
| T10-live | mã sai ≡ bị chặn (cùng 404 cùng body) | PASS 404 {"error": "section_not_available"} |
| TIMELINE-live | GET /api/timeline U05 → D11 có, D06/D07 không | PASS 200 ['D01', 'D02', 'D03', 'D04', 'D10', 'D11', 'D12'] |
| TIMELINE-live | GET /api/timeline U03 → D05 có, D11 không | PASS 200 ['D01', 'D05', 'D06'] |