import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.database import Base, get_db
from app.main import app
from app.slurm.client import SlurmClient, set_client

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def db_engine():
    engine = create_async_engine(TEST_DB_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine):
    SessionLocal = async_sessionmaker(db_engine, expire_on_commit=False)
    async with SessionLocal() as session:
        yield session


class MockSlurmClient:
    _adapter = "mock"

    async def get_jobs(self, user=None):
        return []

    async def get_job(self, job_id):
        return None

    async def get_nodes(self):
        return []

    async def get_partitions(self):
        return []

    async def get_fairshare(self, user):
        from app.slurm.models import FairShare
        return FairShare(user=user, fairshare_factor=0.5)

    async def get_accounting(self, start_time, end_time):
        return []


@pytest_asyncio.fixture
async def client(db_engine):
    SessionLocal = async_sessionmaker(db_engine, expire_on_commit=False)
    set_client(MockSlurmClient())

    async def override_db():
        async with SessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = override_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()
