"""Slurm CLI adapter — communicates via subprocess calls to squeue, sinfo, sacct, sbatch."""

import asyncio
import json
import os
import re
import tempfile
from datetime import datetime

from app.slurm.models import FairShare, Job, JobSubmitRequest, Node, Partition


async def _run(cmd: list[str]) -> str:
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(f"Command {cmd[0]} failed (rc={proc.returncode}): {stderr.decode()}")
    return stdout.decode()


def _ts(epoch: int | None) -> datetime | None:
    if not epoch or epoch <= 0:
        return None
    return datetime.utcfromtimestamp(epoch)


def _parse_tres_value(tres_str: str, key: str) -> int:
    """Parse a value from a TRES string like 'cpu=4,mem=8G,node=2,billing=4'."""
    match = re.search(rf"{key}=(\d+)", tres_str or "")
    return int(match.group(1)) if match else 0


def _parse_gres_gpus(gres_str: str) -> int:
    """Parse GPU count from GRES string like 'gpu:2' or 'gpu:a100:4'."""
    match = re.search(r"gpu:(?:\w+:)?(\d+)", gres_str or "")
    return int(match.group(1)) if match else 0


def _uid_to_username(uid: int | None) -> str:
    """Resolve UID to username via /etc/passwd."""
    if not uid:
        return ""
    try:
        import pwd
        return pwd.getpwuid(uid).pw_name
    except (KeyError, ImportError):
        return str(uid)


async def get_jobs(user: str | None = None) -> list[Job]:
    cmd = ["squeue", "--json"]
    if user:
        cmd += ["--user", user]
    raw = json.loads(await _run(cmd))
    jobs = []
    for j in raw.get("jobs", []):
        # Some Slurm versions return empty user_name; fall back to uid lookup
        username = j.get("user_name") or _uid_to_username(j.get("user_id"))
        jobs.append(Job(
            job_id=j["job_id"],
            array_job_id=j.get("array_job_id") or None,
            array_task_id=j.get("array_task_id") if isinstance(j.get("array_task_id"), int) and j.get("array_task_id") >= 0 else None,
            user=username,
            account=j.get("account", ""),
            partition=j.get("partition", ""),
            name=j.get("name", ""),
            state=j.get("job_state", "UNKNOWN"),
            state_reason=j.get("state_reason", ""),
            num_cpus=j.get("cpus", {}).get("number", 0) if isinstance(j.get("cpus"), dict) else (j.get("cpus") or 0),
            num_nodes=j.get("node_count", {}).get("number", 0) if isinstance(j.get("node_count"), dict) else (j.get("node_count") or 0),
            num_gpus=_parse_gres_gpus(j.get("gres_detail", [""])[0] if j.get("gres_detail") else ""),
            memory_mb=j.get("memory_per_node", {}).get("number", 0) if isinstance(j.get("memory_per_node"), dict) else 0,
            time_limit_seconds=(j.get("time_limit", {}).get("number", 0) or 0) * 60 if isinstance(j.get("time_limit"), dict) else None,
            submit_time=_ts(j.get("submit_time", {}).get("number") if isinstance(j.get("submit_time"), dict) else j.get("submit_time")),
            start_time=_ts(j.get("start_time", {}).get("number") if isinstance(j.get("start_time"), dict) else j.get("start_time")),
            end_time=_ts(j.get("end_time", {}).get("number") if isinstance(j.get("end_time"), dict) else j.get("end_time")),
            node_list=j.get("nodes", ""),
            work_dir=j.get("current_working_directory", ""),
            std_out=j.get("standard_output", ""),
            std_err=j.get("standard_error", ""),
            qos=j.get("qos", ""),
        ))
    return jobs


async def get_nodes() -> list[Node]:
    raw = json.loads(await _run(["sinfo", "--json"]))
    nodes: dict[str, Node] = {}
    for n in raw.get("nodes", []):
        name = n.get("name", "")
        state = n.get("state", ["unknown"])
        state_str = state[0] if isinstance(state, list) else state

        gres = n.get("gres", "") or ""
        gpu_count = _parse_gres_gpus(gres)
        gres_used = n.get("gres_used", "") or ""
        gpus_alloc = _parse_gres_gpus(gres_used)

        nodes[name] = Node(
            name=name,
            state=state_str,
            reason=n.get("reason", "") or "",
            cpus_total=n.get("cpus", 0),
            cpus_allocated=n.get("alloc_cpus", 0),
            memory_mb=n.get("real_memory", 0),
            memory_allocated_mb=n.get("alloc_memory", 0),
            gpus_total=gpu_count,
            gpus_allocated=gpus_alloc,
            partitions=n.get("partitions", []) or [],
        )
    return list(nodes.values())


async def get_partitions() -> list[Partition]:
    raw = json.loads(await _run(["scontrol", "show", "partition", "--json"]))
    partitions = []
    for p in raw.get("partitions", []):
        name = p.get("name", "")
        nodes_raw = p.get("nodes", {})
        total_nodes = nodes_raw.get("total", 0) if isinstance(nodes_raw, dict) else 0
        total_cpus = p.get("cpus", {}).get("total", 0) if isinstance(p.get("cpus"), dict) else 0
        max_time = p.get("maximum_time", {})
        max_time_sec = (max_time.get("number", 0) * 60) if isinstance(max_time, dict) else None
        if max_time_sec == 0:
            max_time_sec = None

        mem = p.get("defaults", {}).get("memory_per_cpu", {})
        default_mem = mem.get("number") if isinstance(mem, dict) else None

        partitions.append(Partition(
            name=name,
            state=p.get("state", {}).get("current", ["UP"])[0] if isinstance(p.get("state"), dict) else "UP",
            total_nodes=total_nodes,
            total_cpus=total_cpus,
            max_time_seconds=max_time_sec,
            default_memory_per_cpu_mb=default_mem,
            has_gpus="gpu" in (p.get("gres", "") or "").lower(),
        ))
    return partitions


async def get_job_detail(job_id: int) -> Job | None:
    try:
        raw = json.loads(await _run(["scontrol", "show", "job", str(job_id), "--json"]))
        jobs = raw.get("jobs", [])
        if not jobs:
            return None
        j = jobs[0]
        return Job(
            job_id=j["job_id"],
            user=j.get("user_name") or _uid_to_username(j.get("user_id")),
            account=j.get("account", ""),
            partition=j.get("partition", ""),
            name=j.get("name", ""),
            state=j.get("job_state", {}).get("current", ["UNKNOWN"])[0] if isinstance(j.get("job_state"), dict) else j.get("job_state", "UNKNOWN"),
            state_reason=j.get("state_reason", ""),
            num_cpus=j.get("cpus", {}).get("number", 0) if isinstance(j.get("cpus"), dict) else j.get("cpus", 0),
            num_nodes=j.get("node_count", {}).get("number", 0) if isinstance(j.get("node_count"), dict) else 1,
            num_gpus=_parse_gres_gpus(j.get("gres_detail", [""])[0] if j.get("gres_detail") else ""),
            memory_mb=j.get("memory_per_node", {}).get("number", 0) if isinstance(j.get("memory_per_node"), dict) else 0,
            time_limit_seconds=(j.get("time_limit", {}).get("number", 0) or 0) * 60 if isinstance(j.get("time_limit"), dict) else None,
            submit_time=_ts(j.get("submit_time", {}).get("number") if isinstance(j.get("submit_time"), dict) else j.get("submit_time")),
            start_time=_ts(j.get("start_time", {}).get("number") if isinstance(j.get("start_time"), dict) else j.get("start_time")),
            end_time=_ts(j.get("end_time", {}).get("number") if isinstance(j.get("end_time"), dict) else j.get("end_time")),
            node_list=j.get("nodes", ""),
            work_dir=j.get("current_working_directory", ""),
            std_out=j.get("standard_output", ""),
            std_err=j.get("standard_error", ""),
            qos=j.get("qos", ""),
        )
    except Exception:
        return None


async def cancel_job(job_id: int) -> None:
    await _run(["scancel", str(job_id)])


async def hold_job(job_id: int) -> None:
    await _run(["scontrol", "hold", str(job_id)])


async def requeue_job(job_id: int) -> None:
    await _run(["scontrol", "requeue", str(job_id)])


async def signal_job(job_id: int, signal: str) -> None:
    await _run(["scancel", f"--signal={signal}", str(job_id)])


async def submit_job(req: JobSubmitRequest, as_user: str | None = None) -> int:
    """Writes a batch script to a temp file and runs sbatch --parsable."""
    lines = ["#!/bin/bash"]
    lines.append(f"#SBATCH --job-name={req.job_name}")
    lines.append(f"#SBATCH --partition={req.partition}")
    lines.append(f"#SBATCH --nodes={req.num_nodes}")
    lines.append(f"#SBATCH --ntasks={req.num_tasks}")
    lines.append(f"#SBATCH --cpus-per-task={req.num_cpus_per_task}")
    if req.memory_mb:
        lines.append(f"#SBATCH --mem={req.memory_mb}M")
    total_seconds = req.time_limit_seconds
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    lines.append(f"#SBATCH --time={hours:02d}:{minutes:02d}:{seconds:02d}")
    if req.account:
        lines.append(f"#SBATCH --account={req.account}")
    if req.qos:
        lines.append(f"#SBATCH --qos={req.qos}")
    if req.num_gpus:
        lines.append(f"#SBATCH --gres=gpu:{req.num_gpus}")
    if req.std_out:
        lines.append(f"#SBATCH --output={req.std_out}")
    if req.std_err:
        lines.append(f"#SBATCH --error={req.std_err}")
    lines.append("")
    # Environment variables
    for k, v in req.env_vars.items():
        lines.append(f"export {k}={v}")
    if req.env_vars:
        lines.append("")
    lines.append(req.script_body)

    script = "\n".join(lines)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False) as f:
        f.write(script)
        script_path = f.name

    try:
        cmd = ["sbatch", "--parsable", script_path]
        if as_user:
            pass  # sbatch runs as the current OS user; sudoing is cluster-specific
        stdout = await _run(cmd)
        job_id = int(stdout.strip().split(";")[0])
        return job_id
    finally:
        os.unlink(script_path)


async def create_cluster_user(username: str, account: str = "default") -> None:
    """Create a Linux user and register them in Slurm accounting."""
    # Create Linux user (no login shell, no home dir creation needed for HPC)
    try:
        await _run(["useradd", "--create-home", "--shell", "/bin/bash", username])
    except RuntimeError as e:
        if "already exists" not in str(e):
            raise

    # Add Slurm account if it doesn't exist
    try:
        await _run(["sacctmgr", "-i", "add", "account", account,
                    "Description=User account", "Organization=cluster"])
    except RuntimeError:
        pass  # account may already exist

    # Add user to Slurm accounting under the account
    await _run(["sacctmgr", "-i", "add", "user", username,
                "Account=" + account, "DefaultAccount=" + account])


async def get_fairshare(user: str) -> FairShare:
    try:
        stdout = await _run(["sshare", "-u", user, "--parsable2", "-l"])
        lines = [l for l in stdout.strip().splitlines() if l and not l.startswith("Account")]
        for line in lines:
            parts = line.split("|")
            if len(parts) >= 7 and parts[1].strip() == user:
                try:
                    fs = float(parts[6]) if parts[6] else 0.0
                except ValueError:
                    fs = 0.0
                return FairShare(
                    user=user,
                    account=parts[0].strip(),
                    fairshare_factor=fs,
                    raw_usage=float(parts[5]) if parts[5] else 0.0,
                )
    except Exception:
        pass
    return FairShare(user=user)


async def get_accounting(start_time: str, end_time: str) -> list[dict]:
    """Returns raw sacct data for analytics aggregation."""
    try:
        stdout = await _run([
            "sacct",
            "--json",
            f"--starttime={start_time}",
            f"--endtime={end_time}",
            "--allocations",
        ])
        raw = json.loads(stdout)
        return raw.get("jobs", [])
    except Exception:
        return []


async def get_job_stats(job_id: int) -> dict:
    """Get live resource utilization for a running job via sstat."""
    stats: dict = {"cpu_efficiency": None, "memory_rss_mb": None, "gpu_util_pct": None}
    try:
        stdout = await _run([
            "sstat", "-j", str(job_id),
            "--format=JobID,AveCPU,MaxRSS,TRESUsageInTot",
            "--parsable2", "--noheader", "-a",
        ])
        lines = [l for l in stdout.strip().splitlines() if l and ".batch" in l]
        if lines:
            parts = lines[0].split("|")
            # MaxRSS: e.g. "1024K" or "256M"
            rss_str = parts[2].strip() if len(parts) > 2 else ""
            if rss_str.endswith("K"):
                stats["memory_rss_mb"] = round(int(rss_str[:-1]) / 1024, 1)
            elif rss_str.endswith("M"):
                stats["memory_rss_mb"] = round(float(rss_str[:-1]), 1)
            elif rss_str.endswith("G"):
                stats["memory_rss_mb"] = round(float(rss_str[:-1]) * 1024, 1)
    except Exception:
        pass

    # GPU utilization via nvidia-smi if available
    try:
        nvidia_out = await _run([
            "nvidia-smi", "--query-gpu=utilization.gpu",
            "--format=csv,noheader,nounits"
        ])
        vals = [int(v.strip()) for v in nvidia_out.strip().splitlines() if v.strip().isdigit()]
        if vals:
            stats["gpu_util_pct"] = round(sum(vals) / len(vals), 1)
    except Exception:
        pass

    return stats
