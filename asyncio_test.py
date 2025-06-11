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

# 예제 3 : 비동기로 웹페이지 가져오기
import asyncio
import aiohttp

async def fetch(session, url):
    async with session.get(url) as response:
        return await response.text()

async def main():
    async with aiohttp.ClientSession() as session:
        html = await fetch(session, 'https://www.example.com')
        print(html)

asyncio.run(main())

