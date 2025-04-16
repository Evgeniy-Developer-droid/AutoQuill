from typing import List

from sqlalchemy.ext.asyncio.session import AsyncSession
from app.auth.models import AuthSession
from sqlalchemy import select, insert, delete, update, func
from app.channels.models import Channel
import traceback


async def create_channel_query(data: dict, session: AsyncSession) -> Channel:
    try:
        stmt = insert(Channel).values(**data).returning(Channel)
        result = await session.execute(stmt)
        await session.commit()
        return result.scalars().first()
    except Exception as e:
        await session.rollback()
        traceback.print_exc()


async def update_channel_query(channel_id: int, data: dict, session: AsyncSession) -> Channel:
    try:
        stmt = (
            update(Channel)
            .where(Channel.id == channel_id)
            .values(**data)
            .returning(Channel)
        )
        result = await session.execute(stmt)
        await session.commit()
        return result.scalars().first()
    except Exception as e:
        await session.rollback()
        traceback.print_exc()


async def delete_channel_query(channel_id: int, session: AsyncSession):
    try:
        stmt = delete(Channel).where(Channel.id == channel_id)
        await session.execute(stmt)
        await session.commit()
        return True
    except Exception as e:
        await session.rollback()
        traceback.print_exc()


async def get_channel_query(channel_id: int, company_id: int, session: AsyncSession) -> Channel:
    try:
        stmt = (
            select(Channel)
            .where(Channel.id == channel_id)
            .where(Channel.company_id == company_id)
        )
        result = await session.execute(stmt)
        return result.scalars().first()
    except Exception as e:
        traceback.print_exc()
        return None


async def get_channels_query(company_id: int, page: int, limit: int, session: AsyncSession) -> tuple[List[Channel], int]:
    try:
        page = max(page, 1)
        stmt = (
            select(Channel)
            .where(Channel.company_id == company_id)
            .offset((page - 1) * limit)
            .limit(limit)
        )
        result = await session.execute(stmt)
        channels = result.scalars().all()

        count_stmt = (
            select(func.count(Channel.id))
            .where(Channel.company_id == company_id)
        )
        count_result = await session.execute(count_stmt)
        total_count = count_result.scalar_one()

        return channels, total_count
    except Exception as e:
        traceback.print_exc()
        return [], 0

