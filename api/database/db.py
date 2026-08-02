import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from bot.database.models import Base, ForceSub
from sqlalchemy import select

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./wardeum.db")

# Ensure data directory exists
db_path = DATABASE_URL.replace("sqlite+aiosqlite:///", "")
if "/" in db_path or "\\" in db_path:
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

engine = create_async_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_session():
    async with AsyncSessionLocal() as session:
        yield session


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # Ensure ForceSub singleton row exists
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(ForceSub).where(ForceSub.id == 1))
        if not result.scalar_one_or_none():
            session.add(ForceSub(id=1, enabled=False, channel_id=None))
            await session.commit()
