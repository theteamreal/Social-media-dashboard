import os
from social_analytics.celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'social_analytics.settings')

app = Celery('social_analytics')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'sync-social-accounts': {
        'task': 'analytics.tasks.sync_all_social_accounts',
        'schedule': crontab(minute='*/30'),
    },
    'update-engagement-patterns': {
        'task': 'analytics.tasks.update_engagement_patterns',
        'schedule': crontab(hour='*/6'),
    },
    'generate-insights': {
        'task': 'analytics.tasks.generate_ai_insights',
        'schedule': crontab(hour='0', minute='0'),
    },
    'sync-competitor-data': {
        'task': 'analytics.tasks.sync_competitor_data',
        'schedule': crontab(hour='*/12'),
    },
}