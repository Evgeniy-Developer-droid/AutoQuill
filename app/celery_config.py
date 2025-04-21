broker_url = 'redis://redis:6379/0'
result_backend = 'redis://redis:6379/0'
timezone = 'UTC'
imports = ('app.celery_tasks',)

beat_schedule = {
    'say-hello-every-30-seconds': {
        'task': 'app.celery_tasks.scheduled_hello',
        'schedule': 30.0,
    },
    'remove-old-channel-logs-every-day': {
        'task': 'app.celery_tasks.remove_old_channel_logs',
        'schedule': 86400.0,  # 24 hours in seconds
    },
    'celery-get-posts-for-loop-every-30-seconds': {
        'task': 'app.celery_tasks.celery_get_posts_for_loop',
        'schedule': 30.0,
    },
}