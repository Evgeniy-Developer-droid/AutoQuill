from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio.session import AsyncSession
from app.auth import auth as auth_tools
from app.billing.schemas import SubscriptionOutSchema
from app.users import models as user_models
from app.billing import schemas as billing_schemas
from app.billing import queries as billing_queries
from app.database import get_session


router = APIRouter()


@router.get("/subscription", response_model=billing_schemas.SubscriptionOutSchema)
async def get_subscription(
    session: AsyncSession = Depends(get_session),
    user: user_models.User = Depends(auth_tools.get_current_active_user),
):
    usages = await billing_queries.get_usages_by_company_id_timeframe_query(
        company_id=user.company.id,
        session=session,
        start_date=user.company.last_payment_at,
        end_date=user.company.subscription_valid_until
    )
    model = SubscriptionOutSchema(
        plan=user.company.current_plan,
        usages=usages,
        plan_started_at=user.company.plan_started_at,
        balance_tokens=user.company.balance_tokens,
        referral_code=user.company.referral_code,
        referred_by_id=user.company.referred_by_id,
        last_payment_at=user.company.last_payment_at,
        subscription_valid_until=user.company.subscription_valid_until,
        payment_service=user.company.payment_service
    )
    return model


@router.get("/payments", response_model=billing_schemas.PaymentListSchema)
async def get_payments(
    page: int = 1,
    limit: int = 10,
    session: AsyncSession = Depends(get_session),
    user: user_models.User = Depends(auth_tools.get_current_active_user),
):
    payments, total = await billing_queries.get_payments_query(
        company_id=user.company.id,
        page=page,
        limit=limit,
        session=session
    )
    return billing_schemas.PaymentListSchema(
        payments=payments,
        total=total
    )


@router.post("/balance/add", response_model=dict)
async def add_balance(
    data: billing_schemas.AddBalanceSchema,
    session: AsyncSession = Depends(get_session),
    user: user_models.User = Depends(auth_tools.get_current_active_user),
):
    # if amount <= 0:
    #     raise HTTPException(status_code=400, detail="Amount must be greater than zero.")
    #
    # await billing_queries.add_balance_query(
    #     company_id=user.company.id,
    #     amount=amount,
    #     session=session
    # )

    return {"message": "Balance successfully added."}
