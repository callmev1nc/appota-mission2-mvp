# Kịch bản video Mission 3 (≤ 5 phút)

> Sản xuất bằng pipeline cũ của Mission 2 (`video_out\`: capture.js + tts_vbee.py + assemble.py).
> Mỗi cảnh = một màn hình đã ghi; giọng TTS tiếng Việt; tổng thời lượng mục tiêu 4:30–4:50.
> Kịch bản khớp với các nút demo có sẵn trong UI (`⛓ T08`, `⚔️ T09`, `📅 T11`, chip `[Dxx#sx]`, panel timeline).

| # | Thời lượng | Màn hình | Tác động trên màn hình | Lời thoại (TTS) |
|---|---|---|---|---|
| 1 | 0:00–0:25 | GitHub repo | scroll đến tag `m2-mvp`, nhánh `mission3`, mở diff so sánh | "Nhiệm vụ 3 tiếp tục ngay trên kho dữ liệu Nhiệm vụ 2, không làm lại. Tag m2-mvp đánh dấu trạng thái trước khi cải tiến — mọi so sánh trước/sau đều kiểm tra trên git." |
| 2 | 0:25–1:05 | Demo — U01 (nền M2) | bấm chip [D03#s1] → dialog viewer: nguyên văn + phiên bản 2.0 + hiệu lực | "Yêu cầu kiểm tra trích dẫn. Ở Nhiệm vụ 2, chip [D03#s1] chỉ là chữ. Bây giờ nhấn chip sẽ mở nguyên văn của đoạn đó, phiên bản tài liệu, thời hạn hiệu lực và người sở hữu — bên trong quyền của hồ sơ đang chọn." |
| 3 | 1:05–1:50 | Demo — U05 (07/10) | bấm nút mẫu "T08 · U05" → câu trả lời | "Yêu cầu đa cấp. Hồ sơ U05 ở Phòng Kinh doanh: Định mức Đoàn là 12, Công ty An là 14, Phòng Kinh doanh ban hành riêng 13 — Tài liệu đã khai báo quan hệ, đã phê duyệt. Hệ thống kết luận 13 ngày và giải thích từng bước: Tài liệu nào bị loại vì quan hệ khai báo nào. Không phải vì 'mới hơn' hay 'cấp thấp hơn'." |
| 4 | 1:50–2:30 | Panel "Vì sao" | scroll xuống panel "Vì sao kết luận như vậy" | "Toàn bộ chuỗi lý do nằm ngay dưới, liền kết — bất kỳ ai cũng kiểm tra được, không cần đọc JSON." |
| 5 | 2:30–3:20 | Demo — U05 (20/11) | bấm "T09 · ngày 20/11" → trạng thái CHƯA KẾT LUẬN | "Mâu thuẫn đa cấp. Ngày 20/11, định mức nhóm B2B 16 ngày có hiệu lực nhưng Tài liệu không khai báo cấu trúc thay thế. Hệ thống từ chối kết luận: Trình bày đối chiếu song song 13 so với 16, ghi rõ cơ sở thiếu — 'chưa khai báo quan hệ thay thế/phê duyệt', và chuyển giao cho HR An. Giống Nhiệm vụ 2: không tự chọn." |
| 6 | 3:20–3:55 | Timeline | mở "Lịch sử phiên bản & hiệu lực"; đổi ngày xét 31/10 → 01/11 | "Yêu cầu phiên bản + thời điểm hiệu lực: bảng lịch sử theo hồ sơ, trạng thái tính theo ngày xét. Chuyển ngày 31/10 sang 01/11 tức D04 kích hoạt, câu trả lời đổi từ 14 ngày sang 15 ngày đúng như ngày xét." |
| 7 | 3:55–4:30 | tests/results.md + Agent D + CI | scroll kết quả; mở tab Actions | "Bằng chứng: 10 chế độ thử nghiệm — 6 chế độ hồi quy giữ nguyên kỳ vọng của Nhiệm vụ 2, cộng với 3 chế độ mới; Agent D 12/12 bao gồm 404 không xác nhận và khung Change Request: bổ sung dữ liệu mới là chạy, không cần sửa mã lõi. CI/CD: kiểm tra offline → deploy → kiểm tra lại trên bản triển khai thực tế + quét rò rỉ canary." |
| 8 | 4:30–4:50 | README — 3 câu bắt buộc + hạn chế | scroll mục Hạn chế + Ba câu hỏi | "Số dư phép vẫn chưa trả lời được vì chưa có HRIS — ghi rõ trong phần hạn chế. Tất cả dữ liệu đều giả lập. Nguồn: callmev1nc/appota-mission2-mvp." |

## Ghi chú sản xuất

- Capture dùng `video_out/capture.js` (Playwright) — thêm các bước: bấm chip mở dialog, bấm nút mẫu T08/T09, đổi ngày xét, mở tab Actions.
- TTS `video_out/tts_vbee.py` không đổi; mỗi cảnh là một file audio độc lập để dễ ghi lại từng phần.
- `video_out/assemble.py` không đổi; thêm tiêu đề cảnh cho cảnh 2 ("M3 · Kiểm chứng trích dẫn") và cảnh 5 ("M3 · Mâu thuẫn đa cấp").
- Kiểm tra cuối cùng: tổng thời lượng ≤ 5:00; ổn định âm lượng ~ -14 LUFS; phụ đề .srt sinh từ kịch bản TTS.
