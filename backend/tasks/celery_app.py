"""Celery application factory — async tasks for recruitment system."""
from celery import Celery
import os


_flask_app = None


def make_celery(app=None):
    """Create Celery instance with Flask app context."""
    broker = os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/0')
    backend = os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/0')

    celery = Celery(
        'recruit_tasks',
        broker=broker,
        backend=backend,
    )

    celery.conf.update(
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='Asia/Shanghai',
        enable_utc=True,
        task_track_started=True,
        task_acks_late=True,
        worker_prefetch_multiplier=1,
    )

    if app:
        celery.conf.update(app.config)

        class ContextTask(celery.Task):
            abstract = True

            def __call__(self, *args, **kwargs):
                with app.app_context():
                    return self.run(*args, **kwargs)

        celery.Task = ContextTask

    return celery


def init_celery(app):
    """Initialize celery with Flask app for context-aware tasks."""
    global _flask_app
    _flask_app = app
    celery_app.conf.update(app.config)

    class ContextTask(celery_app.Task):
        abstract = True

        def __call__(self, *args, **kwargs):
            with _flask_app.app_context():
                return self.run(*args, **kwargs)

    celery_app.Task = ContextTask


# Default celery instance (used when running standalone)
celery_app = make_celery()
