"""Slurm REST adapter — communicates via slurmrestd HTTP API."""

from datetime import datetime

import httpx

from app.config import settings
from app.slurm.models import FairShare, Job, JobSubmitRequest, Node, Partition


def _client() -> httpx.AsyncClient:
    headers = {}
    if settings.slurm_rest_token:
        headers["X-SLURM-USER-TOKEN"] = settings.slurm_rest_token
    return httpx.AsyncClient(
        base_url=settings.slurm_rest_url,
        headers=headers,
        timeout=30.0,
    )


def _ts(epoch: int | None) -> datetime | None:
    if not epoch or epoch <= 0:
        return None
    return datetime.utcfromtimestamp(epoch)


async def check_health() -> bool:
    try:
        async with _client() as c:
            resp = await c.get(f"/slurm/{settings.slurm_rest_version}/ping")
            return resp.status_code == 200
    except Exception:
        return False


async def get_jobs(user: str | None = None) -> list[Job]:
    params = {}
    if user:
        params["user"] = user
    async with _client() as c:
        resp = await c.get(f"/slurm/{settings.slurm_rest_version}/jobs", params=params)
        resp.raise_for_status()
    jobs = []
    for j in resp.json().get("jobs", []):
        jobs.append(_parse_job(j))
    return jobs


def _parse_job(j: dict) -> Job:
    def num(field):
        v = j.get(field, {})
        return v.get("number", 0) if isinstance(v, dict) else (v or 0)

    def ts(field):
        v = j.get(field, {})
        epoch = v.get("number") if isinstance(v, dict) else v
        return _ts(epoch)

    state = j.get("job_state", {})
    state_str = state.get("current", ["UNKNOWN"])[0] if isinstance(state, list) else (
        state[0] if isinstance(state, list) else (state or "UNKNOWN")
    )

    return Job(
        job_id=j["job_id"],
        user=j.get("user_name", ""),
        account=j.get("account", ""),
        partition=j.get("partition", ""),
        name=j.get("name", ""),
        state=state_str,
        state_reason=j.get("state_reason", ""),
        num_cpus=num("cpus"),
        num_nodes=num("node_count"),
        memory_mb=num("memory_per_node"),
        time_limit_seconds=num("time_limit") * 60 or None,
        submit_time=ts("submit_time"),
        start_time=ts("start_time"),
        end_time=ts("end_time"),
        node_list=j.get("nodes", ""),
        work_dir=j.get("current_working_directory", ""),
        std_out=j.get("standard_output", ""),
        std_err=j.get("standard_error", ""),
        qos=j.get("qos", ""),
    )


async def get_nodes() -> list[Node]:
    async with _client() as c:
        resp = await c.get(f"/slurm/{settings.slurm_rest_version}/nodes")
        resp.raise_for_status()
    nodes = []
    for n in resp.json().get("nodes", []):
        state = n.get("state", ["unknown"])
        state_str = state[0] if isinstance(state, list) else state
        nodes.append(Node(
            name=n.get("name", ""),
            state=state_str,
            reason=n.get("reason", "") or "",
            cpus_total=n.get("cpus", 0),
            cpus_allocated=n.get("alloc_cpus", 0),
            memory_mb=n.get("real_memory", 0),
            memory_allocated_mb=n.get("alloc_memory", 0),
            partitions=n.get("partitions", []) or [],
        ))
    return nodes


async def get_partitions() -> list[Partition]:
    async with _client() as c:
        resp = await c.get(f"/slurm/{settings.slurm_rest_version}/partitions")
        resp.raise_for_status()
    partitions = []
    for p in resp.json().get("partitions", []):
        partitions.append(Partition(
            name=p.get("name", ""),
            state="UP",
            total_nodes=p.get("nodes", {}).get("total", 0) if isinstance(p.get("nodes"), dict) else 0,
            total_cpus=p.get("cpus", {}).get("total", 0) if isinstance(p.get("cpus"), dict) else 0,
        ))
    return partitions


async def cancel_job(job_id: int) -> None:
    async with _client() as c:
        resp = await c.delete(f"/slurm/{settings.slurm_rest_version}/job/{job_id}")
        resp.raise_for_status()


async def hold_job(job_id: int) -> None:
    async with _client() as c:
        resp = await c.post(
            f"/slurm/{settings.slurm_rest_version}/job/{job_id}",
            json={"job": {"priority": {"number": 0}}},
        )
        resp.raise_for_status()


async def submit_job(req: JobSubmitRequest) -> int:
    # Build script with sbatch directives
    lines = ["#!/bin/bash"]
    lines.append(f"#SBATCH --job-name={req.job_name}")
    lines.append(f"#SBATCH --partition={req.partition}")
    lines.append(f"#SBATCH --nodes={req.num_nodes}")
    lines.append(f"#SBATCH --ntasks={req.num_tasks}")
    lines.append(f"#SBATCH --cpus-per-task={req.num_cpus_per_task}")
    if req.memory_mb:
        lines.append(f"#SBATCH --mem={req.memory_mb}M")
    total_seconds = req.time_limit_seconds
    h, r = divmod(total_seconds, 3600)
    m, s = divmod(r, 60)
    lines.append(f"#SBATCH --time={h:02d}:{m:02d}:{s:02d}")
    if req.account:
        lines.append(f"#SBATCH --account={req.account}")
    lines.append("")
    lines.append(req.script_body)
    script = "\n".join(lines)

    payload = {
        "job": {
            "name": req.job_name,
            "partition": req.partition,
            "ntasks": req.num_tasks,
            "cpus_per_task": {"number": req.num_cpus_per_task},
            "minimum_nodes": req.num_nodes,
            "time_limit": {"number": req.time_limit_seconds // 60},
        },
        "script": script,
    }
    if req.env_vars:
        payload["job"]["environment"] = {k: v for k, v in req.env_vars.items()}

    async with _client() as c:
        resp = await c.post(f"/slurm/{settings.slurm_rest_version}/job/submit", json=payload)
        resp.raise_for_status()
    return resp.json()["job_id"]
