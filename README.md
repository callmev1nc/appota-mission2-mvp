# Mission 2 — Hiện thực hóa: trả lời đúng tri thức theo đúng người hỏi

**Demo:** https://mission2mvp.vercel.app · **Repo:** public, không chứa API key / mật khẩu / dữ liệu thật.
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

Không cần key nào để chạy. Có key Gemini free tier thì set `GEMINI_API_KEY`
(xem `.env.example`); không set → hệ thống dùng template bám nguyên văn nguồn.

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
4. **LLM template** là mặc định khi chưa set `GEMINI_API_KEY`; Gemini free tier có rate limit.
5. **Chưa kiểm thử adversarial rộng** — 7 ca tối thiểu của Mission 2, bộ 24 ca gốc là kỳ vọng thiết kế.
6. **Prompt injection** được kiểm bằng guard + test mẫu, chưa red-team.

## 6 · Ba câu hỏi bắt buộc

**① Phần quan trọng nhất chọn chứng minh?** → Bộ máy chọn bằng chứng
(`app/engine.py`): lọc đọc quyền → phạm vi → hiệu lực → resolve ngoại lệ/thay thế →
kết luận hoặc từ chối. Nếu phần này đúng, mọi lỗi “trả lời sai/ngộ độc” đều chặn được
*trước* khi LLM diễn đạt — nên hướng giải pháp khả thi: LLM có thể thay thế, cải tiến hoặc
tắt mà kết luận không đổi (ca C04 chứng minh điều đó).

**② Đổi gì so với Mission 1?** → (a) Từ “24 ca là kỳ vọng trên giấy” thành **7 ca chạy thật**
và cả 24 fixture đều giữ nguyên làm oracle; (b) thiết kế “một app Python” thành
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
