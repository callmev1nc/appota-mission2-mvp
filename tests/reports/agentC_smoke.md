# Agent C — Smoke: static, contract, phiên bản, llm, hiệu năng
- 2026-10-12 23:49 · live https://mission2mvp.vercel.app

| Nhóm | Check | Kết luận |
|---|---|---|
| Static | node --check app.js | PASS Debugger listening on ws://127.0.0.1:55174/dcce502e-86e4-41d6-8228-0167437ce532
 |
| Static | GET / contains 'MISSION 2' | PASS HTTP 200 |
| Static | GET / contains 'id="profiles"' | PASS HTTP 200 |
| Static | GET / contains 'id="btn-compare"' | PASS HTTP 200 |
| Static | GET /app.js contains 'askBody' | PASS HTTP 200 |
| Static | GET /app.js contains 'withCites' | PASS HTTP 200 |
| Static | GET /styles.css contains 'status-chip' | PASS HTTP 200 |
| API | health ok + evaluation_date | PASS {'ok': True, 'topic': 'annual_leave', 'dataset_id': 'mission |
| API | 4 hồ sơ, U04 có hr | PASS  |
| API | U01: 1 doc restricted, không id thật | PASS  |
| API | U04: doc ghi chú đọc được (không restricted) | PASS  |
| Contract | U01 general → ANSWER 14 | PASS status=ANSWER days=14 |
| Contract | U02 general → ANSWER 14 | PASS status=ANSWER days=14 |
| Contract | U03 general → CONFLICT None | PASS status=CONFLICT days=None |
| Contract | U04 general → ANSWER 14 | PASS status=ANSWER days=14 |
| Phiên bản | U02 2026-08-31 → 13 [D02#s1] | PASS 13 / ['D01#s3', 'D02#s1'] |
| Phiên bản | U02 2026-09-01 → 14 [D03#s1] | PASS 14 / ['D01#s3', 'D03#s1'] |
| Phiên bản | U02 2026-10-31 → 14 [D03#s1] | PASS 14 / ['D01#s3', 'D03#s1'] |
| Phiên bản | U02 2026-11-01 → 15 [D04#s1] | PASS 15 / ['D01#s3', 'D04#s1'] |
| Chuyên biệt | A05 notice-only: chỉ D01#s3, không trộn xung đột | PASS ANSWER ['D01#s3'] |
| Chuyên biệt | A06 cụm thủ tục: KT-01 + NF-01 + direct_manager | PASS {'request_route': 'direct_manager', 'request_form': 'KT-01', 'handover_form': 'N |
| Chuyên biệt | A07 data-limit + escalate HR An | PASS ANSWER_WITH_DATA_LIMIT escalate=HR An (giả lập) |
| LLM | mode gemini không key → SOURCE_ONLY + error=no_api_key | PASS status=SOURCE_ONLY err=no_api_key |
| LLM | mode auto không key → template fallback, giữ ANSWER | PASS status=ANSWER llm=unavailable_fallback_template |
| LLM | simulate llm_failure → SOURCE_ONLY | PASS SOURCE_ONLY |
| Hiệu năng | 5 request song song đều 200 + ANSWER | PASS 429ms wall |
| Frontend | toàn bộ ${...} đều qua esc()/withCites()/builder đã kiểm chứng (anti-XSS) | PASS clean |
| Hiệu năng | latency trung bình 333ms · worst 412ms (ask 2026-08-31) | PASS  |

## Latency

| Endpoint | ms |
|---|---|
| ask 2026-08-31 | 412 |
| ask 2026-11-01 | 407 |
| /api/health | 406 |
| /api/ask U03 | 401 |
| /api/profiles | 401 |
| /api/ask U01 | 399 |
| ask 2026-09-01 | 397 |
| /api/ask U04 | 394 |
| /api/ask U02 | 391 |
| ask 2026-10-31 | 391 |

**Tổng: 28/28 PASS**