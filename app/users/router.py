from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio.session import AsyncSession
from app.auth import auth as auth_tools
from app.users import models as user_models, queries as user_queries, schemas as user_schemas


router = APIRouter()

@router.get("/me", response_model=user_schemas.UserSchema)
async def me_api(
    user: user_models.User = Depends(auth_tools.get_current_active_user),
):
    return user