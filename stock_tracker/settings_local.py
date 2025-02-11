from django.conf import settings

settings.DATABASES['default']['ENGINE'] = 'django.db.backends.mysql'
settings.DATABASES['default']['NAME'] = 'stock_tracker'
settings.DATABASES['default']['USER'] = ''
settings.DATABASES['default']['PASSWORD'] = ''
settings.DATABASES['default']['HOST'] = 'localhost'

COMPANY_RETRIEVAL_URL = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
API_VIEW_THREAD_COUNT = 10

# Celery
CELERY_BROKER_URL = 'redis://127.0.0.1:6379'
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TASK_SERIALIZER = 'json'
CELERY_TIMEZONE = 'US/Central'
CELERY_RESULT_BACKEND = 'django-db'

CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'


CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [('127.0.0.1', 6379)],
        }       
    }
}