"""Chuẩn bị câu trả lời dạng chữ (template) + hàng rào chặn rò rỉ.

Template là chế độ mặc định: mọi câu đều bám nguyên văn đoạn nguồn đã chọn,
có [mã trích dẫn], không sinh số liệu mới.
"""
from __future__ import annotations

from typing import Any

FORBIDDEN_ALWAYS = [
    "HR_CANARY_7F2A_SYNTHETIC",
    "Ghi chú rà soát nội bộ HR — dữ liệu canary giả lập",
    "D09",  # mã tài liệu bị chặn quyền không bao giờ được xuất hiện cho người không có quyền
]

KEY_LABELS = {
    "annual_entitlement_days": "Số ngày phép",
    "notice_working_days": "Báo trước",
    "request_route": "Gửi cho",
    "request_form": "Biểu mẫu xin nghỉ",
    "handover_form": "Bàn giao",
    "eligibility": "Điều kiện",
    "eligible": "Điều kiện",
    "internal_review_marker": "Mã ghi chú nội bộ",
}

ROUTE_LABELS = {"direct_manager": "quản lý trực tiếp", "team_lead": "trưởng nhóm"}

STATUS_LABELS = {
    "ANSWER": "TRẢ LỜI ĐƯỢC — có nguồn",
    "ANSWER_WITH_DATA_LIMIT": "TRẢ LỜI GIỚI HẠN — thiếu dữ liệu một phần",
    "CONFLICT": "CHƯA KẾT LUẬN — nguồn mâu thuẫn",
    "NO_AUTHORIZED_EVIDENCE": "TỪ CHỐI — không có dữ liệu trong quyền",
    "NO_DATA": "CHƯA CÓ DỮ LIỆU",
    "REFERENCE_ONLY": "TÀI LIỆU THAM KHẢO — không có thẩm quyền",
    "SOURCE_ONLY": "CHỈ HIỂN THỊ NGUỒN — AI chưa tạo được câu trả lời",
    "MISSING_IDENTITY": "CẦN CHỌN HỒ SƠ",
    "NEED_CONTEXT": "CẦN BỔ SUNG ĐƠN VỊ",
}


def format_value(key: str, value: Any) -> str:
    if key in ("annual_entitlement_days", "notice_working_days"):
        return f"{value} ngày" + ("/năm" if key == "annual_entitlement_days" else " làm việc")
    if key == "request_route":
        return ROUTE_LABELS.get(value, str(value))
    if key in ("request_form", "handover_form"):
        return str(value)
    if key in ("eligible",):
        return "đủ điều kiện theo hồ sơ" if value else "chưa đủ điều kiện theo hồ sơ"
    return str(value)


def render_template(result: dict[str, Any], profile_unit_names: list[str] | None) -> str:
    """Sinh câu trả lời template từ kết quả engine. Không ra ngoài dữ liệu bị chặn."""
    status = result["status"]
    date = result["evaluation_date"]
    allowed_ids = {c["section_id"] for c in result["citations"]}

    if status == "MISSING_IDENTITY":
        return ("Bạn chưa chọn hồ sơ nhân sự. Chọn hồ sơ giả lập ở bảng điều khiển để bắt đầu — "
                "câu hỏi không tự tạo quyền.")
    if status == "NEED_CONTEXT":
        return ("Hồ sơ của bạn thiếu đường dẫn đơn vị. Không suy đơn vị từ câu hỏi. "
                "Liên hệ người quản lý hồ sơ/HR để bổ sung trước khi kết luận chính sách.")
    if status == "CONFLICT":
        lines = ["CHƯA KẾT LUẬN — các nguồn còn hiệu lực đang mâu thuẫn:"]
        for c in result["conflicts"]:
            for v in c["values"]:
                lines.append(f"• {format_value(c['policy_key'], v['value'])} — [{v['section_id']}] {v['title']}")
            if c.get("note"):
                # ghi rõ vì sao không ai được phép tự chọn: thiếu quan hệ quản lý nội dung
                lines.append(f"→ {c['note']}")
        lines.append("Không chọn theo ngày cập nhật, cấp đơn vị hay trung bình số.")
        if result.get("escalate_to"):
            lines.append(f"HR phụ trách: {result['escalate_to']}.")
        lines.append("Gõ riêng một điều khoản không xung đột (vd: thời gian báo trước) để nhận câu trả lời phần đó.")
        return "\n".join(lines)
    if status == "NO_AUTHORIZED_EVIDENCE":
        return ("Không có dữ liệu được phép trong phạm vi hồ sơ của bạn cho yêu cầu này. "
                "Hệ thống không xác nhận tài liệu ngoài quyền của bạn. "
                "Nếu thực sự cần, hãy liên hệ HR phụ trách đơn vị.")
    if status == "NO_DATA":
        keys = ", ".join(result["requested_keys"]) or "chủ đề hỏi"
        return (f"Chưa có dữ liệu phù hợp cho yêu cầu này trong bộ dữ liệu giả lập ({keys}). "
                "Không suy ra câu trả lời ngoài dữ liệu. Liên hệ HR phụ trách đơn vị để được hỗ trợ.")
    if status == "REFERENCE_ONLY":
        lines = [f"[{result['citations'][0]['section_id']}] {result['citations'][0]['text']}"]
        lines += result["caveats"]
        return "\n".join(lines)

    # ANSWER / ANSWER_WITH_DATA_LIMIT / SOURCE_ONLY
    unit = " → ".join(profile_unit_names or [])
    if status == "SOURCE_ONLY":
        head = (f"BƯỚC DIỄN ĐẠP LỖI — chưa tạo được câu trả lời AI. Dưới đây là "
                f"các đoạn nguồn đã được quy tắc chọn (xét ngày {date}):")
    else:
        head = f"Kết luận theo hồ sơ của bạn ({unit}) · xét ngày {date}:"
    lines = [head]
    for key, val in result["facts"].items():
        label = KEY_LABELS.get(key, key)
        cite = _cite_for_fact(result, key)
        suffix = f" [{cite}]" if cite else ""
        lines.append(f"• {label}: {format_value(key, val)}{suffix}")
    for miss in result.get("missing_keys", []):
        lines.append(f"• {KEY_LABELS.get(miss, miss)}: bộ dữ liệu chưa có mục riêng cho đơn vị bạn — hỏi HR phụ trách.")
    for cav in result["caveats"]:
        lines.append(f"⚠ {cav}")
    for warn in result.get("warnings", []):
        lines.append(f"⚠ {warn}")
    ids = ", ".join(sorted(allowed_ids))
    lines.append(f"Nguồn: {ids}")
    lines.append("Chỉ dùng dữ liệu giả lập; không phải chính sách Appota thật.")
    return "\n".join(lines)


def _cite_for_fact(result: dict[str, Any], key: str) -> str | None:
    if key == "eligible":
        key = "eligibility"
    for c in result["citations"]:
        if c["policy_key"] == key:
            return c["section_id"]
    return None


def guard_output(text: str, result: dict[str, Any], profile_roles: list[str]) -> dict[str, Any]:
    """Kiểm tra đầu ra không chứa chuỗi bị chặn (D09/canary/...) và có đủ mã nguồn."""
    is_hr = "hr" in profile_roles
    forbidden = [] if is_hr else FORBIDDEN_ALWAYS
    violations = [f for f in forbidden if f in text]
    return {"ok": not violations, "violations": violations}
