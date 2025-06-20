# app/celery.py
from celery import Celery
import os


REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

celery_app = Celery(
    'worker', 
    broker=REDIS_URL,
    backend=REDIS_URL
    
)

# Celery 앱 생성
app = Celery('tasks', broker=REDIS_URL)

@app.task
def add(x, y):
    return x + y

# 비동기 작업 실행
result = add.delay(10, 20)
print(result.get())
