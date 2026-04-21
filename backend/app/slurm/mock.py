"""
Mock Slurm adapter — returns realistic fake data for demos/testing.
Enable with: SLURM_INTERFACE=mock
"""

from datetime import datetime, timedelta
import random

from app.slurm.models import FairShare, Job, JobSubmitRequest, Node, Partition

_submitted_jobs: list[Job] = []
_next_job_id = 1000

_now = datetime.utcnow()

# Per-job fixed efficiency so dashboard always shows realistic variety
_JOB_STATS: dict[int, dict] = {
    # Efficient running jobs
    1001: {"cpu_efficiency": 91.2, "memory_rss_mb": 28400, "gpu_util_pct": 94.5},
    1002: {"cpu_efficiency": 87.6, "memory_rss_mb": 58000, "gpu_util_pct": 89.1},
    # Inefficient running jobs (will appear in admin low-efficiency view)
    1003: {"cpu_efficiency": 18.4, "memory_rss_mb": 4200,  "gpu_util_pct": None},
    1004: {"cpu_efficiency": 31.0, "memory_rss_mb": 12800, "gpu_util_pct": None},
    1005: {"cpu_efficiency": 8.2,  "memory_rss_mb": 620,   "gpu_util_pct": None},
    1009: {"cpu_efficiency": 22.5, "memory_rss_mb": 890,   "gpu_util_pct": 12.3},
    1010: {"cpu_efficiency": 44.8, "memory_rss_mb": 16200, "gpu_util_pct": None},
}

_DEMO_JOBS: list[Job] = [
    # ── RUNNING — efficient ──────────────────────────────────────────────────
    Job(
        job_id=1001, user="alice", account="ml-lab", partition="gpu",
        name="train-resnet50", state="RUNNING",
        num_cpus=8, num_nodes=1, num_gpus=2, memory_mb=32768,
        time_limit_seconds=14400,
        submit_time=_now - timedelta(hours=2, minutes=13),
        start_time=_now - timedelta(hours=2, minutes=10),
        std_out="/scratch/alice/slurm-1001.out",
        work_dir="/home/alice/projects/resnet",
        qos="gpu-normal",
    ),
    Job(
        job_id=1002, user="alice", account="ml-lab", partition="gpu",
        name="finetune-bert-large", state="RUNNING",
        num_cpus=4, num_nodes=1, num_gpus=4, memory_mb=65536,
        time_limit_seconds=28800,
        submit_time=_now - timedelta(hours=1, minutes=45),
        start_time=_now - timedelta(hours=1, minutes=42),
        std_out="/scratch/alice/slurm-1002.out",
        work_dir="/home/alice/projects/bert",
        qos="gpu-normal",
    ),
    # ── RUNNING — inefficient (CPU waste) ───────────────────────────────────
    Job(
        job_id=1003, user="bob", account="genomics", partition="general",
        name="preprocess-fastq", state="RUNNING",
        num_cpus=16, num_nodes=1, num_gpus=0, memory_mb=131072,
        time_limit_seconds=7200,
        submit_time=_now - timedelta(minutes=55),
        start_time=_now - timedelta(minutes=50),
        std_out="/scratch/bob/slurm-1003.out",
        work_dir="/data/genomics/project-alpha",
        qos="normal",
    ),
    Job(
        job_id=1004, user="bob", account="genomics", partition="general",
        name="mpi-md-simulation", state="RUNNING",
        num_cpus=64, num_nodes=4, num_gpus=0, memory_mb=262144,
        time_limit_seconds=43200,
        submit_time=_now - timedelta(hours=3, minutes=20),
        start_time=_now - timedelta(hours=3, minutes=18),
        std_out="/scratch/bob/slurm-1004.out",
        work_dir="/home/bob/md-sim",
        qos="high-priority",
    ),
    Job(
        job_id=1005, user="charlie", account="physics", partition="debug",
        name="postprocess-results", state="RUNNING",
        num_cpus=2, num_nodes=1, num_gpus=0, memory_mb=8192,
        time_limit_seconds=1800,
        submit_time=_now - timedelta(minutes=20),
        start_time=_now - timedelta(minutes=18),
        std_out="/scratch/charlie/slurm-1005.out",
        work_dir="/home/charlie/analysis",
        qos="debug",
    ),
    # ── RUNNING — inefficient (GPU waste + low CPU) ─────────────────────────
    Job(
        job_id=1009, user="dana", account="chem", partition="gpu",
        name="mol-dynamics-gpu", state="RUNNING",
        num_cpus=8, num_nodes=1, num_gpus=4, memory_mb=32768,
        time_limit_seconds=28800,
        submit_time=_now - timedelta(hours=1, minutes=5),
        start_time=_now - timedelta(hours=1),
        std_out="/scratch/dana/slurm-1009.out",
        work_dir="/home/dana/mol-sim",
        qos="gpu-normal",
    ),
    Job(
        job_id=1010, user="eve", account="bioinf", partition="general",
        name="blast-search", state="RUNNING",
        num_cpus=32, num_nodes=2, num_gpus=0, memory_mb=131072,
        time_limit_seconds=14400,
        submit_time=_now - timedelta(minutes=40),
        start_time=_now - timedelta(minutes=38),
        std_out="/scratch/eve/slurm-1010.out",
        work_dir="/data/bioinf/blast",
        qos="normal",
    ),
    # ── PENDING ──────────────────────────────────────────────────────────────
    Job(
        job_id=1006, user="alice", account="ml-lab", partition="gpu",
        name="hyperparameter-sweep", state="PENDING",
        state_reason="Resources",
        num_cpus=32, num_nodes=4, num_gpus=8, memory_mb=131072,
        time_limit_seconds=86400,
        submit_time=_now - timedelta(minutes=5),
        qos="gpu-high",
    ),
    Job(
        job_id=1007, user="bob", account="genomics", partition="general",
        name="genome-assembly", state="PENDING",
        state_reason="Priority",
        num_cpus=128, num_nodes=8, num_gpus=0, memory_mb=524288,
        time_limit_seconds=172800,
        submit_time=_now - timedelta(minutes=12),
        qos="high-priority",
    ),
    Job(
        job_id=1008, user="dana", account="chem", partition="general",
        name="dft-calculation", state="PENDING",
        state_reason="Resources",
        num_cpus=32, num_nodes=2, num_gpus=0, memory_mb=65536,
        time_limit_seconds=28800,
        submit_time=_now - timedelta(minutes=3),
        qos="normal",
    ),
    # ── COMPLETED ────────────────────────────────────────────────────────────
    Job(
        job_id=1011, user="alice", account="ml-lab", partition="gpu",
        name="eval-checkpoint-42", state="COMPLETED",
        num_cpus=4, num_nodes=1, num_gpus=1, memory_mb=16384,
        time_limit_seconds=3600,
        submit_time=_now - timedelta(hours=5),
        start_time=_now - timedelta(hours=4, minutes=58),
        end_time=_now - timedelta(hours=4, minutes=2),
        std_out="/scratch/alice/slurm-1011.out",
        work_dir="/home/alice/projects/resnet",
        qos="gpu-normal",
    ),
    Job(
        job_id=1012, user="bob", account="genomics", partition="general",
        name="trim-reads", state="COMPLETED",
        num_cpus=8, num_nodes=1, num_gpus=0, memory_mb=32768,
        time_limit_seconds=1800,
        submit_time=_now - timedelta(hours=3),
        start_time=_now - timedelta(hours=2, minutes=59),
        end_time=_now - timedelta(hours=2, minutes=30),
        std_out="/scratch/bob/slurm-1012.out",
        work_dir="/data/genomics/project-alpha",
        qos="normal",
    ),
    Job(
        job_id=1013, user="charlie", account="physics", partition="general",
        name="monte-carlo-run-3", state="COMPLETED",
        num_cpus=32, num_nodes=2, num_gpus=0, memory_mb=65536,
        time_limit_seconds=7200,
        submit_time=_now - timedelta(hours=10),
        start_time=_now - timedelta(hours=9, minutes=55),
        end_time=_now - timedelta(hours=7, minutes=10),
        std_out="/scratch/charlie/slurm-1013.out",
        work_dir="/home/charlie/mc-sims",
        qos="normal",
    ),
    Job(
        job_id=1014, user="eve", account="bioinf", partition="gpu",
        name="alphafold-small", state="COMPLETED",
        num_cpus=16, num_nodes=1, num_gpus=2, memory_mb=98304,
        time_limit_seconds=21600,
        submit_time=_now - timedelta(hours=8),
        start_time=_now - timedelta(hours=7, minutes=58),
        end_time=_now - timedelta(hours=3, minutes=45),
        std_out="/scratch/eve/slurm-1014.out",
        work_dir="/data/bioinf/alphafold",
        qos="gpu-normal",
    ),
    # ── FAILED ───────────────────────────────────────────────────────────────
    Job(
        job_id=1015, user="bob", account="genomics", partition="general",
        name="oom-aligner", state="FAILED",
        num_cpus=16, num_nodes=1, num_gpus=0, memory_mb=32768,
        time_limit_seconds=3600,
        submit_time=_now - timedelta(hours=6),
        start_time=_now - timedelta(hours=5, minutes=58),
        end_time=_now - timedelta(hours=5, minutes=10),
        std_out="/scratch/bob/slurm-1015.out",
        work_dir="/data/genomics/bwamem",
        qos="normal",
    ),
    Job(
        job_id=1016, user="dana", account="chem", partition="gpu",
        name="cuda-oom-test", state="FAILED",
        num_cpus=4, num_nodes=1, num_gpus=2, memory_mb=16384,
        time_limit_seconds=7200,
        submit_time=_now - timedelta(hours=12),
        start_time=_now - timedelta(hours=11, minutes=55),
        end_time=_now - timedelta(hours=11, minutes=40),
        std_out="/scratch/dana/slurm-1016.out",
        work_dir="/home/dana/cuda-tests",
        qos="gpu-normal",
    ),
    # ── CANCELLED ────────────────────────────────────────────────────────────
    Job(
        job_id=1017, user="alice", account="ml-lab", partition="gpu",
        name="wrong-config-run", state="CANCELLED",
        num_cpus=16, num_nodes=1, num_gpus=4, memory_mb=65536,
        time_limit_seconds=86400,
        submit_time=_now - timedelta(hours=4),
        start_time=_now - timedelta(hours=3, minutes=55),
        end_time=_now - timedelta(hours=3, minutes=50),
        std_out="/scratch/alice/slurm-1017.out",
        work_dir="/home/alice/projects/experiment",
        qos="gpu-normal",
    ),
    Job(
        job_id=1018, user="charlie", account="physics", partition="general",
        name="timeout-sim", state="CANCELLED",
        num_cpus=64, num_nodes=4, num_gpus=0, memory_mb=262144,
        time_limit_seconds=3600,
        submit_time=_now - timedelta(hours=7),
        start_time=_now - timedelta(hours=6, minutes=58),
        end_time=_now - timedelta(hours=5, minutes=58),
        std_out="/scratch/charlie/slurm-1018.out",
        work_dir="/home/charlie/sims",
        qos="normal",
    ),
    # ── TIMEOUT ──────────────────────────────────────────────────────────────
    Job(
        job_id=1019, user="eve", account="bioinf", partition="general",
        name="metagenome-assembly", state="TIMEOUT",
        num_cpus=32, num_nodes=2, num_gpus=0, memory_mb=131072,
        time_limit_seconds=43200,
        submit_time=_now - timedelta(hours=16),
        start_time=_now - timedelta(hours=15, minutes=55),
        end_time=_now - timedelta(hours=3, minutes=55),
        std_out="/scratch/eve/slurm-1019.out",
        work_dir="/data/bioinf/metagenome",
        qos="normal",
    ),
]

_DEMO_NODES = [
    Node(name="gpu01", state="allocated", cpus_total=32, cpus_allocated=28, memory_mb=131072, memory_allocated_mb=98304, gpus_total=8, gpus_allocated=6, partitions=["gpu"]),
    Node(name="gpu02", state="allocated", cpus_total=32, cpus_allocated=32, memory_mb=131072, memory_allocated_mb=131072, gpus_total=8, gpus_allocated=8, partitions=["gpu"]),
    Node(name="gpu03", state="idle", cpus_total=32, cpus_allocated=0, memory_mb=131072, memory_allocated_mb=0, gpus_total=8, gpus_allocated=0, partitions=["gpu"]),
    Node(name="cpu01", state="allocated", cpus_total=64, cpus_allocated=64, memory_mb=262144, memory_allocated_mb=262144, partitions=["general"]),
    Node(name="cpu02", state="allocated", cpus_total=64, cpus_allocated=64, memory_mb=262144, memory_allocated_mb=262144, partitions=["general"]),
    Node(name="cpu03", state="allocated", cpus_total=64, cpus_allocated=48, memory_mb=262144, memory_allocated_mb=131072, partitions=["general"]),
    Node(name="cpu04", state="allocated", cpus_total=64, cpus_allocated=12, memory_mb=262144, memory_allocated_mb=32768, partitions=["general"]),
    Node(name="cpu05", state="idle", cpus_total=64, cpus_allocated=0, memory_mb=262144, memory_allocated_mb=0, partitions=["general"]),
    Node(name="cpu06", state="down", cpus_total=64, cpus_allocated=0, memory_mb=262144, memory_allocated_mb=0, reason="not responding", partitions=["general"]),
    Node(name="cpu07", state="drain", cpus_total=64, cpus_allocated=0, memory_mb=262144, memory_allocated_mb=0, reason="scheduled maintenance", partitions=["general"]),
    Node(name="debug01", state="idle", cpus_total=16, cpus_allocated=0, memory_mb=32768, memory_allocated_mb=0, partitions=["debug"]),
]

_DEMO_PARTITIONS = [
    Partition(name="general", state="UP", total_nodes=8, total_cpus=512, max_time_seconds=86400, has_gpus=False),
    Partition(name="gpu", state="UP", total_nodes=3, total_cpus=96, max_time_seconds=259200, has_gpus=True),
    Partition(name="debug", state="UP", total_nodes=1, total_cpus=16, max_time_seconds=1800, has_gpus=False),
]


async def get_jobs(user=None) -> list[Job]:
    all_jobs = _DEMO_JOBS + _submitted_jobs
    if user:
        return [j for j in all_jobs if j.user == user]
    return all_jobs


async def get_nodes() -> list[Node]:
    return _DEMO_NODES


async def get_partitions() -> list[Partition]:
    return _DEMO_PARTITIONS


async def get_job_detail(job_id: int) -> Job | None:
    for j in _DEMO_JOBS + _submitted_jobs:
        if j.job_id == job_id:
            return j
    return None


async def cancel_job(job_id: int) -> None:
    for j in _DEMO_JOBS + _submitted_jobs:
        if j.job_id == job_id:
            object.__setattr__(j, 'state', 'CANCELLED')
            object.__setattr__(j, 'end_time', datetime.utcnow())
            break


async def hold_job(job_id: int) -> None:
    pass


async def requeue_job(job_id: int) -> None:
    pass


async def signal_job(job_id: int, signal: str) -> None:
    pass


async def submit_job(req: JobSubmitRequest, as_user: str | None = None) -> int:
    global _next_job_id
    job_id = _next_job_id
    _next_job_id += 1
    job = Job(
        job_id=job_id,
        user=as_user or "demo-user",
        account=req.account or "demo",
        partition=req.partition,
        name=req.job_name,
        state="PENDING",
        state_reason="Resources",
        num_cpus=req.num_cpus_per_task * req.num_tasks,
        num_nodes=req.num_nodes,
        num_gpus=req.num_gpus,
        memory_mb=req.memory_mb,
        time_limit_seconds=req.time_limit_seconds,
        submit_time=datetime.utcnow(),
        qos=req.qos or "normal",
        work_dir="/home/demo",
        std_out=f"/scratch/demo/slurm-{job_id}.out",
    )
    _submitted_jobs.append(job)
    return job_id


async def create_cluster_user(username: str, account: str = "default") -> None:
    """Mock: no-op since there's no real cluster."""
    pass


async def get_fairshare(user: str) -> FairShare:
    fs = {"alice": 0.72, "bob": 0.45, "charlie": 0.88, "dana": 0.31, "eve": 0.60}
    return FairShare(
        user=user,
        account="ml-lab",
        fairshare_factor=fs.get(user, 0.5),
        raw_usage=random.uniform(10000, 50000),
    )


async def get_accounting(start_time: str, end_time: str) -> list[dict]:
    jobs = []
    users = ["alice", "bob", "charlie", "dana", "eve"]
    partitions = ["gpu", "general", "debug"]
    for i in range(50):
        cpus = random.choice([1, 2, 4, 8, 16, 32])
        elapsed = random.randint(300, 86400)
        submit_ts = int((_now - timedelta(hours=random.randint(1, 168))).timestamp())
        jobs.append({
            "job_id": 900 + i,
            "user": random.choice(users),
            "account": "demo",
            "partition": random.choice(partitions),
            "time": {"submission": submit_ts, "elapsed": elapsed},
            "tres": {
                "requested": {"cpu": cpus},
                "consumed": {"cpu_seconds": cpus * elapsed * random.uniform(0.6, 0.95)},
            },
        })
    return jobs


async def get_job_stats(job_id: int) -> dict:
    stats = _JOB_STATS.get(job_id)
    if stats:
        return stats
    # For dynamically submitted running jobs, return decent stats
    for j in _submitted_jobs:
        if j.job_id == job_id and j.state == "RUNNING":
            return {
                "cpu_efficiency": round(random.uniform(70, 95), 1),
                "memory_rss_mb": round(random.uniform(512, (j.memory_mb or 4096) * 0.8 / 1024), 1),
                "gpu_util_pct": round(random.uniform(75, 98), 1) if (j.num_gpus or 0) > 0 else None,
            }
    return {"cpu_efficiency": None, "memory_rss_mb": None, "gpu_util_pct": None}
