from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.billing.models import Referral
from app.users.models import Company

BONUS_TOKENS = 10

async def process_referral_reward(db: AsyncSession, referred_company_id: int):
    result = await db.execute(
        select(Referral).where(
            Referral.referred_id == referred_company_id,
            Referral.reward_given == False
        )
    )
    referral = result.scalar()
    if not referral:
        return  # No referral found or already rewarded

    # Update the referral record to mark the reward as given
    result = await db.execute(select(Company).where(Company.id == referral.referrer_id))
    referrer = result.scalar()
    if not referrer:
        return

    referrer.balance_tokens += BONUS_TOKENS
    referral.reward_given = True
    await db.commit()