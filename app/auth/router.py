from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio.session import AsyncSession
from app.auth import auth as auth_tools
from app.auth import models as auth_models, queries as auth_queries, schemas as auth_schemas
from app.users import models as user_models, queries as user_queries, schemas as user_schemas
from uuid import uuid4
from app import config, schemas as base_schemas
from app.database import get_session
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordRequestForm
from typing_extensions import Annotated


router = APIRouter()


@router.post(
    "/register", response_model=base_schemas.SuccessResponseSchema, tags=["auth"]
)
async def register_api(
    user_data: auth_schemas.RegisterUserInSchema,
    db_session: AsyncSession = Depends(get_session),
):

    company_data_dict = {
        "name": user_data.email
    }
    company = await user_queries.create_company(company_data_dict, db_session)
    if not company:
        raise HTTPException(status_code=400, detail="Something went wrong")

    user_data_dict = user_data.model_dump()
    user_data_dict["password"] = await auth_tools.hash_password(user_data_dict["password"])
    user_data_dict["is_active"] = True
    user_data_dict["company_id"] = company.id
    user = await user_queries.create_user(user_data_dict, db_session)
    if not user:
        raise HTTPException(status_code=400, detail="Email already exist")
    # settings
    user_settings = await user_queries.create_user_settings(
        {"user_id": user.id}, db_session
    )

    return {"message": "Success!"}


@router.post("/token", response_model=auth_schemas.AuthOutSchema, tags=["auth"])
async def login_api(
    data: auth_schemas.AuthInSchema, db_session: AsyncSession = Depends(get_session)
):
    user = await user_queries.get_user_by_email(data.email, db_session)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=404, detail="User is not active")
    if not await auth_tools.password_verify(data.password, user.password):
        raise HTTPException(status_code=404, detail="User not found")
    token = uuid4().hex
    auth_session = await auth_queries.create_auth_session(
        {
            "token": token,
            "user_id": user.id,
            "expired_at": datetime.now()
            + timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES),
        },
        db_session,
    )
    access_token = auth_tools.create_access_token({"jti": token, "sub": user.email})
    refresh_token = auth_tools.create_refresh_token({"jti": token, "sub": user.email})
    return {"access_token": access_token, "refresh_token": refresh_token}


@router.post(
    "/refresh",
    response_model=auth_schemas.AuthOutSchema,
    tags=["auth"],
)
async def refresh_api(
    data: auth_schemas.RefreshTokenInSchema,
    db_session: AsyncSession = Depends(get_session),
):
    token_data = auth_tools.decode_refresh_token(data.refresh_token)
    if not token_data:
        raise HTTPException(status_code=401, detail="Token expired")
    if not token_data["sub"]:
        raise HTTPException(status_code=401, detail="Token expired")
    auth_session = await auth_queries.get_auth_session(
        token_data["jti"], db_session
    )
    if not auth_session:
        raise HTTPException(status_code=401, detail="Token expired")
    return {
        "access_token": auth_tools.create_access_token(
            {"jti": token_data["jti"], "sub": token_data["sub"]}
        ),
        "refresh_token": data.refresh_token
    }


@router.get(
    "/logout", response_model=base_schemas.SuccessResponseSchema, tags=["auth"]
)
async def logout_api(
    auth_session: auth_models.AuthSession = Depends(
        auth_tools.get_current_auth_session
    ),
    db_session: AsyncSession = Depends(get_session),
):
    await auth_queries.delete_auth_session(auth_session.token, db_session)
    return {"message": "Success!"}


@router.post("/swagger/token", response_model=dict, tags=["auth"])
async def login_swagger_api(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db_session: AsyncSession = Depends(get_session),
):
    user = await user_queries.get_user_by_email(form_data.username, db_session)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=404, detail="User is not active")
    if not await auth_tools.password_verify(form_data.password, user.password):
        raise HTTPException(status_code=404, detail="User not found")

    token_hex = uuid4().hex
    auth_session = await auth_queries.create_auth_session(
        {
            "token": token_hex,
            "user_id": user.id,
            "expired_at": datetime.now()
            + timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES),
        },
        db_session,
    )
    token = auth_tools.create_access_token({"jti": token_hex, "sub": user.email})

    return {"access_token": token, "token_type": "bearer"}
