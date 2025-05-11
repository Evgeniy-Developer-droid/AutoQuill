import traceback

from sqlalchemy.ext.asyncio.session import AsyncSession
from app.auth.models import AuthSession
from sqlalchemy import select, insert, delete, update

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


async def update_user_query(user_id: int, data: dict, session: AsyncSession) -> User:
    try:
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(**data)
            .returning(User)
        )
        result = await session.execute(stmt)
        await session.commit()
        return result.scalars().first()
    except Exception as e:
        await session.rollback()
        traceback.print_exc()
        print(f"Error updating user - {user_id}")


async def get_company_by_referral_code_query(
    referral_code: str, session: AsyncSession
) -> Company:
    try:
        stmt = select(Company).where(Company.referral_code == referral_code)
        result = await session.execute(stmt)
        return result.scalars().first()
    except Exception as e:
        print(f"Error getting company by referral code - {referral_code}")
        traceback.print_exc()
