# Mission 3 — Tài liệu cải tiến (Change Documentation)

> Thay đổi trên chính repo Mission 2, tag mốc Before: `m2-mvp` (commit `b8b1e0f`), nhánh làm việc `mission3`.
> Toàn bộ tổ chức, tài liệu, con số là **dữ liệu giả lập** — không dùng dữ liệu nội bộ thật của Appota.

## 1. Yêu cầu mới (điều gì dẫn tới việc thay đổi)

Mission 2 đã chứng minh: lọc quyền → phạm vi → hiệu lực → resolve ngoại lệ/thay thế → từ chối khi thiếu căn cứ. Đưa vào môi trường tổ chức thật, 4 lỗ hổng còn mở:

1. Người dùng **không kiểm chứng được tài liệu gốc** — câu trả lời chỉ có chip `[Dxx#sx]` (yêu cầu Lớp 1 #5: cho người dùng kiểm chứng tài liệu được sử dụng).
2. Trace chỉ đọc được trong JSON API — **UI không giúp được gì** khi cần tra chi tiết phiên bản & hiệu lực (yêu cầu #1: phân biệt phiên bản và thời điểm có hiệu lực).
3. Xung đột chỉ được xử lý với cặp **cùng cấp tổ chức** (Công ty vs Công ty); tri thức tồn tại ở nhiều cấp (Tập đoàn → Công ty → Phòng → Nhóm) chưa được chứng minh (yêu cầu #2, #3).
4. API nhận `date` nhưng UI không có "tra theo ngày" — không dùng được cho bối cảnh "cùng câu hỏi, khác thời điểm".

## 2. Quyết định thay đổi gì / chủ động chưa làm gì

**Làm:**
- [A] **Kiểm chứng trích dẫn**: bấm mọi chip `[Dxx#sx]` (trong câu trả lời, bảng nguồn, bảng timeline) mở hộp thoại nguyên văn + phiên bản + cửa sổ hiệu lực + chủ sở hữu + trạng thái với hồ sơ đang chọn · API `GET /api/source`.
- [B] **Nhiều cấp + xung đột có giải thích**: dữ liệu mới cấp Phòng/Nhóm (D11/D12, cây tổ chức thêm nhánh Kinh doanh/B2B); `trace.chains` giải thích tuần tự "bản nào bị gỡ bởi quan hệ nào, bản nào còn đứng"; CONFLICT hiển thị đối chiếu (giá trị · phiên bản · cấp · đơn vị) + **ghi rõ căn cứ còn thiếu** (note) + hướng xử lý (ai cần phê duyệt quan hệ gì).
- [C] **Timeline phiên bản**: `GET /api/timeline` + bảng UI "Lịch sử phiên bản & hiệu lực", trạng thái tính theo **ngày xét** (hết hiệu lực / đang hiệu lực / chưa tới); đổi ngày xét → timeline và danh mục tài liệu tự reload.
- [D] Panel "Vì sao kết luận như vậy" diễn giải trace thành văn cho người thường — chữ lấy từ engine, không sáng tạo thêm.
- **Bảo mật mới**: `/api/source` áp dụng *bất khả xác nhận* (denial aggregation): mã không tồn tại ≡ mã bị chặn quyền ≡ hồ sơ lạ — cùng một 404, cùng body; canary D09 không xuất hiện ở bất kỳ phản hồi nào.
- **Khung CR-safe**: `ask(profile_id, question, date, dataset=None)` — test tiêm dataset riêng để chứng minh Change Request nhập thêm dữ liệu **không đòi sửa code lõi**.
- CI/CD: chạy thêm Agent D (offline + trên deploy thật); live smoke kiểm tra UI M3 (viewer/timeline).

**Chủ động KHÔNG làm (và vì sao):**
1. **Không cho LLM có thẩm quyền kết luận** — giữ nguyên giả thuyết M2 "quy tắc chọn bằng chứng trước, LLM diễn đạt sau". M3 chỉ thêm lớp giải trình quanh lõi, không chuyển quyền sang model.
2. **Không làm SSO/HRIS thật** — ngoài tầm 3 ngày; danh tính vẫn là hồ sơ giả lập chọn tay; ca T06 (số dư phép) vẫn CHƯA ĐẠT theo thiết kế một cách trung thực.
3. **Không mở rộng chủ đề kiến thức mới** (vẫn một chủ đề nghỉ phép) — ưu tiên chiều sâu (đa cấp + kiểm chứng) hơn chiều rộng; khả năng mở rộng được chứng minh bằng khung T12-CR (dữ liệu mới chạy được ngay, không sửa engine).
4. **Không dựng lại frontend bằng framework khác** — giữ stack tĩnh của M2 để regression đối chiếu được hoàn toàn trên git (tag `m2-mvp` vs `mission3`).

## 3. BEFORE → AFTER

| Năng lực | Trước (M2) | Sau (M3) | Bằng chứng |
|---|---|---|---|
| Kiểm chứng tài liệu | text có trong JSON API nhưng UI bấm không được; không biết `[D01#s4]` ứng nguyên văn nào | bấm được chip → nguyên văn + version + hiệu lực + visibility với hồ sơ | T10 (Agent D 12/12) · Agent C 34/34 |
| Nhiều cấp tổ chức | resolve chỉ công ty vs công ty; tầng Phòng/Nhóm chưa được chứng minh | chuỗi 3 tầng 12 → 14 → 13 phân giải đúng quan hệ khai báo (`approved_overrides` đúng key, scope, phê duyệt) | T08-CHAIN3 |
| Xung đột đa nguồn | cùng cấp (D05 vs D06) | thêm cặp đa cấp (D11 13 vs D12 16) vẫn CHƯA KẾT LUẬN + giải thích "thiếu quan hệ nào" + "ai có thể giải" | T09-EDGE-CONFLICT · T02 giữ nguyên |
| Phiên bản & hiệu lực | API có tham số date nhưng UI không dùng | bảng timeline 7 tài liệu trong phạm vi profile + trạng thái theo ngày xét + nháp được đánh dấu | T11-BOUND-11-11 · T04 giữ nguyên |
| Từ chối khi thiếu căn cứ | 8 trạng thái có sẵn | giữ nguyên + giải trình CONFLICT rõ "căn cứ thiếu" trong template và UI | T03-P01 không rò rỉ · không hồi quy |

## 4. Bộ kiểm thử — kết quả chạy thật (tổng hợp)

| Pin | Phạm vi | Kết quả |
|---|---|---|
| `run_tests.py` (10 ca) | T01–T07 giữ nguyên kỳ vọng của M2 (regression) + T08/T09/T11 mới | 9 PASS · 1 LIMITED (T06 theo thiết kế) · 0 FAIL |
| Agent A — oracle 24 ca | đối chiếu kỳ vọng Mission 1 với engine trên dữ liệu v2 | 16 PASS · 8 PASS+ · 0 FAIL (y hệt M2) |
| Agent B — bảo mật | leak battery / adversarial / malformed / CORS · gitleaks toàn lịch sử | 0 issues |
| Agent C — smoke | static + contract API + biên hiệu lực + anti-XSS + latency | 34/34 PASS |
| Agent D — M3 | viewer bất khả xác nhận + timeline phạm vi + khung CR | 12/12 PASS |

Chi tiết: `tests/results.md` (10 ca) và `tests/reports/agentD_m3.md`. Regression 7 ca M2 giữ nguyên từng kỳ vọng — kết quả xanh sau cải tiến.

## 5. Cơ chế kỹ thuật (tóm tắt, có giải thích)

- **engine (`app/engine.py`)**: `trace.chains` — một mục cho mỗi policy_key: dòng "bỏ khỏi bằng chứng" (quan hệ khai báo: approved_overrides/replaces, đúng điều khoản, đúng phạm vi), dòng "còn đứng" (đúng phiên bản/cấp), dòng KẾT LUẬN — theo quan hệ, không theo "mới hơn"; `conflicts` kèm giá trị + version + cấp + hiệu lực + `note` (chưa khai báo quan hệ, cần chủ sở hữu/HR phê duyệt); `timeline_view()` — chỉ liệt kê tài liệu (1) có quyền đọc và (2) đúng phạm vi đơn vị của hồ sơ, tài liệu bị chặn chỉ đếm số; `source_view()` — kiểm tra quyền đọc TRƯỚC khi hiển thị, trả về cùng một kết quả cho "không tồn tại" và "bị chặn" (bất khả xác nhận); `ask(..., dataset=None)` — khung CR.
- **API (`api/index.py`)**: `GET /api/source` (404 uniform), `GET /api/timeline` (404 khi hồ sơ lạ), validation ngày.
- **UI (index/app/styles)**: hộp thoại viewer; bảng timeline; panel "Vì sao"; chip bấm được ở 3 vị trí (chỉ dùng tài liệu đã nằm trong quyền). Mọi chuỗi động qua `esc()`/`withCites()` — heuristic anti-XSS của Agent C vẫn PASS.
- **CI/CD (`.github/workflows/ci.yml`)**: [test] compile/import + gitleaks lịch sử + 10 ca offline + Agent D offline; [deploy] main → Vercel; [live] smoke + 10 ca + Agent D chạy trên deploy thật + quét rò rỉ canary D09 và phạm vi D11.
- **Dữ liệu (`data/synthetic_dataset.json` v2)**: thêm nhánh Phòng Kinh doanh/B2B, hồ sơ U05, D11 (quy tắc Phòng có khai báo quan hệ), D12 (nguồn Nhóm chưa khai báo — cố tình làm ra ca đa cấp để kiểm thử); quy ước `multi_level` nhập nguyên tắc "cấp sâu hơn chỉ thắng khi khai báo quan hệ".

## 6. Giới hạn còn lại

Xem README (mục "Hạn chế đã biết"). Cốt lõi: vẫn một chủ đề; SSO/HRIS chưa có; T06 số dư chưa động được; kiểm thử viewer chống XSS/CSRF vẫn dùng heuristic hiện có (chưa red-team mở rộng); metadata quan hệ (replaces/overrides) vẫn phụ thuộc con người nhập đúng — sai metadata hệ thống phải từ chối kết luận chứ không tự chọn.
