from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

engine = create_async_engine(settings.database_url, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def seed_default_admin() -> None:
    """Create default admin user on first startup if no users exist."""
    import bcrypt
    from app.db.models import User
    from sqlalchemy import select, func

    async with AsyncSessionLocal() as session:
        count_result = await session.execute(select(func.count()).select_from(User))
        count = count_result.scalar_one()
        if count == 0:
            pw = bcrypt.hashpw(b"admin", bcrypt.gensalt()).decode()
            session.add(User(username="admin", hashed_password=pw, role="admin"))
            await session.commit()


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await seed_default_admin()


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
