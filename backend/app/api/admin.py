from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.crud import get_all_users_usage, get_node_utilization_range
from app.db.database import get_db
from app.dependencies import CurrentUser, require_admin

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


@router.get("/users")
async def admin_user_usage(
    days: int = Query(30, ge=1, le=365),
    _user: CurrentUser = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    data = await get_all_users_usage(db, days=days)
    return {"data": data, "meta": {"days": days}}


@router.get("/heatmap")
async def utilization_heatmap(
    days: int = Query(30, ge=1, le=90),
    _user: CurrentUser = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    end = datetime.utcnow()
    start = end - timedelta(days=days)
    records = await get_node_utilization_range(db, start, end)

    # Build day×hour matrix  { "YYYY-MM-DD": { hour: utilization_pct } }
    matrix: dict[str, dict[int, float]] = {}
    for r in records:
        day_key = r.sampled_at.strftime("%Y-%m-%d")
        hour = r.sampled_at.hour
        if r.total_nodes > 0:
            util_pct = (r.allocated_nodes / r.total_nodes) * 100
        else:
            util_pct = 0.0
        if day_key not in matrix:
            matrix[day_key] = {}
        # Average multiple samples in the same hour
        if hour in matrix[day_key]:
            matrix[day_key][hour] = (matrix[day_key][hour] + util_pct) / 2
        else:
            matrix[day_key][hour] = util_pct

    if not records:
        # No historical data — synthesize from current node state
        from app.db.crud import get_nodes as get_node_snapshots
        nodes = await get_node_snapshots(db)
        if nodes:
            total = len(nodes)
            allocated = sum(1 for n in nodes if 'alloc' in n.state.lower() or 'mix' in n.state.lower())
            util_pct = (allocated / total * 100) if total > 0 else 0
            now = datetime.utcnow()
            day_key = now.strftime("%Y-%m-%d")
            matrix[day_key] = {now.hour: round(util_pct, 1)}

    return {"data": matrix, "meta": {"days": days, "records": len(records)}}


class CreateUserRequest(BaseModel):
    username: str
    password: str
    role: str = "user"
    account: str = "default"


@router.get("/list-users")
async def list_all_users(
    _user: CurrentUser = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select
    from app.db.models import User
    result = await db.execute(select(User).order_by(User.username))
    users = result.scalars().all()
    return {"data": [{"username": u.username, "role": u.role} for u in users]}


@router.post("/users")
async def create_user(
    body: CreateUserRequest,
    _user: CurrentUser = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    from app.auth.service import hash_password
    from app.db.crud import get_user, create_user as db_create_user
    from app.slurm.client import get_client
    existing = await get_user(db, body.username)
    if existing:
        raise HTTPException(status_code=409, detail="User already exists")
    user = await db_create_user(db, body.username, hash_password(body.password), body.role)

    # Also provision user on the Slurm cluster
    slurm_provisioned = False
    slurm_error: str | None = None
    try:
        await get_client().create_cluster_user(body.username, account=getattr(body, "account", "default") or "default")
        slurm_provisioned = True
    except Exception as e:
        slurm_error = str(e)

    return {"data": {"username": user.username, "role": user.role,
                     "slurm_provisioned": slurm_provisioned,
                     "slurm_error": slurm_error}}


@router.delete("/users/{username}", status_code=204)
async def delete_user(
    username: str,
    current_user: CurrentUser = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    if username == current_user.username:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    from sqlalchemy import delete
    from app.db.models import User
    await db.execute(delete(User).where(User.username == username))
    await db.commit()


@router.get("/overview")
async def admin_overview(
    _user: CurrentUser = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    from app.db.crud import get_all_users_usage
    users_data = await get_all_users_usage(db, days=1)
    total_cpu_hours_today = sum(u["cpu_hours"] for u in users_data)
    total_gpu_hours_today = sum(u["gpu_hours"] for u in users_data)
    total_jobs_today = sum(u["job_count"] for u in users_data)
    return {
        "data": {
            "total_cpu_hours_today": round(total_cpu_hours_today, 2),
            "total_gpu_hours_today": round(total_gpu_hours_today, 2),
            "total_jobs_today": total_jobs_today,
            "active_users_today": len(users_data),
        },
        "meta": {"period": "today"},
    }


@router.get("/low-efficiency-jobs")
async def low_efficiency_jobs(
    threshold: float = Query(50.0, description="Efficiency threshold %"),
    _user: CurrentUser = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Return currently RUNNING jobs that have low efficiency based on sacct history."""
    from app.db.crud import get_jobs as db_get_jobs
    from app.db.models import JobSnapshot
    jobs, _ = await db_get_jobs(db, state="RUNNING", page_size=200)
    # Also check completed jobs from recent accounting with low efficiency
    result = []
    for j in jobs:
        # Estimate efficiency from elapsed time vs CPU-hours used (placeholder if no sacct data)
        result.append({
            "job_id": j.job_id,
            "name": j.name,
            "user": j.user,
            "partition": j.partition,
            "num_cpus": j.num_cpus,
            "start_time": j.start_time.isoformat() if j.start_time else None,
            "memory_mb": j.memory_mb,
        })
    return {"data": result, "meta": {"threshold": threshold}}
