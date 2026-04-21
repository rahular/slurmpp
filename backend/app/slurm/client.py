"""
SlurmClient — selects between REST and CLI adapters at startup.
All higher-level code (API routes, poller) imports from here.
"""

from app.config import settings
from app.slurm import cli, mock, rest
from app.slurm.models import FairShare, Job, JobSubmitRequest, JobSubmitResponse, Node, Partition


class SlurmClient:
    def __init__(self, adapter: str):
        self._adapter = adapter  # "rest" | "cli" | "mock"

    @classmethod
    async def create(cls) -> "SlurmClient":
        mode = settings.slurm_interface
        if mode == "mock":
            return cls("mock")
        if mode == "rest":
            return cls("rest")
        if mode == "cli":
            return cls("cli")
        # auto: probe REST, fall back to CLI
        if await rest.check_health():
            return cls("rest")
        return cls("cli")

    # ── Jobs ─────────────────────────────────────────────────────────────────

    async def get_jobs(self, user: str | None = None) -> list[Job]:
        if self._adapter == "mock":
            return await mock.get_jobs(user)
        if self._adapter == "rest":
            return await rest.get_jobs(user)
        return await cli.get_jobs(user)

    async def get_job(self, job_id: int) -> Job | None:
        if self._adapter == "mock":
            return await mock.get_job_detail(job_id)
        if self._adapter == "rest":
            jobs = await rest.get_jobs()
            for j in jobs:
                if j.job_id == job_id:
                    return j
            return None
        return await cli.get_job_detail(job_id)

    async def cancel_job(self, job_id: int) -> None:
        if self._adapter == "mock":
            await mock.cancel_job(job_id)
        elif self._adapter == "rest":
            await rest.cancel_job(job_id)
        else:
            await cli.cancel_job(job_id)

    async def hold_job(self, job_id: int) -> None:
        if self._adapter == "mock":
            await mock.hold_job(job_id)
        elif self._adapter == "rest":
            await rest.hold_job(job_id)
        else:
            await cli.hold_job(job_id)

    async def requeue_job(self, job_id: int) -> None:
        if self._adapter == "mock":
            await mock.requeue_job(job_id)
        elif self._adapter == "rest":
            raise NotImplementedError("requeue via REST not yet implemented")
        else:
            await cli.requeue_job(job_id)

    async def signal_job(self, job_id: int, signal: str) -> None:
        if self._adapter == "mock":
            await mock.signal_job(job_id, signal)
        elif self._adapter == "rest":
            raise NotImplementedError("signal via REST not yet implemented")
        else:
            await cli.signal_job(job_id, signal)

    async def submit_job(self, req: JobSubmitRequest, as_user: str | None = None) -> int:
        if self._adapter == "mock":
            return await mock.submit_job(req, as_user=as_user)
        if self._adapter == "rest":
            return await rest.submit_job(req)
        return await cli.submit_job(req, as_user=as_user)

    # ── Cluster ───────────────────────────────────────────────────────────────

    async def get_nodes(self) -> list[Node]:
        if self._adapter == "mock":
            return await mock.get_nodes()
        if self._adapter == "rest":
            return await rest.get_nodes()
        return await cli.get_nodes()

    async def get_partitions(self) -> list[Partition]:
        if self._adapter == "mock":
            return await mock.get_partitions()
        if self._adapter == "rest":
            return await rest.get_partitions()
        return await cli.get_partitions()

    async def create_cluster_user(self, username: str, account: str = "default") -> None:
        if self._adapter == "mock":
            await mock.create_cluster_user(username, account)
        else:
            await cli.create_cluster_user(username, account)

    async def get_job_stats(self, job_id: int) -> dict:
        if self._adapter == "mock":
            return await mock.get_job_stats(job_id)
        if self._adapter == "rest":
            return await cli.get_job_stats(job_id)  # REST adapter doesn't have sstat, fall back to CLI
        return await cli.get_job_stats(job_id)

    # ── Accounting ────────────────────────────────────────────────────────────

    async def get_fairshare(self, user: str) -> FairShare:
        if self._adapter == "mock":
            return await mock.get_fairshare(user)
        return await cli.get_fairshare(user)

    async def get_accounting(self, start_time: str, end_time: str) -> list[dict]:
        if self._adapter == "mock":
            return await mock.get_accounting(start_time, end_time)
        return await cli.get_accounting(start_time, end_time)


# Module-level singleton — set during app startup
_client: SlurmClient | None = None


def set_client(client: SlurmClient) -> None:
    global _client
    _client = client


def get_client() -> SlurmClient:
    if _client is None:
        raise RuntimeError("SlurmClient not initialized")
    return _client
