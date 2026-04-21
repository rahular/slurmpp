from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import cache
from app.core.exceptions import slurm_unavailable
from app.db.crud import get_nodes
from app.db.database import get_db
from app.dependencies import CurrentUser, get_current_user
from app.slurm.client import get_client
from app.slurm.models import ClusterOverview

router = APIRouter(prefix="/api/v1/cluster", tags=["cluster"])


@router.get("/overview", response_model=ClusterOverview)
async def cluster_overview(
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    cached = cache.get("cluster:overview")
    if cached:
        return cached

    nodes_summary = cache.get("nodes:summary") or {}
    jobs_counts = cache.get("jobs:counts") or {}

    overview = ClusterOverview(
        total_nodes=nodes_summary.get("total", 0),
        allocated_nodes=nodes_summary.get("allocated", 0),
        idle_nodes=nodes_summary.get("idle", 0),
        down_nodes=nodes_summary.get("down", 0),
        total_cpus=nodes_summary.get("total_cpus", 0),
        allocated_cpus=nodes_summary.get("alloc_cpus", 0),
        running_jobs=jobs_counts.get("running", 0),
        pending_jobs=jobs_counts.get("pending", 0),
        completing_jobs=jobs_counts.get("completing", 0),
        polled_at=datetime.utcnow(),
        source="cache",
    )
    cache.set("cluster:overview", overview, ttl=10)
    return overview


@router.get("/nodes")
async def list_nodes(
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    cached = cache.get("nodes:list")
    if cached:
        return {"data": cached, "meta": {"source": "cache"}}

    nodes = await get_nodes(db)
    result = [
        {
            "name": n.name,
            "state": n.state,
            "reason": n.reason,
            "cpus_total": n.cpus_total,
            "cpus_allocated": n.cpus_allocated,
            "memory_mb": n.memory_mb,
            "memory_allocated_mb": n.memory_allocated_mb,
            "gpus_total": n.gpus_total,
            "gpus_allocated": n.gpus_allocated,
            "partitions": n.partitions.split(",") if n.partitions else [],
            "polled_at": n.polled_at.isoformat() if n.polled_at else None,
        }
        for n in nodes
    ]
    cache.set("nodes:list", result, ttl=30)
    return {"data": result, "meta": {"source": "db"}}


@router.get("/partitions")
async def list_partitions(
    user: CurrentUser = Depends(get_current_user),
):
    cached = cache.get("partitions:list")
    if cached:
        return {"data": cached, "meta": {"source": "cache"}}

    try:
        client = get_client()
        partitions = await client.get_partitions()
        result = [p.model_dump() for p in partitions]
        cache.set("partitions:list", result, ttl=60)
        return {"data": result, "meta": {"source": "live"}}
    except Exception as e:
        raise slurm_unavailable()


@router.get("/health")
async def cluster_health():
    try:
        client = get_client()
        partitions = await client.get_partitions()
        return {"status": "ok", "adapter": client._adapter}
    except Exception:
        return {"status": "degraded"}
