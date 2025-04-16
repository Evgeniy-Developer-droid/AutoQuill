from fastapi import FastAPI
from app import config
from app.auth.router import router as auth_router
from app.users.router import router as users_router
from app.channels.router import router as channels_router
from app.posts.router import router as posts_router
from fastapi.middleware.cors import CORSMiddleware
from app.admin.admin import init_admin
from app.manager import init_superuser
from contextlib import asynccontextmanager
from fastapi.staticfiles import StaticFiles


@asynccontextmanager
async def on_startup(app: FastAPI):
    await init_superuser()
    yield


app = FastAPI(
    debug=config.DEBUG,
    title="AutoQuill API",
    version="1.0.0",
    docs_url=(None if not config.DEBUG else "/docs"),
    redoc_url=(None if not config.DEBUG else "/redoc"),
    lifespan=on_startup
)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(users_router, prefix="/api/v1/users", tags=["users"])
app.include_router(channels_router, prefix="/api/v1/channels", tags=["channels"])
app.include_router(posts_router, prefix="/api/v1/posts", tags=["posts"])

init_admin(app)



