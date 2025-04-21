from datetime import datetime
from typing import List

from sqlalchemy.ext.asyncio.session import AsyncSession
from app.auth.models import AuthSession
from sqlalchemy import select, insert, delete, update, func
from app.posts.models import Post
import traceback


async def create_post_query(data: dict, session: AsyncSession) -> Post:
    try:
        stmt = insert(Post).values(**data).returning(Post)
        result = await session.execute(stmt)
        await session.commit()
        return result.scalars().first()
    except Exception as e:
        await session.rollback()
        traceback.print_exc()


async def update_post_query(post_id: int, data: dict, session: AsyncSession) -> Post:
    try:
        stmt = (
            update(Post)
            .where(Post.id == post_id)
            .values(**data)
            .returning(Post)
        )
        result = await session.execute(stmt)
        await session.commit()
        return result.scalars().first()
    except Exception as e:
        await session.rollback()
        traceback.print_exc()


async def delete_post_query(post_id: int, session: AsyncSession):
    try:
        stmt = delete(Post).where(Post.id == post_id)
        await session.execute(stmt)
        await session.commit()
        return True
    except Exception as e:
        await session.rollback()
        traceback.print_exc()


async def get_post_query(post_id: int, company_id: int, session: AsyncSession) -> Post:
    try:
        stmt = (
            select(Post)
            .where(Post.id == post_id)
            .where(Post.company_id == company_id)
        )
        result = await session.execute(stmt)
        return result.scalars().first()
    except Exception as e:
        traceback.print_exc()
        return None


async def get_posts_query(company_id: int, channel_id: int, page: int, limit: int, session: AsyncSession) -> tuple[List[Post], int]:
    try:
        page = max(page, 1)
        stmt = (
            select(Post)
            .where(Post.company_id == company_id)
            .where(Post.channel_id == channel_id)
            .offset((page - 1) * limit)
            .limit(limit).order_by(Post.created_at.desc())
        )
        result = await session.execute(stmt)
        posts = result.scalars().all()

        count_stmt = (
            select(func.count(Post.id))
            .where(Post.company_id == company_id)
            .where(Post.channel_id == channel_id)
        )
        count_result = await session.execute(count_stmt)
        total_count = count_result.scalar_one()

        return posts, total_count
    except Exception as e:
        traceback.print_exc()
        return [], 0


async def celery_get_posts_for_loop_query(end_date: datetime, session: AsyncSession) -> List[Post]:
    try:
        stmt = (
            select(Post)
            .where(Post.scheduled_time <= end_date)
            .where(Post.status == "scheduled")
        )
        result = await session.execute(stmt)
        return result.scalars().all()
    except Exception as e:
        traceback.print_exc()
        return []

