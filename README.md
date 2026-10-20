# Mission 3 — Cải tiến: tri thức nội bộ được **kiểm chứng** theo đúng người hỏi

[![CI/CD](https://github.com/callmev1nc/appota-mission2-mvp/actions/workflows/ci.yml/badge.svg)](https://github.com/callmev1nc/appota-mission2-mvp/actions/workflows/ci.yml)

**Demo:** https://mission2mvp.vercel.app · **Repo:** https://github.com/callmev1nc/appota-mission2-mvp
(public, không chứa API key / mật khẩu / dữ liệu thật — quét gitleaks toàn lịch sử; **mốc Before của Mission 2 được tag `m2-mvp`** để đối chiếu Before→After ngay trên git.)
Toàn bộ tổ chức, tài liệu, con số là **dữ liệu giả lập** — không phải chính sách Appota và không phải tư vấn pháp luật.

> Mission 3 tiếp tục trên chính MVP của Mission 2 (không làm lại). Nền lõi vẫn là: **quy tắc chọn bằng chứng trước, LLM chỉ diễn đạt sau**. Mission 3 không thêm tính năng cho có — nó giải quyết 4 lỗ hổng thực tế khi đưa vào tổ chức thật, và phải chứng minh **tốt hơn bằng kết quả chạy lại được**.

---

## 0 · Phần Before → After bắt buộc

```
M2 (tag m2-mvp) ──→ Yêu cầu mới ──→ Quyết định ──→ M3 (mission3→main) ──→ Bằng chứng ──→ Giới hạn
```

| Yêu cầu mới (Lớp 1) | Trước (M2) | Sau (M3) | Bằng chứng |
|---|---|---|---|
| Kiểm chứng tài liệu được sử dụng | Chip `[Dxx#sx]` không bấm được | Bấm được (3 vị trí) → nguyên văn + phiên bản + hiệu lực + chủ sở hữu + trạng thái theo hồ sơ; tài liệu ngoài quyền → 404 không xác nhận tồn tại | T10 · Agent D 12/12 |
| Nhiều cấp tổ chức (Tập đoàn→Công ty→Phòng→Nhóm) | Chỉ cặp cùng cấp | Chuỗi 3 tầng 12→14→13 phân giải **theo quan hệ khai báo**, kèm giải thích từng bước | T08-CHAIN3 |
| Xung đột đa nguồn/đa cấp | Cùng cấp, không giải thích | Thêm cặp đa cấp → vẫn CHƯA KẾT LUẬN + ghi rõ "thiếu quan hệ nào, ai giải" | T09-EDGE-CONFLICT |
| Phiên bản & thời điểm hiệu lực | Chỉ trong trace JSON | Timeline theo hồ sơ + ngày xét; đổi ngày → trạng thái đổi theo; mốc biên 01/11 trả 15 ngày | T11-BOUND-11-11 |
| Từ chối khi thiếu căn cứ | 8 trạng thái | Giữ nguyên + giải trình rõ ràng trong UI/docs | T01–T07 tái chạy cùng kỳ vọng |

Chi tiết dài: `docs/m3_improvements.md` (quyết định + vì sao + hướng kỹ thuật) và `docs/before_after.md` (bằng chứng từng lệnh).

## 1 · Vấn đề mới & phần tôi chọn cải thiện

Bài toán thay đổi: tài liệu có hiệu lực theo thời gian, phân tầng nhiều cấp tổ chức, và không phải lúc nào cũng đủ căn cứ. Câu "Quy định nghỉ phép của tôi như thế nào?" **ngày 20/11** ở Phòng Kinh doanh An giờ đụng chuyện mới: định mức Phòng (13 ngày [D11#s1]) vs định mức Nhóm B2B mới ban hành (16 ngày [D12#s1]) — cùng hiệu lực, **chưa khai báo quan hệ**. M2 sẽ chỉ nói "CHƯA KẾT LUẬN". M3 nói thêm *vì sao chưa thể kết luận*, *căn cứ còn thiếu gì*, và *ai có thể giải* — mà vẫn không được phép tự chọn.

| Hồ sơ | Trước (M2) | Sau (M3, cùng engine lõi) |
|---|---|---|
| **U01** — An → KT → Nền tảng | 14 ngày [D03#s1] | 14 ngày [D03#s1] — **không thay đổi** + bấm được chip xem nguyên văn D03 (v2.0, 01/09→31/10) |
| **U05** — An → Kinh doanh *(mới)* | — | 13 ngày [D11#s1] chuỗi 3 tầng Tập đoàn→Công ty→Phòng, giải thích ra từng bước |
| **U05 @20/11** | — | CHƯA KẾT LUẬN 13 [D11#s1] vs 16 [D12#s1] + note căn cứ thiếu + escalate HR An |

## 2 · Kiến trúc — nền M2 bất biến, M3 thêm lớp kiểm chứng quanh lõi

```
Câu hỏi + hồ sơ (profile_id, ngày xét)
        │
        ▼
[1] Phân loại câu hỏi → policy_key                    (bất biến từ M2)
[2] Lọc: ĐỌC QUYỀN → PHẠM VI → PHÊ DUYỆT → HIỆU LỰC   (bất biến từ M2)
[3] Resolve: replaces → approved_overrides → CONFLICT  (bất biến từ M2)
[4] Trạng thái: ANSWER|CONFLICT|NO_AUTHORIZED...        (bất biến từ M2)
        │
        ▼
[5] Diễn đáp: template/Gemini + guard                  (bất biến từ M2)
        │
M3 thêm ─┼→ [6] trace.chains: chuỗi giải thích "bản nào bị gỡ bởi quan hệ khai báo nào"
         ┼→ conflicts kèm version/cấp/hiệu lực + note "căn cứ còn thiếu, ai phê duyệt"
         ┼→ GET /api/source  — nguyên văn trích dẫn (404 bất khả xác nhận)
         ┼→ GET /api/timeline — lịch sử phiên bản theo hồ sơ + ngày xét
         └→ UI: chip bấm được + bảng timeline + panel "Vì sao"
```

- **Bất khả xác nhận (new):** `/api/source` trả **cùng một 404/body** cho: mã không tồn tại ≡ mã ngoài quyền đọc ≡ hồ sơ lạ — không thể dùng endpoint để dò dữ liệu hạn chế.
- **Cấp sâu hơn không tự thắng (mở từ M2):** được chứng minh bằng ca đối lập — D11 khai báo quan hệ → thắng (T08); D12 không khai báo → mâu thuẫn (T09).
- **LLM vẫn không có thẩm quyền kết luận** — guard chặn rò rỉ chạy trên cả văn bản AI; chain/note sinh từ engine thuần.

## 3 · Chạy thử

**Online:** https://mission2mvp.vercel.app — chọn hồ sơ → hỏi; hoặc bấm các tình huống mẫu mới:
`⛓ T08 · U05 chuỗi 3 tầng` · `⚔️ T09 · U05 ngày 20/11 mâu thuẫn đa cấp` · `📅 T11 · U02 mốc 01/11`.

**Local:**

```powershell
pip install -r requirements.txt
python -m uvicorn api.index:app --port 8000        # http://localhost:8000
```

Không cần key nào; demo prod có `GEMINI_API_KEY` (free tier) — lỗi → fallback template bám nguyên văn nguồn.

**Kiểm thử (10 ca policy + 3 pin agent):**

```powershell
python -X utf8 tests/run_tests.py                                   # offline
python -X utf8 tests/run_tests.py --live https://mission2mvp.vercel.app
python -X utf8 tests/reports/agentD_m3.py                           # M3: viewer/timeline/CR
python -X utf8 tests/reports/agentD_m3.py --live https://mission2mvp.vercel.app
```

Kết quả trong `tests/results.md` + `tests/reports/`:

| Ca | Tình huống | Kết luận |
|---|---|---|
| T01–T07 | **Regression Mission 2 — kỳ vọng giữ nguyên từng chữ** | 6 ĐẠT · T06 CHƯA ĐẠT theo thiết kế |
| T08-CHAIN3 | **M3** — chuỗi 3 tầng phân giải theo quan hệ khai báo | ĐẠT |
| T09-EDGE-CONFLICT | **M3** — mâu thuẫn đa cấp chưa khai báo quan hệ | ĐẠT (chưa kết luận đúng + note giải thích) |
| T11-BOUND-11-11 | **M3** — biên hiệu lực mốc 01/11 | ĐẠT |
| T10 (Agent D) | **M3** — kiểm chứng trích dẫn + bất khả xác nhận | 12/12 check PASS |
| T12-CR (Agent D) | **M3** — khung Change Request: dữ liệu CR chạy được không cần sửa lõi | PASS |

Tổng: **9 PASS · 1 LIMITED (theo thiết kế) · 0 FAIL** (run_tests) + **Agent A (oracle 24): 16 PASS·8 PASS+·0 FAIL** + **Agent B (bảo mật): 0 issues** + **Agent C (smoke): 34/34** + **Agent D (M3): 12/12**.

**CI/CD (GitHub Actions — `.github/workflows/ci.yml`):**

```
push/PR ─→ [test]   compile+import · gitleaks toàn lịch sử · 10 ca offline · Agent D offline
             └→ [deploy] uv + vercel build --prod → Vercel production   (chỉ main)
                  └→ [live] smoke UI M3 · 10 ca trên deploy · Agent D trên deploy · quét rò rỉ canary
```

## 4 · Quyết định chính và đánh đổi (M3)

| Quyết định | Vì sao | Đánh đổi |
|---|---|---|
| Giải thích bằng **quan hệ khai báo**, không thêm "cấp thấp tự nhiên thắng" | Truy vết được từng bước, không đổi giả thuyết M2 | Hầu hết tổ chức thật quen logic "nguồn mới hơn ở cấp thấp tự nhiên thắng" — sản phẩm yêu cầu metadata đúng |
| Viewer áp **bất khả xác nhận** (KHÔNG phân biệt "không tồn tại" và "bị chặn") | Endpoint mới = mặt dò dữ liệu mới | UX hơi khó chịu khi mã gõ sai (chỉ nhận thông báo chung chung) |
| Timeline lọc **quyền + phạm vi + ngày xét**, không phải ngày hệ thống | "Của tôi" nghĩa là đúng bối cảnh hồ sơ | Không xem được tài liệu của phòng khác dù đọc được (hiện trong danh mục với lý do scope_out) |
| Khung CR = tiêm dataset thay vì fork code | CR nhập dữ liệu → chạy ngay, không sửa lõi | Test cần dataset cú pháp đúng (được Agent D kiểm chứng) |
| **Chủ động không làm**: cho LLM quyết / SSO/HRIS / chủ đề mới / frontend framework mới | Giữ nguyên giả thuyết "quy tắc chọn bằng chứng trước, LLM diễn đạt sau" và ưu tiên chiều sâu hơn chiều rộng | T06 số dư vẫn chưa đáp được — trung thực ghi là LIMITED |

## 5 · Hạn chế đã biết (không che) — cập nhật sau M3

1. **Vẫn một chủ đề** (nghỉ phép) — khả năng mở rộng chứng minh qua khung T12-CR nhưng chưa có sản phẩm chạy đa chủ đề.
2. **Không SSO/HRIS** — T06 số dư phép vẫn CHƯA ĐẠT theo thiết kế; danh tính là hồ sơ giả lập chọn tay.
3. **Dữ liệu giả lập** — không xác nhận chính sách Appota thật; slot Change Request đang chờ reviewer/HR chỉ định (khung T12-CR sẵn sàng chạy ngay khi CR bổ sung dữ liệu).
4. **Gemini free tier** — lỗi → template fallback ngay; guard chặn rò rỉ trên văn bản AI.
5. **Anti-XSS/CSRF của viewer** — chạy bằng heuristic Agent C + escape toàn diện, chưa red-team mở rộng; static server không có CSRF surface rõ nhưng chưa được kiểm thử chuyên sâu.
6. **Metadata quan hệ vẫn do người nhập** — sai replaces/overrides (thiếu approved_by) hệ thống phải từ chối kết luận chứ không tự chọn; nhu cầu nhìn từ HR: cần công cụ quản lý quan hệ (chưa làm).

## 6 · Ba câu hỏi bắt buộc (Mission 3)

**① Ưu tiên thay đổi gì / chủ động chưa làm điều gì, vì sao?**
Chọn ưu tiên ba nhóm: (a) kiểm chứng trích dẫn — thứ duy nhất nằm trong yêu cầu nhưng M2 chưa có sản phẩm; (b) dữ liệu + giải thích đa cấp — chặn mối nguy "cấp thấp tự nhiên thắng" và làm CONFLICT có giải trình; (c) timeline theo ngày xét — chứng minh hiệu lực "theo bối cảnh hồ sơ" ngay trên UI. **Chủ động chưa làm**: cho LLM quyết kết quả (giả thuyết lõi), SSO/HRIS, chủ đề mới, frontend mới — vì Mission 3 chấm "hiểu bài toán → lựa chọn → kiểm chứng", nên giữ bằng chứng regression nguyên trạng (T01–T07 không đổi một kỳ vọng, oracle 24 vẫn 16/8/0) để Before/After có nghĩa.

**② Thay đổi tạo khác biệt lớn nhất & bằng chứng nào?**
Khác biệt lớn nhất là lớp **kiểm chứng quanh lõi**: bấm `Dxx#sx` ra nguyên văn + phiên bản + trạng thái trong quyền, gắn với panel "Vì sao" (trace.chains) và conflict note "căn cứ còn thiếu". Bằng chứng: Agent D 12/12 (bất khả xác nhận — kiểm cả offline lẫn endpoint thật sau deploy), T08/T09/T11 ĐẠT, toàn bộ 5 pin tái chạy xanh: 10 ca (9 PASS + 1 LIMITED) · oracle 16/8/0 · Agent B 0 issues · Agent C 34/34 · CI deploy + live hồi quy (xem `tests/results.md`, `tests/reports/agentD_m3.md`, `docs/before_after.md`).

**③ Nếu đưa cho người dùng thật ngày mai, rủi ro lớn nhất còn lại? Xử lý như thế nào?**
Rủi ro nhất: **metadata quan hệ (replaces/approved_overrides) do con người nhập** — nếu nhập sai approved_by/scope, hệ thống sẽ từ chối kết luận và chuyển HR thay vì trả lời dứt khoát sai (đây là lựa chọn an toàn có chủ đích); nhưng nếu người quản lý tài liệu bỏ bắt buộc ghi quan hệ, nhiều câu sẽ dừng ở CHƯA KẾT LUẬN. Xử lý kế tiếp: (1) công cụ quản lý quan hệ cho HR + validation tại lúc nhập liệu; (2) audit log "từ chối vì thiếu quan hệ khai báo" để HR thấy điểm tắc; (3) tích hợp HRIS thật để đóng ca T06 (số dư phép).

## 7 · Video cải tiến (≤5 phút) — xem `docs/video_m3_script.md`

## 8 · Nhật ký AI

Tôi dùng AI (OpenCode) phân tích đề, thiết kế dữ liệu đa cấp, làm engine chain/timeline/viewer, viết test và rà soát từng ca chạy thật (10 ca + 5 pin). Quyết định "khi nào kết luận / khi nào từ chối" **không** delegate cho LLM — là giả thuyết sản phẩm từ Mission 1 giữ nguyên ở Mission 3.
