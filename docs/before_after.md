# Mission 3 — Before → After (bằng chứng đối chiếu)

Mốc Before: tag `m2-mvp` (commit `b8b1e0f`) · Sau: nhánh `mission3` → merge `main`.
Mọi dòng dưới đây đều gọi được lệnh lại và ra kết quả như ghi (không phải "kỳ vọng").

## 1. Đối chiếu năng lực theo 5 yêu cầu Lớp 1 của đề

| # | Yêu cầu | Trước (M2, tag m2-mvp) | Sau (M3, mission3) | Bằng chứng chạy lại được |
|---|---|---|---|---|
| 1 | Phân biệt phiên bản & thời điểm có hiệu lực | Lọc hiệu lực có, nhưng user chỉ thấy trong trace JSON; không biết bản nào là "hiện hành của tôi" | Bảng **timeline** theo hồ sơ + ngày xét: D02 (hết 31/8 → hết hiệu lực) · D03 (→31/10 → đang) · D11 (đang, cấp Phòng) · D04/D12 (từ 01/11 → chưa tới); D10 nháp đánh dấu "nháp" | `GET /api/timeline?profile_id=U05` · T11-BOUND-11-11 · Agent D (TIMELINE) |
| 2 | Kiểm soát quyền theo bối cảnh | Lọc quyền trong engine (T03-P01 ĐẠT) | Giữ nguyên lõi + mở rộng sang 2 API kiểm chứng mới: source/timeline đều lọc quyền trước khi trả; chặn quyền → 404 khẳng không xác nhận tồn tại | `/api/source?profile_id=U01&section_id=D09#s1` → 404 ≡ mã ZZZ → 404 (Agent D: T10) |
| 3 | Xử lý mâu thuẫn giữa nhiều nguồn/cấp | Băm cặp cùng cấp (D05 16 vs D06 18) → CHƯA KẾT LUẬN, không giải thích vì sao không ai được chọn | Thêm ca **đa cấp** (D11 13 vs D12 16 — Phòng vs Nhóm) → vẫn không tự chọn + **giải thích rõ**: cùng hiệu lực, chưa khai báo quan hệ nào, cần chủ sở hữu/HR phê duyệt quan hệ; đối chiếu giá trị-nguồn-phiên bản-cấp | T09-EDGE-CONFLICT · T02-A03 giữ nguyên ĐẠT |
| 4 | Từ chối / thể hiện khi chưa đủ căn cứ | 8 trạng thái đã chứng minh | Giữ nguyên + mọi KẾT LUẬN/CONFLICT có chuỗi giải thích đi kèm; template CONFLICT sinh note "căn cứ thiếu" | T01–T07 tái chạy đúng; response T09 chứa "chưa khai báo quan hệ replaces/approved_overrides" |
| 5 | Cho người dùng kiểm chứng tài liệu được sử dụng | Không có — bấm `[Dxx#sx]` không làm gì | Bấm chip ở 3 vị trí → nguyên văn đoạn + phiên bản + hiệu lực + chủ sở hữu; tài liệu ngoài quyền không bao giờ mở được | T10 trong Agent D (source_view 6 check) |

## 2. Đối chiếu số liệu kiểm thử (theo từng pin)

| Pin | M2 (m2-mvp) | M3 (mission3) | Ghi chú |
|---|---|---|---|
| run_tests.py | 7 ca: 6 ĐẠT · 1 LIMITED · 0 FAIL | **10 ca: 9 PASS · 1 LIMITED · 0 FAIL** | +3 ca mới (T08/T09/T11), T01–T07 giữ nguyên kỳ vọng |
| Oracle 24 ca (Agent A) | 16 PASS · 8 PASS+ · 0 FAIL | **16 PASS · 8 PASS+ · 0 FAIL** | so sánh thẳng (kỳ vọng không đổi) |
| Agent B bảo mật | 0 issues | **0 issues** | gitleaks lịch sử vẫn xanh sau M3 |
| Agent C smoke | 28/28 PASS (avg 333ms) | **34/34 PASS** (avg ~15ms local / chưa đo prod) | +view+timeline+needle M3 UI |
| Agent D M3 | — | **12/12 PASS (offline)** · live chạy sau deploy | mới hoàn toàn |

## 3. Trước/Sau theo từng lệnh (chạy lại được)

**Kiểm chứng trích dẫn — Before:** UI M2 không có đường nào xem nguyên văn; trích dẫn chỉ là chữ trong JSON. **After:**

```
GET /api/source?profile_id=U01&section_id=D03#s1
→ 200 {section:{text:"Định mức tại Công ty An là 14 ngày...",...},
       doc:{version:"2.0", effective:[2026-09-01, 2026-10-31], owner,...},
       with_profile:{visibility:"included"}}
GET /api/source?profile_id=U01&section_id=D09#s1
→ 404 {"error":"section_not_available"}     # không xác nhận tồn tại
GET /api/source?profile_id=U01&section_id=ZZZ
→ 404 {"error":"section_not_available"}     # giống hệt: không dò được dữ liệu
```

**Đa cấp + giải thích — After (từ run_tests T08):**

```
U05 (G → An → Kinh doanh) hỏi 07/10 → ANSWER 13 [D11#s1]
trace.chains["annual_entitlement_days"]:
  D01#s2 • bỏ khỏi bằng chứng • quan hệ approved_overrides khai báo trong D11 ...
  D03#s1 • bỏ khỏi bằng chứng • quan hệ approved_overrides khai báo trong D11 ...
  D11#s1 • (Phòng Kinh doanh, v1.0) còn đứng • giá trị 13
  KẾT LUẬN D11#s1 = 13 — thắng theo quan hệ khai báo, không phải vì «mới hơn»
```

**Mâu thuẫn đa cấp — After (T09: U05 hỏi 20/11):** CHƯA KẾT LUẬN 13 [D11#s1] vs 16 [D12#s1] + note:
"Các nguồn D11#s1, D12#s1 đang đồng thời trong thời hạn hiệu lực và chưa khai báo quan hệ
replaces/approved_overrides giữa các bản — không nguồn nào có căn cứ gỡ nguồn khác. Cần chủ
sở hữu/HR có thẩm quyền ban hành quan hệ quản lý nội dung..." + escalate HR An.

**Timeline — After:** bảng lịch sử 7 tài liệu của U05 (chỉ tài liệu được phép), đổi ngày xét ngay trên UI, trạng thái tính theo ngày xét, không phải ngày hệ thống.

## 4. Regression cam kết

- T01–T07 (7 ca Mission 2) **không đổi một kỳ vọng nào** trong `tests/cases.json` — tái chạy sau M3: 9/10 PASS + 1 LIMITED (T06 vẫn LIMITED theo thiết kế như M2).
- Oracle 24 ca Mission 1: y hệt M2 (16/8/0) — dữ liệu v2 không phá kỳ vọng cũ nhờ thiết kế tài liệu mới nằm ngoài đường dẫn đơn vị của 4 hồ sơ cũ (Phòng Kinh doanh/B2B chỉ phục vụ hồ sơ U05).
- Agent B (bảo mật) & A (oracle) tái chạy 0 rác; Agent C mở rộng needle UI M3 (tất cả PASS).
