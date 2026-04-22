from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import crud
from app.db.crud import get_node_utilization_range
from app.db.database import get_db
from app.dependencies import CurrentUser, get_current_user
from app.slurm.client import get_client

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


@router.get("/usage")
async def usage_stats(
    days: int = Query(30, ge=1, le=365),
    partition: str | None = Query(None),
    account: str | None = Query(None),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stats = await crud.get_usage_stats(db, current_user.username, days=days, partition=partition, account=account)
    return {
        "data": [
            {
                "date": s.date.isoformat(),
                "user": s.user,
                "account": s.account,
                "partition": s.partition,
                "cpu_hours": s.cpu_hours,
                "gpu_hours": s.gpu_hours,
                "mem_gb_hours": s.mem_gb_hours,
                "job_count": s.job_count,
                "wall_hours": s.wall_hours,
                "cpu_efficiency": s.cpu_efficiency,
            }
            for s in stats
        ],
        "meta": {"days": days, "user": current_user.username},
    }


@router.get("/fairshare")
async def fairshare(
    current_user: CurrentUser = Depends(get_current_user),
):
    try:
        client = get_client()
        fs = await client.get_fairshare(current_user.username)
        return {"data": fs.model_dump(), "meta": {"source": "live"}}
    except Exception:
        return {
            "data": {
                "user": current_user.username,
                "fairshare_factor": None,
                "account": "",
            },
            "meta": {"source": "unavailable"},
        }


@router.get("/burn-rate")
async def burn_rate(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stats_7d = await crud.get_usage_stats(db, current_user.username, days=7)
    total_cpu_hours = sum(s.cpu_hours for s in stats_7d)
    total_gpu_hours = sum(s.gpu_hours for s in stats_7d)
    days_with_data = len({s.date for s in stats_7d}) or 1

    return {
        "data": {
            "cpu_hours_per_day": round(total_cpu_hours / days_with_data, 2),
            "gpu_hours_per_day": round(total_gpu_hours / days_with_data, 2),
            "period_days": 7,
            "total_cpu_hours": round(total_cpu_hours, 2),
            "total_gpu_hours": round(total_gpu_hours, 2),
        },
        "meta": {"user": current_user.username},
    }


@router.get("/efficiency")
async def efficiency(
    days: int = Query(30, ge=1, le=365),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stats = await crud.get_usage_stats(db, current_user.username, days=days)
    total_jobs = sum(s.job_count for s in stats)
    avg_eff = (sum(s.cpu_efficiency * s.job_count for s in stats) / total_jobs) if total_jobs > 0 else 0

    by_partition: dict[str, dict] = {}
    for s in stats:
        p = s.partition or "unknown"
        if p not in by_partition:
            by_partition[p] = {"cpu_hours": 0.0, "job_count": 0, "efficiency_sum": 0.0}
        by_partition[p]["cpu_hours"] += s.cpu_hours
        by_partition[p]["job_count"] += s.job_count
        by_partition[p]["efficiency_sum"] += s.cpu_efficiency * s.job_count

    partitions_data = [
        {
            "partition": p,
            "cpu_hours": round(v["cpu_hours"], 2),
            "job_count": v["job_count"],
            "avg_efficiency": round(v["efficiency_sum"] / v["job_count"], 1) if v["job_count"] > 0 else 0,
        }
        for p, v in by_partition.items()
    ]

    return {
        "data": {
            "total_jobs": total_jobs,
            "avg_cpu_efficiency": round(avg_eff, 1),
            "by_partition": partitions_data,
        },
        "meta": {"days": days},
    }
