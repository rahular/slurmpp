from datetime import datetime
from pydantic import BaseModel, Field


class Job(BaseModel):
    job_id: int
    array_job_id: int | None = None
    array_task_id: int | None = None
    user: str
    account: str = ""
    partition: str
    name: str = ""
    state: str
    state_reason: str = ""
    num_cpus: int = 0
    num_nodes: int = 0
    num_gpus: int = 0
    memory_mb: int = 0
    time_limit_seconds: int | None = None
    submit_time: datetime | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    node_list: str = ""
    work_dir: str = ""
    std_out: str = ""
    std_err: str = ""
    qos: str = ""


class Node(BaseModel):
    name: str
    state: str
    reason: str = ""
    cpus_total: int = 0
    cpus_allocated: int = 0
    memory_mb: int = 0
    memory_allocated_mb: int = 0
    gpus_total: int = 0
    gpus_allocated: int = 0
    partitions: list[str] = Field(default_factory=list)


class Partition(BaseModel):
    name: str
    state: str = "UP"
    total_nodes: int = 0
    total_cpus: int = 0
    max_time_seconds: int | None = None
    default_memory_per_cpu_mb: int | None = None
    max_memory_per_cpu_mb: int | None = None
    allowed_accounts: list[str] = Field(default_factory=list)
    allowed_qos: list[str] = Field(default_factory=list)
    has_gpus: bool = False


class FairShare(BaseModel):
    user: str
    account: str = ""
    fairshare_factor: float = 0.0
    raw_shares: int = 0
    normalized_shares: float = 0.0
    raw_usage: float = 0.0
    effective_usage: float = 0.0


class JobSubmitRequest(BaseModel):
    job_name: str = "slurm-job"
    partition: str
    num_nodes: int = 1
    num_cpus_per_task: int = 1
    num_tasks: int = 1
    num_gpus: int = 0
    memory_mb: int = 0
    time_limit_seconds: int = 3600
    account: str = ""
    qos: str = ""
    script_body: str = "#!/bin/bash\necho hello"
    env_vars: dict[str, str] = Field(default_factory=dict)
    std_out: str = ""
    std_err: str = ""


class JobSubmitResponse(BaseModel):
    job_id: int


class ClusterOverview(BaseModel):
    total_nodes: int = 0
    allocated_nodes: int = 0
    idle_nodes: int = 0
    down_nodes: int = 0
    drain_nodes: int = 0
    total_cpus: int = 0
    allocated_cpus: int = 0
    running_jobs: int = 0
    pending_jobs: int = 0
    completing_jobs: int = 0
    polled_at: datetime | None = None
    source: str = "cache"
