import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'orders.settings')
app = Celery('orders')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.conf.worker_concurrency = 2
app.conf.broker_connection_retry_on_startup = True
app.autodiscover_tasks()
