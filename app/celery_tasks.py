from celery import Celery
from celery.utils.log import get_task_logger

from app.database import async_session_maker
import asyncio
from datetime import datetime, timedelta, timezone
from app.channels.queries import delete_channel_logs_by_before_date_query
from app.posts.queries import celery_get_posts_for_loop_query
from app.providers import telegram

celery_app = Celery("tasks")
celery_app.config_from_object("app.celery_config")

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
