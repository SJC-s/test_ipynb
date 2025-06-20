from background.tasks.default_tasks import multi_task, add_task, sum_multiply_task
from celery import chain, group

import logging

async def chain_task(a, b):

    print(f"Chain task start : {a=}, {b=}")

    # Chain 구성 - 각 작업을 개별적으로 정의
    step1 = add_task.s(a, b)
    step2 = sum_multiply_task.s(a, b)
    
    task = chain(step1, step2)
    result = task.apply_async()

    return result

async def group_task(a, b):
    print(f"Group task start : {a=}, {b=}")

    task = group(
        add_task.s(a, b),
        multi_task.s(a, b),
    )

    # Group 결과를 저장하도록 설정
    result = task.apply_async()
    result.save()  # GroupResult를 Redis에 저장
    
    print(f"Group task submitted with ID: {result.id}")

    return result