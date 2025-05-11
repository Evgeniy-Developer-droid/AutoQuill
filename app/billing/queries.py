from app.billing.models import Plan, Referral
from datetime import datetime
from typing import List

from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy import select, insert, delete, update, func
import traceback


async def get_or_create_trial_plan_query(
    db_session: AsyncSession
) -> Plan:
    try:
        stmt = select(Plan).where(Plan.is_trial == True)
        result = await db_session.execute(stmt)
        trial_plan = result.scalars().first()
        if not trial_plan:
            trial_plan = Plan(
                name="Trial",
                price=0,
                send_post_limit=10,
                ai_generation_limit=10,
                channels_limit=1,
                is_trial=True,
            )
            db_session.add(trial_plan)
            await db_session.commit()
            await db_session.refresh(trial_plan)
        return trial_plan
    except Exception as e:
        print(f"Error in get_or_create_trial_plan_query: {e}")
        traceback.print_exc()


async def create_referral_query(
    db_session: AsyncSession,
        data: dict
) -> Referral:
    try:
        referral = Referral(
            referrer_id=data["referrer_id"],
            referred_id=data["referred_id"],
            reward_given=data["reward_given"],
        )
        db_session.add(referral)
        await db_session.commit()
        await db_session.refresh(referral)
        return referral
    except Exception as e:
        print(f"Error in create_referral_query: {e}")
        traceback.print_exc()

