from datetime import datetime, timedelta
from sqlalchemy import delete, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import JobSnapshot, NodeSnapshot, NodeUtilization, UsageStat, User


# ── User ─────────────────────────────────────────────────────────────────────

async def get_user(db: AsyncSession, username: str) -> User | None:
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, username: str, hashed_password: str, role: str = "user") -> User:
    user = User(username=username, hashed_password=hashed_password, role=role)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def count_users(db: AsyncSession) -> int:
    result = await db.execute(select(func.count()).select_from(User))
    return result.scalar_one()


# ── JobSnapshot ───────────────────────────────────────────────────────────────

async def upsert_job_snapshot(db: AsyncSession, snapshot: JobSnapshot) -> None:
    existing = await db.get(JobSnapshot, snapshot.job_id)
    if existing:
        for col in JobSnapshot.__table__.columns:
            if col.name != "job_id":
                setattr(existing, col.name, getattr(snapshot, col.name))
    else:
        db.add(snapshot)
    await db.commit()


async def upsert_job_snapshots_bulk(db: AsyncSession, snapshots: list[JobSnapshot]) -> None:
    for snapshot in snapshots:
        existing = await db.get(JobSnapshot, snapshot.job_id)
        if existing:
            for col in JobSnapshot.__table__.columns:
                if col.name != "job_id":
                    setattr(existing, col.name, getattr(snapshot, col.name))
        else:
            db.add(snapshot)
    await db.commit()


async def get_jobs(
    db: AsyncSession,
    state: str | None = None,
    user: str | None = None,
    partition: str | None = None,
    account: str | None = None,
    page: int = 1,
    page_size: int = 50,
    sort_by: str = "submit_time",
    sort_order: str = "desc",
) -> tuple[list[JobSnapshot], int]:
    query = select(JobSnapshot)
    count_query = select(func.count()).select_from(JobSnapshot)

    filters = []
    if state:
        filters.append(JobSnapshot.state == state.upper())
    if user:
        filters.append(JobSnapshot.user == user)
    if partition:
        filters.append(JobSnapshot.partition == partition)
    if account:
        filters.append(JobSnapshot.account == account)

    for f in filters:
        query = query.where(f)
        count_query = count_query.where(f)

    col = getattr(JobSnapshot, sort_by, JobSnapshot.submit_time)
    query = query.order_by(col.desc() if sort_order == "desc" else col.asc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    count_result = await db.execute(count_query)
    return result.scalars().all(), count_result.scalar_one()


async def get_job(db: AsyncSession, job_id: int) -> JobSnapshot | None:
    return await db.get(JobSnapshot, job_id)


async def purge_old_job_snapshots(db: AsyncSession, hours: int = 24) -> None:
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    await db.execute(
        delete(JobSnapshot).where(
            (JobSnapshot.polled_at < cutoff) &
            (JobSnapshot.state.in_(["COMPLETED", "FAILED", "CANCELLED", "TIMEOUT", "NODE_FAIL"]))
        )
    )
    await db.commit()


# ── NodeSnapshot ──────────────────────────────────────────────────────────────

async def upsert_node_snapshots_bulk(db: AsyncSession, snapshots: list[NodeSnapshot]) -> None:
    for snapshot in snapshots:
        existing = await db.get(NodeSnapshot, snapshot.name)
        if existing:
            for col in NodeSnapshot.__table__.columns:
                if col.name != "name":
                    setattr(existing, col.name, getattr(snapshot, col.name))
        else:
            db.add(snapshot)
    await db.commit()


async def get_nodes(db: AsyncSession) -> list[NodeSnapshot]:
    result = await db.execute(select(NodeSnapshot))
    return result.scalars().all()


# ── NodeUtilization ───────────────────────────────────────────────────────────

async def insert_node_utilization(db: AsyncSession, record: NodeUtilization) -> None:
    db.add(record)
    await db.commit()


async def get_node_utilization_range(
    db: AsyncSession, start: datetime, end: datetime
) -> list[NodeUtilization]:
    result = await db.execute(
        select(NodeUtilization)
        .where(NodeUtilization.sampled_at >= start)
        .where(NodeUtilization.sampled_at <= end)
        .order_by(NodeUtilization.sampled_at)
    )
    return result.scalars().all()


# ── UsageStat ─────────────────────────────────────────────────────────────────

async def upsert_usage_stats_bulk(db: AsyncSession, stats: list[UsageStat]) -> None:
    for stat in stats:
        result = await db.execute(
            select(UsageStat).where(
                (UsageStat.date == stat.date) &
                (UsageStat.user == stat.user) &
                (UsageStat.account == stat.account) &
                (UsageStat.partition == stat.partition)
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            existing.cpu_hours = stat.cpu_hours
            existing.gpu_hours = stat.gpu_hours
            existing.mem_gb_hours = stat.mem_gb_hours
            existing.job_count = stat.job_count
            existing.wall_hours = stat.wall_hours
            existing.cpu_efficiency = stat.cpu_efficiency
        else:
            db.add(stat)
    await db.commit()


async def get_usage_stats(
    db: AsyncSession,
    user: str,
    days: int = 30,
    partition: str | None = None,
    account: str | None = None,
) -> list[UsageStat]:
    start_date = (datetime.utcnow() - timedelta(days=days)).date()
    query = select(UsageStat).where(
        (UsageStat.user == user) & (UsageStat.date >= start_date)
    )
    if partition:
        query = query.where(UsageStat.partition == partition)
    if account:
        query = query.where(UsageStat.account == account)
    query = query.order_by(UsageStat.date)
    result = await db.execute(query)
    return result.scalars().all()


async def get_all_users_usage(db: AsyncSession, days: int = 30) -> list[dict]:
    start_date = (datetime.utcnow() - timedelta(days=days)).date()
    result = await db.execute(
        select(
            UsageStat.user,
            func.sum(UsageStat.cpu_hours).label("total_cpu_hours"),
            func.sum(UsageStat.gpu_hours).label("total_gpu_hours"),
            func.sum(UsageStat.job_count).label("total_jobs"),
            func.avg(UsageStat.cpu_efficiency).label("avg_efficiency"),
        )
        .where(UsageStat.date >= start_date)
        .group_by(UsageStat.user)
        .order_by(func.sum(UsageStat.cpu_hours).desc())
    )
    rows = result.all()
    return [
        {
            "user": r.user,
            "cpu_hours": round(r.total_cpu_hours or 0, 2),
            "gpu_hours": round(r.total_gpu_hours or 0, 2),
            "job_count": int(r.total_jobs or 0),
            "avg_efficiency": round(r.avg_efficiency or 0, 1),
        }
        for r in rows
    ]
