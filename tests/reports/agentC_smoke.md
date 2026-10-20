# Agent C — Smoke: static, contract, phiên bản, llm, hiệu năng
- 2026-10-20 21:14 · live https://mission2mvp.vercel.app

| Nhóm | Check | Kết luận |
|---|---|---|
| Static | node --check app.js | PASS Debugger listening on ws://127.0.0.1:58132/a9b59d4b-cf08-4521-8f86-1cfe59ba50ff
 |
| Static | GET / contains 'MISSION 3' | PASS HTTP 200 |
| Static | GET / contains 'id="profiles"' | PASS HTTP 200 |
| Static | GET / contains 'id="btn-compare"' | PASS HTTP 200 |
| Static | GET / contains 'id="timeline-list"' | PASS HTTP 200 |
| Static | GET / contains 'id="viewer"' | PASS HTTP 200 |
| Static | GET /app.js contains 'askBody' | PASS HTTP 200 |
| Static | GET /app.js contains 'withCites' | PASS HTTP 200 |
| Static | GET /app.js contains 'openViewer' | PASS HTTP 200 |
| Static | GET /app.js contains 'loadTimeline' | PASS HTTP 200 |
| Static | GET /styles.css contains 'status-chip' | PASS HTTP 200 |
| Static | GET /styles.css contains 'st-current' | PASS HTTP 200 |
| API | health ok + evaluation_date | PASS {'ok': True, 'topic': 'annual_leave', 'dataset_id': 'mission |
| API | 5 hồ sơ (M3 thêm U05 4-tầng), U05 có đường dẫn 4 tầng, U04 có hr | PASS  |
| API | U01: 1 doc restricted, không id thật | PASS  |
| API | U04: doc ghi chú đọc được (không restricted) | PASS  |
| Contract | U01 general → ANSWER 14 | PASS status=ANSWER days=14 |
| Contract | U02 general → ANSWER 14 | PASS status=ANSWER days=14 |
| Contract | U03 general → CONFLICT None | PASS status=CONFLICT days=None |
| Contract | U04 general → ANSWER 14 | PASS status=ANSWER days=14 |
| Contract | U05 general → ANSWER 13 | PASS status=ANSWER days=13 |
| Phiên bản | U02 2026-08-31 → 13 [D02#s1] | PASS 13 / ['D01#s3', 'D02#s1'] |
| Phiên bản | U02 2026-09-01 → 14 [D03#s1] | PASS 14 / ['D01#s3', 'D03#s1'] |
| Phiên bản | U02 2026-10-31 → 14 [D03#s1] | PASS 14 / ['D01#s3', 'D03#s1'] |
| Phiên bản | U02 2026-11-01 → 15 [D04#s1] | PASS 15 / ['D01#s3', 'D04#s1'] |
| Chuyên biệt | A05 notice-only: chỉ D01#s3, không trộn xung đột | PASS ANSWER ['D01#s3'] |
| Chuyên biệt | A06 cụm thủ tục: KT-01 + NF-01 + direct_manager | PASS {'request_route': 'direct_manager', 'request_form': 'KT-01', 'handover_form': 'N |
| Chuyên biệt | A07 data-limit + escalate HR An | PASS ANSWER_WITH_DATA_LIMIT escalate=HR An (giả lập) |
| LLM | mode auto không key → template fallback, giữ ANSWER | PASS status=ANSWER llm=unavailable_fallback_template |
| LLM | mode gemini không dùng được → SOURCE_ONLY trung thực (không giả vờ AI) | PASS status=SOURCE_ONLY err=TimeoutError |
| LLM | simulate llm_failure → SOURCE_ONLY | PASS SOURCE_ONLY |
| Hiệu năng | 5 request song song đều 200 + ANSWER | PASS 483ms wall |
| Frontend | toàn bộ ${...} đều qua esc()/withCites()/builder đã kiểm chứng (anti-XSS) | PASS clean |
| Hiệu năng | latency trung bình 304ms · worst 453ms (/api/profiles) — đo khi nóng | PASS  |

## Latency

| Endpoint | ms |
|---|---|
| /api/profiles | 453 |
| /api/ask U05 | 439 |
| ask 2026-11-01 | 426 |
| ask 2026-10-31 | 425 |
| /api/ask U04 | 417 |
| /api/health | 412 |
| /api/ask U03 | 407 |
| /api/ask U02 | 404 |
| /api/ask U01 | 402 |
| ask 2026-08-31 | 401 |

Lạnh (warm-up, không tính vào check): /=357ms, /app.js=180ms, /styles.css=186ms, /api/health=392ms

**Tổng: 34/34 PASS**