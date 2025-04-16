
from app.database import async_session_maker
from app.auth.auth import hash_password
from app.users import queries as user_queries
from app import config


async def init_superuser():
    async with async_session_maker() as db_session:
        new_user = {
            "email": config.SUPERUSER_EMAIL,
            "password": await hash_password(config.SUPERUSER_PASSWORD),
            "full_name": "Admin",
            "is_active": True,
            "is_superuser": True,
        }
        user = await user_queries.get_user_by_email(new_user["email"], db_session)
        if not user:
            new_company = {
                "name": "Admin"
            }
            company = await user_queries.create_company(new_company, db_session)
            if not company:
                print(f"Error creating company {new_company['name']}")
                return
            new_user["company_id"] = company.id
            user = await user_queries.create_user(new_user, db_session)
            if not user:
                print(f"Error creating superuser {new_user['email']}")
                return
            user_settings = await user_queries.create_user_settings(
                {"user_id": user.id}, db_session
            )
            print(f"Superuser {new_user['email']} created")
        else:
            print(f"Superuser {new_user['email']} already exists")