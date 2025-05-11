from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio.session import AsyncSession
from app.auth import auth as auth_tools
from app.billing.models import ActionType
from app.billing.services.usage import check_and_consume_usage
from app.posts import queries as post_queries
from app.posts import schemas as post_schemas
from app.schemas import SuccessResponseSchema
from app.users import models as user_models
from app.database import get_session
from app.providers import telegram
import pytz


router = APIRouter()


@router.post("", response_model=post_schemas.PostOutSchema)
async def create_post(
    post: post_schemas.PostInSchema,
    session: AsyncSession = Depends(get_session),
    user: user_models.User = Depends(auth_tools.get_current_active_user),
):
    """
    Create a new post.
    """
    post_data = post.model_dump()
    post_data["company_id"] = user.company_id
    if post_data["scheduled_time"]:
        post_data["scheduled_time"] = post_data["scheduled_time"].replace(tzinfo=None)
        post_data['timezone'] = post.timezone or "UTC"
        user_tz = pytz.timezone(post_data['timezone'])
        localized_time = user_tz.localize(post_data["scheduled_time"])
        utc_time = localized_time.astimezone(pytz.utc)
        post_data["scheduled_time"] = utc_time.replace(tzinfo=None)
    new_post = await post_queries.create_post_query(post_data, session)
    if not new_post:
        raise HTTPException(status_code=400, detail="Failed to create post")
    return new_post


@router.put("/{post_id}", response_model=post_schemas.PostOutSchema)
async def update_post(
    post_id: int,
    post: post_schemas.PostUpdateSchema,
    session: AsyncSession = Depends(get_session),
    user: user_models.User = Depends(auth_tools.get_current_active_user),
):
    """
    Update an existing post.
    """
    existing_post = await post_queries.get_post_query(post_id, user.company_id, session)
    if not existing_post:
        raise HTTPException(status_code=404, detail="Post not found")

    updated_data = post.model_dump(exclude_none=True)

    if updated_data.get("scheduled_time"):
        updated_data["scheduled_time"] = updated_data["scheduled_time"].replace(tzinfo=None)
        updated_data['timezone'] = post.timezone or "UTC"
        user_tz = pytz.timezone(updated_data['timezone'])
        localized_time = user_tz.localize(updated_data["scheduled_time"])
        utc_time = localized_time.astimezone(pytz.utc)
        updated_data["scheduled_time"] = utc_time.replace(tzinfo=None)

    updated_post = await post_queries.update_post_query(post_id, updated_data, session)
    if not updated_post:
        raise HTTPException(status_code=400, detail="Failed to update post")
    return updated_post


@router.delete("/{post_id}")
async def delete_post(
    post_id: int,
    session: AsyncSession = Depends(get_session),
    user: user_models.User = Depends(auth_tools.get_current_active_user),
):
    """
    Delete a post.
    """
    existing_post = await post_queries.get_post_query(post_id, user.company_id, session)
    if not existing_post:
        raise HTTPException(status_code=404, detail="Post not found")

    deleted = await post_queries.delete_post_query(post_id, session)
    if not deleted:
        raise HTTPException(status_code=400, detail="Failed to delete post")
    return {"detail": "Post deleted successfully"}


@router.get("/{post_id}", response_model=post_schemas.PostOutSchema)
async def get_post(
    post_id: int,
    session: AsyncSession = Depends(get_session),
    user: user_models.User = Depends(auth_tools.get_current_active_user),
):
    """
    Get a post by ID.
    """
    existing_post = await post_queries.get_post_query(post_id, user.company_id, session)
    if not existing_post:
        raise HTTPException(status_code=404, detail="Post not found")
    return existing_post


@router.get("", response_model=post_schemas.PostListSchema)
async def list_posts(
    channel_id: int,
    page: int = 1,
    limit: int = 10,
    session: AsyncSession = Depends(get_session),
    user: user_models.User = Depends(auth_tools.get_current_active_user),
):
    """
    List posts for a specific channel.
    """
    posts, total = await post_queries.get_posts_query(user.company_id, channel_id, page, limit, session)
    return {"posts": posts, "total": total}


@router.post("/{post_id}/send", response_model=SuccessResponseSchema)
async def send_post(
    post_id: int,
    session: AsyncSession = Depends(get_session),
    user: user_models.User = Depends(auth_tools.get_current_active_user),
):
    """
    Send a post to the channel.
    """
    existing_post = await post_queries.get_post_query(post_id, user.company_id, session)
    if not existing_post:
        raise HTTPException(status_code=404, detail="Post not found")

    provider = None
    if existing_post.channel.channel_type == "telegram":
        provider = telegram.Telegram(existing_post)

    if not provider:
        raise HTTPException(status_code=404, detail="Post not found")

    await check_and_consume_usage(
        db=session,
        company=user.company,
        action=ActionType.POST,
    )

    result = await provider.send()
    if not result:
        raise HTTPException(status_code=400, detail="Failed to send post")

    return {"message": "Post sent successfully"}




