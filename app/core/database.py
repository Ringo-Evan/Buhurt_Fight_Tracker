"""
Database connection and session management.

Provides async SQLAlchemy engine and session factory for FastAPI dependency injection.
"""

import ssl
from collections.abc import AsyncGenerator
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

from app.core.config import settings


def _parse_engine_args(database_url: str) -> tuple[str, dict]:
    """Strip SSL query params from asyncpg URL and return them as connect_args.

    asyncpg does not accept 'sslmode' or 'ssl' as URL query params — it needs
    an ssl.SSLContext passed via connect_args. This keeps the URL clean and
    avoids 'unexpected keyword argument' errors at runtime.
    """
    connect_args: dict = {}

    if "+asyncpg" not in database_url:
        return database_url, connect_args

    parsed = urlparse(database_url)
    params = parse_qs(parsed.query, keep_blank_values=True)

    sslmode = (params.pop("sslmode", [None])[0] or params.pop("ssl", [None])[0])
    if sslmode and sslmode not in ("disable", "false"):
        connect_args["ssl"] = ssl.create_default_context()

    clean_query = urlencode({k: v[0] for k, v in params.items()})
    clean_url = urlunparse(parsed._replace(query=clean_query))
    return clean_url, connect_args


_db_url, _connect_args = _parse_engine_args(settings.DATABASE_URL)

# Create async engine
engine = create_async_engine(
    _db_url,
    connect_args=_connect_args,
    echo=settings.DEBUG,
    future=True,
)

# Create async session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base class for models
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that provides a database session.

    Yields:
        AsyncSession: Database session for the request

    Note:
        Session is automatically closed after the request completes.
    """
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()
