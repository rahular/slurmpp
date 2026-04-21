"""Background poller — periodically fetches Slurm state into SQLite."""

import logging
from datetime import datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import settings
from app.core.cache import cache
from app.db.crud import (
    insert_node_utilization,
    upsert_job_snapshots_bulk,
    upsert_node_snapshots_bulk,
    upsert_usage_stats_bulk,
)
from app.db.database import AsyncSessionLocal
from app.db.models import JobSnapshot, NodeSnapshot, NodeUtilization, UsageStat
from app.slurm.client import get_client

log = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def _poll_jobs():
    try:
        client = get_client()
        jobs = await client.get_jobs()
        snapshots = [
            JobSnapshot(
                job_id=j.job_id,
                array_job_id=j.array_job_id,
                array_task_id=j.array_task_id,
                user=j.user,
                account=j.account,
                partition=j.partition,
                name=j.name,
                state=j.state,
                state_reason=j.state_reason,
                num_cpus=j.num_cpus,
                num_nodes=j.num_nodes,
                num_gpus=j.num_gpus,
                memory_mb=j.memory_mb,
                time_limit_seconds=j.time_limit_seconds,
                submit_time=j.submit_time,
                start_time=j.start_time,
                end_time=j.end_time,
                node_list=j.node_list,
                work_dir=j.work_dir,
                std_out=j.std_out,
                std_err=j.std_err,
                qos=j.qos,
                polled_at=datetime.utcnow(),
            )
            for j in jobs
        ]
        async with AsyncSessionLocal() as db:
            await upsert_job_snapshots_bulk(db, snapshots)

        # Build overview stats for cache
        running = sum(1 for j in jobs if j.state == "RUNNING")
        pending = sum(1 for j in jobs if j.state == "PENDING")
        completing = sum(1 for j in jobs if j.state == "COMPLETING")
        cache.set("jobs:counts", {"running": running, "pending": pending, "completing": completing}, ttl=30)
        cache.invalidate("cluster:overview")
        log.debug(f"Polled {len(jobs)} jobs (running={running}, pending={pending})")
    except Exception as e:
        log.warning(f"Job poll failed: {e}")


async def _poll_nodes():
    try:
        client = get_client()
        nodes = await client.get_nodes()
        snapshots = [
            NodeSnapshot(
                name=n.name,
                state=n.state,
                reason=n.reason,
                cpus_total=n.cpus_total,
                cpus_allocated=n.cpus_allocated,
                memory_mb=n.memory_mb,
                memory_allocated_mb=n.memory_allocated_mb,
                gpus_total=n.gpus_total,
                gpus_allocated=n.gpus_allocated,
                partitions=",".join(n.partitions),
                polled_at=datetime.utcnow(),
            )
            for n in nodes
        ]
        async with AsyncSessionLocal() as db:
            await upsert_node_snapshots_bulk(db, snapshots)

        # Compute utilization summary
        total = len(nodes)
        allocated = sum(1 for n in nodes if "alloc" in n.state.lower())
        idle = sum(1 for n in nodes if "idle" in n.state.lower())
        down = sum(1 for n in nodes if any(s in n.state.lower() for s in ("down", "drain", "error")))
        total_cpus = sum(n.cpus_total for n in nodes)
        alloc_cpus = sum(n.cpus_allocated for n in nodes)

        record = NodeUtilization(
            sampled_at=datetime.utcnow(),
            total_nodes=total,
            allocated_nodes=allocated,
            idle_nodes=idle,
            down_nodes=down,
            total_cpus=total_cpus,
            allocated_cpus=alloc_cpus,
        )
        async with AsyncSessionLocal() as db:
            await insert_node_utilization(db, record)

        cache.set("nodes:summary", {
            "total": total, "allocated": allocated, "idle": idle, "down": down,
            "total_cpus": total_cpus, "alloc_cpus": alloc_cpus,
        }, ttl=90)
        cache.invalidate("cluster:overview")
        log.debug(f"Polled {total} nodes (alloc={allocated}, idle={idle}, down={down})")
    except Exception as e:
        log.warning(f"Node poll failed: {e}")


async def _poll_accounting():
    try:
        client = get_client()
        end = datetime.utcnow()
        start = end - timedelta(days=1)
        raw_jobs = await client.get_accounting(
            start_time=start.strftime("%Y-%m-%dT%H:%M:%S"),
            end_time=end.strftime("%Y-%m-%dT%H:%M:%S"),
        )
        # Aggregate by (date, user, account, partition)
        buckets: dict[tuple, dict] = {}
        for j in raw_jobs:
            user = j.get("user", "")
            account = j.get("account", "")
            partition = j.get("partition", "")
            submit_ts = j.get("time", {}).get("submission", 0)
            if not submit_ts:
                continue
            day = datetime.utcfromtimestamp(submit_ts).date()
            key = (day, user, account, partition)
            if key not in buckets:
                buckets[key] = {"cpu_hours": 0.0, "gpu_hours": 0.0, "mem_gb_hours": 0.0,
                                "job_count": 0, "wall_hours": 0.0, "cpu_efficiency": 0.0}
            b = buckets[key]
            elapsed = j.get("time", {}).get("elapsed", 0)
            allocated_cpus = j.get("tres", {}).get("requested", {}).get("cpu", 0) if isinstance(j.get("tres"), dict) else 0
            used_cpus = j.get("tres", {}).get("consumed", {}).get("cpu_seconds", 0) if isinstance(j.get("tres"), dict) else 0
            wall_h = elapsed / 3600
            cpu_h = allocated_cpus * wall_h
            b["cpu_hours"] += cpu_h
            b["wall_hours"] += wall_h
            b["job_count"] += 1
            if cpu_h > 0:
                b["cpu_efficiency"] = (used_cpus / (allocated_cpus * elapsed)) * 100 if elapsed > 0 else 0

        stats = [
            UsageStat(
                date=key[0], user=key[1], account=key[2], partition=key[3],
                **vals
            )
            for key, vals in buckets.items()
        ]
        if stats:
            async with AsyncSessionLocal() as db:
                await upsert_usage_stats_bulk(db, stats)
        log.debug(f"Accounting poll: {len(raw_jobs)} jobs → {len(stats)} stat buckets")
    except Exception as e:
        log.warning(f"Accounting poll failed: {e}")


def start_scheduler():
    scheduler.add_job(_poll_jobs, "interval", seconds=settings.poll_jobs_interval, id="poll_jobs")
    scheduler.add_job(_poll_nodes, "interval", seconds=settings.poll_nodes_interval, id="poll_nodes")
    scheduler.add_job(_poll_accounting, "interval", seconds=settings.poll_accounting_interval, id="poll_accounting")
    scheduler.start()
    log.info("Slurm poller scheduler started")


def stop_scheduler():
    scheduler.shutdown(wait=False)
