from uuid import uuid4

import arrow
import fitz
from celery import Celery
from celery.utils.log import get_task_logger
from pathlib import Path

from langchain_huggingface import HuggingFaceEmbeddings

from app.ai import schemas as ai_schemas
from langchain_elasticsearch import ElasticsearchStore
from langchain_text_splitters import CharacterTextSplitter
from app.ai import queries as ai_queries
from app import config
from app.ai.graph import PostGraph
from app.database import async_session_maker
import asyncio
from datetime import datetime, timedelta, timezone
from app.posts.queries import create_post_query
from app.channels.queries import delete_channel_logs_by_before_date_query, create_channel_log_query
from app.posts.queries import celery_get_posts_for_loop_query
from app.providers import telegram

celery_app = Celery("tasks")
celery_app.config_from_object("app.celery_config")

post_graph = PostGraph().get_compiled_graph()
embedding_model = HuggingFaceEmbeddings(
    model_name=config.HUGGINGFACE_EMBEDDING_MODEL,
    model_kwargs={"device": config.MODEL_DEVICE}
)

logger = get_task_logger(__name__)

@celery_app.task
def scheduled_hello():
    logger.info(f"Now: {datetime.now()}")
    logger.info(f"Now in UTC: {datetime.now(tz=timezone.utc)}")
    logger.info("Scheduled Hello from Celery Beat!")


@celery_app.task
def remove_old_channel_logs():

    async def remove_old_channel_logs_task():
        async with async_session_maker() as session:
            await delete_channel_logs_by_before_date_query(
                before_date=datetime.now(tz=timezone.utc).replace(tzinfo=None) - timedelta(days=30),
                session=session,
            )

    loop = asyncio.get_event_loop()
    loop.run_until_complete(remove_old_channel_logs_task())


@celery_app.task
def celery_get_posts_for_loop():
    async def get_posts_for_loop_task():
        async with async_session_maker() as session:
            posts = await celery_get_posts_for_loop_query(
                end_date=datetime.now(tz=timezone.utc).replace(tzinfo=None),
                session=session,
            )
            for post in posts:
                provider = None
                if post.channel.channel_type == "telegram":
                    provider = telegram.Telegram(post)

                if not provider:
                    continue
                await provider.send()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(get_posts_for_loop_task())


@celery_app.task
def ai_generate_post_task(input_values):
    async def ai_generate_post():
        nonlocal input_values
        async with async_session_maker() as session:
            try:
                result = await post_graph.ainvoke(input_values)
                if "additional_kwargs" in result and "response" in result["additional_kwargs"]:
                    response = result["additional_kwargs"]["response"]
                    if isinstance(response, str) and len(response) > 0:
                        await create_post_query(
                            data={
                                "channel_id": input_values["additional_kwargs"]["channel_id"],
                                "company_id": input_values["additional_kwargs"]["company_id"],
                                "content": response,
                                "ai_generated": True,
                                "timezone": input_values["additional_kwargs"]["timezone"],
                            },
                            session=session,
                        )
                        await create_channel_log_query(
                            data={
                                "channel_id": input_values["additional_kwargs"]["channel_id"],
                                "message": f"AI generated post successfully.",
                            },
                            session=session,
                        )
                    else:
                        await create_channel_log_query(
                            data={
                                "channel_id": input_values["additional_kwargs"]["channel_id"],
                                "message": f"Sorry, I couldn't generate a post by topic {input_values['additional_kwargs']['topic']}. Please try again.",
                            },
                            session=session,
                        )

            except Exception as e:
                logger.error(f"Error in ai_generate_post: {e}")
                await create_channel_log_query(
                    data={
                        "channel_id": input_values["additional_kwargs"]["channel_id"],
                        "message": f"Error while generating post, try again later. Topic: {input_values['additional_kwargs']['topic']}.",
                    },
                    session=session,
                )

    loop = asyncio.get_event_loop()
    loop.run_until_complete(ai_generate_post())


@celery_app.task
def proceed_upload_file_task(file_path, credentials):
    print(f"Proceeding with file: {file_path}")
    if not Path(file_path).exists():
        print(f"File {file_path} does not exist.")
        return
    async def proceed_upload_file():
        nonlocal file_path
        nonlocal credentials
        document_id = uuid4().hex
        text_splitter = CharacterTextSplitter(chunk_size=512, chunk_overlap=64)

        es = ElasticsearchStore(
            es_url=config.ELASTICSEARCH_HOST,
            index_name="documents",
        )

        async with async_session_maker() as session:
            try:
                if file_path.endswith(".pdf"):
                    doc = fitz.open(file_path, filetype="pdf")
                    texts = []
                    for page in doc:
                        texts.append(page.get_text())

                    text = "\n\n".join(texts)

                    if text:
                        chunked_texts = text_splitter.split_text(text)
                    else:
                        await create_channel_log_query(
                            data={
                                "channel_id": credentials["channel_id"],
                                "message": f"Sorry, I couldn't extract text from the PDF file {credentials['source_metadata']['file_name']}. Please try again.",
                            },
                            session=session,
                        )
                        return
                elif file_path.endswith(".txt") or file_path.endswith(".md"):
                    with open(file_path, "r", encoding="utf-8") as file:
                        text = file.read()
                        chunked_texts = text_splitter.split_text(text)
                else:
                    await create_channel_log_query(
                        data={
                            "channel_id": credentials["channel_id"],
                            "message": f"Sorry, I couldn't process the file type {credentials['source_metadata']['file_name']}.",
                        },
                        session=session,
                    )
                    return
                if not chunked_texts:
                    await create_channel_log_query(
                        data={
                            "channel_id": credentials["channel_id"],
                            "message": f"Sorry, I couldn't extract text from the file {credentials['source_metadata']['file_name']}. Please try again.",
                        },
                        session=session,
                    )
                    return
                print(f"Chunked texts: {chunked_texts}")
                for i, chunk in enumerate(chunked_texts):
                    es_document = ai_schemas.ES_Document(
                        id=uuid4().hex,
                        document_id=document_id,
                        title=credentials["source_metadata"]["file_name"],
                        text=chunk,
                        timestamp=arrow.now().format("YYYY-MM-DD"),
                        channel_id=credentials["channel_id"],
                        company_id=credentials["company_id"],
                        embedding=embedding_model.embed_documents(chunk)[0],
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
                        "file_name": credentials["source_metadata"]["file_name"],
                        "file_type": credentials["source_metadata"]["file_type"],
                    },
                    document_id=document_id,
                    channel_id=credentials["channel_id"],
                    company_id=credentials["company_id"],
                )
                await ai_queries.create_source_query(
                    session=session,
                    data=source.model_dump(),
                )
                await create_channel_log_query(
                    data={
                        "channel_id": credentials["channel_id"],
                        "message": f"File {credentials['source_metadata']['file_name']} uploaded successfully.",
                    },
                    session=session,
                )
            except Exception as e:
                logger.error(f"Error in proceed_upload_file: {e}")
                await create_channel_log_query(
                    data={
                        "channel_id": credentials["channel_id"],
                        "message": f"Error while uploading file, try again later. File: {credentials['source_metadata']['file_name']}.",
                    },
                    session=session,
                )

    loop = asyncio.get_event_loop()
    loop.run_until_complete(proceed_upload_file())

