#!/usr/bin/env python3
"""
Minimal web UI for TikTok tracking jobs.
"""
from __future__ import annotations

import asyncio
import html
import json
from urllib.parse import quote as urlquote
import threading
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse

import config
from src.database import Database
from run_automated import run_snapshot, run_analysis


app = FastAPI(title="TikTok Tracking UI")
db = Database()

jobs_lock = threading.Lock()
jobs: Dict[str, Dict[str, Any]] = {}


def _format_dt(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    return str(value)


def _remain_text(job: Dict[str, Any]) -> str:
    status = job.get("status") or ""
    remaining = int(job.get("remaining_seconds", 0))
    if status == "waiting_t2" and remaining > 0:
        return f"{remaining // 60}m {remaining % 60}s"
    return "-"


def _progress_html(job: Dict[str, Any]) -> str:
    status = job.get("status") or ""
    total_u = int(job.get("total_urls") or 0)
    processed = job.get("processed_urls")
    if status in ("running_t1", "running_t2") and total_u > 0 and processed is not None:
        pct = min(100.0, 100.0 * float(processed) / float(total_u))
        return (
            f"<p><b>Tien do URL:</b> {processed} / {total_u} ({pct:.1f}%)</p>"
            '<div style="background:#eee;border-radius:6px;height:24px;overflow:hidden;max-width:560px">'
            f'<div style="background:#1f4e78;height:100%;width:{pct:.1f}%"></div></div>'
        )
    if status == "waiting_t2" and total_u > 0:
        return (
            f"<p><b>Snapshot 1:</b> da xu ly xong {total_u}/{total_u} URL. "
            f"Dang cho den snapshot 2...</p>"
        )
    if status == "analyzing":
        return (
            "<p><b>Tien do:</b> Dang phan tich &amp; xuat bao cao "
            "(khong theo tung URL).</p>"
        )
    return ""


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


def _run_job(job_id: str, urls: List[str], interval_hours: float) -> None:
    try:
        session_id = db.create_session(check_interval_hours=interval_hours, total_products=len(urls))
        total = len(urls)

        def progress_t1(current: int, tot: int) -> None:
            _set_job(
                job_id,
                processed_urls=current,
                total_urls=tot,
                message=f"Dang chay snapshot 1... ({current}/{tot})",
            )

        _set_job(
            job_id,
            status="running_t1",
            session_id=session_id,
            message=f"Dang chay snapshot 1... (0/{total})",
            processed_urls=0,
            total_urls=total,
            started_at=datetime.now(),
        )

        success1, errors1, snap1_report = asyncio.run(
            run_snapshot(urls, session_id, snapshot_order=1, on_progress=progress_t1)
        )
        _set_job(
            job_id,
            status="waiting_t2",
            message="Snapshot 1 xong, dang doi den snapshot 2...",
            snapshot1={"success": success1, "errors": errors1, "report": snap1_report},
            next_check_at=datetime.now().timestamp() + (interval_hours * 3600),
            processed_urls=total,
        )

        wait_seconds = max(int(interval_hours * 3600), 0)
        for remain in range(wait_seconds, -1, -1):
            if remain % 5 == 0:
                _set_job(job_id, remaining_seconds=remain)
            time.sleep(1)

        def progress_t2(current: int, tot: int) -> None:
            _set_job(
                job_id,
                processed_urls=current,
                total_urls=tot,
                message=f"Dang chay snapshot 2... ({current}/{tot})",
            )

        _set_job(
            job_id,
            status="running_t2",
            message=f"Dang chay snapshot 2... (0/{total})",
            processed_urls=0,
            total_urls=total,
        )
        success2, errors2, snap2_report = asyncio.run(
            run_snapshot(urls, session_id, snapshot_order=2, on_progress=progress_t2)
        )
        _set_job(
            job_id,
            snapshot2={"success": success2, "errors": errors2, "report": snap2_report},
            status="analyzing",
            message="Dang phan tich va xuat bao cao...",
            processed_urls=None,
        )

        run_analysis(session_id)
        outputs = [f.name for f in _find_session_outputs(session_id)]

        _set_job(
            job_id,
            status="completed",
            message="Hoan tat!",
            outputs=outputs,
            completed_at=datetime.now(),
            remaining_seconds=0,
        )
    except Exception as exc:  # pragma: no cover
        _set_job(job_id, status="failed", message=f"Loi: {exc}", completed_at=datetime.now())


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    with jobs_lock:
        recent_jobs = list(jobs.values())[-20:][::-1]

    rows = ""
    esc = html.escape
    for j in recent_jobs:
        jn = j.get("job_name") or "-"
        rows += (
            f"<tr><td><a href='/jobs/{j['job_id']}'>{j['job_id'][:8]}</a></td>"
            f"<td>{esc(str(jn))}</td>"
            f"<td>{j.get('session_id','-')}</td>"
            f"<td>{j.get('status','-')}</td>"
            f"<td>{_format_dt(j.get('created_at'))}</td></tr>"
        )

    if not rows:
        rows = "<tr><td colspan='5'>Chua co job nao</td></tr>"

    return f"""
    <html><head><title>TikTok Tracking</title>
    <style>
    body{{font-family:Arial,sans-serif;max-width:980px;margin:24px auto;padding:0 16px}}
    textarea{{width:100%;height:220px}}
    input,button{{padding:8px}}
    table{{width:100%;border-collapse:collapse;margin-top:14px}}
    td,th{{border:1px solid #ddd;padding:8px;text-align:left}}
    .box{{border:1px solid #ddd;padding:16px;border-radius:8px;margin:12px 0}}
    </style></head><body>
    <h2>TikTok Shop Tracking UI</h2>
    <div class="box">
      <form method="post" action="/run">
        <label><b>Ten job (tuy chon — de phan biet tung niche / file SP):</b></label><br/>
        <input type="text" name="job_name" style="width:100%;max-width:560px" maxlength="120"
               placeholder="Vi du: Phu kien dien thoai T4"/><br/><br/>
        <label><b>URLs (moi dong 1 link):</b></label><br/>
        <textarea name="urls" placeholder="https://www.tiktok.com/view/product/..."></textarea><br/><br/>
        <label><b>Interval (gio):</b></label>
        <input type="number" step="0.01" min="0" name="interval_hours" value="3"/><br/><br/>
        <button type="submit">Run Tracking</button>
      </form>
    </div>
    <div class="box">
      <h3>Recent Jobs</h3>
      <table><tr><th>Job</th><th>Ten job</th><th>Session</th><th>Status</th><th>Created</th></tr>{rows}</table>
    </div>
    </body></html>
    """


@app.post("/run")
def run_tracking(
    urls: str = Form(...),
    interval_hours: float = Form(3.0),
    job_name: str = Form(""),
) -> RedirectResponse:
    parsed = [line.strip() for line in urls.splitlines() if line.strip() and not line.strip().startswith("#")]
    if not parsed:
        raise HTTPException(status_code=400, detail="Danh sach URL dang rong.")

    name_clean = job_name.strip()[:120] or None

    job_id = uuid.uuid4().hex
    created = datetime.now()

    with jobs_lock:
        jobs[job_id] = {
            "job_id": job_id,
            "job_name": name_clean,
            "status": "queued",
            "created_at": created,
            "message": "Dang xep hang...",
            "interval_hours": interval_hours,
            "total_urls": len(parsed),
            "remaining_seconds": int(interval_hours * 3600),
            "outputs": [],
        }

    worker = threading.Thread(target=_run_job, args=(job_id, parsed, interval_hours), daemon=True)
    worker.start()

    return RedirectResponse(url=f"/jobs/{job_id}", status_code=303)


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
        "progress_html": _progress_html(job),
        "remain_text": _remain_text(job),
        "created_at": _format_dt(job.get("created_at")),
        "completed_at": _format_dt(job.get("completed_at")),
        "outputs": outputs,
        "terminal": job.get("status") in ("completed", "failed"),
    }


@app.get("/jobs/{job_id}", response_class=HTMLResponse)
def job_detail(job_id: str) -> str:
    with jobs_lock:
        job = jobs.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        _sync_outputs_into_job(job)
        outputs = list(job.get("outputs", []))

    outputs_html = ""
    for name in outputs:
        safe_name = html.escape(name)
        outputs_html += (
            f"<li><a href='/files/{urlquote(name, safe='')}'>{safe_name}</a></li>"
        )
    if not outputs_html:
        outputs_html = "<li>Chua co file output.</li>"

    progress_block = _progress_html(job)
    remain_text = _remain_text(job)
    esc = html.escape
    job_title = esc(job.get("job_name") or "")
    job_heading = (
        f"{esc(job_id[:8])} — {job_title}"
        if job.get("job_name")
        else esc(job_id[:8])
    )

    poll_script = ""
    if job.get("status") not in ("completed", "failed"):
        poll_script = f"""
    <script>
    (function() {{
      const jobId = {json.dumps(job_id)};
      function renderOutputs(names) {{
        const ul = document.getElementById('js-outputs');
        if (!names.length) {{
          ul.innerHTML = '<li>Chua co file output.</li>';
          return;
        }}
        ul.innerHTML = names.map(function(n) {{
          const esc = (s) => String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;')
            .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
          return '<li><a href="/files/' + encodeURIComponent(n) + '">' + esc(n) + '</a></li>';
        }}).join('');
      }}
      async function poll() {{
        try {{
          const r = await fetch('/api/jobs/' + encodeURIComponent(jobId));
          if (!r.ok) return;
          const d = await r.json();
          document.getElementById('js-status').textContent = d.status || '';
          document.getElementById('js-message').textContent = d.message || '';
          document.getElementById('js-progress').innerHTML = d.progress_html || '';
          document.getElementById('js-remain').textContent = d.remain_text || '-';
          document.getElementById('js-completed').textContent = d.completed_at || '-';
          renderOutputs(d.outputs || []);
          if (d.terminal) {{
            clearInterval(timer);
          }}
        }} catch (e) {{}}
      }}
      const timer = setInterval(poll, 5000);
      poll();
    }})();
    </script>"""

    return f"""
    <html><head><title>Job {esc(job_id[:8])}</title>
    <style>body{{font-family:Arial,sans-serif;max-width:980px;margin:24px auto;padding:0 16px}}
    .box{{border:1px solid #ddd;padding:16px;border-radius:8px;margin:12px 0}}</style></head><body>
    <h2>Job {job_heading}</h2>
    <a href="/">← Back</a>
    <div class="box">
      <p><b>Ten job:</b> {esc(str(job.get('job_name') or '-'))}</p>
      <p><b>Status:</b> <span id="js-status">{esc(str(job.get('status','')))}</span></p>
      <p><b>Message:</b> <span id="js-message">{esc(str(job.get('message','')))}</span></p>
      <div id="js-progress">{progress_block}</div>
      <p><b>Session ID:</b> {esc(str(job.get('session_id','-')))}</p>
      <p><b>Total URLs:</b> {esc(str(job.get('total_urls','-')))}</p>
      <p><b>Remaining (cho snapshot 2):</b> <span id="js-remain">{esc(remain_text)}</span></p>
      <p><b>Created:</b> {_format_dt(job.get('created_at'))}</p>
      <p><b>Completed:</b> <span id="js-completed">{_format_dt(job.get('completed_at'))}</span></p>
    </div>
    <div class="box">
      <h3>Output Files</h3>
      <ul id="js-outputs">{outputs_html}</ul>
    </div>
{poll_script}
    </body></html>
    """


@app.get("/files/{filename}")
def download_file(filename: str) -> FileResponse:
    safe_name = Path(filename).name
    file_path = config.OUTPUT_DIR / safe_name
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path=file_path, filename=safe_name)

