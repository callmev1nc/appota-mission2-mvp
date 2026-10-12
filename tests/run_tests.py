#!/usr/bin/env python3
"""Bộ kiểm thử Mission 2 — chạy thật trên policy engine + renderer.

Chạy offline (mặc định):
    python -X utf8 tests/run_tests.py
Chạy qua API đã deploy:
    python -X utf8 tests/run_tests.py --live https://mission2mvp.vercel.app

Ghi kết quả ra tests/results.md theo format: Kỳ vọng → Thực tế → Đạt/Chưa → Học được.
Exit code 1 nếu có ca FAIL (lỗi thật); ca "CHƯA ĐẠT" theo thiết kế không tính fail.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.engine import ask as engine_ask  # noqa: E402
from app.llm import compose  # noqa: E402

CASES_PATH = ROOT / "tests" / "cases.json"
RESULTS_PATH = ROOT / "tests" / "results.md"


def run_local(case: dict) -> dict:
    r = engine_ask(case["profile_id"], case["question"], case.get("date"))
    r = compose(
        r,
        case["question"],
        mode=case.get("llm", "template"),
        simulate=case.get("simulate", []),
    )
    return r


def run_live(case: dict, base: str) -> dict:
    payload = {
        k: case[k]
        for k in ("profile_id", "question", "date", "llm", "simulate")
        if k in case
    }
    req = urllib.request.Request(
        base.rstrip("/") + "/api/ask",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def check(case: dict, r: dict) -> list[str]:
    exp = case["expect"]
    fails: list[str] = []
    dump = json.dumps(r, ensure_ascii=False)
    answer = (r.get("answer") or {}).get("text", "")

    if "status" in exp and r.get("status") != exp["status"]:
        fails.append(f"status: mong đợi `{exp['status']}`, thực tế `{r.get('status')}`")
    if "facts" in exp and r.get("facts") != exp["facts"]:
        fails.append(f"facts: mong đợi `{exp['facts']}`, thực tế `{r.get('facts')}`")
    if "citation_ids" in exp:
        got = sorted(c["section_id"] for c in r.get("citations", []))
        want = sorted(exp["citation_ids"])
        if got != want:
            fails.append(f"citations: mong đợi `{want}`, thực tế `{got}`")
    if "forbidden_anywhere" in exp:
        hit = [s for s in exp["forbidden_anywhere"] if s in dump]
        if hit:
            fails.append(f"rò rỉ trong response: {hit}")
    if "forbidden_in_answer" in exp:
        hit = [s for s in exp["forbidden_in_answer"] if s in answer]
        if hit:
            fails.append(f"câu trả lời chứa chuỗi bị cấm: {hit}")
    for t in exp.get("trace_contains", []):
        doc = next((d for d in r.get("trace", {}).get("documents", []) if d["id"] == t["id"]), None)
        if doc is None:
            fails.append(f"trace thiếu tài liệu {t['id']}")
            continue
        if "decision" in t and doc["decision"] != t["decision"]:
            fails.append(f"trace {t['id']}: decision `{doc['decision']}` != `{t['decision']}`")
        if "reason" in t and t["reason"] not in doc.get("reasons", []):
            fails.append(f"trace {t['id']}: thiếu reason `{t['reason']}` (có {doc.get('reasons')})")
    if "read_denied_count" in exp:
        got = r.get("trace", {}).get("read_denied_count")
        if got != exp["read_denied_count"]:
            fails.append(f"read_denied_count: {got} != {exp['read_denied_count']}")
    if "conflict_values" in exp:
        got = {
            v["section_id"]: v["value"]
            for c in r.get("conflicts", [])
            for v in c["values"]
        }
        if got != exp["conflict_values"]:
            fails.append(f"conflict_values: `{got}` != `{exp['conflict_values']}`")
    if "escalate_to" in exp and r.get("escalate_to") != exp["escalate_to"]:
        fails.append(f"escalate_to: `{r.get('escalate_to')}` != `{exp['escalate_to']}`")
    if "context_sections" in exp:
        got = (r.get("answer") or {}).get("llm", {}).get("context_sections")
        if got != exp["context_sections"]:
            fails.append(f"context_sections: `{got}` != `{exp['context_sections']}`")
    if "llm_status" in exp:
        got = (r.get("answer") or {}).get("llm", {}).get("status")
        if got != exp["llm_status"]:
            fails.append(f"llm.status: `{got}` != `{exp['llm_status']}`")
    for s in exp.get("answer_contains", []):
        if s not in answer:
            fails.append(f"câu trả lời thiếu chuỗi `{s}`")
    for s in exp.get("caveat_contains", []):
        if not any(s in c for c in r.get("caveats", [])):
            fails.append(f"thiếu caveat chứa `{s}`")
    for s in exp.get("warning_contains", []):
        if not any(s in w for w in r.get("warnings", [])):
            fails.append(f"thiếu warning chứa `{s}`")
    return fails


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", default=None, help="base URL để chạy qua API thật")
    args = ap.parse_args()

    suite = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    mode = f"live: {args.live}" if args.live else "offline (import engine trực tiếp)"

    rows, details = [], []
    n_pass = n_limit = n_fail = 0

    for case in suite["cases"]:
        r = run_live(case, args.live) if args.live else run_local(case)
        fails = check(case, r)
        if fails:
            verdict, badge = "CHƯA ĐẠT (lỗi kiểm thử)", "FAIL"
            n_fail += 1
        elif case.get("verdict_if_pass", "").startswith("CHƯA ĐẠT"):
            verdict, badge = case["verdict_if_pass"], "LIMITED"
            n_limit += 1
        else:
            verdict, badge = "ĐẠT", "PASS"
            n_pass += 1

        facts = r.get("facts", {})
        ids = ", ".join(c["section_id"] for c in r.get("citations", [])) or "(không)"
        actual = (
            f"trạng thái `{r.get('status')}` · facts `{json.dumps(facts, ensure_ascii=False)}` · "
            f"nguồn `{ids}`"
        )
        rows.append((case["id"], r.get("status"), verdict, badge))
        details.append(
            f"### {case['id']} — {case['label']}\n\n"
            f"**Kỳ vọng:** {case['expectation_text']}\n\n"
            f"**Thực tế:** {actual}\n\n"
            f"> {((r.get('answer') or {}).get('text') or '').strip()}\n\n"
            f"**Đạt/Chưa đạt:** {verdict}"
            + (f"\n\n**Lý do FAIL:** " + "; ".join(fails) if fails else "")
            + f"\n\n**Điều học được:** {case['learning']}\n"
        )

    lines = [
        "# Bộ kiểm thử Mission 2 — KẾT QUẢ CHẠY THẬT\n",
        f"- Thời điểm chạy: {now} (giây địa phương) · chế độ: `{mode}`",
        f"- Dữ liệu: `{suite['dataset_id']}` · toàn bộ tổ chức/tài liệu là giả lập",
        f"- Tổng kết: **{n_pass} ĐẠT** · **{n_limit} CHƯA ĐẠT theo thiết kế** · **{n_fail} lỗi kiểm thử**"
        f" ({len(suite['cases'])} ca)\n",
        "| Ca | Trạng thái | Kết luận |",
        "|---|---|---|",
    ]
    lines += [f"| {i} | {s} | {v} |" for i, s, v, _ in rows]
    lines += ["", "---", ""]
    lines += details
    RESULTS_PATH.write_text("\n".join(lines), encoding="utf-8")

    print(f"PASS={n_pass} LIMITED={n_limit} FAIL={n_fail} -> {RESULTS_PATH}")
    for i, s, v, b in rows:
        print(f"  [{b:7}] {i:12} {s} {v if b != 'PASS' else ''}")
    return 1 if n_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
