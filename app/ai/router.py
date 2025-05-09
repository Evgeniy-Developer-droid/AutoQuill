from typing import Optional, List

from sympy.assumptions.cnf import Literal

from app.ai import prompts
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from langchain_elasticsearch import ElasticsearchStore
from sqlalchemy.ext.asyncio.session import AsyncSession
from app.ai import queries as ai_queries
from uuid import uuid4
from app import config
from app.ai.utils import add_ai_config_prompt
from app.auth import auth as auth_tools
from app.celery_tasks import ai_generate_post_task, proceed_upload_file_task
from app.channels import queries as channel_queries
from app.schemas import SuccessResponseSchema
from app.ai import schemas as ai_schemas
from app.users import models as user_models
from app.database import get_session


router = APIRouter()


@router.post("/files", response_model=SuccessResponseSchema)
async def upload_file(
    channel_id: int,
    file: Optional[UploadFile] = File(...),
    user: user_models.User = Depends(auth_tools.get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    print("Uploading file...")

    # get channel
    channel = await channel_queries.get_channel_query(
        session=session,
        channel_id=channel_id,
        company_id=user.company_id
    )
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found.")

    filename = f"{uuid4().hex}_{file.filename}"
    file_path = f"{config.UPLOAD_FOLDER}/{filename}"

    with open(file_path, "wb") as f:
        while content := await file.read(1024 * 1024): # 1MB chunks
            f.write(content)
    credentials = {
        "channel_id": channel_id,
        "company_id": user.company_id,
        "source_type": "file",
        "source_metadata": {
            "file_name": file.filename,
            "file_type": file.content_type
        },
    }
    proceed_upload_file_task.delay(file_path, credentials)
    return {"message": f"File will be processed in background and you will see the result in the channel soon."}


@router.post("/documents", response_model=SuccessResponseSchema)
async def upload_document(
    channel_id: int,
    data: ai_schemas.DocumentInSchema,
    user: user_models.User = Depends(auth_tools.get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    print("Uploading document...")
    # get channel
    channel = await channel_queries.get_channel_query(
        session=session,
        channel_id=channel_id,
        company_id=user.company_id
    )
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found.")

    filename = f"{uuid4().hex}.txt"
    file_path = f"{config.UPLOAD_FOLDER}/{filename}"
    with open(file_path, "w") as f:
        f.write(data.text)
    credentials = {
        "channel_id": channel_id,
        "company_id": user.company_id,
        "source_type": "document",
        "source_metadata": {
            "file_name": filename,
            "file_type": "text/plain",
        },
    }
    proceed_upload_file_task.delay(file_path, credentials)
    return {"message": f"Document is being processed in background."}


@router.get("/sources", response_model=ai_schemas.SourcesListSchema)
async def get_sources(
    channel_id: int,
    page: int = 1,
    limit: int = 10,
    user: user_models.User = Depends(auth_tools.get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    print("Getting sources...")

    # get channel
    channel = await channel_queries.get_channel_query(
        session=session,
        channel_id=channel_id,
        company_id=user.company_id
    )
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found.")

    sources, total_count = await ai_queries.get_sources_query(
        session=session,
        company_id=user.company_id,
        channel_id=channel_id,
        page=page,
        limit=limit,
    )

    return {
        "sources": sources,
        "total": total_count
    }

@router.delete("/sources", response_model=SuccessResponseSchema)
async def delete_source(
    source_id: int,
    user: user_models.User = Depends(auth_tools.get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    print("Deleting source...")

    # get source
    source = await ai_queries.get_source_query(
        session=session,
        source_id=source_id,
        company_id=user.company_id,
    )
    if not source:
        raise HTTPException(status_code=404, detail="Source not found.")

    es = ElasticsearchStore(
        es_url=config.ELASTICSEARCH_HOST,
        index_name="documents",
    )
    if es.client.indices.exists(index="documents"):
        result = es.client.delete_by_query(
            index="documents",
            query={
                "bool": {
                    "must": [
                        {"match": {"document_id": source.document_id}},
                        {"match": {"channel_id": str(source.channel_id)}},
                        {"match": {"company_id": str(source.company_id)}},
                    ]
                }
            }
        )
        print(f"Deleted {result['deleted']} documents from Elasticsearch.")
    # delete source
    await ai_queries.delete_source_query(
        session=session,
        source_id=source_id,
        company_id=user.company_id,
    )

    return {"message": "Source deleted successfully."}


@router.post("/generate/posts", response_model=SuccessResponseSchema)
async def generate_posts(
    channel_id: int,
    data: ai_schemas.GeneratePostsInSchema,
    user: user_models.User = Depends(auth_tools.get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    print("Generating posts...")

    # get channel
    channel = await channel_queries.get_channel_query(
        session=session,
        channel_id=channel_id,
        company_id=user.company_id
    )
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found.")

    prompt = prompts.GENERAL
    if channel.channel_type == "telegram":
        prompt = prompts.TELEGRAM
    elif channel.channel_type == "api":
        prompt = prompts.API

    # get ai config
    ai_config = await ai_queries.get_or_create_ai_config_query(
        session=session,
        channel_id=channel_id,
        company_id=user.company_id,
    )
    if not ai_config:
        raise HTTPException(status_code=404, detail="AI config not found.")

    prompt = await add_ai_config_prompt(prompt, ai_config)

    input_values = {
        "additional_kwargs": {
            "prompt": prompt,
            "channel_id": channel_id,
            "company_id": user.company_id,
            "topic": data.topic,
            "timezone": user.settings.timezone
        }
    }
    ai_generate_post_task.delay(input_values)

    return {"message": "Added to queue. You will see the post in the channel soon."}


@router.get("/ai/config", response_model=ai_schemas.AIConfigOutSchema)
async def get_ai_config(
    channel_id: int,
    user: user_models.User = Depends(auth_tools.get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    print("Getting AI config...")

    # get channel
    channel = await channel_queries.get_channel_query(
        session=session,
        channel_id=channel_id,
        company_id=user.company_id
    )
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found.")

    # get ai config
    ai_config = await ai_queries.get_or_create_ai_config_query(
        session=session,
        channel_id=channel_id,
        company_id=user.company_id,
    )
    if not ai_config:
        raise HTTPException(status_code=404, detail="AI config not found.")

    return ai_config


@router.put("/ai/config", response_model=ai_schemas.AIConfigOutSchema)
async def update_ai_config(
    channel_id: int,
    data: ai_schemas.AIConfigUpdateSchema,
    user: user_models.User = Depends(auth_tools.get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    print("Updating AI config...")

    # get channel
    channel = await channel_queries.get_channel_query(
        session=session,
        channel_id=channel_id,
        company_id=user.company_id
    )
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found.")

    # get ai config
    ai_config = await ai_queries.get_or_create_ai_config_query(
        session=session,
        channel_id=channel_id,
        company_id=user.company_id,
    )
    if not ai_config:
        raise HTTPException(status_code=404, detail="AI config not found.")

    # update ai config
    updated_ai_config = await ai_queries.update_ai_config_query(
        session=session,
        company_id=user.company_id,
        channel_id=channel_id,
        data=data.model_dump(exclude_none=True),
    )

    return updated_ai_config


@router.get("/scheduled-posts", response_model=List[ai_schemas.ScheduledAIPostOutSchema])
async def get_scheduled_posts(
    channel_id: int,
    user: user_models.User = Depends(auth_tools.get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    print("Getting scheduled posts...")

    # get channel
    channel = await channel_queries.get_channel_query(
        session=session,
        channel_id=channel_id,
        company_id=user.company_id
    )
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found.")

    # get scheduled posts
    scheduled_posts = await ai_queries.get_scheduled_ai_posts_query(
        session=session,
        company_id=user.company_id,
        channel_id=channel_id,
    )

    return scheduled_posts


@router.delete("/scheduled-posts/{scheduled_post_id}", response_model=SuccessResponseSchema)
async def delete_scheduled_post(
    scheduled_post_id: int,
    channel_id: int,
    user: user_models.User = Depends(auth_tools.get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    print("Deleting scheduled post...")

    # get channel
    channel = await channel_queries.get_channel_query(
        session=session,
        channel_id=channel_id,
        company_id=user.company_id
    )
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found.")

    # delete scheduled post
    await ai_queries.delete_scheduled_ai_post_query(
        session=session,
        scheduled_ai_post_id=scheduled_post_id,
        company_id=user.company_id,
    )

    return {"message": "Scheduled post deleted successfully."}


@router.post("/scheduled-posts", response_model=ai_schemas.ScheduledAIPostOutSchema)
async def create_scheduled_post(
    channel_id: int,
    data: ai_schemas.ScheduledAIPostInSchema,
    user: user_models.User = Depends(auth_tools.get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    print("Creating scheduled post...")

    # get channel
    channel = await channel_queries.get_channel_query(
        session=session,
        channel_id=channel_id,
        company_id=user.company_id
    )
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found.")

    data_dict = data.model_dump(exclude_none=True)
    data_dict["channel_id"] = channel_id
    data_dict["company_id"] = user.company_id
    data_dict["timezone"] = data.timezone or user.settings.timezone

    # create scheduled post
    scheduled_post = await ai_queries.create_scheduled_ai_post_query(
        session=session,
        data=data_dict
    )
    if not scheduled_post:
        raise HTTPException(status_code=500, detail="Failed to create scheduled post.")

    return scheduled_post

@router.post("/scheduled-posts/{scheduled_post_id}/{action}", response_model=SuccessResponseSchema)
async def activate_scheduled_post(
    scheduled_post_id: int,
    channel_id: int,
    action: str = "activate",
    user: user_models.User = Depends(auth_tools.get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    print("Activating scheduled post...")

    # get channel
    channel = await channel_queries.get_channel_query(
        session=session,
        channel_id=channel_id,
        company_id=user.company_id
    )
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found.")

    # get scheduled post
    scheduled_post = await ai_queries.update_scheduled_ai_post_query(
        session=session,
        scheduled_ai_post_id=scheduled_post_id,
        company_id=user.company_id,
        data={"is_active": action == "activate"}
    )
    if not scheduled_post:
        raise HTTPException(status_code=404, detail="Scheduled post not found.")
    return {"message": "Scheduled post updated successfully."}

