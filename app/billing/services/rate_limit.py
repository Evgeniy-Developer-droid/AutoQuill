
from datetime import datetime, timedelta
from app import config
from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.billing.models import Plan
from app.channels.models import Channel,ChannelLog
from app.ai.models import Source
from app.users.models import Company


async def check_rate_limit(
    db: AsyncSession,
    channel: Channel,
    action: str,
    raise_exception: bool = True,
):
    now = datetime.now()
    window_start = now - timedelta(minutes=1)
    # Count the number of actions performed in the last minute
    stmt = select(func.count()).where(
        ChannelLog.channel_id == channel.id,
        ChannelLog.action == action,
        ChannelLog.created_at >= window_start
    )
    result = await db.execute(stmt)
    action_count = result.scalar() or 0
    limit = config.RATE_LIMITS_PER_MINUTE.get(action, 0)
    if action_count >= limit:
        if raise_exception:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Try again later."
            )
        return False
    return True


async def check_source_rate_limit(
    db: AsyncSession,
    channel: Channel,
    plan: Plan,
    raise_exception: bool = True,
):
    stmt = select(func.count()).where(
        Source.channel_id == channel.id
    )
    result = await db.execute(stmt)
    source_count = result.scalar() or 0
    if source_count >= plan.knowledge_base_limit:
        if raise_exception:
            raise HTTPException(
                status_code=403,
                detail="Knowledge base limit exceeded. Upgrade your plan to add more sources."
            )
        return False
    return True


