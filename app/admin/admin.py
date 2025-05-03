from datetime import datetime, timedelta
from uuid import uuid4
from app import config
from jose import JWTError, jwt
from sqladmin import Admin
from app.database import engine, async_session_maker
from app.admin import admin_models
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
from app.users import queries as user_queries
from starlette.responses import RedirectResponse
from app.auth import auth as auth_tools
from app.auth import queries as auth_queries


class AdminAuth(AuthenticationBackend):

    async def login(self, request: Request) -> bool:
        form = await request.form()
        username, password = form["username"], form["password"]

        async with async_session_maker() as db_session:
            user = await user_queries.get_user_by_email(username, db_session)
            if any([
                not user,
                not user.is_active,
                not user.is_superuser,
                not await auth_tools.password_verify(password, user.password)
            ]):
                return False
            token_hex = uuid4().hex
            auth_session = await auth_queries.create_auth_session(
                {
                    "token": token_hex,
                    "user_id": user.id,
                    "expired_at": datetime.now()
                                  + timedelta(minutes=7 * 24 * 60),
                },
                db_session,
            )
            token = auth_tools.create_access_token({"sub": token_hex})
            request.session.update({"token": token})

        return True

    async def logout(self, request: Request) -> bool:
        # Usually you'd want to just clear the session
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        token = request.session.get("token")

        if not token:
            return False

        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        token_session: str = payload.get("sub")
        if token_session is None:
            return False
        async with async_session_maker() as db_session:
            auth_session = await auth_queries.get_auth_session(token_session, db_session)
            if not auth_session:
                return False
            user = auth_session.user
            if any([not user, not user.is_active, not user.is_superuser]):
                return False

        return True


authentication_backend = AdminAuth(secret_key=config.SECRET_KEY)

def init_admin(app):
    admin = Admin(
        app=app,
        engine=engine,
        base_url="/admin",
        authentication_backend=authentication_backend,
        title="AutoQuill Admin",
    )
    admin.add_view(admin_models.CompanyAdmin)
    admin.add_view(admin_models.UserAdmin)
    admin.add_view(admin_models.UserSettingAdmin)
    admin.add_view(admin_models.AuthSessionAdmin)
    admin.add_view(admin_models.ChannelAdmin)
    admin.add_view(admin_models.PostAdmin)
    admin.add_view(admin_models.SourceAdmin)
    return admin