from celery import Celery

celery_app = Celery(
    "Celery-Test-App",
    include=[
        "background.tasks.default_tasks",
        "background.tasks.document_tasks"
    ]
)

celery_app.config_from_object("background.celeryconfig")