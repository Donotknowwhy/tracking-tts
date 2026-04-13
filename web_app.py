#!/usr/bin/env python3
"""
Minimal web UI for TikTok tracking jobs.
"""
from __future__ import annotations

import asyncio
import os
import shutil
import threading
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
from zoneinfo import ZoneInfo

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

import json
import config
from src.database import Database
from src.proxy_check import is_http_proxy_configured, verify_http_proxy
from run_automated import run_snapshot, run_analysis, CaptchaError


app = FastAPI(title="TikTok Tracking UI")

_cors_origins = [
    "http://127.0.0.1:5173",
    "http://localhost:5173",
]
_extra = os.environ.get("CORS_ORIGINS", "").strip()
if _extra:
    _cors_origins.extend(o.strip() for o in _extra.split(",") if o.strip())

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    # Preview + production trên Vercel (*.vercel.app) không cần liệt kê từng URL
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
db = Database()

jobs_lock = threading.Lock()
jobs: Dict[str, Dict[str, Any]] = {}

# Load jobs from DB on startup
def _load_jobs_from_db():
    """Load recent jobs from database into memory on server start"""
    with jobs_lock:
        db_jobs = db.get_all_jobs(limit=50)
        for job in db_jobs:
            job_id = job["job_id"]
            # Sync outputs for completed jobs
            if job.get("session_id"):
                _sync_outputs_into_job(job)
            jobs[job_id] = job

JOBS_PROFILE_DIR = config.BASE_DIR / "browser_profiles"
JOBS_PROFILE_DIR.mkdir(exist_ok=True)

BASE_PROFILE_DIR = config.BASE_DIR / "browser_data"


def _get_job_profile_dir(job_id: str) -> Path:
    return JOBS_PROFILE_DIR / f"job_{job_id}"


def _create_job_profile(job_id: str) -> str:
    profile_dir = _get_job_profile_dir(job_id)
    if profile_dir.exists():
        shutil.rmtree(profile_dir)
    if BASE_PROFILE_DIR.exists():
        shutil.copytree(BASE_PROFILE_DIR, profile_dir)
    else:
        profile_dir.mkdir(parents=True, exist_ok=True)
    return str(profile_dir)


def _cleanup_job_profile(job_id: str) -> None:
    profile_dir = _get_job_profile_dir(job_id)
    if profile_dir.exists():
        try:
            shutil.rmtree(profile_dir)
        except Exception:
            pass


def _cleanup_stale_profiles() -> None:
    if not JOBS_PROFILE_DIR.exists():
        return
    for entry in JOBS_PROFILE_DIR.iterdir():
        if entry.is_dir() and entry.name.startswith("job_"):
            try:
                shutil.rmtree(entry)
            except Exception:
                pass


VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")


def _now_vn() -> datetime:
    """Giờ hiện tại theo múi Asia/Ho_Chi_Minh (UTC+7)."""
    return datetime.now(VN_TZ)


class JobCancelled(Exception):
    """Raised when user requests cancellation for a running job."""


def _format_dt(value: Any) -> str:
    """Hiển thị thời gian theo giờ Việt Nam (UTC+7)."""
    if value is None:
        return "-"
    if isinstance(value, datetime):
        dt = value
        if dt.tzinfo is None:
            # Dữ liệu cũ (naive): coi là đã ở giờ VN
            dt = dt.replace(tzinfo=VN_TZ)
        else:
            dt = dt.astimezone(VN_TZ)
        return dt.strftime("%d/%m/%Y %H:%M:%S")
    return str(value)


def _url_dedup_key(url: str) -> str:
    """Chuẩn hóa nhẹ để coi trùng: trim và bỏ / cuối (giữ bản gốc khi lưu job)."""
    s = url.strip()
    return s.rstrip("/") if s else ""


def _parse_urls_dedupe(raw: str) -> List[str]:
    """Mỗi dòng một URL; bỏ comment #; loại trùng, giữ thứ tự xuất hiện đầu tiên."""
    lines = [
        line.strip()
        for line in raw.splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    seen: set[str] = set()
    out: List[str] = []
    for line in lines:
        key = _url_dedup_key(line)
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(line)
    return out


def _remain_text(job: Dict[str, Any]) -> str:
    status = job.get("status") or ""
    remaining = int(job.get("remaining_seconds", 0))
    if status == "waiting_t2" and remaining > 0:
        return f"{remaining // 60}m {remaining % 60}s"
    return "-"


def _progress_payload(job: Dict[str, Any]) -> Dict[str, Any]:
    status = job.get("status") or ""
    total_u = int(job.get("total_urls") or 0)
    processed = job.get("processed_urls")
    if status in ("running_t1", "running_t2") and total_u > 0 and processed is not None:
        pct = min(100.0, 100.0 * float(processed) / float(total_u))
        return {
            "mode": "urls",
            "processed": processed,
            "total": total_u,
            "percent": round(pct, 1),
        }
    if status == "waiting_t2" and total_u > 0:
        return {"mode": "waiting", "total": total_u}
    if status == "analyzing":
        return {"mode": "analyzing"}
    return {"mode": "none"}


def _sync_outputs_into_job(job: Dict[str, Any]) -> None:
    session_id = job.get("session_id")
    if not session_id:
        return
    outs = job.setdefault("outputs", [])
    for f in _find_session_outputs(session_id):
        if f.name not in outs:
            outs.append(f.name)


def _find_session_outputs(session_id: int) -> List[Path]:
    patterns = [
        f"snapshot_1_session_{session_id}_*.xlsx",
        f"snapshot_2_session_{session_id}_*.xlsx",
        f"products_session_{session_id}_*.csv",
        f"keywords_session_{session_id}_*.csv",
        f"report_session_{session_id}_*.xlsx",
    ]
    files: List[Path] = []
    for pattern in patterns:
        files.extend(sorted(config.OUTPUT_DIR.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True))
    # de-duplicate by name while preserving order
    seen = set()
    uniq = []
    for f in files:
        if f.name not in seen:
            seen.add(f.name)
            uniq.append(f)
    return uniq


def _set_job(job_id: str, **updates: Any) -> None:
    with jobs_lock:
        if job_id in jobs:
            jobs[job_id].update(updates)
            # Sync to DB after updating memory
            db.save_job(job_id, jobs[job_id])


# Trạng thái job còn worker thread đang chạy (hoặc sắp chạy). Sau khi process tắt, không còn thread → phải xử lý khi boot.
_JOB_ACTIVE_STATUSES = frozenset(
    {"queued", "running_t1", "running_t2", "waiting_t2", "analyzing"}
)


def _reconcile_orphan_jobs_on_startup() -> None:
    """Đánh dấu failed các job đang 'treo' vì server đã dừng giữa chừng (không còn worker)."""
    msg = (
        "Server đã dừng hoặc khởi động lại khi job chưa xong. "
        'Tiến trình cũ không còn; dùng nút "Chạy lại" nếu job đã lưu danh sách URL.'
    )
    with jobs_lock:
        stale_ids = [
            jid
            for jid, j in jobs.items()
            if (j.get("status") or "") in _JOB_ACTIVE_STATUSES
        ]
    done_at = _now_vn()
    for jid in stale_ids:
        _set_job(
            jid,
            status="failed",
            message=msg,
            completed_at=done_at,
            remaining_seconds=0,
        )


def _is_cancel_requested(job_id: str) -> bool:
    with jobs_lock:
        job = jobs.get(job_id) or {}
        return bool(job.get("cancel_requested"))


def _can_cancel(job: Dict[str, Any]) -> bool:
    return (job.get("status") not in ("completed", "failed", "cancelled")) and (not job.get("cancel_requested"))


def _urls_from_stored(job: Dict[str, Any]) -> List[str]:
    raw = job.get("urls_raw") or ""
    if not raw.strip():
        return []
    return [
        ln.strip()
        for ln in raw.replace("\r\n", "\n").splitlines()
        if ln.strip()
    ]


def _can_restart(job: Dict[str, Any]) -> bool:
    if job.get("status") not in ("failed", "cancelled"):
        return False
    return bool(_urls_from_stored(job))


def _job_summary(j: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "job_id": j["job_id"],
        "job_short": j["job_id"][:8],
        "job_name": j.get("job_name"),
        "session_id": j.get("session_id"),
        "status": j.get("status"),
        "created_at": _format_dt(j.get("created_at")),
        "can_cancel": _can_cancel(j),
        "message": j.get("message"),
        "total_urls": j.get("total_urls"),
        "processed_urls": j.get("processed_urls"),
        "remain_text": _remain_text(j),
        "progress": _progress_payload(j),
        "can_restart": _can_restart(j),
    }


def _job_created_ts(job: Dict[str, Any]) -> float:
    """Timestamp để sort: job mới nhất có giá trị lớn nhất."""
    ca = job.get("created_at")
    if ca is None:
        return 0.0
    if isinstance(ca, datetime):
        dt = ca
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=VN_TZ)
        return dt.timestamp()
    return 0.0


def _recent_jobs_sorted(limit: int = 50) -> List[Dict[str, Any]]:
    """50 job gần nhất theo thời điểm tạo (mới → cũ)."""
    with jobs_lock:
        vals = list(jobs.values())
    vals.sort(key=_job_created_ts, reverse=True)
    return vals[:limit]


def _enqueue_job(
    urls: List[str],
    interval_hours: float,
    job_name: Any,
    seo_keywords: str = "",
    win_keywords: str = "",
) -> str:
    job_id = uuid.uuid4().hex
    created = _now_vn()
    with jobs_lock:
        jobs[job_id] = {
            "job_id": job_id,
            "job_name": job_name,
            "status": "queued",
            "cancel_requested": False,
            "created_at": created,
            "message": "Đang xếp hàng…",
            "interval_hours": interval_hours,
            "total_urls": len(urls),
            "remaining_seconds": int(interval_hours * 3600),
            "outputs": [],
            "seo_keywords": seo_keywords,
            "win_keywords": win_keywords,
            "urls_raw": "\n".join(urls),
        }
        # Save to DB immediately
        db.save_job(job_id, jobs[job_id])
    worker = threading.Thread(
        target=_run_job,
        args=(job_id, urls, interval_hours, seo_keywords, win_keywords),
        daemon=True,
    )
    worker.start()
    return job_id


def _restart_job_in_place(job_id: str) -> None:
    """Chạy lại với cùng job_id (failed/cancelled, đã lưu urls_raw); không tạo bản ghi mới."""
    with jobs_lock:
        job = jobs.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        if not _can_restart(job):
            raise HTTPException(
                status_code=400,
                detail="Chỉ có thể chạy lại job đã failed hoặc cancelled và còn danh sách URL đã lưu.",
            )
        urls_list = _urls_from_stored(job)
        if not urls_list:
            raise HTTPException(status_code=400, detail="Không có danh sách URL đã lưu.")
        interval = float(job.get("interval_hours") or 3)
        name = job.get("job_name")
        seo = job.get("seo_keywords") or ""
        win = job.get("win_keywords") or ""
        urls_raw = (job.get("urls_raw") or "").strip() or "\n".join(urls_list)
        created = job.get("created_at")

        jobs[job_id] = {
            "job_id": job_id,
            "job_name": name,
            "status": "queued",
            "cancel_requested": False,
            "cancel_requested_at": None,
            "created_at": created,
            "message": "Đang xếp hàng…",
            "interval_hours": interval,
            "total_urls": len(urls_list),
            "remaining_seconds": int(interval * 3600),
            "outputs": [],
            "seo_keywords": seo,
            "win_keywords": win,
            "urls_raw": urls_raw,
            "session_id": None,
            "started_at": None,
            "completed_at": None,
            "processed_urls": None,
            "snapshot1": {},
            "snapshot2": {},
        }
        db.save_job(job_id, jobs[job_id])

    worker = threading.Thread(
        target=_run_job,
        args=(job_id, urls_list, interval, seo, win),
        daemon=True,
    )
    worker.start()


def _fail_job(
    job_id: str,
    message: str,
    session_id: Any = None,
    **extra: Any,
) -> None:
    """Đặt job failed; nếu có session_id thì đồng bộ file output vào job."""
    outs: List[str] = []
    with jobs_lock:
        job = jobs.get(job_id)
        if job and session_id:
            _sync_outputs_into_job(job)
            outs = list(job.get("outputs", []))
    updates = {
        "status": "failed",
        "message": message,
        "completed_at": _now_vn(),
        "remaining_seconds": 0,
        "outputs": outs,
        **extra,
    }
    _set_job(job_id, **updates)


def _run_job(
    job_id: str,
    urls: List[str],
    interval_hours: float,
    seo_keywords: str = "",
    win_keywords: str = "",
) -> None:
    profile_dir = _create_job_profile(job_id)
    try:
        def _check_cancel() -> None:
            if _is_cancel_requested(job_id):
                raise JobCancelled("User requested cancellation")

        _check_cancel()
        if is_http_proxy_configured():
            _set_job(job_id, message="Đang kiểm tra proxy…")
            ok, proxy_err = verify_http_proxy()
            if not ok:
                _fail_job(
                    job_id,
                    "Proxy không hoạt động. Kiểm tra user/pass, hạn dùng hoặc nhà cung cấp. "
                    f"Chi tiết: {proxy_err}",
                )
                return

        session_id = db.create_session(
            check_interval_hours=interval_hours,
            total_products=len(urls),
            seo_keywords=seo_keywords.strip()[:8000] or None,
            win_keywords=win_keywords.strip()[:8000] or None,
        )
        total = len(urls)

        def progress_t1(current: int, tot: int) -> None:
            _check_cancel()
            _set_job(
                job_id,
                processed_urls=current,
                total_urls=tot,
                message=f"Đang chạy snapshot 1… ({current}/{tot})",
            )

        _check_cancel()
        _set_job(
            job_id,
            status="running_t1",
            session_id=session_id,
            message=f"Đang chạy snapshot 1… (0/{total})",
            processed_urls=0,
            total_urls=total,
            started_at=_now_vn(),
        )

        try:
            success1, errors1, snap1_report = asyncio.run(
                run_snapshot(urls, session_id, snapshot_order=1, on_progress=progress_t1, profile_dir=profile_dir)
            )
        except CaptchaError as exc:
            _fail_job(
                job_id,
                f"CAPTCHA block: TikTok chặn scraping. "
                f"Không thể tiếp tục snapshot 1 cho job này. "
                f"Chi tiết: {exc}",
                session_id=session_id,
            )
            return

        if total > 0 and success1 == 0:
            db.update_session_status(session_id, "failed")
            _fail_job(
                job_id,
                f"Lỗi: Không lấy được dữ liệu từ web (0/{total} URL thành công ở snapshot 1). "
                "Kiểm tra proxy, mạng hoặc URL (vd. net::ERR_HTTP_RESPONSE_CODE_FAILURE).",
                session_id=session_id,
                snapshot1={"success": success1, "errors": errors1, "report": snap1_report},
            )
            return

        _set_job(
            job_id,
            status="waiting_t2",
            message="Đã xong snapshot 1. Đang chờ đến snapshot 2…",
            snapshot1={"success": success1, "errors": errors1, "report": snap1_report},
            next_check_at=_now_vn().timestamp() + (interval_hours * 3600),
            processed_urls=total,
        )

        wait_seconds = max(int(interval_hours * 3600), 0)
        for remain in range(wait_seconds, -1, -1):
            _check_cancel()
            if remain % 5 == 0:
                _set_job(job_id, remaining_seconds=remain)
            time.sleep(1)

        def progress_t2(current: int, tot: int) -> None:
            _check_cancel()
            _set_job(
                job_id,
                processed_urls=current,
                total_urls=tot,
                message=f"Đang chạy snapshot 2… ({current}/{tot})",
            )

        _check_cancel()
        _set_job(
            job_id,
            status="running_t2",
            message=f"Đang chạy snapshot 2… (0/{total})",
            processed_urls=0,
            total_urls=total,
        )
        try:
            success2, errors2, snap2_report = asyncio.run(
                run_snapshot(urls, session_id, snapshot_order=2, on_progress=progress_t2, profile_dir=profile_dir)
            )
        except CaptchaError as exc:
            with jobs_lock:
                snap1_meta = (jobs.get(job_id) or {}).get("snapshot1")
            _fail_job(
                job_id,
                f"CAPTCHA block: TikTok chặn scraping. "
                f"Không thể tiếp tục snapshot 2 cho job này. "
                f"Chi tiết: {exc}",
                session_id=session_id,
                snapshot1=snap1_meta,
            )
            return

        if total > 0 and success2 == 0:
            db.update_session_status(session_id, "failed")
            with jobs_lock:
                snap1_meta = (jobs.get(job_id) or {}).get("snapshot1")
            _fail_job(
                job_id,
                f"Lỗi: Không lấy được dữ liệu từ web (0/{total} URL thành công ở snapshot 2). "
                "Kiểm tra proxy, mạng hoặc URL.",
                session_id=session_id,
                snapshot1=snap1_meta,
                snapshot2={"success": success2, "errors": errors2, "report": snap2_report},
            )
            return

        _set_job(
            job_id,
            snapshot2={"success": success2, "errors": errors2, "report": snap2_report},
            status="analyzing",
            message="Đang phân tích và xuất báo cáo…",
            processed_urls=total,
            total_urls=total,
        )

        _check_cancel()
        run_analysis(session_id)
        outputs = [f.name for f in _find_session_outputs(session_id)]

        _set_job(
            job_id,
            status="completed",
            message="Hoàn tất!",
            outputs=outputs,
            completed_at=_now_vn(),
            remaining_seconds=0,
            processed_urls=total,
            total_urls=total,
        )
    except JobCancelled:
        outputs = []
        with jobs_lock:
            job = jobs.get(job_id)
            if job:
                _sync_outputs_into_job(job)
                outputs = list(job.get("outputs", []))
        _set_job(
            job_id,
            status="cancelled",
            message="Đã hủy theo yêu cầu.",
            completed_at=_now_vn(),
            remaining_seconds=0,
            outputs=outputs,
        )
    except Exception as exc:  # pragma: no cover
        _set_job(job_id, status="failed", message=f"Lỗi: {exc}", completed_at=_now_vn())
    finally:
        _cleanup_job_profile(job_id)


class CreateJobBody(BaseModel):
    urls: str
    interval_hours: float = Field(default=3.0, ge=0)
    job_name: str = ""
    seo_keywords: str = ""
    win_keywords: str = ""


@app.get("/api/jobs")
def api_jobs_list() -> Dict[str, Any]:
    recent = _recent_jobs_sorted(50)
    return {"jobs": [_job_summary(j) for j in recent]}


@app.get("/api/jobs/stream")
async def api_jobs_stream():
    """SSE: danh sách 50 job gần nhất, push mỗi khi có thay đổi."""
    async def event_generator():
        last_snapshot = None
        while True:
            recent = _recent_jobs_sorted(50)
            summaries = [_job_summary(j) for j in recent]
            snapshot = json.dumps(summaries, ensure_ascii=False)
            if snapshot != last_snapshot:
                yield f"data: {snapshot}\n\n"
                last_snapshot = snapshot
            await asyncio.sleep(1)
    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.post("/api/jobs")
def api_create_job(body: CreateJobBody) -> Dict[str, str]:
    parsed = _parse_urls_dedupe(body.urls)
    if not parsed:
        raise HTTPException(status_code=400, detail="Danh sách URL đang trống.")
    name_clean = body.job_name.strip()[:120] or None
    seo_clean = (body.seo_keywords or "").strip()[:8000]
    win_clean = (body.win_keywords or "").strip()[:8000]
    job_id = _enqueue_job(parsed, body.interval_hours, name_clean, seo_clean, win_clean)
    return {"job_id": job_id}


@app.get("/api/jobs/{job_id}/stream")
async def api_job_stream(job_id: str):
    """SSE: push chi tiết một job, dừng khi terminal."""
    async def event_generator():
        while True:
            with jobs_lock:
                job = jobs.get(job_id)
                if not job:
                    yield f"data: {json.dumps({'error': 'Job not found'}, ensure_ascii=False)}\n\n"
                    break
                _sync_outputs_into_job(job)
                outputs = list(job.get("outputs", []))

            payload = {
                "status": job.get("status"),
                "message": job.get("message"),
                "job_name": job.get("job_name"),
                "session_id": job.get("session_id"),
                "total_urls": job.get("total_urls"),
                "processed_urls": job.get("processed_urls"),
                "progress": _progress_payload(job),
                "remain_text": _remain_text(job),
                "created_at": _format_dt(job.get("created_at")),
                "completed_at": _format_dt(job.get("completed_at")),
                "outputs": outputs,
                "can_cancel": _can_cancel(job),
                "cancel_requested": bool(job.get("cancel_requested")),
                "terminal": job.get("status") in ("completed", "failed", "cancelled"),
                "can_restart": _can_restart(job),
            }
            yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

            if payload["terminal"]:
                break
            await asyncio.sleep(1)
    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/api/jobs/{job_id}")
def api_job_status(job_id: str) -> Dict[str, Any]:
    """Lightweight JSON for live updates without full page reload."""
    with jobs_lock:
        job = jobs.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        _sync_outputs_into_job(job)
        outputs = list(job.get("outputs", []))

    return {
        "status": job.get("status"),
        "message": job.get("message"),
        "job_name": job.get("job_name"),
        "session_id": job.get("session_id"),
        "total_urls": job.get("total_urls"),
        "processed_urls": job.get("processed_urls"),
        "progress": _progress_payload(job),
        "remain_text": _remain_text(job),
        "created_at": _format_dt(job.get("created_at")),
        "completed_at": _format_dt(job.get("completed_at")),
        "outputs": outputs,
        "can_cancel": _can_cancel(job),
        "cancel_requested": bool(job.get("cancel_requested")),
        "terminal": job.get("status") in ("completed", "failed", "cancelled"),
        "can_restart": _can_restart(job),
    }


@app.post("/api/jobs/{job_id}/restart")
def api_restart_job(job_id: str) -> Dict[str, str]:
    """Chạy lại cùng job_id với URL/cấu hình đã lưu (failed / cancelled)."""
    _restart_job_in_place(job_id)
    return {"job_id": job_id}


@app.post("/api/jobs/{job_id}/cancel")
def api_cancel_job(job_id: str) -> Dict[str, Any]:
    with jobs_lock:
        job = jobs.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        if job.get("status") in ("completed", "failed", "cancelled"):
            return {"ok": False, "status": job.get("status")}
        if not job.get("cancel_requested"):
            job["cancel_requested"] = True
            job["cancel_requested_at"] = _now_vn()
            job["message"] = "Đã nhận yêu cầu hủy. Đang dừng job…"
            db.save_job(job_id, job)
    return {"ok": True}


@app.post("/jobs/{job_id}/cancel")
def cancel_job_redirect(job_id: str, request: Request) -> RedirectResponse:
    """Legacy: HTML form POST redirect."""
    with jobs_lock:
        job = jobs.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        if job.get("status") not in ("completed", "failed", "cancelled") and not job.get("cancel_requested"):
            job["cancel_requested"] = True
            job["cancel_requested_at"] = _now_vn()
            job["message"] = "Đã nhận yêu cầu hủy. Đang dừng job…"
    back_url = request.headers.get("referer") or "/"
    return RedirectResponse(url=back_url, status_code=303)


@app.get("/files/{filename}")
def download_file(filename: str) -> FileResponse:
    safe_name = Path(filename).name
    file_path = config.OUTPUT_DIR / safe_name
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path=file_path, filename=safe_name)


_BASE_DIR = Path(__file__).resolve().parent
_FRONTEND_DIST = _BASE_DIR / "frontend" / "dist"

# Load jobs from DB on startup; job đang chạy trong DB nhưng không còn thread → failed
_load_jobs_from_db()
_reconcile_orphan_jobs_on_startup()
_cleanup_stale_profiles()

if _FRONTEND_DIST.is_dir():
    app.mount("/", StaticFiles(directory=str(_FRONTEND_DIST), html=True), name="spa")
else:

    @app.get("/")
    def _frontend_not_built() -> HTMLResponse:
        return HTMLResponse(
            "<html><body style='font-family:sans-serif;padding:24px'>"
            "<p><b>Frontend chua build.</b> Chay:</p>"
            "<pre>cd frontend && npm install && npm run build</pre>"
            "<p>API van hoat dong tai <code>/api/</code> va <code>/docs</code>.</p>"
            "</body></html>",
            status_code=503,
        )
