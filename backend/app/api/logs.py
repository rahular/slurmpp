import asyncio
import os

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from app.core.exceptions import not_found
from app.db import crud
from app.db.database import get_db
from app.dependencies import CurrentUser, get_current_user
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])


@router.get("/{job_id}/output")
async def stream_job_output(
    job_id: int,
    follow: bool = Query(False),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """SSE endpoint that streams the job's stdout file."""
    job = await crud.get_job(db, job_id)
    if not job:
        raise not_found(f"Job {job_id}")
    if not current_user.is_admin and job.user != current_user.username:
        raise not_found(f"Job {job_id}")

    log_path = job.std_out
    # Resolve %j placeholder in Slurm output paths
    if log_path:
        log_path = log_path.replace("%j", str(job_id))

    async def event_stream():
        if not log_path or not os.path.exists(log_path):
            yield f"data: [Log file not accessible: {log_path or 'path unknown'}]\n\n"
            return

        with open(log_path, "r", errors="replace") as f:
            while True:
                line = f.readline()
                if line:
                    escaped = line.rstrip("\n").replace("\n", "\\n")
                    yield f"data: {escaped}\n\n"
                else:
                    if not follow:
                        break
                    await asyncio.sleep(0.5)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
