from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio.session import AsyncSession
from app.auth import auth as auth_tools
from app.channels.models import Channel
from app.users import models as user_models, queries as user_queries, schemas as user_schemas
from app.channels import queries as channel_queries
from app.posts import queries as posts_queries
from app.database import get_session


router = APIRouter()

@router.get("/me", response_model=user_schemas.UserSchema)
async def me_api(
    user: user_models.User = Depends(auth_tools.get_current_active_user),
):
    return user


@router.put("/password", response_model=user_schemas.UserSchema)
async def update_password_api(
    password_data: user_schemas.PasswordUpdateSchema,
    user: user_models.User = Depends(auth_tools.get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Update the password for the current user.
    """
    # Check if the old password is correct
    if not await auth_tools.password_verify(password_data.old_password, user.password):
        raise HTTPException(status_code=400, detail="Incorrect old password")
    # Hash the new password
    hashed_new_password = await auth_tools.hash_password(password_data.password)

    # Update the user's password in the database
    await user_queries.update_user_query(user.id, {"password": hashed_new_password}, session=session)

    return user


@router.put("/me", response_model=user_schemas.UserSchema)
async def update_me_api(
    user_data: user_schemas.UserUpdateSchema,
    user: user_models.User = Depends(auth_tools.get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Update the current user's profile.
    """
    # Update the user's profile in the database
    await user_queries.update_user_query(user.id, user_data.model_dump(exclude_none=True), session=session)
    return user


@router.get("/dashboard", response_model=user_schemas.DashboardOutSchemas)
async def dashboard_api(
    user: user_models.User = Depends(auth_tools.get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Get the dashboard data for the current user.
    """
    company_id = user.company_id
    all_channels_count = await channel_queries.get_count_all_channels_query(company_id=company_id, session=session)
    all_posts_count = await posts_queries.get_all_posts_count_query(company_id=company_id, session=session)
    all_ai_generated_posts_count = await posts_queries.get_all_posts_ai_generated_count_query(company_id=company_id, session=session)
    last_channels: List[Channel] = await channel_queries.get_last_channels_query(company_id=company_id, limit=10, session=session)
    last_posts = await posts_queries.get_last_posts_query(company_id=company_id, limit=10, session=session)
    last_channel_logs = await channel_queries.get_last_channels_logs_query(company_id=company_id, limit=10, session=session)
    return {
        "all_channels_count": all_channels_count,
        "all_posts_count": all_posts_count,
        "all_ai_generated_posts_count": all_ai_generated_posts_count,
        "last_channels": [dict(posts_count=len(channel.posts), **channel.to_dict()) for channel in last_channels],
        "last_posts": [post.to_dict()  for post in last_posts],
        "last_channel_logs": [channel_log.to_dict()  for channel_log in last_channel_logs],
    }