# Mission 2 — Hiện thực hóa: trả lời đúng tri thức theo đúng người hỏi

[![CI/CD](https://github.com/callmev1nc/appota-mission2-mvp/actions/workflows/ci.yml/badge.svg)](https://github.com/callmev1nc/appota-mission2-mvp/actions/workflows/ci.yml)

**Demo:** https://mission2mvp.vercel.app · **Repo:** https://github.com/callmev1nc/appota-mission2-mvp (public, không chứa API key / mật khẩu / dữ liệu thật — đã quét gitleaks trước khi push).
Toàn bộ tổ chức, tài liệu, con số là **dữ liệu giả lập** — không phải chính sách Appota và không phải tư vấn pháp luật.

> MVP chứng minh một giả thuyết: **chọn đúng bằng chứng (quyền + phạm vi + hiệu lực + ngoại lệ)
> bằng quy tắc trước, LLM chỉ diễn đạt sau** — thì cùng một câu hỏi, hai người khác đơn vị
> sẽ nhận kết quả đúng khác nhau, và hệ thống từ chối được khi thiếu căn cứ.

---

## 1 · Vấn đề và phần tôi chọn chứng minh

Cùng câu hỏi *“Quy định nghỉ phép của tôi như thế nào?”*:

| Hồ sơ | Kết quả trên demo |
|---|---|
| **U01** — Công ty An → Kỹ thuật → Nền tảng | **TRẢ LỜI**: 14 ngày/năm `[D03#s1]`, báo trước 3 ngày `[D01#s3]`, gửi quản lý trực tiếp `[D01#s4]`, mẫu KT-01 `[D07#s1]`, bàn giao NF-01 `[D08#s1]` |
| **U03** — Công ty Bình → Vận hành → Hỗ trợ | **CHƯA KẾT LUẬN**: D05 ghi 16 ngày, D06 ghi 18 ngày, cùng hiệu lực, thiếu quan hệ thay thế → dẫn đúng 2 nguồn, chuyển HR Bình |

Phần quan trọng nhất: **bộ máy chọn bằng chứng** (`app/engine.py`) — vì mọi lỗi nghiêm trọng
(sai đơn vị, dùng bản hết hiệu lực/bản nháp, lộ tài liệu hạn chế, “chọn bừa” khi xung đột)
đều xảy ra ở bước này, không ở bước viết văn của LLM.

## 2 · Kiến trúc — quy tắc trước, LLM sau

```
Câu hỏi + hồ sơ (profile_id, ngày xét)
        │
        ▼
[1] Phân loại câu hỏi → các policy_key thực sự hỏi được
        │
        ▼
[2] Lọc ứng viên theo thứ tự:  ĐỌC QUYỀN → PHẠM VI ĐƠN VỊ → PHÊ DUYỆT → HIỆU LỰC (ngày xét)
        │                       (tài liệu bị chặn: không id, không tiêu đề, không gì cả)
        ▼
[3] Resolve từng policy_key:   replaces (bản thay thế) → approved override (ngoại lệ khai báo)
        │                       → còn >1 giá trị bất đồng = CONFLICT (không top-k, không “mới hơn”)
        ▼
[4] Trạng thái: ANSWER | CONFLICT | NO_AUTHORIZED_EVIDENCE | NO_DATA | SOURCE_ONLY | NEED_CONTEXT
        │
        ▼
[5] Diễn đáp: template bám nguyên văn nguồn (mặc định) hoặc Gemini (nếu có key)
        │      + guard: chặn chuỗi ngoài quyền & mã trích dẫn không thuộc tập nguồn
        ▼
Câu trả lời + [trích dẫn Dxx#sx] + trace chọn bằng chứng + ngữ cảnh đã gửi cho model
```

- **Danh tính không đổi theo câu hỏi.** Query là dữ liệu, không phải lệnh (ca X04).
- **Không lộ metadata:** tài liệu không có quyền bị loại ngay ở [2], response chỉ ghi *số lượng*
  bị loại, không id/tiêu đề (ca P01 — kiểm chứng cả trong payload gửi model).
- **Lỗi LLM ≠ đổi kết luận:** evidence đã chọn độc lập; Gemini lỗi → `SOURCE_ONLY`
  (hiện nguồn + thông báo chưa tạo được câu trả lời AI — ca C04).

## 3 · Chạy thử

**Online:** mở https://mission2mvp.vercel.app — chọn hồ sơ → hỏi (hoặc bấm tình huống mẫu,
hoặc nút *“Cùng câu hỏi — 2 người khác đơn vị”* để chạy song song U01 vs U03).

**Local:**

```powershell
pip install -r requirements.txt
uvicorn api.index:app --port 8000        # mở http://localhost:8000
```

Không cần key nào để chạy local. **Bản demo trên Vercel đã set `GEMINI_API_KEY`
(free tier — `gemini-flash-lite-latest`)**: mặc định `auto` → Gemini diễn đạt, lỗi
hoặc rate limit → tự fallback template bám nguyên văn nguồn; key chỉ nằm trong
Vercel Secret, không trong repo. Local chưa set key → luôn dùng template.

**Kiểm thử (7 ca, chạy thật):**

```powershell
python -X utf8 tests\run_tests.py                  # offline — import engine trực tiếp
python -X utf8 tests\run_tests.py --live https://mission2mvp.vercel.app   # trên bản deploy
```

Kết quả trong [`tests/results.md`](tests/results.md):

| Ca | Tình huống | Kết luận |
|---|---|---|
| T01-A01 | U01 — hồ sơ có ngoại lệ hợp lệ | **ĐẠT** |
| T02-A03 | U03 — hai nguồn xung đột 16 vs 18 | **ĐẠT** (chưa kết luận đúng) |
| T03-P01 | U01 — xin tài liệu ngoài quyền | **ĐẠT** (từ chối, không rò rỉ) |
| T04-V03 | Mốc 31/10 — D04 mới hơn nhưng chưa hiệu lực | **ĐẠT** |
| T05-X04 | Prompt injection đòi bí mật | **ĐẠT** |
| T06-BALANCE | Hỏi số dư — MVP không có HRIS | **CHƯA ĐẠT theo thiết kế** |
| T07-C04 | LLM lỗi sau khi chọn bằng chứng | **ĐẠT** (chỉ hiện nguồn) |

Tổng: **6 ĐẠT · 1 CHƯA ĐẠT theo thiết kế · 0 lỗi kiểm thử** (cả offline lẫn trên bản deploy).

**CI/CD (GitHub Actions — `.github/workflows/ci.yml`):**

```
push / PR ─→ [test]   compile + import · gitleaks toàn lịch sử · 7 ca offline
              └→ [deploy] uv + vercel build --prod → Vercel production   (chỉ nhánh main)
                   └→ [live] smoke endpoint · 7 ca trên bản deploy · quét rò rỉ D09/canary
```

Mỗi lần push vào `main` tự chạy đủ: quét secret (chặn), test, deploy, rồi kiểm thử lại
trên bản deploy thật. Token Vercel chỉ nằm trong GitHub Secrets (`VERCEL_TOKEN`,
`VERCEL_ORG_ID`, `VERCEL_PROJECT_ID`) — không bao giờ có trong file.

**Kiểm thử đa tác tử — 3 pin chạy độc lập trên bản deploy + oracle 24 ca:**

| Pin | Phạm vi | Script | Kết quả |
|---|---|---|---|
| A — đúng giả thuyết | Đối chiếu **toàn bộ 24 ca oracle** (kỳ vọng Mission 1) với engine | `tests/reports/agentA_oracle.py` | **16 PASS · 8 PASS+ · 0 FAIL** |
| B — bảo mật | gitleaks lịch sử, leak battery (4 câu hỏi × 3 hồ sơ), adversarial X01–X04/P04, malformed, CORS | `tests/reports/agentB_security.py` | **0 vấn đề** |
| C — smoke | tĩnh + contract API + 4 mốc hiệu lực + chế độ LLM + anti-XSS + latency | `tests/reports/agentC_smoke.py` | **28/28 PASS** (avg 333ms, worst 412ms) |

Báo cáo chi tiết: [`tests/reports/`](tests/reports/). Các pin đã **tìm và sửa thật**:
echo câu hỏi bị gỡ khỏi response (ngăn echo chuỗi cấm), `/api/documents` che luôn *id*
của tài liệu hạn chế, validate `question`/`date` (trước đây 500), phân loại câu hỏi
“định mức/nhóm”, escalate khi thiếu dữ liệu, tách marker HR khỏi phần quyền lợi (P02).<br>
“PASS+” = engine trả đúng mọi dữ kiện oracle yêu cầu nhưng trích thêm nguồn hợp lệ
(superset, không mâu thuẫn) — do engine mở rộng cụm thủ tục khi hỏi cấp đơn vị.

## 4 · Quyết định chính và đánh đổi

| Quyết định | Vì sao | Đánh đổi |
|---|---|---|
| Quy tắc chọn bằng chứng bằng Python, không để LLM quyết | Truy trình được kiểm chứng, deterministic | Mới phục vụ chủ đề nghỉ phép có cấu trúc metadata |
| Ngoại lệ / thay thế phải **khai báo** (`approved_overrides`, `replaces`) | Giải thích được, không “mới hơn thắng” | HR phải quản metadata đúng — sai metadata vẫn ra kết quả sai |
| Xung đột → **không kết luận**, chuyển HR | An toàn hơn trả lời dứt khoát sai | Trải nghiệm “chưa trả lời” cần người dùng hiểu |
| Template mặc định, Gemini tùy chọn | Demo không bao giờ chết vì quota/key | Template nghèo văn phong hơn LLM |
| Hồ sơ giả lập chọn tay (không SSO) | Dành 3 ngày cho logic thay vì auth | Chưa chứng minh bảo mật danh tính thật |

## 5 · Hạn chế đã biết (không che)

1. **Không có HRIS/chấm công** → không trả lời được “còn bao nhiêu ngày phép” (T06) — chỉ trả định mức năm và nói rõ giới hạn.
2. **Một chủ đề** (nghỉ phép) — metadata model đủ chung cho chủ đề khác nhưng chưa tích hợp.
3. **Dữ liệu giả lập** — không xác nhận chính sách Appota hay bất kỳ thực tế nào.
4. **Gemini free tier** — bản demo set key free tier (`gemini-flash-lite-latest`); rate limit
   hoặc lỗi → fallback template ngay (không bao giờ chết demo); guard chặn rò rỉ chạy trên cả
   văn bản AI. Chưa set key (local mặc định) → dùng template.
5. **Adversarial có giới hạn** — đã chạy battery 24 ca oracle (`agentA_oracle.py`) và pin bảo mật (leak/adversarial/malformed) thật trên deploy, nhưng chưa red-team mở rộng (fuzz, đo rate limit, thử đa người dùng thật).
6. **Prompt injection** được kiểm bằng guard + test mẫu (T05, X01–X04) chạy thật, chưa red-team bằng người.

## 6 · Ba câu hỏi bắt buộc

**① Phần quan trọng nhất chọn chứng minh?** → Bộ máy chọn bằng chứng
(`app/engine.py`): lọc đọc quyền → phạm vi → hiệu lực → resolve ngoại lệ/thay thế →
kết luận hoặc từ chối. Nếu phần này đúng, mọi lỗi “trả lời sai/ngộ độc” đều chặn được
*trước* khi LLM diễn đạt — nên hướng giải pháp khả thi: LLM có thể thay thế, cải tiến hoặc
tắt mà kết luận không đổi (ca C04 chứng minh điều đó).

**② Đổi gì so với Mission 1?** → (a) Từ “24 ca là kỳ vọng trên giấy” thành **7 ca chạy thật**
và cả 24 fixture giữ nguyên làm oracle — nay đã được đối chiếu thật bằng
`tests/reports/agentA_oracle.py` (0 FAIL); (b) thiết kế “một app Python” thành
**engine Python + API Vercel + trang tĩnh** để có link demo; (c) thêm **template fallback +
content guard** — Mission 1 chưa có lớp chặn rò rỉ sau khi LLM sinh văn bản;
(d) trace theo từng section thay vì cả tài liệu — phát hiện khi dựng assertion cho T01
(sửa trước khi chạy, T01 xác nhận), cộng hai lỗi bắt được ở lần chạy đầu (`KeyError` khi
nhóm theo giá trị; expectation T07 sai — engine đúng, test sai).

**③ Trường hợp dễ trả lời sai nhất, kiểm soát ra sao?** → **Metadata thiếu/sai của ngoại lệ**
(ví dụ D03 mất trường `approved_overrides`): hệ thống sẽ thấy hai giá trị cùng hiệu lực và
*phải* chuyển HR thay vì chọn 14 hoặc quay về 12 — logic này có ca riêng chờ chạy khi có
fixture sửa đổi; và **rò rỉ tài liệu hạn chế qua metadata** (tiêu đề, trace) — kiểm soát bằng
cách loại ngay ở tầng đọc quyền + guard chuỗi bị cấm chạy trên *toàn bộ response* và
ngữ cảnh gửi model (ca P01 assert cả ba vị trí).

## 7 · Nhật ký AI

Tôi dùng AI (OpenCode) để phân tích đề, dựng engine, viết test và rà soát từng ca chạy thật.
Quyết định số phận dữ liệu (khi nào kết luận, khi nào từ chối) **không** delegate cho LLM —
đó chính là giả thuyết của sản phẩm này. Prompt/trao đổi chính được tóm tắt trong 3 câu trả lời
bắt buộc; kết quả kiểm thử là bằng chứng chạy thật, không phải kỳ vọng.
