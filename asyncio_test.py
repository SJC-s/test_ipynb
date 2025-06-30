# 메모
# async def: 비동기 함수 정의
# await: 비동기 함수 호출 및 대기
# asyncio.run(): 최상위 비동기 함수 실행(이벤트 루프 자동 관리)
# asyncio.create_task(): 여러 비동기 작업을 병렬로 실행할 때 사용
# asyncio.sleep(): 비동기적으로 대기


# -------------------------------------------------------------


# # 예제
# import asyncio
# import time

# async def main():
#     print(f'{time.ctime()} Hello!')
#     await asyncio.sleep(1.0)
#     print(f'{time.ctime()} Goodbye!')



# asyncio.run(main())

# -------------------------------------------------------------

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

# -------------------------------------------------------------

# # asyncio.Task 취소(Cancel) 패턴
# import asyncio
# from typing import Dict

# # response_id 별로 현재 예약된 Task를 보관
# pending_tasks: Dict[str, asyncio.Task] = {}

# async def _process(response_id: str):
#     # 실제 처리 로직 (예: 외부 API 호출, DB 조회 등)
#     await asyncio.sleep(1.0)  # 예시 지연
#     print(f"[Processed] {response_id}")

# async def handle_request(response_id: str):
#     # 이전에 대기 중인 Task가 있으면 취소
#     old = pending_tasks.get(response_id)
#     if old and not old.done():
#         old.cancel()
#         try:
#             await old
#         except asyncio.CancelledError:
#             print(f"[Cancelled] 이전 요청: {response_id}")

#     # 새로운 Task 생성 후 저장
#     task = asyncio.create_task(_process(response_id))
#     pending_tasks[response_id] = task

# # 테스트
# async def main():
#     # A에 3번 호출, 마지막만 처리되어야 함
#     await handle_request("A")
#     await asyncio.sleep(0.3)
#     await handle_request("A")
#     await asyncio.sleep(0.3)
#     await handle_request("A")
#     # 충분히 기다려서 처리된 것 출력 확인
#     await asyncio.sleep(2.0)

# asyncio.run(main())

# -------------------------------------------------------------

# # 예제 4 : 취소 패턴
# import asyncio

# async def worker(name: str):
#     try:
#         print(f"[{name}] 시작")
#         # 무한 루프 대신 적절한 awaitable 사용
#         while True:
#             print(f"[{name}] 작업 진행 중...")
#             await asyncio.sleep(1)
#     except asyncio.CancelledError:
#         print(f"[{name}] 취소 요청 받음!")
#         # 필요하다면 여기서 추가 clean-up 작업 수행
#         raise
#     finally:
#         print(f"[{name}] 정리 작업 완료")

# async def main():
#     # 여러 작업 생성
#     tasks = [
#         asyncio.create_task(worker("태스크1"), name="task1"),
#         asyncio.create_task(worker("태스크2"), name="task2"),
#         asyncio.create_task(worker("태스크3"), name="task3"),
#     ]

#     # 5초 후 모든 태스크 취소
#     await asyncio.sleep(5)
#     print("모든 태스크에 취소 요청 전송")
#     for t in tasks:
#         t.cancel()  # 취소 요청 :contentReference[oaicite:1]{index=1}

#     # 태스크들이 취소될 때까지 대기
#     for t in tasks:
#         try:
#             await t
#         except asyncio.CancelledError:
#             print(f"[{t.get_name()}] 취소 완료")

#     print("모든 태스크 종료")

# if __name__ == "__main__":
#     asyncio.run(main())

# -------------------------------------------------------------

# PendingTaskManager 테스트 예제
import asyncio
import logging
from typing import Awaitable, Any

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# request_key 별로 현재 예약된 Task를 보관
class PendingTaskManager:
    def __init__(self):
        self._tasks: dict[str, asyncio.Task] = {}
        self._lock = asyncio.Lock()

    async def add(self, key: str, coro: Awaitable[Any]) -> asyncio.Task:
        async with self._lock:
            # 이전 태스크가 남아 있으면 취소
            previous = self._tasks.get(key)
            if previous and not previous.done():
                logger.info(f"🚫 이전 요청 취소 중: {key}")
                previous.cancel()
                try:
                    await previous
                except asyncio.CancelledError:
                    logger.info(f"✅ 이전 요청 취소 완료: {key}")
                except Exception as e:
                    logger.error(f"❌ 취소 중 오류: {e}")
            # 새로운 태스크 생성 및 등록
            task = asyncio.create_task(coro)
            self._tasks[key] = task
            logger.info(f"🔄 새로운 요청 등록: {key}")
            return task

    async def cancel_all(self):
        async with self._lock:
            for key, task in self._tasks.items():
                if not task.done():
                    task.cancel()
            # 모든 태스크가 정리될 때까지 대기
            await asyncio.gather(*self._tasks.values(), return_exceptions=True)
    
    async def remove(self, key: str):
        """완료된 태스크를 관리 목록에서 제거"""
        async with self._lock:
            if key in self._tasks:
                del self._tasks[key]
                logger.info(f"🗑️ 태스크 제거됨: {key}")

# 모의 앱 상태 (FastAPI app.state 대신)
class AppState:
    def __init__(self):
        self.task_manager = PendingTaskManager()

app_state = AppState()

# DI로 관리자 주입
def get_task_manager() -> PendingTaskManager:
    """앱 상태에서 PendingTaskManager 인스턴스를 반환"""
    return app_state.task_manager

# 테스트용 비동기 작업 함수들
async def long_running_task(task_id: str, duration: int = 3):
    """오래 걸리는 작업을 시뮬레이션"""
    try:
        logger.info(f"🚀 [{task_id}] 작업 시작 (예상 소요 시간: {duration}초)")
        for i in range(duration):
            await asyncio.sleep(1)
            logger.info(f"⏳ [{task_id}] 진행 중... ({i+1}/{duration})")
        logger.info(f"✅ [{task_id}] 작업 완료!")
        return f"결과: {task_id}"
    except asyncio.CancelledError:
        logger.info(f"🛑 [{task_id}] 작업이 취소되었습니다")
        raise

async def api_simulation(request_key: str, data: str):
    """API 요청을 시뮬레이션하는 함수"""
    try:
        logger.info(f"📡 [{request_key}] API 요청 처리 시작: {data}")
        # 실제 API 호출을 시뮬레이션 (2초 소요)
        await asyncio.sleep(2)
        result = f"API 응답: {data} 처리 완료"
        logger.info(f"📥 [{request_key}] API 응답 완료")
        return result
    except asyncio.CancelledError:
        logger.info(f"🚫 [{request_key}] API 요청이 취소되었습니다")
        raise

# 테스트 시나리오들
async def test_scenario_1_cancel_previous():
    """시나리오 1: 이전 요청 취소 테스트"""
    logger.info("=" * 50)
    logger.info("🧪 테스트 시나리오 1: 이전 요청 취소")
    logger.info("=" * 50)
    
    task_manager = get_task_manager()
    
    # 같은 키로 여러 요청 생성 (마지막 요청만 완료되어야 함)
    await task_manager.add("user_123", long_running_task("첫번째_요청", 5))
    await asyncio.sleep(1)  # 잠시 대기
    
    await task_manager.add("user_123", long_running_task("두번째_요청", 5))
    await asyncio.sleep(1)  # 잠시 대기
    
    final_task = await task_manager.add("user_123", long_running_task("최종_요청", 3))
    
    # 최종 요청 완료까지 대기
    try:
        result = await final_task
        logger.info(f"🎉 최종 결과: {result}")
    except Exception as e:
        logger.error(f"❌ 오류 발생: {e}")
    
    # 완료된 태스크 제거
    await task_manager.remove("user_123")

async def test_scenario_2_multiple_users():
    """시나리오 2: 여러 사용자 동시 처리"""
    logger.info("=" * 50)
    logger.info("🧪 테스트 시나리오 2: 여러 사용자 동시 처리")
    logger.info("=" * 50)
    
    task_manager = get_task_manager()
    
    # 서로 다른 사용자의 요청들 (병렬 처리)
    tasks = []
    users = ["user_A", "user_B", "user_C"]
    
    for user in users:
        task = await task_manager.add(user, api_simulation(user, f"{user}의 데이터"))
        tasks.append(task)
    
    # 모든 사용자의 요청 완료까지 대기
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    for user, result in zip(users, results):
        if isinstance(result, Exception):
            logger.error(f"❌ {user} 오류: {result}")
        else:
            logger.info(f"✅ {user} 완료: {result}")
        await task_manager.remove(user)

async def test_scenario_3_cancel_all():
    """시나리오 3: 모든 태스크 취소"""
    logger.info("=" * 50)
    logger.info("🧪 테스트 시나리오 3: 모든 태스크 취소")
    logger.info("=" * 50)
    
    task_manager = get_task_manager()
    
    # 여러 장기 실행 태스크 생성
    await task_manager.add("task_1", long_running_task("장기작업_1", 10))
    await task_manager.add("task_2", long_running_task("장기작업_2", 10))
    await task_manager.add("task_3", long_running_task("장기작업_3", 10))
    
    # 3초 후 모든 태스크 취소
    await asyncio.sleep(3)
    logger.info("🛑 모든 태스크 취소 요청")
    await task_manager.cancel_all()
    logger.info("✅ 모든 태스크 취소 완료")

async def test_scenario_4_rapid_requests():
    """시나리오 4: 빠른 연속 요청 (디바운싱 효과)"""
    logger.info("=" * 50)
    logger.info("🧪 테스트 시나리오 4: 빠른 연속 요청")
    logger.info("=" * 50)
    
    task_manager = get_task_manager()
    
    # 0.2초 간격으로 10번 요청 (마지막 요청만 처리되어야 함)
    for i in range(10):
        await task_manager.add("rapid_user", api_simulation("rapid_user", f"요청_{i+1}"))
        await asyncio.sleep(0.2)
    
    # 마지막 요청 완료까지 충분히 대기
    await asyncio.sleep(3)
    await task_manager.remove("rapid_user")

# 메인 테스트 실행 함수
async def run_all_tests():
    """모든 테스트 시나리오 실행"""
    logger.info("🎯 PendingTaskManager 테스트 시작")
    
    try:
        await test_scenario_1_cancel_previous()
        await asyncio.sleep(1)  # 시나리오 간 간격
        
        await test_scenario_2_multiple_users()
        await asyncio.sleep(1)
        
        await test_scenario_3_cancel_all()
        await asyncio.sleep(1)
        
        await test_scenario_4_rapid_requests()
        
    except Exception as e:
        logger.error(f"❌ 테스트 중 오류 발생: {e}")
    
    logger.info("🏁 모든 테스트 완료")

# 테스트 실행
if __name__ == "__main__":
    asyncio.run(run_all_tests())
