from sqlalchemy.ext.asyncio import AsyncSession

from app.billing.models import Payment
from app.billing.services.referral import process_referral_reward
from app.users.models import Company


async def handle_successful_payment(db: AsyncSession, company: Company, amount: int, description: str):
    # Add a new payment record
    payment = Payment(
        company_id=company.id,
        amount=amount,
        description=description,
        is_successful=True
    )
    db.add(payment)

    # Process referral reward
    await process_referral_reward(db, referred_company_id=company.id)

    await db.commit()