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

    # Only propagate broker/backend settings, using NEW-style key names.
    # Pushing the whole Flask config would mix legacy CELERY_* keys with
    # new-style keys and raise ImproperlyConfigured.
    celery_app.conf.update(
        broker_url=app.config.get('CELERY_BROKER_URL', celery_app.conf.broker_url),
        result_backend=app.config.get('CELERY_RESULT_BACKEND', celery_app.conf.result_backend),
    )

    class ContextTask(celery_app.Task):
        abstract = True

        def __call__(self, *args, **kwargs):
            with _flask_app.app_context():
                return self.run(*args, **kwargs)

    celery_app.Task = ContextTask


# Default celery instance (used when running standalone)
celery_app = make_celery()

# Register task modules so the worker/beat knows them
celery_app.conf.update(
    include=['tasks.email_sync', 'tasks.notify', 'tasks.match_batch'],
)

# Bind a Flask app so every task runs inside an application context
# (db.session, config, crypto, etc. depend on it). create_app does not
# import tasks, so there is no circular-import risk.
try:
    from app import create_app as _create_app
    init_celery(_create_app())
except Exception as _exc:  # worker can still boot; tasks will surface errors
    import logging as _logging
    _logging.getLogger(__name__).warning(
        "init_celery skipped (Flask app not ready): %s", _exc)
