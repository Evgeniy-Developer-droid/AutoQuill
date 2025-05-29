from datetime import datetime
from typing import Optional, List, Literal

from pydantic import BaseModel


class BillingBaseSchema(BaseModel):
    method: Literal["liqpay", "coinbase"] = "liqpay"


class UsageOutSchema(BaseModel):
    id: int
    action_type: str
    created_at: datetime

    model_config = {
        "from_attributes": True,
    }


class PlanOutSchema(BaseModel):
    id: int
    name: str
    price: int
    send_post_limit: int
    ai_generation_limit: int
    channels_limit: int
    ai_enabled: bool
    is_active: bool
    is_trial: bool

    model_config = {
        "from_attributes": True,
    }


class SubscriptionOutSchema(BaseModel):
    plan_started_at: datetime
    balance_tokens: int
    referral_code: Optional[str] = None
    referred_by_id: Optional[int] = None
    last_payment_at: Optional[datetime] = None
    subscription_valid_until: Optional[datetime] = None
    payment_service: Optional[str] = None
    plan: PlanOutSchema
    usages: List[UsageOutSchema] = []

    model_config = {
        "from_attributes": True,
    }


class PaymentOutSchema(BaseModel):
    id: int
    order_id: Optional[str] = None
    amount: int
    description: str
    is_successful: bool
    payment_service: Optional[str] = None
    created_at: datetime

    model_config = {
        "from_attributes": True,
    }


class PaymentListSchema(BaseModel):
    payments: List[PaymentOutSchema]
    total: int

    model_config = {
        "from_attributes": True,
    }


class AddBalanceSchema(BillingBaseSchema):
    one_time_plan_id: int
