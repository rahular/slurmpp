from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
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

    return {"data": matrix, "meta": {"days": days, "records": len(records)}}


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
