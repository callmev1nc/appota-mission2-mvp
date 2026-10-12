"""API — Vercel serverless entry. Routing theo path gốc (rewrite giữ nguyên path)."""
from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from fastapi import FastAPI, Request  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.responses import FileResponse  # noqa: E402

from app.engine import ask as engine_ask  # noqa: E402
from app.engine import load_dataset  # noqa: E402
from app.llm import compose  # noqa: E402
from app.render import STATUS_LABELS  # noqa: E402

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent

app = FastAPI(title="appota-leave-mvp", version="0.2.0")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)


# Chạy local (uvicorn api.index:app) thì serve luôn trang tĩnh;
# trên Vercel, file tĩnh được hệ thống phục vụ trước nên các route này không kích hoạt.
@app.get("/")
async def index_page():
    return FileResponse(ROOT_DIR / "index.html")


@app.get("/styles.css")
async def styles():
    return FileResponse(ROOT_DIR / "styles.css", media_type="text/css")


@app.get("/app.js")
async def app_js():
    return FileResponse(ROOT_DIR / "app.js", media_type="application/javascript")


def _profiles_payload() -> dict:
    ds = load_dataset()
    orgs = {o["id"]: o for o in ds["organizations"]}
    return {
        "evaluation_date": ds["evaluation_date"],
        "disclaimer": ds["disclaimer"],
        "profiles": [
            {
                "id": p["id"],
                "display_name": p["display_name"],
                "unit_path": p["unit_path"],
                "unit_names": [orgs[u]["name"] for u in p["unit_path"]],
                "read_roles": p["read_roles"],
                "employment_type": p["employment_type"],
                "tenure_months": p["tenure_months"],
            }
            for p in ds["profiles"]
        ],
        "organizations": ds["organizations"],
    }


def _documents_payload(profile_id: str | None) -> dict:
    """Danh mục tài liệu theo góc nhìn hồ sơ (tài liệu bị chặn quyền ẩn metadata)."""
    from app.engine import _base_filter, load_dataset as _load

    ds = _load()
    orgs = {o["id"]: o for o in ds["organizations"]}
    profiles = {p["id"]: p for p in ds["profiles"]}
    profile = profiles.get(profile_id) if profile_id else None

    docs = []
    for d in ds["documents"]:
        row = {
            "id": d["id"],
            "title": d["title"],
            "kind": d["kind"],
            "unit_name": orgs[d["applicability"]["unit_id"]]["name"],
            "version": d["version"],
            "publication_status": d["publication_status"],
            "policy_authority": d["policy_authority"],
            "effective": [d.get("effective_from"), d.get("effective_to")],
        }
        if profile and profile.get("unit_path"):
            readable = set(profile.get("read_roles", [])) & set(d.get("read_roles", []))
            if not readable:
                row["visibility"] = "restricted"
                row["title"] = "(không hiển thị cho hồ sơ này)"
                row.pop("kind", None)
            else:
                included, reasons = _base_filter(
                    d, profile, profile["unit_path"], _eval_date()
                )
                row["visibility"] = "included" if included else "excluded"
                row["reasons"] = reasons
        else:
            row["visibility"] = "all"
        docs.append(row)
    return {"documents": docs}


def _eval_date():
    from datetime import date

    return date.fromisoformat(load_dataset()["evaluation_date"])


@app.get("/api/health")
async def health():
    ds = load_dataset()
    return {"ok": True, "topic": "annual_leave", "dataset_id": ds["dataset_id"],
            "evaluation_date": ds["evaluation_date"]}


@app.get("/api/profiles")
async def profiles():
    return _profiles_payload()


@app.get("/api/documents")
async def documents(profile_id: str = ""):
    return _documents_payload(profile_id or None)


@app.post("/api/ask")
async def ask_endpoint(request: Request):
    body = await request.json()
    question = (body.get("question") or "").strip()
    if not question:
        return {"error": "question_required"}
    profile_id = body.get("profile_id") or ""
    date = body.get("date") or None
    mode = body.get("llm") or "auto"  # auto | template | gemini
    simulate = body.get("simulate") or []

    result = engine_ask(profile_id, question, date)
    result = compose(result, question, mode=mode, simulate=simulate)
    result["status_label"] = STATUS_LABELS.get(result["status"], result["status"])
    return result
