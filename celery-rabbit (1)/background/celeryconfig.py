import os

broker_url = os.getenv("CELERY_BROKER_URL", "pyamqp://guest:guest@localhost:5672")
result_backend = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379")

task_serializer = "json"
accept_content = ["json"]
result_serializer = "json"
enable_utc = True
timezone = "UTC"
broker_connection_retry_on_startup = True

# Group 결과 저장 설정
result_expires = 3600  # 결과를 1시간 동안 보관
task_track_started = True  # 작업 시작 상태 추적
task_store_eager_result = True  # eager 모드에서도 결과 저장
result_persistent = True  # 결과를 지속적으로 저장