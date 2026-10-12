# Agent C — Smoke: static, contract, phiên bản, llm, hiệu năng
- 2026-10-13 00:07 · live https://mission2mvp.vercel.app

| Nhóm | Check | Kết luận |
|---|---|---|
| Static | node --check app.js | PASS Debugger listening on ws://127.0.0.1:52929/75394e00-1f26-4b00-840b-2e916f3f01fe
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
| LLM | auto + key → Gemini thật (used, ok), ANSWER, đủ 6 citations | PASS status=ANSWER llm=ok cites=6 |
| LLM | gemini tường minh + key → used=True (hoặc rate-limit free tier → degrade trung thực) | PASS status=ANSWER llm=ok err=None |
| LLM | văn bản AI chỉ trích citation thuộc tập nguồn (content guard) | PASS ngoài tập: [] |
| LLM | simulate llm_failure → SOURCE_ONLY | PASS SOURCE_ONLY |
| Hiệu năng | 5 request song song đều 200 + ANSWER | PASS 452ms wall |
| Frontend | toàn bộ ${...} đều qua esc()/withCites()/builder đã kiểm chứng (anti-XSS) | PASS clean |
| Hiệu năng | latency trung bình 378ms · worst 603ms (/) | PASS  |

## Latency

| Endpoint | ms |
|---|---|
| / | 603 |
| /api/ask U01 | 456 |
| /app.js | 442 |
| /styles.css | 425 |
| /api/profiles | 410 |
| ask 2026-10-31 | 404 |
| ask 2026-11-01 | 402 |
| /api/ask U03 | 400 |
| /api/documents U01 | 395 |
| /api/ask U04 | 394 |

**Tổng: 29/29 PASS**