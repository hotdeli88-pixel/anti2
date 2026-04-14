"""Async SQLAlchemy session + per-request tenancy guard."""
from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings

_settings = get_settings()

engine = create_async_engine(
    _settings.database_url,
    echo=False,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

SessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def set_tenant(session: AsyncSession, school_id: UUID | None) -> None:
    """Set row-level tenancy for this transaction (enforced by RLS)."""
    if school_id is None:
        # 미승인·관리자 전역 쿼리 시 NULL. RLS 정책에서 superuser bypass.
        await session.execute(text("RESET app.school_id"))
    else:
        await session.execute(
            text("SET LOCAL app.school_id = :sid"),
            {"sid": str(school_id)},
        )


@asynccontextmanager
async def scoped_session(school_id: UUID | None = None) -> AsyncIterator[AsyncSession]:
    """Context manager for background tasks."""
    async with SessionLocal() as session:
        await set_tenant(session, school_id)
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_db() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency. Tenancy set in `current_user` dep after auth."""
    async with SessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


# Introspection helper for health check
async def check_db() -> dict[str, Any]:
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}
