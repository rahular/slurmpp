from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import cache
from app.core.exceptions import not_found, slurm_unavailable
from app.db import crud
from app.db.database import get_db
from app.dependencies import CurrentUser, get_current_user
from app.slurm.client import get_client

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])


@router.get("")
async def list_jobs(
    state: str | None = Query(None),
    user: str | None = Query(None),
    partition: str | None = Query(None),
    account: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    sort_by: str = Query("submit_time"),
    sort_order: str = Query("desc"),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Non-admin users can only see their own jobs
    effective_user = user
    if not current_user.is_admin and (user is None or user != current_user.username):
        effective_user = current_user.username

    jobs, total = await crud.get_jobs(
        db,
        state=state,
        user=effective_user,
        partition=partition,
        account=account,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return {
        "data": [_job_to_dict(j) for j in jobs],
        "meta": {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
        },
    }


@router.get("/{job_id}")
async def get_job(
    job_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    job = await crud.get_job(db, job_id)
    if not job:
        # Try live fetch
        try:
            client = get_client()
            live_job = await client.get_job(job_id)
            if live_job:
                return {"data": live_job.model_dump(mode="json"), "meta": {"source": "live"}}
        except Exception:
            pass
        raise not_found(f"Job {job_id}")

    if not current_user.is_admin and job.user != current_user.username:
        raise not_found(f"Job {job_id}")

    return {"data": _job_to_dict(job), "meta": {"source": "db"}}


class ActionBody(BaseModel):
    signal: str = "SIGUSR1"


@router.post("/{job_id}/cancel", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_job(
    job_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _check_job_ownership(job_id, current_user, db)
    try:
        from datetime import datetime
        client = get_client()
        await client.cancel_job(job_id)
        # Immediately update DB so job stays in history as CANCELLED
        job = await crud.get_job(db, job_id)
        if job:
            job.state = "CANCELLED"
            if not job.end_time:
                job.end_time = datetime.utcnow()
            await db.commit()
        cache.invalidate_prefix("jobs:")
        cache.invalidate("cluster:overview")
    except Exception as e:
        raise slurm_unavailable()


@router.post("/{job_id}/hold", status_code=status.HTTP_204_NO_CONTENT)
async def hold_job(
    job_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _check_job_ownership(job_id, current_user, db)
    try:
        client = get_client()
        await client.hold_job(job_id)
        cache.invalidate_prefix("jobs:")
    except Exception as e:
        raise slurm_unavailable()


@router.post("/{job_id}/requeue", status_code=status.HTTP_204_NO_CONTENT)
async def requeue_job(
    job_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _check_job_ownership(job_id, current_user, db)
    try:
        client = get_client()
        await client.requeue_job(job_id)
        cache.invalidate_prefix("jobs:")
    except Exception as e:
        raise slurm_unavailable()


@router.post("/{job_id}/signal", status_code=status.HTTP_204_NO_CONTENT)
async def signal_job(
    job_id: int,
    body: ActionBody,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _check_job_ownership(job_id, current_user, db)
    try:
        client = get_client()
        await client.signal_job(job_id, body.signal)
    except Exception as e:
        raise slurm_unavailable()


async def _check_job_ownership(job_id: int, current_user: CurrentUser, db: AsyncSession):
    if current_user.is_admin:
        return
    job = await crud.get_job(db, job_id)
    if not job or job.user != current_user.username:
        raise not_found(f"Job {job_id}")


def _job_to_dict(j) -> dict:
    return {
        "job_id": j.job_id,
        "array_job_id": j.array_job_id,
        "array_task_id": j.array_task_id,
        "user": j.user,
        "account": j.account,
        "partition": j.partition,
        "name": j.name,
        "state": j.state,
        "state_reason": j.state_reason,
        "num_cpus": j.num_cpus,
        "num_nodes": j.num_nodes,
        "num_gpus": j.num_gpus,
        "memory_mb": j.memory_mb,
        "time_limit_seconds": j.time_limit_seconds,
        "submit_time": j.submit_time.isoformat() if j.submit_time else None,
        "start_time": j.start_time.isoformat() if j.start_time else None,
        "end_time": j.end_time.isoformat() if j.end_time else None,
        "node_list": j.node_list,
        "work_dir": j.work_dir,
        "std_out": j.std_out,
        "std_err": j.std_err,
        "qos": j.qos,
        "polled_at": j.polled_at.isoformat() if hasattr(j, "polled_at") and j.polled_at else None,
    }


@router.get("/{job_id}/stats")
async def get_job_stats(
    job_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return live CPU/memory/GPU utilization for a running job."""
    job = await crud.get_job(db, job_id)
    if job and not current_user.is_admin and job.user != current_user.username:
        raise not_found(f"Job {job_id}")

    client = get_client()
    try:
        stats = await client.get_job_stats(job_id)
        return {"data": stats}
    except Exception:
        return {"data": {"cpu_efficiency": None, "memory_rss_mb": None, "gpu_util_pct": None}}
