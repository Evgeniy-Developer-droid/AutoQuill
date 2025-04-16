from sqlalchemy.ext.asyncio.session import AsyncSession
from app.auth.models import AuthSession
from sqlalchemy import select, insert, delete


async def create_auth_session(data: dict, session: AsyncSession) -> AuthSession:
    try:
        stmt = insert(AuthSession).values(**data).returning(AuthSession)
        result = await session.execute(stmt)
        await session.commit()
        return result.scalars().first()
    except Exception as e:
        print(f"Error create auth session - {data}")


async def get_auth_session(token, session: AsyncSession) -> AuthSession:
    try:
        stmt = select(AuthSession).where(AuthSession.token == token)
        result = await session.execute(stmt)
        return result.scalars().first()
    except Exception as e:
        print(f"Error getting auth session - {token}")


async def delete_auth_session(token, session: AsyncSession) -> bool:
    try:
        stmt = delete(AuthSession).where(AuthSession.token == token)
        result = await session.execute(stmt)
        return bool(result.rowcount)
    except Exception as e:
        print(f"Error deleting auth session - {token}")
        return False

