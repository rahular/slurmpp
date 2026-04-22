from datetime import date, datetime
from sqlalchemy import DateTime, Date, Float, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(128), nullable=False)
    role: Mapped[str] = mapped_column(String(16), nullable=False, default="user")  # "user" | "admin"
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class JobSnapshot(Base):
    __tablename__ = "job_snapshots"
    __table_args__ = (
        Index("ix_job_snapshots_user", "user"),
        Index("ix_job_snapshots_state", "state"),
        Index("ix_job_snapshots_partition", "partition"),
        Index("ix_job_snapshots_polled_at", "polled_at"),
    )

    job_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    array_job_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    array_task_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    user: Mapped[str] = mapped_column(String(64), nullable=False)
    account: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    partition: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(256), nullable=False, default="")
    state: Mapped[str] = mapped_column(String(32), nullable=False)
    state_reason: Mapped[str] = mapped_column(String(256), nullable=False, default="")
    num_cpus: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    num_nodes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    num_gpus: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    memory_mb: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    time_limit_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    submit_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    start_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    end_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    node_list: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    work_dir: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    std_out: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    std_err: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    qos: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    polled_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)


class NodeSnapshot(Base):
    __tablename__ = "node_snapshots"
    __table_args__ = (Index("ix_node_snapshots_polled_at", "polled_at"),)

    name: Mapped[str] = mapped_column(String(64), primary_key=True)
    state: Mapped[str] = mapped_column(String(32), nullable=False)
    reason: Mapped[str] = mapped_column(String(256), nullable=False, default="")
    cpus_total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cpus_allocated: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    memory_mb: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    memory_allocated_mb: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    gpus_total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    gpus_allocated: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    partitions: Mapped[str] = mapped_column(String(256), nullable=False, default="")
    polled_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)


class UsageStat(Base):
    __tablename__ = "usage_stats"
    __table_args__ = (
        Index("ix_usage_stats_user_date", "user", "date"),
        Index("ix_usage_stats_date", "date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    user: Mapped[str] = mapped_column(String(64), nullable=False)
    account: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    partition: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    cpu_hours: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    gpu_hours: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    mem_gb_hours: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    job_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    wall_hours: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    cpu_efficiency: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)


class NodeUtilization(Base):
    __tablename__ = "node_utilization"
    __table_args__ = (Index("ix_node_utilization_sampled_at", "sampled_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sampled_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    total_nodes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    allocated_nodes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    idle_nodes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    down_nodes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_cpus: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    allocated_cpus: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
