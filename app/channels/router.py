from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio.session import AsyncSession
from app.auth import auth as auth_tools
from app.channels import queries as channel_queries
from app.channels import schemas as channel_schemas
from app.users import models as user_models
from app.database import get_session


router = APIRouter()


@router.post("", response_model=channel_schemas.ChannelOutSchema)
async def create_channel(
    channel: channel_schemas.ChannelInSchema,
    session: AsyncSession = Depends(get_session),
    user: user_models.User = Depends(auth_tools.get_current_active_user),
):
    """
    Create a new channel.
    """
    channel_data = channel.model_dump()
    channel_data["company_id"] = user.company_id
    new_channel = await channel_queries.create_channel_query(channel_data, session)
    if not new_channel:
        raise HTTPException(status_code=400, detail="Failed to create channel")
    return new_channel


@router.put("/{channel_id}", response_model=channel_schemas.ChannelOutSchema)
async def update_channel(
    channel_id: int,
    channel: channel_schemas.ChannelUpdateSchema,
    session: AsyncSession = Depends(get_session),
    user: user_models.User = Depends(auth_tools.get_current_active_user),
):
    """
    Update an existing channel.
    """
    print(channel.model_dump(exclude_none=True))
    existing_channel = await channel_queries.get_channel_query(channel_id, user.company_id, session)
    if not existing_channel:
        raise HTTPException(status_code=404, detail="Channel not found")

    updated_channel = await channel_queries.update_channel_query(channel_id, channel.model_dump(exclude_none=True), session)
    if not updated_channel:
        raise HTTPException(status_code=400, detail="Failed to update channel")
    return updated_channel


@router.delete("/{channel_id}")
async def delete_channel(
    channel_id: int,
    session: AsyncSession = Depends(get_session),
    user: user_models.User = Depends(auth_tools.get_current_active_user),
):
    """
    Delete a channel.
    """
    existing_channel = await channel_queries.get_channel_query(channel_id, user.company_id, session)
    if not existing_channel:
        raise HTTPException(status_code=404, detail="Channel not found")

    deleted = await channel_queries.delete_channel_query(channel_id, session)
    if not deleted:
        raise HTTPException(status_code=400, detail="Failed to delete channel")
    return {"detail": "Channel deleted successfully"}


@router.get("/{channel_id}", response_model=channel_schemas.ChannelOutSchema)
async def get_channel(
    channel_id: int,
    session: AsyncSession = Depends(get_session),
    user: user_models.User = Depends(auth_tools.get_current_active_user),
):
    """
    Get a channel by ID.
    """
    channel = await channel_queries.get_channel_query(channel_id, user.company_id, session)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    return channel


@router.get("", response_model=channel_schemas.ChannelListSchema)
async def list_channels(
    page: int = 1,
    limit: int = 10,
    session: AsyncSession = Depends(get_session),
    user: user_models.User = Depends(auth_tools.get_current_active_user),
):
    """
    List channels with pagination.
    """
    channels, total = await channel_queries.get_channels_query(user.company_id, page, limit, session)
    return {"channels": channels, "total": total}


@router.get("/{channel_id}/logs", response_model=channel_schemas.ChannelLogListSchema)
async def list_channel_logs(
    channel_id: int,
    page: int = 1,
    limit: int = 10,
    session: AsyncSession = Depends(get_session),
    user: user_models.User = Depends(auth_tools.get_current_active_user),
):
    """
    List logs for a specific channel with pagination.
    """
    logs, total = await channel_queries.get_channel_logs_query(channel_id, page, limit, session)
    return {"logs": logs, "total": total}
