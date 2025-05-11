import base64
import hashlib
import json
from app.celery_tasks import liqpay_callback_task
from app import config
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio.session import AsyncSession
from app.database import get_session


router = APIRouter()


@router.post("/payment/liqpay-callback")
async def liqpay_callback(request: Request, session: AsyncSession = Depends(get_session)):
    form_data = await request.form()
    data_b64 = form_data.get("data")
    signature = form_data.get("signature")

    expected_sig = base64.b64encode(
        hashlib.sha1((config.LIQPAY_PRIVATE_KEY + data_b64 + config.LIQPAY_PRIVATE_KEY).encode()).digest()
    ).decode()

    if signature != expected_sig:
        raise HTTPException(status_code=400, detail="Bad signature")

    json_data = json.loads(base64.b64decode(data_b64).decode())
    liqpay_callback_task.delay(json_data)
    return {"status": "ok"}


