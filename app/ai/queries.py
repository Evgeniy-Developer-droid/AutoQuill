from app.ai.models import Source, AIConfig
from datetime import datetime
from typing import List

from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy import select, insert, delete, update, func
import traceback


async def create_source_query(data: dict, session: AsyncSession) -> Source:
    try:
        stmt = insert(Source).values(**data).returning(Source)
        result = await session.execute(stmt)
        await session.commit()
        return result.scalars().first()
    except Exception as e:
        await session.rollback()
        traceback.print_exc()


async def delete_source_query(source_id: int, company_id: int, session: AsyncSession) -> bool:
    try:
        stmt = (
            delete(Source)
            .where(Source.id == source_id)
            .where(Source.company_id == company_id)
        )
        await session.execute(stmt)
        await session.commit()
        return True
    except Exception as e:
        await session.rollback()
        traceback.print_exc()
        return False


async def get_source_query(source_id: int, company_id: int, session: AsyncSession) -> Source:
    try:
        stmt = (
            select(Source)
            .where(Source.id == source_id)
            .where(Source.company_id == company_id)
        )
        result = await session.execute(stmt)
        return result.scalars().first()
    except Exception as e:
        traceback.print_exc()
        return None


async def get_sources_query(company_id: int, channel_id: int, page: int, limit: int, session: AsyncSession) -> tuple[List[Source], int]:
    try:
        page = max(page, 1)
        stmt = (
            select(Source)
            .where(Source.company_id == company_id)
            .where(Source.channel_id == channel_id)
            .offset((page - 1) * limit)
            .limit(limit).order_by(Source.created_at.desc())
        )
        result = await session.execute(stmt)
        sources = result.scalars().all()

        count_stmt = (
            select(func.count(Source.id))
            .where(Source.company_id == company_id)
            .where(Source.channel_id == channel_id)
        )
        count_result = await session.execute(count_stmt)
        total_count = count_result.scalar_one()

        return sources, total_count
    except Exception as e:
        traceback.print_exc()
        return [], 0


async def get_or_create_ai_config_query(
    company_id: int,
    channel_id: int,
    session: AsyncSession,
) -> AIConfig:
    try:
        stmt = (
            select(AIConfig)
            .where(AIConfig.company_id == company_id)
            .where(AIConfig.channel_id == channel_id)
        )
        result = await session.execute(stmt)
        ai_config = result.scalars().first()

        if not ai_config:
            new_ai_config = AIConfig(
                company_id=company_id,
                channel_id=channel_id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            session.add(new_ai_config)
            await session.commit()
            return new_ai_config

        return ai_config
    except Exception as e:
        traceback.print_exc()


async def update_ai_config_query(
    company_id: int,
    channel_id: int,
    data: dict,
    session: AsyncSession,
) -> AIConfig:
    try:
        stmt = (
            update(AIConfig)
            .where(AIConfig.company_id == company_id)
            .where(AIConfig.channel_id == channel_id)
            .values(**data)
            .returning(AIConfig)
        )
        result = await session.execute(stmt)
        await session.commit()
        return result.scalars().first()
    except Exception as e:
        await session.rollback()
        traceback.print_exc()
