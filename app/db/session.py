from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

engine = create_async_engine(url=settings.database_url, echo=settings.debug)

async_session = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession]:
    """Yield an async database session.

    Yields:
        AsyncSession: SQLAlchemy async session.
    """
    async with async_session() as session:
        yield session
