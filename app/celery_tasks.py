from select import select
from uuid import uuid4

import arrow
import fitz
import pytz
from celery import Celery
from celery.utils.log import get_task_logger
from pathlib import Path
from langchain_huggingface import HuggingFaceEmbeddings
import os, sys
from app.billing import queries as billing_queries
from app.billing.models import Payment, Plan
from app.billing.services.referral import process_referral_reward
from app.posts import queries as post_queries
from app.ai import schemas as ai_schemas, prompts
from langchain_elasticsearch import ElasticsearchStore
from langchain_text_splitters import CharacterTextSplitter
from app.ai import queries as ai_queries
from app.ai.utils import add_ai_config_prompt
from app.billing.services.usage import check_and_consume_usage
from app.channels import queries as channel_queries
from app import config
from app.ai.graph import PostGraph
from app.database import async_session_maker
import asyncio
from datetime import datetime, timedelta, timezone
from app.posts.queries import create_post_query
from app.channels.queries import delete_channel_logs_by_before_date_query, create_channel_log_query
from app.posts.queries import celery_get_posts_for_loop_query
from app.providers import telegram
from app.users.models import Company

celery_app = Celery("tasks")
celery_app.config_from_object("app.celery_config")

post_graph = PostGraph().get_compiled_graph()
embedding_model = HuggingFaceEmbeddings(
    model_name=config.HUGGINGFACE_EMBEDDING_MODEL,
    model_kwargs={"device": config.MODEL_DEVICE}
)

logger = get_task_logger(__name__)


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
                success, message = await check_and_consume_usage(
                    db=session,
                    company=post.channel.company,
                    action="post",
                    raise_exception=False,
                )
                if not success:
                    await create_channel_log_query(
                        data={
                            "channel_id": post.channel_id,
                            "message": f"Post not sent. {message}",
                        },
                        session=session,
                    )
                    await post_queries.update_post_query(
                        session=session,
                        post_id=post.id,
                        data={"status": "failed"},
                    )
                    continue
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
    # !!!!! check and consume usage relized in router
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
                for i, chunk in enumerate(chunked_texts):
                    _id = uuid4().hex
                    es_document = ai_schemas.ES_Document(
                        id=_id,
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
                        id=_id,
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
                # delete the file after processing
                os.remove(file_path)
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


@celery_app.task
def ai_generate_scheduled_post_task(data: dict, draft: bool = False):
    # validate data
    if not isinstance(data, dict):
        raise ValueError("Data must be a dictionary.")

    if "channel_id" not in data or "company_id" not in data:
        raise ValueError("Data must contain 'channel_id' and 'company_id'.")
    async def ai_generate_scheduled_post():
        async with async_session_maker() as session:
            channel = await channel_queries.get_channel_query(
                channel_id=data["channel_id"],
                company_id=data["company_id"],
                session=session,
            )
            if not channel:
                raise ValueError("Channel not found.")

            # check and consume usage
            success, message = await check_and_consume_usage(
                db=session,
                company=channel.company,
                action="ai",
                raise_exception=False,
            )
            if not success:
                await create_channel_log_query(
                    data={
                        "channel_id": data["channel_id"],
                        "message": f"AI generation failed. {message}",
                    },
                    session=session,
                )
                return

            prompt = prompts.GENERAL
            if channel.channel_type == "telegram":
                prompt = prompts.TELEGRAM
            elif channel.channel_type == "api":
                prompt = prompts.API

            scheduler = await ai_queries.get_scheduled_ai_post_by_id_query(
                session=session,
                scheduled_ai_post_id=data["scheduler_id"],
                company_id=data["company_id"],
            )
            if not scheduler:
                raise ValueError("Scheduler not found.")

            # get ai config
            ai_config = await ai_queries.get_or_create_ai_config_query(
                session=session,
                channel_id=data["channel_id"],
                company_id=data["company_id"],
            )
            if not ai_config:
                raise ValueError("AI config not found.")

            prompt = await add_ai_config_prompt(prompt, ai_config)

            input_values = {
                "additional_kwargs": {
                    "prompt": prompt,
                    "channel_id": data["channel_id"],
                    "company_id": data["company_id"],
                    "topic": None,
                    "random": True
                }
            }
            try:
                result = await post_graph.ainvoke(input_values)
                if "additional_kwargs" in result and "response" in result["additional_kwargs"]:
                    response = result["additional_kwargs"]["response"]
                    if isinstance(response, str) and len(response) > 0:
                        await create_post_query(
                            data={
                                "channel_id": data["channel_id"],
                                "company_id": data["company_id"],
                                "content": response,
                                "ai_generated": True,
                                "timezone": scheduler.timezone,
                                "scheduled_time": datetime.now(),
                                "status": "scheduled" if not draft else "draft",
                            },
                            session=session,
                        )
                        await create_channel_log_query(
                            data={
                                "channel_id": data["channel_id"],
                                "message": f"AI generated post successfully.",
                            },
                            session=session,
                        )
                        await ai_queries.update_scheduled_ai_post_query(
                            session=session,
                            scheduled_ai_post_id=data["scheduler_id"],
                            data={"last_run_at": datetime.now()},
                            company_id=data["company_id"],
                        )
                    else:
                        await create_channel_log_query(
                            data={
                                "channel_id": data["channel_id"],
                                "message": f"Sorry, I couldn't generate a post by topic {input_values['additional_kwargs']['topic']}. Please try again.",
                            },
                            session=session,
                        )
                else:
                    await create_channel_log_query(
                        data={
                            "channel_id": data["channel_id"],
                            "message": f"Sorry, I couldn't generate a post by topic {input_values['additional_kwargs']['topic']}. Please try again.",
                        },
                        session=session,
                    )
            except Exception as e:
                logger.error(f"Error in ai_generate_scheduled_post: {e}")
                await create_channel_log_query(
                    data={
                        "channel_id": data["channel_id"],
                        "message": f"Error while generating post, try again later. Topic: {input_values['additional_kwargs']['topic']}.",
                    },
                    session=session,
                )

    loop = asyncio.get_event_loop()
    loop.run_until_complete(ai_generate_scheduled_post())


@celery_app.task
def scheduled_ai_post_task():

    async def scheduled_ai_post():
        now = datetime.now()
        async with async_session_maker() as session:
            try:
                schedulers = await ai_queries.get_all_scheduled_ai_posts_query(
                    session=session,
                )
                for scheduler in schedulers:
                    tz_info = pytz.timezone(scheduler.timezone)
                    now_local = now.astimezone(tz_info)
                    current_weekday_local = now_local.weekday()
                    current_time_local = now_local.strftime("%H:%M")
                    if current_weekday_local in scheduler.weekdays and current_time_local in scheduler.times:
                        ai_generate_scheduled_post_task.delay({
                            "scheduler_id": scheduler.id,
                            "channel_id": scheduler.channel_id,
                            "company_id": scheduler.company_id
                        })

            except Exception as e:
                logger.error(f"Error in scheduled_ai_post: {e}")

    loop = asyncio.get_event_loop()
    loop.run_until_complete(scheduled_ai_post())


@celery_app.task
def liqpay_callback_task(data: dict):
    async def liqpay_callback():
        async with async_session_maker() as session:
            try:
                status = data.get("status")
                order_id = data.get("order_id")
                amount = float(data.get("amount"))
                company_id = int(order_id.split("-")[0])
                plan_id = int(order_id.split("-")[-1])

                if status in ("subscribed", "success", "sandbox"):
                    result = await session.execute(select(Company).where(Company.id == company_id))
                    company: Company = result.scalar()

                    if not company:
                        logger.error(f"Company with id {company_id} not found.")
                        return None

                    result = await session.execute(
                        select(Payment).where(Payment.order_id == order_id)
                    )
                    existing = result.scalar()
                    if existing:
                        logger.error(f"Payment with order_id {order_id} already exists.")
                        return None

                    payment = Payment(
                        company_id=company.id,
                        amount=int(amount),
                        order_id=order_id,
                        description=data.get("description"),
                        is_successful=True,
                        payment_service="liqpay",
                    )
                    session.add(payment)

                    plan = await session.scalar(select(Plan).where(Plan.id == plan_id))
                    if plan.id != company.current_plan_id:
                        company.current_plan_id = plan.id
                        company.plan_started_at = datetime.now()
                    company.last_payment_at = datetime.now()
                    company.subscription_valid_until = datetime.now() + timedelta(days=30)
                    company.payment_service = "liqpay"

                    await process_referral_reward(session, referred_company_id=company.id)
                    await session.commit()
                elif status in ("failure", "error", "reversed"):
                    trial_plan = await billing_queries.get_or_create_trial_plan_query(session)
                    result = await session.execute(select(Company).where(Company.id == company_id))
                    company = result.scalar()
                    company.current_plan_id = trial_plan.id if trial_plan else None
                    company.plan_started_at = datetime.now()
                    company.subscription_valid_until = None
                    company.payment_service = ""
                    company.last_payment_at = datetime.now()
                    await session.commit()

                return None
            except Exception as e:
                logger.error(f"Error in liqpay_callback: {e}")

    loop = asyncio.get_event_loop()
    loop.run_until_complete(liqpay_callback())


@celery_app.task
def check_expired_subscription_task():
    async def check_expired_subscription():
        async with async_session_maker() as session:
            try:
                now = datetime.now()
                companies = await session.execute(
                    select(Company).where(
                        Company.subscription_valid_until < now,
                        Company.subscription_valid_until.isnot(None),
                    )
                )
                trial_plan = await billing_queries.get_or_create_trial_plan_query(session)
                for company in companies.scalars():
                    company.current_plan_id = trial_plan.id if trial_plan else None
                    company.plan_started_at = datetime.now()
                    company.subscription_valid_until = None
                    company.payment_service = ""
                    company.last_payment_at = datetime.now()
                await session.commit()
            except Exception as e:
                logger.error(f"Error in check_expired_subscription: {e}")

    loop = asyncio.get_event_loop()
    loop.run_until_complete(check_expired_subscription())


@celery_app.task
def renew_trials_task():
    async def renew_trials():
        async with async_session_maker() as session:
            try:
                trial_plan = await billing_queries.get_or_create_trial_plan_query(session)
                if not trial_plan:
                    raise ValueError("Trial plan not found.")
                now = datetime.now()
                companies = await session.execute(
                    select(Company).where(
                        Company.current_plan_id == trial_plan.id,
                        Company.last_payment_at < now - timedelta(days=30),
                    )
                )
                for company in companies.scalars():
                    company.last_payment_at = datetime.now()
                await session.commit()
            except Exception as e:
                logger.error(f"Error in renew_trials: {e}")

    loop = asyncio.get_event_loop()
    loop.run_until_complete(renew_trials())
