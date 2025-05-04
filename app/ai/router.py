from typing import Optional
from app.ai import prompts
import arrow
import fitz
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File
from langchain_elasticsearch import ElasticsearchStore
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import CharacterTextSplitter
from sqlalchemy.ext.asyncio.session import AsyncSession
from torch.nn.functional import embedding
from app.ai import queries as ai_queries
from uuid import uuid4
from app import config
from app.ai.graph import PostGraph
from app.auth import auth as auth_tools
from app.celery_tasks import ai_generate_post_task
from app.channels import queries as channel_queries
from app.posts import schemas as post_schemas
from app.schemas import SuccessResponseSchema
from app.ai import schemas as ai_schemas
from app.users import models as user_models
from app.database import get_session
from app.providers import telegram
import pytz


router = APIRouter()

embedding_model = HuggingFaceEmbeddings(
    model_name=config.HUGGINGFACE_EMBEDDING_MODEL,
    model_kwargs={"device": config.MODEL_DEVICE}
)
post_graph = PostGraph().get_compiled_graph()


async def get_embedding_model() -> HuggingFaceEmbeddings:
    return embedding_model


@router.post("/files", response_model=SuccessResponseSchema)
async def upload_file(
    channel_id: int,
    file: Optional[UploadFile] = File(...),
    user: user_models.User = Depends(auth_tools.get_current_active_user),
    model: HuggingFaceEmbeddings = Depends(get_embedding_model),
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

    document_id = uuid4().hex

    es = ElasticsearchStore(
        es_url=config.ELASTICSEARCH_HOST,
        index_name="documents",
    )

    text_splitter = CharacterTextSplitter(chunk_size=512, chunk_overlap=64)
    if file:
        if file.filename.endswith(".pdf"):
            doc = fitz.open(stream=file.file.read(), filetype="pdf")
            texts = []
            for page in doc:
                texts.append(page.get_text())

            text = "\n\n".join(texts)

            if text:
                chunked_texts = text_splitter.split_text(text)
            else:
                raise HTTPException(status_code=400, detail="No text found in PDF file.")
        elif file.filename.endswith(".txt") or file.filename.endswith(".md"):
            text = file.file.read().decode()
            if not text:
                raise HTTPException(status_code=400, detail="No text found in TXT file.")
            chunked_texts = text_splitter.split_text(text)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type. Only PDF, TXT, and MD files are supported.")

    if not chunked_texts:
        raise HTTPException(status_code=400, detail="No text to process.")
    print(f"Chunked texts: {chunked_texts}")
    for i, chunk in enumerate(chunked_texts):
        es_document = ai_schemas.ES_Document(
            id=uuid4().hex,
            document_id=document_id,
            title=f"{file.filename if file else 'text'}",
            text=chunk,
            timestamp=arrow.now().format("YYYY-MM-DD"),
            channel_id=channel_id,
            company_id=user.company_id,
            embedding=model.embed_documents(chunk)[0],
            metadata={"source": "document"},
            page=i,
        )
        es.client.index(
            index="documents",
            id=es_document.document_id,
            document=es_document.model_dump()
        )
    # save source to db
    source = ai_schemas.SourcesInSchema(
        source_type="file",
        source_metadata={
            "file_name": file.filename,
            "file_type": file.content_type,
        },
        document_id=document_id,
        channel_id=channel_id,
        company_id=user.company_id,
    )
    await ai_queries.create_source_query(
        session=session,
        data=source.model_dump(),
    )

    return {"message": f"File is being processed in background."}


@router.post("/documents", response_model=SuccessResponseSchema)
async def upload_document(
    channel_id: int,
    data: ai_schemas.DocumentInSchema,
    user: user_models.User = Depends(auth_tools.get_current_active_user),
    model: HuggingFaceEmbeddings = Depends(get_embedding_model),
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

    document_id = uuid4().hex

    es = ElasticsearchStore(
        es_url=config.ELASTICSEARCH_HOST,
        index_name="documents",
    )

    text_splitter = CharacterTextSplitter(chunk_size=512, chunk_overlap=64)

    if not data.text:
        raise HTTPException(status_code=400, detail="No text provided.")
    text = data.text
    chunked_texts = text_splitter.split_text(text)
    if not chunked_texts:
        raise HTTPException(status_code=400, detail="No text to process.")

    for i, chunk in enumerate(chunked_texts):
        es_document = ai_schemas.ES_Document(
            id=uuid4().hex,
            document_id=document_id,
            title=f"No title",
            text=chunk,
            timestamp=arrow.now().format("YYYY-MM-DD"),
            channel_id=channel_id,
            embedding=model.embed_documents(chunk)[0],
            company_id=user.company_id,
            metadata={"source": "document"},
            page=i,
        )
        es.client.index(
            index="documents",
            id=es_document.document_id,
            document=es_document.model_dump()
        )

    # save source to db
    source = ai_schemas.SourcesInSchema(
        source_type="document",
        source_metadata={
            "text": data.text,
        },
        document_id=document_id,
        channel_id=channel_id,
        company_id=user.company_id,
    )
    await ai_queries.create_source_query(
        session=session,
        data=source.model_dump(),
    )

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
        "total_count": total_count
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
