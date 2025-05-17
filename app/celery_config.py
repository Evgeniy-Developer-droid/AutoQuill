from celery.schedules import crontab
from app import config

broker_url = config.CELERY_BROKER_URL
result_backend = config.CELERY_RESULT_BACKEND
timezone = 'UTC'
imports = ('app.celery_tasks',)

beat_schedule = {
    'remove-old-channel-logs-every-day': {
        'task': 'app.celery_tasks.remove_old_channel_logs',
        'schedule': crontab(hour=0, minute=0), # every day at midnight
    },
    'celery-get-posts-for-loop-every-minute': {
        'task': 'app.celery_tasks.celery_get_posts_for_loop',
        'schedule': crontab(minute='*/1'),  # every minute
    },
    'celery-scheduled-ai-post-every-minute': {
        'task': 'app.celery_tasks.scheduled_ai_post_task',
        'schedule': crontab(minute='*/1'),  # every minute
    },
    'celery-check-expired-subscription-task': {
        'task': 'app.celery_tasks.check_expired_subscription_task',
        'schedule': crontab(hour=0, minute=0),
    },
    'celery-renew-trials-task': {
        'task': 'app.celery_tasks.renew_trials_task',
        'schedule': crontab(hour=0, minute=0),
    },
}