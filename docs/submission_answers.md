# Bản thảo nộp portal — Mission 2

- **LINK GITHUB REPO:** https://github.com/callmev1nc/appota-mission2-mvp
- **LINK DEMO SẢN PHẨM:** https://mission2mvp.vercel.app
- **LINK YOUTUBE:** *(điền sau khi quay — kịch bản: `docs/video_script.md`)*

## TRÌNH BÀI BÀI LÀM (≥50 ký tự)

> MVP chứng minh phần quan trọng nhất: **bộ máy chọn bằng chứng** (quyền đọc → phạm vi đơn vị
> → hiệu lực theo ngày → ngoại lệ/thay thế khai báo), quy tắc trước và LLM chỉ diễn đạt sau.
> Chạy thử: mở https://mission2mvp.vercel.app, chọn hồ sơ U01–U04, bấm “Cùng câu hỏi — 2 người
> khác đơn vị” để thấy U01 trả lời 14 ngày với đủ nguồn, U03 báo CHƯA KẾT LUẬN (16 vs 18) và
> chuyển HR Bình. Chạy local: `pip install -r requirements.txt && uvicorn api.index:app --port 8000`.
> Kiểm thử thật: `python -X utf8 tests/run_tests.py --live https://mission2mvp.vercel.app`
> → 6 ĐẠT, 1 CHƯA ĐẠT theo thiết kế (hỏi số dư phép — MVP chưa có HRIS), 0 lỗi;
> chi tiết `tests/results.md`. Đối chiếu thêm **toàn bộ 24 ca oracle Mission 1** bằng
> `tests/reports/agentA_oracle.py` → 0 FAIL, cùng 2 pin kiểm thử độc lập (bảo mật:
> `agentB_security.py` 0 vấn đề; smoke/contract/latency: `agentC_smoke.py` 28/28 PASS).
> CI/CD GitHub Actions chạy mỗi push: gitleaks → 7 ca offline → deploy Vercel →
> kiểm thử lại trên bản deploy (token chỉ trong GitHub Secrets, không trong repo).
> Quyết định đã đổi so với Mission 1: thêm template fallback +
> content guard chặn rò rỉ, truy vết theo từng section thay vì cả tài liệu. Hạn chế đã biết:
> chưa SSO/HRIS, một chủ đề (nghỉ phép), dữ liệu giả lập 100%, LLM template là mặc định khi
> chưa set GEMINI_API_KEY. Repo public, không chứa API key hay dữ liệu thật.

## 3 câu hỏi bắt buộc

### ① Phần quan trọng nhất chọn hiện thực hóa? Vì sao nếu phần này hoạt động, hướng giải quyết khả thi?

> Tôi chọn **bộ máy chọn bằng chứng** (`app/engine.py`) — bước quyết định “trả lời nào được
> phép tồn tại”: lọc theo đọc quyền → phạm vi đơn vị của người hỏi → phê duyệt → hiệu lực tại
> ngày xét → resolve quan hệ ngoại lệ (`approved_overrides`) và thay thế (`replaces`), và
> **không kết luận** khi nhiều nguồn còn hiệu lực bất đồng.
>
> Tôi chọn phần này vì mọi tai nạn nghiêm trọng của bài toán đều xảy ra ở đây, không ở bước
> viết văn: trả lời sai đơn vị, dùng bản hết hiệu lực/bản nháp, chọn bừa khi mâu thuẫn, và lộ
> tài liệu hạn chế (kể cả chỉ metadata/tiêu đề). Nếu bước này đúng thì LLM trở thành chi tiết
> có thể thay thế: cùng một bộ nguồn đã chọn, có LLM, không có LLM hay LLM bị lỗi thì kết luận
> vẫn giữ nguyên — ca C04 (giả lập Gemini lỗi → chỉ hiện nguồn, không bịa) chứng minh trực tiếp
> tính khả thi đó. Và demo chạy được ngay cho thấy bằng chứng: cùng một câu hỏi, U01 nhận đủ
> căn cứ 14 ngày, U03 nhận “chưa kết luận” kèm hai nguồn và HR phụ trách.

### ② So với kế hoạch Mission 1, đã thay đổi quyết định/thiết kế nào? Điều gì khiến đổi?

> 1. **Từ kỳ vọng trên giấy sang chạy thật:** Mission 1 có 24 ca trạng thái `NOT_EXECUTED`.
>    Sản phẩm có **7 ca đại diện chạy thật** (6 ĐẠT, 1 CHƯA ĐẠT theo thiết kế) — và khi làm
>    CI/CD + kiểm thử đa tác tử, tôi đã đối chiếu **toàn bộ 24 ca oracle** bằng
>    `tests/reports/agentA_oracle.py`: **0 FAIL** (8 ca PASS+ — engine trích thêm nguồn hợp
>    lệ ngoài oracle, superset không mâu thuẫn), nhờ đó bắt và sửa thật được 6 lỗi
>    (rò metadata id, echo chuỗi bị cấm, validate question/date, phân loại “định mức/nhóm”,
>    escalate khi thiếu dữ liệu, tách marker HR khỏi phần quyền lợi).
> 2. **Kiến trúc một app Python → engine Python + Vercel + trang tĩnh:** để có link demo online
>    đúng yêu cầu, tôi tách engine (thuần, test được offline) khỏi API/giao diện. Điều kiện
>    thực tế (cần link `.vercel.app`, 3 ngày) buộc quyết định này.
> 3. **Thêm lớp template fallback + content guard** mà Mission 1 chưa có: đề bài coi “không lộ
>    thông tin ngoài quyền” là yêu cầu bắt buộc, nên ngoài quy tắc lọc, tôi thêm guard kiểm tra
>    chuỗi bị cấm và mã trích dẫn không thuộc tập nguồn ngay trên câu trả lời LLM sinh ra.
> 4. **Hai lỗi/thay đổi phát hiện khi chạy thật lần đầu** (chi tiết `tests/results.md`):
>    (i) engine crash `KeyError` khi nhóm các section theo giá trị — chạy bộ test lần đầu là
>    chết ngay, sửa bằng `setdefault`; (ii) **trace chuyển sang theo từng section thay vì cả
>    tài liệu** — phát hiện khi dựng assertion cho T01: nếu gộp theo tài liệu thì D01 hiện
>    “loại (bị D03 thay)” trong khi D01 vẫn là nguồn của báo trước/quy trình — dữ liệu đúng
>    nhưng hiển thị mâu thuẫn. Ngoài ra ca T07 ban đầu tôi **kỳ vọng sai** (2 facts) trong khi
>    engine trả 4 facts đúng cho U02 — tôi sửa test chứ không sửa engine: phân biệt được
>    “sản phẩm sai” với “kỳ vọng sai” cũng là điều bộ kiểm thử này kiểm được.
> 5. **Bỏ ý định làm đẹp giao diện sâu** — đề nói rõ không cần; tôi giữ UI tối giản, dành
>    phần lớn thời gian cho engine + kiểm thử.

### ③ Trường hợp nào dễ trả lời sai / dùng sai tri thức nhất? Phát hiện và kiểm soát thế nào?

> **(a) Metadata ngoại lệ thiếu hoặc sai** — dữ liệu nguy hiểm nhất vì sai ở *nguồn* mà hệ
> thống vẫn “tự tin”: nếu D03 mất trường `approved_overrides`, engine sẽ thấy hai định mức cùng
> hiệu lực ở An và **phải** báo CONFLICT thay vì âm thầm chọn 14 (hoặc “mới hơn thắng”, hoặc
> quay về 12). Kiểm soát: quy tắc chỉ tôn trọng quan hệ khai báo có `approved_by` + phạm vi;
> và đã **chạy thật** bằng bản sao dataset thiếu `approved_overrides` (C02 trong
> `agentA_oracle.py`): engine ra CONFLICT với đúng hai nguồn D01#s2 + D03#s1, chuyển HR An,
> không kết luận — đúng như thiết kế. README ghi rõ “dữ liệu sai → kết quả sai dù quy tắc đúng”.
>
> **(b) Rò rỉ tài liệu hạn chế qua metadata/trace** — câu trả lời có thể sạch mà response vẫn
> lộ “D09 tồn tại” qua danh sách trace. Kiểm soát: chặn **ngay ở tầng đọc quyền** (tài liệu
> không đọc được thì không id, không tiêu đề, không reason — response chỉ ghi *số lượng* bị
> loại); guard chạy trên **toàn bộ response** và **ngữ cảnh gửi model**; ca P01 assert cả ba
> vị trí (câu trả lời, trích dẫn, context_sections) và trả về rỗng.
>
> **(c) Prompt injection đổi quyền** (X04): câu hỏi là dữ liệu — phân loại yêu cầu nội bộ bị
> gạt bỏ khi đi kèm yêu cầu quyền lợi, danh tính lấy từ hồ sơ đã chọn, không suy từ câu chữ.
> Phát hiện: 7 ca chính có 2 ca adversarial/rò rỉ chạy cả offline lẫn trên bản deploy, cộng
> battery bảo mật độc lập (`agentB_security.py`): 4 câu hỏi dò tài liệu hạn chế × 3 hồ sơ
> không-HR → 0 chuỗi cấm, X01–X04/P04 + payload hỏng (question số, ngày sai, hồ sơ lạ)
> không leak và không 500, quét gitleaks cả lịch sử commit → sạch. CI chạy lại toàn bộ
> này trên mỗi push trước khi deploy.
