# 메모
# async def: 비동기 함수 정의
# await: 비동기 함수 호출 및 대기
# asyncio.run(): 최상위 비동기 함수 실행(이벤트 루프 자동 관리)
# asyncio.create_task(): 여러 비동기 작업을 병렬로 실행할 때 사용
# asyncio.sleep(): 비동기적으로 대기


# # 예제
# import asyncio
# import time

# async def main():
#     print(f'{time.ctime()} Hello!')
#     await asyncio.sleep(1.0)
#     print(f'{time.ctime()} Goodbye!')



# asyncio.run(main())


# # 예제 2 : 여러 페이지
# import asyncio

# async def say_hello():
#     await asyncio.sleep(1)
#     print("Hello, World!")

# async def main():
#     task1 = asyncio.create_task(say_hello())
#     task2 = asyncio.create_task(say_hello())
#     await task1
#     await task2

# asyncio.run(main())

# # 예제 3 : 비동기로 웹페이지 가져오기
# import asyncio
# import aiohttp

# async def fetch(session, url):
#     async with session.get(url) as response:
#         return await response.text()

# async def main():
#     async with aiohttp.ClientSession() as session:
#         html = await fetch(session, 'https://www.example.com')
#         print(html)

# asyncio.run(main())



# asyncio.Task 취소(Cancel) 패턴
import asyncio
from typing import Dict

# response_id 별로 현재 예약된 Task를 보관
pending_tasks: Dict[str, asyncio.Task] = {}

async def _process(response_id: str):
    # 실제 처리 로직 (예: 외부 API 호출, DB 조회 등)
    await asyncio.sleep(1.0)  # 예시 지연
    print(f"[Processed] {response_id}")

async def handle_request(response_id: str):
    # 이전에 대기 중인 Task가 있으면 취소
    old = pending_tasks.get(response_id)
    if old and not old.done():
        old.cancel()
        try:
            await old
        except asyncio.CancelledError:
            print(f"[Cancelled] 이전 요청: {response_id}")

    # 새로운 Task 생성 후 저장
    task = asyncio.create_task(_process(response_id))
    pending_tasks[response_id] = task

# 테스트
async def main():
    # A에 3번 호출, 마지막만 처리되어야 함
    await handle_request("A")
    await asyncio.sleep(0.3)
    await handle_request("A")
    await asyncio.sleep(0.3)
    await handle_request("A")
    # 충분히 기다려서 처리된 것 출력 확인
    await asyncio.sleep(2.0)

asyncio.run(main())


