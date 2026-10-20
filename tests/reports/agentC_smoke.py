#!/usr/bin/env python3
"""Agent C — smoke: static assets, API contract, date boundaries, llm modes, latency.

Chạy: python -X utf8 tests/reports/agentC_smoke.py
Xuất: tests/reports/agentC_smoke.md
"""
from __future__ import annotations

import concurrent.futures as cf
import datetime as dt
import json
import re
import subprocess
import time
import urllib.request

BASE = "https://mission2mvp.vercel.app"
REPORT = "tests/reports/agentC_smoke.md"


def req(path: str, payload: dict | None = None) -> tuple[int, dict | str, float]:
    t0 = time.perf_counter()
    if payload is None:
        r = urllib.request.Request(BASE + path)
    else:
        r = urllib.request.Request(
            BASE + path, data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(r, timeout=30) as resp:
            body = resp.read().decode()
            code = resp.status
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        code = e.code
    ms = (time.perf_counter() - t0) * 1000
    try:
        return code, json.loads(body), ms
    except Exception:
        return code, body, ms


def main() -> int:
    rows: list[tuple[str, str, str]] = []  # (group, check, verdict)
    lat: list[tuple[str, float]] = []
    issues: list[str] = []

    def check(group: str, name: str, ok: bool, detail: str = ""):
        rows.append((group, name, ("PASS " if ok else "FAIL ") + detail))
        if not ok:
            issues.append(f"{group} · {name} · {detail}")

    # 1 · static
    out = subprocess.run(["node", "--check", "app.js"], capture_output=True, text=True)
    check("Static", "node --check app.js", out.returncode == 0, out.stderr.strip()[:80])
    for path, needle in [("/", "MISSION 3"), ("/", 'id="profiles"'), ("/", 'id="btn-compare"'),
                         ("/", 'id="timeline-list"'), ("/", 'id="viewer"'),
                         ("/app.js", "askBody"), ("/app.js", "withCites"),
                         ("/app.js", "openViewer"), ("/app.js", "loadTimeline"),
                         ("/styles.css", "status-chip"), ("/styles.css", "st-current")]:
        code, body, ms = req(path)
        lat.append((path, ms))
        check("Static", f"GET {path} contains {needle!r}", code == 200 and needle in str(body), f"HTTP {code}")

    # 2 · health & profiles
    code, j, ms = req("/api/health"); lat.append(("/api/health", ms))
    check("API", "health ok + evaluation_date", code == 200 and j.get("ok") and j.get("evaluation_date") == "2026-10-07", str(j)[:60])
    code, j, ms = req("/api/profiles"); lat.append(("/api/profiles", ms))
    profs = j.get("profiles", [])
    check("API", "5 hồ sơ (M3 thêm U05 4-tầng), U05 có đường dẫn 4 tầng, U04 có hr",
          len(profs) == 5 and "hr" in next(p["read_roles"] for p in profs if p["id"] == "U04")
          and len(next(p["unit_path"] for p in profs if p["id"] == "U05")) == 4)

    # 3 · documents panel
    code, j, ms = req("/api/documents?profile_id=U01"); lat.append(("/api/documents U01", ms))
    restricted = [d for d in j["documents"] if d.get("visibility") == "restricted"]
    check("API", "U01: 1 doc restricted, không id thật", len(restricted) == 1 and restricted[0]["id"] == "(bị hạn chế)")
    code, j, ms = req("/api/documents?profile_id=U04")
    vis4 = {d["id"]: d["visibility"] for d in j["documents"]}
    check("API", "U04: doc ghi chú đọc được (không restricted)", "restricted" not in vis4.values())

    # 4 · general question 4 hồ sơ
    Q = "Quy định nghỉ phép của tôi như thế nào?"
    exp4 = {"U01": ("ANSWER", 14, ["D07#s1", "D08#s1"]),
            "U02": ("ANSWER", 14, ["D01#s4"]),
            "U03": ("CONFLICT", None, ["D05#s1", "D06#s1"]),
            "U04": ("ANSWER", 14, []),
            "U05": ("ANSWER", 13, ["D11#s1"])}
    for u, (est, edays, ecite) in exp4.items():
        code, j, ms = req("/api/ask", {"profile_id": u, "question": Q, "llm": "template"})
        lat.append((f"/api/ask {u}", ms))
        days = j.get("facts", {}).get("annual_entitlement_days")
        cites = {c["section_id"] for c in j.get("citations", [])}
        ok = j.get("status") == est and (edays is None or days == edays) and set(ecite) <= cites
        check("Contract", f"{u} general → {est} {edays}", ok, f"status={j.get('status')} days={days}")

    # 5 · date boundaries (U02)
    for date, days, src in [("2026-08-31", 13, "D02#s1"), ("2026-09-01", 14, "D03#s1"),
                            ("2026-10-31", 14, "D03#s1"), ("2026-11-01", 15, "D04#s1")]:
        code, j, ms = req("/api/ask", {"profile_id": "U02", "question": "Quy định định mức của tôi là gì?", "date": date, "llm": "template"})
        lat.append((f"ask {date}", ms))
        cites = {c["section_id"] for c in j.get("citations", [])}
        check("Phiên bản", f"U02 {date} → {days} [{src}]", j.get("facts", {}).get("annual_entitlement_days") == days and src in cites,
              f"{j.get('facts', {}).get('annual_entitlement_days')} / {sorted(cites)}")

    # 6 · special queries
    code, j, ms = req("/api/ask", {"profile_id": "U03", "question": "Tôi cần báo trước bao nhiêu ngày làm việc khi xin nghỉ?", "llm": "template"})
    cites = {c["section_id"] for c in j.get("citations", [])}
    check("Chuyên biệt", "A05 notice-only: chỉ D01#s3, không trộn xung đột", j.get("status") == "ANSWER" and cites == {"D01#s3"}, f"{j.get('status')} {sorted(cites)}")

    code, j, ms = req("/api/ask", {"profile_id": "U01", "question": "Tôi ở nhóm Nền tảng, cần dùng biểu mẫu nào và gửi ai?", "llm": "template"})
    f = j.get("facts", {})
    check("Chuyên biệt", "A06 cụm thủ tục: KT-01 + NF-01 + direct_manager",
          f.get("request_form") == "KT-01" and f.get("handover_form") == "NF-01" and f.get("request_route") == "direct_manager", str(f)[:80])

    code, j, ms = req("/api/ask", {"profile_id": "U02", "question": "Bộ dữ liệu có biểu mẫu nghỉ phép riêng của phòng Kế toán không? Tôi nên gửi ai?", "llm": "template"})
    check("Chuyên biệt", "A07 data-limit + escalate HR An",
          j.get("status") == "ANSWER_WITH_DATA_LIMIT" and j.get("escalate_to") == "HR An (giả lập)" and "request_form" in j.get("missing_keys", []),
          f"{j.get('status')} escalate={j.get('escalate_to')}")

    # 7 · llm modes — hai nhánh theo môi trường:
    #   CÓ key (demo production): Gemini diễn đạt thật; content guard chạy trên văn bản AI
    #   KHÔNG key / rate-limit free tier: auto → template fallback giữ ANSWER;
    #                                     gemini tường minh → SOURCE_ONLY trung thực (không giả vờ AI)
    code, j, ms = req("/api/ask", {"profile_id": "U01", "question": Q, "llm": "auto"})
    llm = j.get("answer", {}).get("llm", {})
    has_key = bool(llm.get("used")) and llm.get("error") != "no_api_key"
    if has_key:
        check("LLM", "auto + key → Gemini thật (used, ok), ANSWER, đủ 6 citations",
              j.get("status") == "ANSWER" and llm.get("used")
              and llm.get("status") == "ok" and len(j.get("citations", [])) == 6,
              f"status={j.get('status')} llm={llm.get('status')} cites={len(j.get('citations', []))}")
        code, j, ms = req("/api/ask", {"profile_id": "U01", "question": Q, "llm": "gemini"})
        llm = j.get("answer", {}).get("llm", {})
        err = str(llm.get("error") or "")
        transient = (not llm.get("used")) and (
            err in ("http_429", "http_503", "URLError", "TimeoutError")
            or err.endswith("Error"))
        check("LLM", "gemini tường minh + key → used=True (hoặc rate-limit free tier → degrade trung thực)",
              (j.get("status") == "ANSWER" and llm.get("used") and llm.get("status") == "ok")
              or (transient and j.get("status") == "SOURCE_ONLY"),
              f"status={j.get('status')} llm={llm.get('status')} err={llm.get('error')}")
        ai_cites = set(re.findall(r"D\d{2}#s\d+", j["answer"]["text"]))
        allowed = {c["section_id"] for c in j["citations"]}
        check("LLM", "văn bản AI chỉ trích citation thuộc tập nguồn (content guard)",
              ai_cites <= allowed, f"ngoài tập: {sorted(ai_cites - allowed)}")
    else:
        check("LLM", "mode auto không key → template fallback, giữ ANSWER",
              j.get("status") == "ANSWER" and not llm.get("used")
              and "fallback" in str(llm.get("status")),
              f"status={j.get('status')} llm={llm.get('status')}")
        code, j, ms = req("/api/ask", {"profile_id": "U01", "question": Q, "llm": "gemini"})
        llm = j.get("answer", {}).get("llm", {})
        check("LLM", "mode gemini không dùng được → SOURCE_ONLY trung thực (không giả vờ AI)",
              j.get("status") == "SOURCE_ONLY" and not llm.get("used"),
              f"status={j.get('status')} err={llm.get('error')}")
    code, j, ms = req("/api/ask", {"profile_id": "U02", "question": Q, "llm": "gemini", "simulate": ["llm_failure"]})
    check("LLM", "simulate llm_failure → SOURCE_ONLY", j.get("status") == "SOURCE_ONLY", str(j.get("status")))

    # 8 · concurrency
    t0 = time.perf_counter()
    with cf.ThreadPoolExecutor(5) as ex:
        results = list(ex.map(lambda _: req("/api/ask", {"profile_id": "U01", "question": Q, "llm": "template"}), range(5)))
    ok5 = all(c == 200 and j.get("status") == "ANSWER" for c, j, _ in results)
    check("Hiệu năng", "5 request song song đều 200 + ANSWER", ok5, f"{(time.perf_counter()-t0)*1000:.0f}ms wall")

    # 9 · XSS heuristic: quét MỌI biểu thức ${...} trong app.js (kể cả trong
    # template được gán vào innerHTML gián tiếp qua resultCard) — mỗi biểu thức
    # chứa dữ liệu động phải đi qua esc()/withCites( hoặc là join(mảng đã escape).
    js = open("app.js", encoding="utf-8").read()

    def inner_exprs(s: str) -> list[str]:
        out = []
        for m in re.finditer(r"\$\{", s):
            d, k = 1, m.end()
            while k < len(s) and d:
                if s[k] == "{":
                    d += 1
                elif s[k] == "}":
                    d -= 1
                k += 1
            out.append(s[m.end():k - 1])
        return out

    def builder_ok(name: str) -> bool:
        # biến HTML dựng sẵn: mọi gán của nó phải chứa esc(/withCites( trong 600 ký tự
        return any(
            "esc(" in js[m.end():m.end() + 600]
            or "withCites(" in js[m.end():m.end() + 600]
            for m in re.finditer(rf"(?<![\w.$]){re.escape(name)}\s*=", js)
        )

    def length_expr(e: str) -> bool:
        return ".length" in e and re.fullmatch(r"[\w$?.\s|[\](){}]+", e) is not None

    def expr_safe(e: str, depth: int = 0, line_txt: str = "") -> bool:
        # ngữ cảnh không phải innerHTML → an toàn: gán textContent (DOM text),
        # ném Error (điểm bắt lỗi luôn esc()), chuỗi URL api(/fetch( (đã encode)
        line_safe = any(
            t in line_txt for t in ("textContent", "new Error(", "api(", "fetch("))
        if depth > 5:
            return False
        if "esc(" in e or "withCites(" in e or ".join(" in e:
            return True
        es = e.strip()
        if length_expr(es):  # .length luôn là số
            return True
        if re.fullmatch(r"[A-Za-z_$][\w$]*", es):  # biến dựng sẵn đã kiểm chứng
            return builder_ok(es) or line_safe
        if re.fullmatch(r'[\w.]+\s*\?\s*"[^"{}]*"\s*:\s*"[^"{}]*"', es):  # ternary nhãn tĩnh
            return True
        inners = inner_exprs(e)
        if not inners:
            return ("." not in e and "(" not in e) or line_safe
        # composite (ternary có nhánh template): gỡ inner + text template,
        # phần code còn lại chỉ được là điều kiện length/biến đã escape + toán tử tĩnh
        rest = e
        for _ in inners:
            j = rest.find("${")
            k, d = j + 2, 1
            while d:
                if rest[k] == "{":
                    d += 1
                elif rest[k] == "}":
                    d -= 1
                k += 1
            rest = rest[:j] + rest[k:]
            if not expr_safe(_, depth + 1):
                return False
        rest = re.sub(r"`[^`]*`", " ", rest)
        rest = re.sub(r'"[^"]*"', "S", rest)
        if "?" in rest:
            cond, branches = rest.split("?", 1)
            c = cond.strip()
            ok_cond = (not c) or length_expr(c) or (
                bool(re.fullmatch(r"[A-Za-z_$][\w$]*", c)) and builder_ok(c))
            words_left = re.sub(r"\bS\b", "", branches)
            return ok_cond and not re.search(r"[A-Za-z_][\w$]*", words_left)
        return re.fullmatch(r"[\s?:,()\[\]{}+*/|&<>=!.S-]*", rest) is not None

    sinks = []
    for m in re.finditer(r"\$\{", js):
        d, k = 1, m.end()
        while k < len(js) and d:
            if js[k] == "{":
                d += 1
            elif js[k] == "}":
                d -= 1
            k += 1
        expr = js[m.end():k - 1]
        line_txt = js[js.rfind("\n", 0, m.start()) + 1: js.find("\n", m.start())]
        if not expr_safe(expr, 0, line_txt):
            sinks.append((js[:m.start()].count("\n") + 1, expr[:70]))
    check("Frontend", "toàn bộ ${...} đều qua esc()/withCites()/builder đã kiểm chứng (anti-XSS)",
          not sinks, str(sinks[:3]) if sinks else "clean")

    # latency summary
    worst = max(lat, key=lambda x: x[1])
    avg = sum(m for _, m in lat) / len(lat)
    check("Hiệu năng", f"latency trung bình {avg:.0f}ms · worst {worst[1]:.0f}ms ({worst[0]})", worst[1] < 5000)

    # report
    lines = [
        "# Agent C — Smoke: static, contract, phiên bản, llm, hiệu năng",
        f"- {dt.datetime.now():%Y-%m-%d %H:%M} · live {BASE}\n",
        "| Nhóm | Check | Kết luận |", "|---|---|---|",
    ]
    lines += [f"| {g} | {n} | {v} |" for g, n, v in rows]
    lines += ["", "## Latency\n", "| Endpoint | ms |", "|---|---|"]
    lines += [f"| {p} | {m:.0f} |" for p, m in sorted(lat, key=lambda x: -x[1])[:10]]
    lines += ["", f"**Tổng: {sum(1 for _,_,v in rows if v.startswith('PASS'))}/{len(rows)} PASS**"
              + ("" if not issues else "\n\n## Issues\n" + "\n".join(f"- {i}" for i in issues))]
    open(REPORT, "w", encoding="utf-8").write("\n".join(lines))
    npass = sum(1 for _, _, v in rows if v.startswith("PASS"))
    print(f"{npass}/{len(rows)} PASS · issues={len(issues)} -> {REPORT}")
    for i in issues:
        print(f"  ❌ {i}")
    print(f"latency avg={avg:.0f}ms worst={worst[1]:.0f}ms ({worst[0]})")
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
