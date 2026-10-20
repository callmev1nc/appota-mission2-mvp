#!/usr/bin/env python3
"""Agent D — bộ kiểm thử Mission 3: kiểm chứng chích dẫn + timeline + khung Change Request.

Chạy offline (mặc định):
    python -X utf8 tests/reports/agentD_m3.py
Chạy trên bản deploy (thêm phần API thật):
    python -X utf8 tests/reports/agentD_m3.py --live https://mission2mvp.vercel.app

Xuất: tests/reports/agentD_m3.md
"""
from __future__ import annotations

import copy
import json
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
import sys  # noqa: E402

sys.path.insert(0, str(ROOT))

from app import engine  # noqa: E402

REPORT = ROOT / "tests" / "reports" / "agentD_m3.md"
CANARY = "HR_CANARY_7F2A_SYNTHETIC"
D09_TITLE = "Ghi chú rà soát nội bộ HR — dữ liệu canary giả lập"


class AgentD:
    def __init__(self) -> None:
        self.rows: list[tuple[str, str, str]] = []
        self.issues: list[str] = []

    def check(self, group: str, name: str, ok: bool, detail: str = "") -> None:
        self.rows.append((group, name, ("PASS " if ok else "FAIL ") + detail))
        if not ok:
            self.issues.append(f"{group} · {name} · {detail}")


def dump(obj) -> str:
    return json.dumps(obj, ensure_ascii=False)


# ------------------------------------------------------------------ offline
def offline(a: AgentD) -> None:
    # ---- T10 · kiểm chứng trích dẫn (viewer) --------------------------------
    sv = engine.source_view("U01", "D03#s1")
    ok = sv.get("accessible") is True
    ok = ok and "14 ngày mỗi năm" in sv.get("section", {}).get("text", "")
    ok = ok and sv.get("doc", {}).get("version") == "2.0"
    ok = ok and sv.get("with_profile", {}).get("visibility") == "included"
    a.check("T10", "U01 xem D03#s1: nguyên văn + version 2.0 + visibility", ok, dump(sv)[:120])

    # Bất khả xác nhận: bị chặn quyền (D09) và mã không tồn tại (D99) → CÙNG KẾT QUẢ
    sv_d09 = engine.source_view("U01", "D09#s1")
    sv_none = engine.source_view("U01", "D99#s9")
    same = (dump(sv_d09) == dump(sv_none)) and sv_d09.get("accessible") is False
    a.check("T10", "U01 D09#s1 ≡ D99#s9 (không xác nhận sự tồn tại)", same, f"{dump(sv_d09)} vs {dump(sv_none)}")

    leak = CANARY in dump(sv_d09) or D09_TITLE in dump(sv_d09)
    a.check("T10", "phản hồi từ chối không chứa canary/title D09", not leak)

    # Đọc được nhưng ngoài phạm vi áp dụng → cho xem nguyên văn + lý do scope
    sv_d05 = engine.source_view("U01", "D05#s1")
    ok5 = (
        sv_d05.get("accessible") is True
        and sv_d05.get("with_profile", {}).get("reasons") == ["scope_out"]
        and "16 ngày" in sv_d05.get("section", {}).get("text", "")
    )
    a.check("T10", "U01 xem D05#s1 (đọc được, khác phạm vi) — lộ lý do scope, giá trị", ok5, dump(sv_d05)[:120])

    # Viewer phải xem ĐƯỢC báo trước/biểu mẫu (mọi section trong quyền) và
    # không tự quyết thay engine: value thuộc về section thật trong dataset
    sv_notef = engine.source_view("U05", "D11#s1")
    ok_l = sv_notef.get("accessible") is True and sv_notef.get("section", {}).get("value") == 13
    a.check("T10", "U05 xem D11#s1 (nguồn được chọn) — value khớp dataset", ok_l)

    # ---- Timeline -----------------------------------------------------------
    tl = engine.timeline_view("U05")
    ids = {r["id"]: r for r in tl["rows"]}
    ok_t = (
        set(ids) == {"D01", "D02", "D03", "D11", "D04", "D10", "D12"}
        and ids["D02"]["status"] == "expired"
        and ids["D04"]["status"] == "future"
        and ids["D12"]["status"] == "future"
        and ids["D03"]["status"] == "current"
        and ids["D10"]["publication_status"] == "draft"
        and tl["restricted_count"] == 1
        and tl["out_of_scope_count"] == 4
    )
    a.check("TIMELINE", "U05: 7 row đúng trạng thái + restricted=1 + out_of_scope=4", ok_t, dump(ids)[:140])

    tl3 = engine.timeline_view("U03")
    ids3 = {r["id"] for r in tl3["rows"]}
    ok_3 = ids3 == {"D01", "D05", "D06"}  # D11/D12/D02/D07/D08/D10: ngoài phạm vi Bình
    a.check("TIMELINE", "U03 (Công ty Bình): không lộ tài liệu phòng Kinh doanh An", ok_3, str(sorted(ids3)))

    tl4 = engine.timeline_view("U04")
    ok4 = all(r["publication_status"] != "hidden" for r in tl4["rows"])  # only sanity
    a.check("TIMELINE", "U04 (HR): timeline ngang quyền ghi chú", ok4)

    # ---- T12 · khung Change Request: dữ liệu CR mới → hệ thống phục vụ ngay ---
    main_ds = engine.load_dataset()
    ok_shipped = "U90" not in {p["id"] for p in main_ds["profiles"]}
    a.check("T12-CR", "bản chạy thật KHÔNG chứa hồ sơ kịch bản U90 (chỉ ở khung test)", ok_shipped)

    overlay = copy.deepcopy(main_ds)
    overlay["organizations"].append(
        {"id": "CC", "name": "Công ty CR (kịch bản)", "level": "company", "parent_id": "G"}
    )
    overlay["profiles"].append(
        {
            "id": "U90",
            "display_name": "SEO Kịch Bản",
            "unit_path": ["G", "CC"],
            "read_roles": ["employee"],
            "employment_type": "full_time",
            "tenure_months": 20,
        }
    )
    overlay["documents"].append(
        {
            "id": "D90",
            "title": "Định mức Công ty CR (kịch bản từ Change Request)",
            "topic": "annual_leave",
            "kind": "policy",
            "version": "1.0",
            "published_at": "2026-10-01",
            "publication_status": "published",
            "approval_status": "approved",
            "approved_by": "Hội đồng Chính sách G (kịch bản)",
            "effective_from": "2026-09-01",
            "effective_to": None,
            "read_roles": ["employee"],
            "applicability": {"unit_id": "CC", "include_descendants": True},
            "owner": "HR CR (kịch bản)",
            "policy_authority": "approved_policy",
            "approved_overrides": [
                {
                    "policy_key": "annual_entitlement_days",
                    "base_document_id": "D01",
                    "scope_unit_id": "CC",
                    "approved_by": "Hội đồng Chính sách G (kịch bản)",
                }
            ],
            "replaces": [],
            "sections": [
                {
                    "id": "D90#s1",
                    "policy_key": "annual_entitlement_days",
                    "value": 21,
                    "text": "Định mức tại Công ty CR (dữ liệu do Change Request nhập) là 21 ngày mỗi năm, thay riêng định mức D01 trong phạm vi Công ty CR.",
                }
            ],
        }
    )
    res = engine.ask("U90", "Quy định nghỉ phép của tôi như thế nào?", "2026-10-07", dataset=overlay)
    ok_cr = (
        res["status"] == "ANSWER"
        and res["facts"].get("annual_entitlement_days") == 21
        and any(c["section_id"] == "D90#s1" for c in res["citations"])
    )
    a.check("T12-CR", "CR thêm D90/U90 → ask() trả 21 [D90#s1] KHÔNG sửa lõi engine", ok_cr, dump(res["facts"]))

    # bảo toàn dữ liệu gốc: ask(overlay) không biến dịch dataset thật of tác
    ok_safe = "U90" not in {p["id"] for p in engine.load_dataset()["profiles"]}
    a.check("T12-CR", "engine không biến dịch bộ dữ liệu thật sau khi ask(overlay)", ok_safe)

    # hồ sơ thật không nhìn thấy tài liệu của kịch bản CR
    res_u01 = engine.ask("U01", "Quy định nghỉ phép của tôi như thế nào?", "2026-10-07", dataset=overlay)
    ok_isolate = (
        res_u01["status"] == "ANSWER"
        and res_u01["facts"].get("annual_entitlement_days") == 14
        and all(c["section_id"] != "D90#s1" for c in res_u01["citations"])
    )
    a.check("T12-CR", "U01 (khách) vẫn 14 — phạm vi D90 không lan truyền", ok_isolate, dump(res_u01["facts"]))


# ------------------------------------------------------------------ live
def live(a: AgentD, base: str) -> None:
    base = base.rstrip("/")

    def get(path: str):
        try:
            with urllib.request.urlopen(base + path, timeout=30) as resp:
                return resp.status, json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "replace")
            return e.code, json.loads(body)

    code, j = get("/api/source?profile_id=U01&section_id=D03%23s1")
    ok = code == 200 and "14 ngày mỗi năm" in j.get("section", {}).get("text", "")
    a.check("T10-live", "GET /api/source U01 D03#s1 → 200 nguyên văn", ok, f"{code} {dump(j)[:80]}")

    code, j = get(f"/api/source?profile_id=U01&section_id=D09%23s1")
    ok = code == 404 and CANARY not in dump(j) and "D09" not in dump(j)
    a.check("T10-live", "GET /api/source U01 D09#s1 → 404 + rỗng metadata bị chặn", ok, f"{code} {dump(j)}")

    code, j2 = get("/api/source?profile_id=U01&section_id=ZZZ")
    same404 = code == 404 and dump(j2) == dump(j)
    a.check("T10-live", "mã sai ≡ bị chặn (cùng 404 cùng body)", same404, f"{code} {dump(j2)}")

    code, j = get("/api/timeline?profile_id=U05")
    ids = {r["id"] for r in j.get("rows", [])}
    ok = code == 200 and "D11" in ids and "D06" not in ids and "D07" not in ids
    a.check("TIMELINE-live", "GET /api/timeline U05 → D11 có, D06/D07 không", ok, f"{code} {sorted(ids)}")
    code, j = get("/api/timeline?profile_id=U03")
    ids = {r["id"] for r in j.get("rows", [])}
    ok = code == 200 and "D05" in ids and "D11" not in ids
    a.check("TIMELINE-live", "GET /api/timeline U03 → D05 có, D11 không", ok, f"{code} {sorted(ids)}")


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--live", default=None)
    args = ap.parse_args()
    a = AgentD()
    offline(a)
    if args.live:
        live(a, args.live)
    rows = [
        "# Agent D — Mission 3: kiểm chứng trích dẫn + timeline + khung CR",
        f"- {datetime.now():%Y-%m-%d %H:%M} · {'live ' + args.live if args.live else 'offline (import engine trực tiếp)'}\n",
        "| Nhóm | Check | Kết luận |",
        "|---|---|---|",
    ]
    rows += [f"| {g} | {n} | {v} |" for g, n, v in a.rows]
    if a.issues:
        rows += ["", "## Issues", *[f"- {i}" for i in a.issues]]
    REPORT.write_text("\n".join(rows), encoding="utf-8")
    npass = sum(1 for _, _, v in a.rows if v.startswith("PASS"))
    print(f"{npass}/{len(a.rows)} PASS · issues={len(a.issues)} -> {REPORT}")
    for i in a.issues:
        print(f"  ❌ {i}")
    return 1 if a.issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
