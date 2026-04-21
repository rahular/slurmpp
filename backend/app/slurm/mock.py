"""
Mock Slurm adapter — returns realistic fake data for demos/testing.
Enable with: SLURM_INTERFACE=mock
"""

from datetime import datetime, timedelta
import random

from app.slurm.models import FairShare, Job, JobSubmitRequest, Node, Partition

_submitted_jobs: list[Job] = []
_next_job_id = 1000

_DEMO_JOBS = [
    Job(
        job_id=1001, user="alice", account="ml-lab", partition="gpu",
        name="train-resnet50", state="RUNNING",
        num_cpus=8, num_nodes=1, num_gpus=2, memory_mb=32768,
        time_limit_seconds=14400,
        submit_time=datetime.utcnow() - timedelta(hours=2, minutes=13),
        start_time=datetime.utcnow() - timedelta(hours=2, minutes=10),
        std_out="/scratch/alice/slurm-1001.out",
        work_dir="/home/alice/projects/resnet",
        qos="gpu-normal",
    ),
    Job(
        job_id=1002, user="alice", account="ml-lab", partition="gpu",
        name="finetune-bert-large", state="RUNNING",
        num_cpus=4, num_nodes=1, num_gpus=4, memory_mb=65536,
        time_limit_seconds=28800,
        submit_time=datetime.utcnow() - timedelta(hours=1, minutes=45),
        start_time=datetime.utcnow() - timedelta(hours=1, minutes=42),
        std_out="/scratch/alice/slurm-1002.out",
        work_dir="/home/alice/projects/bert",
        qos="gpu-normal",
    ),
    Job(
        job_id=1003, user="bob", account="genomics", partition="general",
        name="preprocess-fastq", state="RUNNING",
        num_cpus=16, num_nodes=1, num_gpus=0, memory_mb=131072,
        time_limit_seconds=7200,
        submit_time=datetime.utcnow() - timedelta(minutes=55),
        start_time=datetime.utcnow() - timedelta(minutes=50),
        std_out="/scratch/bob/slurm-1003.out",
        work_dir="/data/genomics/project-alpha",
        qos="normal",
    ),
    Job(
        job_id=1004, user="bob", account="genomics", partition="general",
        name="mpi-md-simulation", state="RUNNING",
        num_cpus=64, num_nodes=4, num_gpus=0, memory_mb=262144,
        time_limit_seconds=43200,
        submit_time=datetime.utcnow() - timedelta(hours=3, minutes=20),
        start_time=datetime.utcnow() - timedelta(hours=3, minutes=18),
        std_out="/scratch/bob/slurm-1004.out",
        work_dir="/home/bob/md-sim",
        qos="high-priority",
    ),
    Job(
        job_id=1005, user="charlie", account="physics", partition="debug",
        name="postprocess-results", state="RUNNING",
        num_cpus=2, num_nodes=1, num_gpus=0, memory_mb=8192,
        time_limit_seconds=1800,
        submit_time=datetime.utcnow() - timedelta(minutes=20),
        start_time=datetime.utcnow() - timedelta(minutes=18),
        std_out="/scratch/charlie/slurm-1005.out",
        work_dir="/home/charlie/analysis",
        qos="debug",
    ),
    Job(
        job_id=1006, user="alice", account="ml-lab", partition="gpu",
        name="hyperparameter-sweep", state="PENDING",
        state_reason="Resources",
        num_cpus=32, num_nodes=4, num_gpus=8, memory_mb=131072,
        time_limit_seconds=86400,
        submit_time=datetime.utcnow() - timedelta(minutes=5),
        qos="gpu-high",
    ),
    Job(
        job_id=1007, user="bob", account="genomics", partition="general",
        name="genome-assembly", state="PENDING",
        state_reason="Priority",
        num_cpus=128, num_nodes=8, num_gpus=0, memory_mb=524288,
        time_limit_seconds=172800,
        submit_time=datetime.utcnow() - timedelta(minutes=12),
        qos="high-priority",
    ),
    Job(
        job_id=1008, user="dana", account="chem", partition="general",
        name="dft-calculation", state="PENDING",
        state_reason="Resources",
        num_cpus=32, num_nodes=2, num_gpus=0, memory_mb=65536,
        time_limit_seconds=28800,
        submit_time=datetime.utcnow() - timedelta(minutes=3),
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
    Node(name="cpu04", state="idle", cpus_total=64, cpus_allocated=0, memory_mb=262144, memory_allocated_mb=0, partitions=["general"]),
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
    global _submitted_jobs
    _submitted_jobs = [j for j in _submitted_jobs if j.job_id != job_id]
    for j in _DEMO_JOBS:
        if j.job_id == job_id:
            object.__setattr__(j, 'state', 'CANCELLED')
            object.__setattr__(j, 'end_time', datetime.utcnow())


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


async def get_fairshare(user: str) -> FairShare:
    fs = {"alice": 0.72, "bob": 0.45, "charlie": 0.88, "dana": 0.31}
    return FairShare(
        user=user,
        account="ml-lab",
        fairshare_factor=fs.get(user, 0.5),
        raw_usage=random.uniform(10000, 50000),
    )


async def get_accounting(start_time: str, end_time: str) -> list[dict]:
    from datetime import datetime
    jobs = []
    users = ["alice", "bob", "charlie", "dana"]
    partitions = ["gpu", "general", "debug"]
    for i in range(50):
        cpus = random.choice([1, 2, 4, 8, 16, 32])
        elapsed = random.randint(300, 86400)
        submit_ts = int((datetime.utcnow() - timedelta(hours=random.randint(1, 168))).timestamp())
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
