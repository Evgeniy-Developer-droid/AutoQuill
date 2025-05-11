import json

from elasticsearch import Elasticsearch
from fastapi import FastAPI
from langchain_elasticsearch import ElasticsearchStore

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
from app.ai.router import router as ai_router
from app.billing.webhooks import router as webhooks_router


async def create_elasticsearch_indices():

    index_mapping = {
        "documents": "documents"
    }
    try:
        for index, mapping in index_mapping.items():

            es = ElasticsearchStore(
                es_url=config.ELASTICSEARCH_HOST,
                index_name=index,
            )

            if not es.client.indices.exists(index=mapping):
                with open(f"app/ai/mapping/{mapping}.json") as f:
                    mapping_data = json.load(f)
                es.client.indices.create(
                    index=mapping,
                    mappings=mapping_data["mappings"],
                    settings=mapping_data["settings"],
                )
                es.client.indices.refresh(index=mapping)
            else:
                print(f"Index {mapping} already exists. Skipping creation.")
        print("Elasticsearch indices created successfully.")
    except Exception as e:
        print(f"Error creating Elasticsearch indices: {e}")


# @asynccontextmanager
# async def on_startup(app: FastAPI):
#     await init_superuser()
#     await create_elasticsearch_indices()
#     yield


app = FastAPI(
    debug=config.DEBUG,
    title="AutoQuill API",
    version="1.0.0",
    docs_url=(None if not config.DEBUG else "/docs"),
    redoc_url=(None if not config.DEBUG else "/redoc"),
    # lifespan=on_startup
)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    await init_superuser()
    await create_elasticsearch_indices()


app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(users_router, prefix="/api/v1/users", tags=["users"])
app.include_router(channels_router, prefix="/api/v1/channels", tags=["channels"])
app.include_router(posts_router, prefix="/api/v1/posts", tags=["posts"])
app.include_router(ai_router, prefix="/api/v1/ai", tags=["ai"])

app.include_router(webhooks_router, prefix="/webhooks", tags=["webhooks"])

init_admin(app)



