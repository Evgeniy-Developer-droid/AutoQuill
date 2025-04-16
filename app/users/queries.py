from sqlalchemy.ext.asyncio.session import AsyncSession
from app.auth.models import AuthSession
from sqlalchemy import select, insert, delete

from app.users.models import User, UserSetting, Company


async def create_user(data: dict, session: AsyncSession) -> User:
    try:
        stmt = insert(User).values(**data).returning(User)
        result = await session.execute(stmt)
        await session.commit()
        return result.scalars().first()
    except Exception as e:
        print(f"Error create user -{data}")


async def create_company(data: dict, session: AsyncSession) -> Company:
    try:
        stmt = insert(Company).values(**data).returning(Company)
        result = await session.execute(stmt)
        await session.commit()
        return result.scalars().first()
    except Exception as e:
        print(f"Error create company -{data}")


async def get_user_by_id(user_id: int, session: AsyncSession) -> User:
    try:
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        return result.scalars().first()
    except Exception as e:
        print(f"Error gretting user(id) -{user_id}")


async def get_user_by_email(email: str, session: AsyncSession) -> User:
    try:
        stmt = select(User).where(User.email == email)
        result = await session.execute(stmt)
        return result.scalars().first()
    except Exception as e:
        print(f"Error gretting user(email) -{email}")


async def create_user_settings(data: dict, session: AsyncSession) -> UserSetting:
    try:
        stmt = insert(UserSetting).values(**data).returning(UserSetting)
        result = await session.execute(stmt)
        await session.commit()
        return result.scalars().first()
    except Exception as e:
        print(f"Error create user settings - {data}")
