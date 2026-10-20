"""Policy engine — quy tắc chọn bằng chứng trước, LLM chỉ diễn đạt sau.

Mission 2 MVP · chủ đề annual_leave · dữ liệu giả lập.
Không gọi mạng, không LLM ở đây: mọi quyết định là hàm thuần của
(hồ sơ, câu hỏi, ngày xét, bộ dữ liệu).
"""
from __future__ import annotations

import datetime as dt
import json
import re
from pathlib import Path
from typing import Any

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "synthetic_dataset.json"

TOPIC = "annual_leave"
LEVEL_VN = {"group": "Tập đoàn", "company": "Công ty", "department": "Phòng", "team": "Nhóm"}
KEY_VN = {
    "annual_entitlement_days": "định mức nghỉ phép năm",
    "notice_working_days": "thời gian báo trước",
    "request_route": "nơi gửi đề nghị",
    "request_form": "biểu mẫu",
    "handover_form": "bàn giao",
    "eligibility": "điều kiện",
}
ALL_BENEFIT_KEYS = [
    "annual_entitlement_days",
    "notice_working_days",
    "request_route",
    "request_form",
    "handover_form",
    "eligibility",
]
INTERNAL_KEYS = ["internal_review_marker"]

# --------------------------------------------------------------------------
# dataset
# --------------------------------------------------------------------------

_cache: dict[str, Any] | None = None


def load_dataset() -> dict[str, Any]:
    global _cache
    if _cache is None:
        _cache = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    return _cache


def _org_depth(dataset: dict[str, Any]) -> dict[str, int]:
    depth: dict[str, int] = {}
    for org in dataset["organizations"]:
        d, cur = 0, org
        while cur.get("parent_id"):
            d += 1
            cur = next(o for o in dataset["organizations"] if o["id"] == cur["parent_id"])
        depth[org["id"]] = d
    return depth


# --------------------------------------------------------------------------
# câu hỏi → các policy_key người dùng thực sự hỏi
# --------------------------------------------------------------------------

GENERAL_PATTERNS = [
    "quy định nghỉ phép",
    "chính sách nghỉ phép",
    "nghỉ phép của tôi",
    "nghỉ phép như thế nào",
    "nghỉ phép thế nào",
    "quy định nghỉ hằng năm",
]

KEY_PATTERNS: dict[str, list[str]] = {
    "internal_review_marker": ["ghi chú", "rà soát nội bộ", "canary", "mã bí mật"],
    "handover_form": ["bàn giao"],
    "request_form": ["biểu mẫu", "mẫu đơn", "đơn xin nghỉ"],
    "request_route": ["gửi cho ai", "gửi ai", "gửi cho", "ai duyệt", "quy trình gửi"],
    "notice_working_days": ["báo trước", "bao trước", "trước bao nhiêu ngày", "trước mấy ngày"],
    "eligibility": ["điều kiện", "đủ điều kiện", "có được nghỉ"],
    "annual_entitlement_days": [
        "nghỉ phép",
        "ngày nghỉ",
        "số ngày",
        "định mức",
        "bao nhiêu ngày nghỉ",
        "còn mấy ngày",
        "còn bao nhiêu ngày",
    ],
}

# cụm thủ tục: hỏi một phần thì đưa cả cụm liên quan vào để trả lời đủ thủ tục
PROCEDURE_CLUSTER = {"request_form", "request_route", "handover_form"}

BALANCE_PATTERNS = ["còn mấy ngày", "còn bao nhiêu ngày", "số dư", "còn dư", "dư phép", "balance"]


def classify(question: str) -> dict[str, Any]:
    """Trả về {requested_keys: [...], explicit: bool, balance_intent: bool, dropped_internal: bool}."""
    q = (question or "").lower().strip()
    matched = {k for k, pats in KEY_PATTERNS.items() if any(p in q for p in pats)}
    benefit = matched - set(INTERNAL_KEYS)

    dropped_internal = bool(benefit and matched & set(INTERNAL_KEYS))

    if benefit:
        if any(p in q for p in GENERAL_PATTERNS):
            keys = list(ALL_BENEFIT_KEYS)
            explicit = False
        else:
            keys = set(benefit)
            if keys & PROCEDURE_CLUSTER or any(w in q for w in ("nhóm", "phòng ")):
                keys |= PROCEDURE_CLUSTER  # hỏi tới cấp đơn vị → đưa cả cụm thủ tục vào
            if ("định mức" in q or "quy định" in q) and "annual_entitlement_days" in keys:
                # hỏi "định mức" → kèm minh chứng ngoại lệ không giết điều khoản khác
                keys.add("notice_working_days")
            keys = [k for k in ALL_BENEFIT_KEYS if k in keys] + [
                k for k in INTERNAL_KEYS if k in matched
            ]
            explicit = True
    elif matched & set(INTERNAL_KEYS):
        keys = list(INTERNAL_KEYS)
        explicit = True
    else:
        keys = list(ALL_BENEFIT_KEYS)
        explicit = False

    balance_intent = any(p in q for p in BALANCE_PATTERNS)
    return {
        "requested_keys": keys,
        "explicit": explicit,
        "balance_intent": balance_intent,
        "dropped_internal": dropped_internal,
    }


# --------------------------------------------------------------------------
# lọc ứng viên
# --------------------------------------------------------------------------


def _parse_date(s: str) -> dt.date:
    return dt.date.fromisoformat(s)


def _doc_effective(doc: dict[str, Any], date: dt.date) -> str:
    """'ok' | 'expired' | 'not_yet_effective' | 'no_date'"""
    ef, et = doc.get("effective_from"), doc.get("effective_to")
    if ef and date < _parse_date(ef):
        return "not_yet_effective"
    if et and date > _parse_date(et):
        return "expired"
    return "ok"


def _scope_ok(doc: dict[str, Any], unit_path: list[str]) -> bool:
    unit_id = doc["applicability"]["unit_id"]
    if doc["applicability"].get("include_descendants", False):
        return unit_id in unit_path
    return unit_id == unit_path[-1]


def _is_authority(doc: dict[str, Any]) -> bool:
    return doc.get("policy_authority") in ("approved_policy", "approved_procedure")


def _is_reference(doc: dict[str, Any]) -> bool:
    """Tài liệu đọc được nhưng không có thẩm quyền quyền lợi (ghi chú nội bộ...)."""
    return (
        doc.get("policy_authority") == "none"
        and doc.get("kind") == "internal_note"
        and doc.get("publication_status") == "published"
    )


def _base_filter(
    doc: dict[str, Any], profile: dict[str, Any], unit_path: list[str], date: dt.date
) -> tuple[bool, list[str]]:
    """Lọc đọc quyền + phạm vi + phê duyệt + hiệu lực. Trả (included, reason_codes)."""
    reasons: list[str] = []
    roles = set(profile.get("read_roles", []))
    if not roles & set(doc.get("read_roles", [])):
        return False, ["read_denied"]
    if not _scope_ok(doc, unit_path):
        reasons.append("scope_out")
    if doc.get("publication_status") != "published":
        reasons.append("draft")
    if not _is_authority(doc):
        if _is_reference(doc):
            pass  # ghi chú nội bộ đọc được nhưng không có thẩm quyền → xử lý riêng
        else:
            reasons.append("not_authority")
    eff = _doc_effective(doc, date)
    if eff != "ok":
        reasons.append(eff)
    # đọc được nhưng không qua được các cửa sổ khác → không phải read_denied
    return (len(reasons) == 0), reasons


# --------------------------------------------------------------------------
# resolve từng policy_key
# --------------------------------------------------------------------------


def _resolve_key(
    key: str,
    profile: dict[str, Any],
    unit_path: list[str],
    authority_docs: list[dict[str, Any]],
    date: dt.date,
    trace_docs: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    entries: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for doc in authority_docs:
        for sec in doc["sections"]:
            if sec["policy_key"] == key:
                entries.append((doc, sec))

    def scope_ok(unit_id: str) -> bool:
        return unit_id in unit_path

    # 1) replaces: bản thay thế có hiệu lực gỡ bản bị thay cho đúng policy_key
    survivors: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for doc, sec in entries:
        superseded_by = None
        for other, _ in entries:
            if other["id"] == doc["id"]:
                continue
            for r in other.get("replaces", []):
                if (
                    r["document_id"] == doc["id"]
                    and key in r["policy_keys"]
                    and scope_ok(r["scope_unit_id"])
                ):
                    superseded_by = other["id"]
        if superseded_by:
            trace_docs[doc["id"]]["reasons"].append(
                f"section {sec['id']} superseded_by:{superseded_by}"
            )
        else:
            survivors.append((doc, sec))

    # 2) approved override: ngoại lệ khai báo đúng scope thắng bản cơ sở
    final: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for doc, sec in survivors:
        overridden_by = None
        for other, _ in survivors:
            if other["id"] == doc["id"]:
                continue
            for ov in other.get("approved_overrides", []):
                if (
                    ov["policy_key"] == key
                    and ov["base_document_id"] == doc["id"]
                    and scope_ok(ov["scope_unit_id"])
                    and ov.get("approved_by")
                ):
                    overridden_by = other["id"]
        if overridden_by:
            trace_docs[doc["id"]]["reasons"].append(
                f"section {sec['id']} overridden_by:{overridden_by}"
            )
        else:
            final.append((doc, sec))

    if not final:
        return {"policy_key": key, "decision": "no_data", "value": None, "sections": []}

    # 3) còn lại: cùng giá trị thì hợp nhất, khác giá trị thì CONFLICT
    by_value: dict[str, list[tuple[dict[str, Any], dict[str, Any]]]] = {}
    for doc, sec in final:
        by_value.setdefault(
            json.dumps(sec["value"], ensure_ascii=False, sort_keys=True), []
        ).append((doc, sec))

    if len(by_value) > 1:
        return {
            "policy_key": key,
            "decision": "conflict",
            "value": None,
            "sections": [sec for _, sec in (s for grp in by_value.values() for s in grp)],
            "groups": [
                {"value": json.loads(v), "sections": [sec for _, sec in grp]}
                for v, grp in by_value.items()
            ],
        }

    group = next(iter(by_value.values()))
    decision = "single" if len(group) == 1 else "dedup_equal"
    if group[0][0].get("approved_overrides"):
        decision = "override_wins"
    return {
        "policy_key": key,
        "decision": decision,
        "value": group[0][1]["value"],
        "sections": [sec for _, sec in group],
    }


# --------------------------------------------------------------------------
# ask() — orchestration
# --------------------------------------------------------------------------


def ask(
    profile_id: str,
    question: str,
    date_str: str | None = None,
    dataset: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """dataset=None dùng bộ dữ liệu chuẩn; truyền dataset riêng chỉ dùng cho khung test CR
    (tiêm dữ liệu thay đổi do Change Request mà KHÔNG sửa lõi engine)."""
    dataset = dataset or load_dataset()
    date = _parse_date(date_str or dataset["evaluation_date"])
    depth = _org_depth(dataset)

    profiles = {p["id"]: p for p in dataset["profiles"]}
    orgs = {o["id"]: o for o in dataset["organizations"]}

    result: dict[str, Any] = {
        "status": None,
        "topic": TOPIC,
        "evaluation_date": date.isoformat(),
        "profile": None,
        "classification": None,
        "requested_keys": [],
        "facts": {},
        "missing_keys": [],
        "unresolved_policy_keys": [],
        "conflicts": [],
        "escalate_to": None,
        "citations": [],
        "caveats": [],
        "warnings": [],
        "trace": {"documents": [], "resolution": [], "read_denied_count": 0},
    }

    # 1) danh tính
    profile = profiles.get(profile_id)
    if profile is None:
        result["status"] = "MISSING_IDENTITY"
        return result
    unit_path = profile.get("unit_path")
    if not unit_path:
        result["status"] = "NEED_CONTEXT"
        result["profile"] = {"id": profile["id"], "display_name": profile["display_name"]}
        # thiếu đơn vị đáng tin cậy → hướng tới người quản lý hồ sơ, không tự suy
        result["escalate_to"] = "Người quản lý hồ sơ giả lập / HR G (giả lập)"
        return result

    unit_names = [orgs[u]["name"] for u in unit_path]
    result["profile"] = {
        "id": profile["id"],
        "display_name": profile["display_name"],
        "unit_path": unit_path,
        "unit_names": unit_names,
        "read_roles": profile["read_roles"],
    }

    # 2) phân loại câu hỏi
    cls = classify(question)
    requested = cls["requested_keys"]
    result["classification"] = cls
    result["requested_keys"] = requested
    # HR hỏi kèm ghi chú nội bộ: trả lời REFERENCE_ONLY cho ghi chú, không trộn
    # phần quyền lợi vào cùng một câu (tách bạch quyền đọc ↔ thẩm quyền — P02).
    if "hr" in profile.get("read_roles", []) and "internal_review_marker" in requested:
        requested = ["internal_review_marker"]
        result["requested_keys"] = requested
    if cls["dropped_internal"]:
        result["warnings"].append(
            "Một yêu cầu truy cập thông tin hạn chế bị bỏ qua vì đi kèm yêu cầu khác. "
            "Câu hỏi không thay đổi quyền của hồ sơ."
        )

    # 3) lọc ứng viên (trace cho mọi tài liệu đọc được; tài liệu bị chặn quyền chỉ đếm)
    trace_docs: dict[str, dict[str, Any]] = {}
    read_denied = 0
    authority_docs: list[dict[str, Any]] = []
    reference_docs: list[dict[str, Any]] = []

    for doc in dataset["documents"]:
        if doc["topic"] != TOPIC:
            continue
        roles = set(profile.get("read_roles", []))
        if not roles & set(doc.get("read_roles", [])):
            read_denied += 1  # không ghi id/title vào response → tránh lộ metadata
            continue
        included, reasons = _base_filter(doc, profile, unit_path, date)
        entry = {
            "id": doc["id"],
            "title": doc["title"],
            "version": doc.get("version"),
            "unit_id": doc["applicability"]["unit_id"],
            "unit_name": orgs[doc["applicability"]["unit_id"]]["name"],
            "effective": [doc.get("effective_from"), doc.get("effective_to")],
            "decision": "included" if included else "excluded",
            "reasons": reasons,
        }
        trace_docs[doc["id"]] = entry
        if included:
            if _is_authority(doc):
                authority_docs.append(doc)
            else:  # reference_only (đọc được, không thẩm quyền)
                entry["decision"] = "reference"
                reference_docs.append(doc)

    result["trace"]["read_denied_count"] = read_denied
    result["trace"]["documents"] = list(trace_docs.values())

    # 4) resolve từng key được hỏi
    resolutions: list[dict[str, Any]] = []
    explicit_missing: list[str] = []
    denied_keys: set[str] = set()

    for key in requested:
        if key in INTERNAL_KEYS:
            readable_ref = [
                d
                for d in reference_docs
                if any(s["policy_key"] == key for s in d["sections"])
            ]
            if readable_ref:
                sec = next(s for s in readable_ref[0]["sections"] if s["policy_key"] == key)
                res = {
                    "policy_key": key,
                    "decision": "reference_only",
                    "value": sec["value"],
                    "sections": [sec],
                }
            else:
                # không có tài liệu nào đọc được cho key này → không xác nhận tồn tại
                res = {"policy_key": key, "decision": "no_data", "value": None, "sections": []}
                denied_keys.add(key)
            resolutions.append(res)
            continue

        res = _resolve_key(key, profile, unit_path, authority_docs, date, trace_docs)
        if res["decision"] == "no_data":
            # có tài liệu cùng key nhưng bị loại ở khâu phạm vi/hiệu lực → cần phân biệt
            same_key_denied = any(
                any(s["policy_key"] == key for s in d["sections"])
                for d in dataset["documents"]
                if d["topic"] == TOPIC
                and d["id"] not in trace_docs  # bị loại ngay ở bước đọc quyền
            )
            if same_key_denied:
                denied_keys.add(key)
            # key nội bộ bị từ chối không phải "thiếu dữ liệu" → không hạ cấp ANSWER xuống DATA_LIMIT
            if cls["explicit"] and key not in INTERNAL_KEYS:
                explicit_missing.append(key)
        resolutions.append(res)

    result["trace"]["resolution"] = [
        {"policy_key": r["policy_key"], "decision": r["decision"],
         "sections": [s["id"] for s in r["sections"]],
         "value": r.get("value")}
        for r in resolutions
    ]

    # 4b) chuỗi giải thích "vì sao" cho từng điều khoản: bản nào bị gỡ bởi quan hệ
    # khai báo nào, bản nào còn đứng, kết luận dựa trên quan hệ chứ không phải "mới hơn".
    chains: list[dict[str, Any]] = []
    for r in resolutions:
        key = r["policy_key"]
        if r["decision"] in ("no_data", "reference_only"):
            continue
        lines: list[str] = []
        for did in sorted(trace_docs):
            for reason in trace_docs[did]["reasons"]:
                rel_type, target = None, None
                if " overridden_by:" in reason:
                    rel_type, target = "approved_overrides", reason.split(" overridden_by:", 1)[1]
                elif " superseded_by:" in reason:
                    rel_type, target = "replaces", reason.split(" superseded_by:", 1)[1]
                else:
                    continue
                sid = reason[len("section "):].split(" ", 1)[0]
                e = trace_docs.get(sid.split("#")[0], {})
                lines.append(
                    f"{sid} • bỏ khỏi bằng chứng cho điều khoản «{KEY_VN.get(key, key)}» • "
                    f"quan hệ {rel_type} khai báo trong {target} (đúng điều khoản, đúng phạm vi, có phê duyệt)."
                )
        for sec in r["sections"]:
            e = trace_docs.get(sec["id"].split("#")[0], {})
            lines.append(
                f"{sec['id']} • {e.get('title', '?')} — {e.get('unit_name', '?')} (v{e.get('version', '?')}) "
                f"còn đứng tại ngày xét • giá trị {json.dumps(sec['value'], ensure_ascii=False)}."
            )
        if r["decision"] == "conflict":
            lines.append(
                "CHƯA KẾT LUẬN: trên là các nguồn cùng hiệu lực nhưng khác giá trị, và CHƯA khai báo "
                "quan hệ replaces/approved_overrides giữa chúng — không nguồn nào có căn cứ gỡ nguồn nào. "
                "Hệ thống không tự chọn theo «mới hơn» hay theo cấp đơn vị."
            )
        elif r["decision"] == "override_wins":
            sid = r["sections"][0]["id"]
            lines.append(
                f"KẾT LUẬN {sid} = {json.dumps(r['value'], ensure_ascii=False)} — thắng theo quan hệ "
                "khai báo (approved_overrides/replaces), không phải vì «mới hơn»."
            )
        elif r["decision"] == "dedup_equal":
            lines.append("Nhóm nguồn cùng giá trị, không mâu thuẫn — hợp nhất làm một bằng chứng cùng ý.")
        chains.append({"policy_key": key, "decision": r["decision"], "lines": lines})
    result["trace"]["chains"] = chains

    conflicts = [r for r in resolutions if r["decision"] == "conflict"]
    answered = [r for r in resolutions if r["decision"] in ("single", "dedup_equal", "override_wins")]
    reference = [r for r in resolutions if r["decision"] == "reference_only"]
    no_data = [r for r in resolutions if r["decision"] == "no_data"]

    if conflicts:
        for c in conflicts:
            sids = sorted({s["id"] for g in c["groups"] for s in g["sections"]})
            c["note"] = (
                f"Các nguồn {', '.join(sids)} đang CÙNG trong thời hạn hiệu lực tại ngày xét "
                f"{date.isoformat()} và chưa khai báo quan hệ replaces/approved_overrides giữa các bản — "
                "không nguồn nào có căn cứ gỡ nguồn khác. Cần chủ sở hữu/HR có thẩm quyền ban hành "
                "quan hệ quản lý nội dung (thay thế hoặc điều chỉnh có phê duyệt) giữa các bản này."
            )

    # 5) trạng thái tổng
    if conflicts and any(r["policy_key"] not in INTERNAL_KEYS for r in conflicts):
        result["status"] = "CONFLICT"
        owners = []
        for c in conflicts:
            vals = []
            for g in c["groups"]:
                for sec in g["sections"]:
                    doc_id = sec["id"].split("#")[0]
                    doc_row = next(d for d in dataset["documents"] if d["id"] == doc_id)
                    unit_id = doc_row["applicability"]["unit_id"]
                    vals.append(
                        {
                            "value": g["value"],
                            "section_id": sec["id"],
                            "doc_id": doc_id,
                            "title": trace_docs[doc_id]["title"],
                            "version": doc_row.get("version"),
                            "unit_name": trace_docs[doc_id]["unit_name"],
                            "unit_level": orgs[unit_id]["level"],
                            "effective": [doc_row.get("effective_from"), doc_row.get("effective_to")],
                            "owner": doc_row["owner"],
                        }
                    )
                    owners.append(vals[-1]["owner"])
            result["conflicts"].append({"policy_key": c["policy_key"], "values": vals, "note": c.get("note")})
        result["unresolved_policy_keys"] = [c["policy_key"] for c in conflicts]
        # trích dẫn của CONFLICT chỉ gồm các nguồn bất đồng
        conflict_sec_ids = {
            s["id"] for c in conflicts for g in c["groups"] for s in g["sections"]
        }
        result["citations"] = [
            _cite(s, dataset, trace_docs)
            for r in conflicts
            for s in r["sections"]
            if s["id"] in conflict_sec_ids
        ]
        # escalate: HR của đơn vị sâu nhất trong nhóm nguồn bất đồng
        result["escalate_to"] = _deepest_owner(
            [v["doc_id"] for c in result["conflicts"] for v in c["values"]], trace_docs, depth, dataset
        )
        return result

    if reference and not answered:
        result["status"] = "REFERENCE_ONLY"
        for r in reference:
            sec = r["sections"][0]
            result["facts"][r["policy_key"]] = r["value"]
            result["citations"].append(_cite(sec, dataset, trace_docs))
        result["caveats"].append(
            "Đây là ghi chú nội bộ, KHÔNG có thẩm quyền xác định quyền lợi nghỉ phép."
        )
        return result

    if answered:
        if cls["explicit"] and explicit_missing:
            result["status"] = "ANSWER_WITH_DATA_LIMIT"
            result["missing_keys"] = explicit_missing
        else:
            result["status"] = "ANSWER"
        for r in answered:
            key = r["policy_key"]
            if key == "eligibility":
                ok = _eligible(profile, r["value"])
                result["facts"]["eligible"] = ok
            else:
                result["facts"][key] = r["value"]
            for sec in r["sections"]:
                result["citations"].append(_cite(sec, dataset, trace_docs))
        if cls["explicit"] and explicit_missing:
            # escalate: HR của đơn vị sâu nhất trong các tài liệu ĐƯỢC CHỌN cho hồ sơ này
            included_ids = [d["id"] for d in trace_docs.values() if d["decision"] == "included"]
            result["escalate_to"] = _deepest_owner(included_ids, trace_docs, depth, dataset)
        if cls["balance_intent"]:
            result["caveats"].append(
                "Hệ thống chưa có số dư cá nhân: đây là ĐỊNH MỨC năm theo chính sách, "
                "không phải số ngày còn lại của bạn. Số dư cần dữ liệu chấm công/HRIS."
            )
        return result

    # không có gì trả lời được
    if not answered and not reference and not conflicts:
        if denied_keys and set(requested) <= denied_keys:
            result["status"] = "NO_AUTHORIZED_EVIDENCE"
        else:
            result["status"] = "NO_DATA"
        if cls["explicit"]:
            result["missing_keys"] = [r["policy_key"] for r in no_data]
    return result


def _eligible(profile: dict[str, Any], cond: dict[str, Any] | None) -> bool:
    if not cond:
        return True
    if cond.get("employment_type") and profile.get("employment_type") != cond["employment_type"]:
        return False
    min_months = cond.get("minimum_tenure_months")
    if min_months is not None and profile.get("tenure_months", 0) < min_months:
        return False
    return True


def _cite(sec: dict[str, Any], dataset: dict[str, Any], trace_docs: dict[str, Any]) -> dict[str, Any]:
    doc_id = sec["id"].split("#")[0]
    doc = next(d for d in dataset["documents"] if d["id"] == doc_id)
    return {
        "section_id": sec["id"],
        "doc_id": doc_id,
        "title": doc["title"],
        "policy_key": sec["policy_key"],
        "text": sec["text"],
        "value": sec["value"],
        "owner": doc["owner"],
        "unit_name": trace_docs[doc_id]["unit_name"] if doc_id in trace_docs else None,
        "effective": [doc.get("effective_from"), doc.get("effective_to")],
    }


def _deepest_owner(
    doc_ids: list[str], trace_docs: dict[str, Any], depth: dict[str, int], dataset: dict[str, Any]
) -> str | None:
    best, best_d = None, -1
    for did in sorted(set(doc_ids)):
        unit = trace_docs.get(did, {}).get("unit_id")
        if unit is None:
            continue
        d = depth.get(unit, 0)
        if d > best_d:
            best_d = d
            best = next(doc["owner"] for doc in dataset["documents"] if doc["id"] == did)
    return best

# --------------------------------------------------------------------------
# M3 · kiểm chứng cho người dùng: timeline phiên bản + nguyên văn trích dẫn
# --------------------------------------------------------------------------

SECTION_ID_RE = re.compile(r"^D\d{1,3}#s\d+$")


def timeline_view(
    profile_id: str,
    date_str: str | None = None,
    dataset: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Lịch sử phiên bản & hiệu lực của chủ đề theo góc MỘT hồ sơ.

    Chỉ liệt kê tài liệu hồ sơ này (a) ĐƯỢC ĐỌC và (b) nằm trong phạm vi áp dụng
    của đơn vị hồ sơ; tài liệu bị chặn quyền đọc chỉ được đếm số — không xác nhận
    sự tồn tại. Trạng thái tính theo ngày xét, không theo ngày hệ thống.
    """
    dataset = dataset or load_dataset()
    date = _parse_date(date_str or dataset["evaluation_date"])
    profile = next((p for p in dataset["profiles"] if p["id"] == profile_id), None)
    if profile is None:
        return {"error": "profile_not_found"}
    unit_path = profile.get("unit_path") or []
    roles = set(profile.get("read_roles", []))
    rows: list[dict[str, Any]] = []
    restricted_count = out_of_scope_count = 0
    for doc in dataset["documents"]:
        if doc["topic"] != TOPIC:
            continue
        if not roles & set(doc.get("read_roles", [])):
            restricted_count += 1  # tài liệu không được đọc: không ghi id/title
            continue
        if unit_path and not _scope_ok(doc, unit_path):
            out_of_scope_count += 1  # đọc được nhưng áp dụng đơn vị khác
            continue
        status = {
            "ok": "current",
            "expired": "expired",
            "not_yet_effective": "future",
            "no_date": "no_date",
        }[_doc_effective(doc, date)]
        org = next(o for o in dataset["organizations"] if o["id"] == doc["applicability"]["unit_id"])
        rows.append(
            {
                "id": doc["id"],
                "title": doc["title"],
                "version": doc.get("version"),
                "kind": doc["kind"],
                "publication_status": doc["publication_status"],
                "policy_authority": doc.get("policy_authority"),
                "owner": doc["owner"],
                "unit_name": org["name"],
                "unit_level": org["level"],
                "effective": [doc.get("effective_from"), doc.get("effective_to")],
                "status": status,
                "values": {
                    s["policy_key"]: s["value"]
                    for s in doc["sections"]
                    if s["policy_key"] in ALL_BENEFIT_KEYS
                },
                "section_ids": [s["id"] for s in doc["sections"]],
            }
        )
    rows.sort(key=lambda r: (r["effective"][0] or "0000-00-00", r["id"]))
    return {
        "profile": {
            "id": profile_id,
            "display_name": profile["display_name"],
            "unit_path": unit_path,
        },
        "evaluation_date": date.isoformat(),
        "topic": TOPIC,
        "rows": rows,
        "restricted_count": restricted_count,
        "out_of_scope_count": out_of_scope_count,
        "note": (
            "Chỉ liệt kê tài liệu hồ sơ này ĐƯỢC ĐỌC và trong phạm vi áp dụng đơn vị. "
            "Tài liệu chặn quyền không được xác nhận sự tồn tại, không hiển thị metadata."
        ),
    }


def source_view(
    profile_id: str,
    section_id: str,
    date_str: str | None = None,
    dataset: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Kiểm chứng trích dẫn: nguyên văn đoạn + phiên bản tài liệu, phục vụ CHỈ khi
    hồ sơ được phép đọc tài liệu đó.

    Bất khả xác nhận: tài liệu không tồn tại, sai mã, hoặc ngoài quyền đọc trả về
    CÙNG MỘT kết quả {"accessible": False} — gọi API phải phản ứng như nhau,
    không cho biết tài liệu có tồn tại hay không.
    """
    dataset = dataset or load_dataset()
    if not SECTION_ID_RE.match(section_id or ""):
        return {"accessible": False}
    profile = next((p for p in dataset["profiles"] if p["id"] == profile_id), None)
    if profile is None:
        return {"accessible": False}
    doc = next(
        (
            d
            for d in dataset["documents"]
            if d["topic"] == TOPIC and any(s["id"] == section_id for s in d["sections"])
        ),
        None,
    )
    if doc is None or not set(profile.get("read_roles", [])) & set(doc.get("read_roles", [])):
        return {"accessible": False}
    sec = next(s for s in doc["sections"] if s["id"] == section_id)
    unit_path = profile.get("unit_path") or []
    date = _parse_date(date_str or dataset["evaluation_date"])
    included, reasons = _base_filter(doc, profile, unit_path, date) if unit_path else (False, ["scope_out"])
    org = next(o for o in dataset["organizations"] if o["id"] == doc["applicability"]["unit_id"])
    return {
        "accessible": True,
        "section": {"id": sec["id"], "policy_key": sec["policy_key"], "value": sec["value"], "text": sec["text"]},
        "doc": {
            "id": doc["id"],
            "title": doc["title"],
            "version": doc.get("version"),
            "kind": doc["kind"],
            "publication_status": doc["publication_status"],
            "approved_by": doc.get("approved_by"),
            "effective": [doc.get("effective_from"), doc.get("effective_to")],
            "owner": doc["owner"],
            "policy_authority": doc.get("policy_authority"),
            "unit_name": org["name"],
            "unit_level": org["level"],
        },
        "with_profile": {
            "visibility": "included" if included else "excluded",
            "reasons": reasons,
        },
        "evaluation_date": date.isoformat(),
    }
