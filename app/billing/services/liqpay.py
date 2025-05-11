from uuid import uuid4

from app.billing.models import Plan
from app import config
import base64
import json
import hashlib


def generate_liqpay_data_and_signature(data: dict, private_key: str, public_key: str):
    data["public_key"] = public_key
    json_data = json.dumps(data)
    encoded_data = base64.b64encode(json_data.encode()).decode()
    signature_str = private_key + encoded_data + private_key
    signature = base64.b64encode(hashlib.sha1(signature_str.encode()).digest()).decode()
    return encoded_data, signature


def create_liqpay_subscription_data(company_id: int, plan: Plan):
    order_id = f"{company_id}-{uuid4().hex}-{plan.id}"
    liqpay_data = {
        "action": "subscribe",
        "version": "3",
        "amount": plan.price,
        "currency": "USD",
        "description": f"Підписка на тариф {plan.name}",
        "order_id": order_id,
        "subscribe_periodicity": "month",  # або "day", "week"
        "server_url": f"{config.BACKEND_URL}/webhooks/payment/liqpay-callback",
        "result_url": f"{config.FRONTEND_URL}/dashboard/subscription/success",
        "sandbox": 1 if config.LIQPAY_SANDBOX else 0
    }

    data, signature = generate_liqpay_data_and_signature(
        liqpay_data,
        private_key=config.LIQPAY_PRIVATE_KEY,
        public_key=config.LIQPAY_PUBLIC_KEY
    )

    return {
        "liqpay_url": "https://www.liqpay.ua/api/3/checkout",
        "data": data,
        "signature": signature,
        "order_id": order_id
    }

