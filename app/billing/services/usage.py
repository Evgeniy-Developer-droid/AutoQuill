from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.billing.models import ActionType, Usage, Plan
from app.users.models import Company


async def check_and_consume_usage(
    db: AsyncSession,
    company: Company,
    action: str,
    raise_exception: bool = True,
):
    # actions - post, ai
    month_start = company.last_payment_at

    # count usage for the current month for this company and action
    stmt = select(func.count()).where(
        Usage.company_id == company.id,
        Usage.action_type == action,
        Usage.created_at >= month_start
    )
    result = await db.execute(stmt)
    usage_count = result.scalar()

    # limits
    plan: Plan = company.current_plan
    if not plan:
        if raise_exception:
            raise HTTPException(status_code=400, detail="No active plan")
        return False, "No active plan"

    limit = plan.send_post_limit if action == ActionType.POST else plan.ai_generation_limit
    if usage_count < limit:
        # everything is ok, we can use the action
        new_usage = Usage(company_id=company.id, action_type=action)
        db.add(new_usage)
        await db.commit()
        return True, "Usage consumed"

    # if limit is reached, check if we can use tokens
    if company.balance_tokens > 0:
        company.balance_tokens -= 1
        new_usage = Usage(company_id=company.id, action_type=action)
        db.add(new_usage)
        await db.commit()
        return True, "Usage consumed with tokens"

    if raise_exception:
        raise HTTPException(status_code=402, detail="Usage limit exceeded. Upgrade plan or buy tokens.")
    return False, "Usage limit exceeded. Upgrade plan or buy tokens."