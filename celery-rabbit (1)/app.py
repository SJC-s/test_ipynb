from unittest import result
from fastapi import FastAPI
from fastapi.responses import JSONResponse, PlainTextResponse
app = FastAPI()

from document_parser.app import document_router
routers = [
    document_router
]

for router in routers:
    app.include_router(router)

@app.get("/")
async def root():
    return JSONResponse(content={"message": "Celery RabbitMQ TEST"})

from random import randint
from background.celery import celery_app

from default.service import (
    chain_task,
    group_task
)


@app.get("/solo/add" , tags = ["default"] , description = "랜덤한 숫자를 더하는 task => 20초 뒤 완료")
async def publish_task():
    try:
        a = randint(1, 100)
        b = randint(1, 100)

        result = celery_app.send_task(
            "background.tasks.default_tasks.add_task", # 첫번째 인자값(=name)으로 생성하는 작업을 처리할 worker(=처리 함수)를 지정
            kwargs={"a" : a , "b" : b} # kwargs 인자값으로 worker 인자값을 전달 가능
        )

        return JSONResponse(content = {
            "message" : f"FastAPI : {a=},{ b=} Published to the queue",
            "task_id" : result.id
        }, status_code =200)
    except Exception as e:
        return JSONResponse(content = {
            "message" : f"Error : {e}",
            "status_code" : 500
        }, status_code = 500)
    


@app.get("/solo/chain", tags= ["default"] , description = "랜덤한 숫자 더한 후 => 더한 결과를 * 각각 a, b 에 곱하기")
async def publish_chain_task():
    try:
        a = randint(1, 100)
        b = randint(1, 100)

        result = await chain_task(a, b)

        return JSONResponse(content = {
            "message" : f"Chain task result : {result}",
            "first_step_id" : result.parent.id,
            "task_id" : result.id,
            "status_code" : 200
        }, status_code = 200)

        
    except Exception as e:
        return JSONResponse(content = {
            "message" : f"Error : {e}",
            "status_code" : 500
        }, status_code = 500)
    
@app.get("/solo/group", tags= ["default"] , description = "랜덤한 숫자 더하기와 곱하기 동시 실행")
async def publish_group_task():
    try:
        a = randint(1, 100)
        b = randint(1, 100)

        result = await group_task(a, b)

        return JSONResponse(content={
            "message" : f"Group task submitted : a = {a}, b = {b}",
            "group_id" : result.id,
            "individual_tasks": [task.id for task in result.results] if hasattr(result, 'results') else [],
            "check_result_url": f"/result/group/{result.id}"
        }, status_code = 200)


    except Exception as e:
        return JSONResponse(content = {
            "message" : f"Error : {e}",
            "status_code" : 500
        }, status_code = 500)




# 결과 확인 용 Endpoint
@app.get(
    "/result/{task_id}", 
    tags= ["default"] , 
    description = """
    랜덤한 숫자 결과 확인하는 엔드포인트

    완료 전에는 202 상태 코드 반환

    chain 과 일반 요청은 가능 
    group 은 다른 방식으로 사용해야할듯
    """
)
async def get_result(task_id : str):
    print(f"Task ID : {task_id}")

    result = celery_app.AsyncResult(task_id)

    info = result.info if result.info else {}

    result_data = {
        "task_id" : task_id,
        "status" : result.status,
        "result" : result.result if result.ready() else None,
        "ready" : result.ready(),
        "successful" : result.successful(),
        "failed" : result.failed() if result.ready() else False,
        "info" : info
    }

    if result.ready():
        return JSONResponse(content = {
            "message" : f"Task {task_id} is ready",
            "result" : result_data
        }, status_code = 200)
    else:
        return JSONResponse(content = {
            "message" : f"Task {task_id} is not ready",
            "result" : result_data,
            "status_code" : 202
        }, status_code = 202)

@app.get("/result/chain/detail/{chain_id}", tags=["default"], description="Chain 작업의 상세 진행 상황 확인")
async def get_chain_detail(chain_id: str):
    try:
        # Chain의 메인 결과 확인
        chain_result = celery_app.AsyncResult(chain_id)
        
        response_data = {
            "chain_id": chain_id,
            "chain_status": chain_result.status,
            "chain_ready": chain_result.ready(),
            "chain_successful": chain_result.successful() if chain_result.ready() else False,
            "chain_result": chain_result.result if chain_result.ready() else None,
            "steps": []
        }
        
        # Chain의 개별 작업들 확인
        if hasattr(chain_result, 'children') and chain_result.children:
            for i, child in enumerate(chain_result.children):
                if hasattr(child, 'id'):
                    child_result = celery_app.AsyncResult(child.id)
                    step_info = {
                        "step_number": i + 1,
                        "task_id": child.id,
                        "status": child_result.status,
                        "ready": child_result.ready(),
                        "successful": child_result.successful() if child_result.ready() else False,
                        "result": child_result.result if child_result.ready() else None
                    }
                    
                    # 작업 이름 추정
                    if i == 0:
                        step_info["task_name"] = "add_task (Step 1: 덧셈)"
                        step_info["estimated_duration"] = "20초"
                    elif i == 1:
                        step_info["task_name"] = "sum_multiply_task (Step 2: 곱셈)"
                        step_info["estimated_duration"] = "2초"
                    
                    response_data["steps"].append(step_info)
        
        # 현재 진행 중인 단계 파악
        current_step = None
        for i, step in enumerate(response_data["steps"]):
            if step["status"] == "PENDING":
                current_step = f"Step {step['step_number']}: {step['task_name']}"
                break
            elif step["status"] == "STARTED":
                current_step = f"Step {step['step_number']}: {step['task_name']} (실행 중)"
                break
        
        if current_step:
            response_data["current_step"] = current_step
        elif chain_result.ready():
            response_data["current_step"] = "완료됨"
        else:
            response_data["current_step"] = "알 수 없음"
        
        # 전체 진행률 계산
        completed_steps = sum(1 for step in response_data["steps"] if step["ready"])
        total_steps = len(response_data["steps"])
        response_data["progress_percentage"] = (completed_steps / total_steps * 100) if total_steps > 0 else 0
        
        status_code = 200 if chain_result.ready() else 202
        
        return JSONResponse(content=response_data, status_code=status_code)
        
    except Exception as e:
        return JSONResponse(content={
            "error": f"Failed to get chain detail: {str(e)}",
            "chain_id": chain_id
        }, status_code=500)
    
@app.get("/result/group/{group_id}", tags= ["default"] , description = "group 결과 확인")
async def get_group_result(group_id : str):
    try:
        # GroupResult 복원 시도
        from celery.result import GroupResult
        results = GroupResult.restore(group_id)

        if not results:
            # 복원 실패 시 직접 생성 시도
            print(f"Trying to restore group {group_id} failed, attempting direct access...")
            
            # group_id로 직접 AsyncResult 생성
            async_result = celery_app.AsyncResult(group_id)
            
            if async_result.state == 'PENDING':
                return JSONResponse(content={
                    "error": f"Group {group_id} not found or pending", 
                    "suggestion": "Check if the group_id is correct"
                }, status_code=404)
            
            # AsyncResult를 GroupResult로 변환 시도
            return JSONResponse(content={
                "group_id": group_id,
                "status": async_result.status,
                "result": async_result.result if async_result.ready() else None,
                "ready": async_result.ready(),
                "note": "This appears to be a single task, not a group"
            }, status_code=200)
        
        # GroupResult가 성공적으로 복원된 경우
        children = []
        for r in results.results:
            children.append({
                "task_id" : r.id,
                "status" : r.status,
                "result" : r.result if r.ready() else None,
                "ready": r.ready(),
                "successful": r.successful() if r.ready() else False
            })

        return JSONResponse(content={
            "group_id": group_id,
            "ready" : results.ready(),
            "completed" : results.completed_count(),
            "total" : len(results.results),
            "successful": results.successful() if results.ready() else False,
            "children" : children
        }, status_code=200)
        
    except Exception as e:
        print(f"Error getting group result: {e}")
        return JSONResponse(content={
            "error": f"Failed to get group result: {str(e)}",
            "group_id": group_id
        }, status_code=500)

def get_chain_steps(chain_id):
    result = celery_app.AsyncResult(chain_id)
    
    print(f"="*10)
    print(f"=         STEPS        =")
    print(f"="*10)

    print(f"Chain ID : {chain_id}")
    print(f"Status : {result.status}")
    print(f"Ready : {result.ready()}")
    print(f"Successful : {result.successful()}")
    print(f"Failed : {result.failed()}")
    print(f"Result : {result.result}")
    print(f"children : {result.children}")

    steps = []
    idx = 1
    cur = result
    while cur:
        steps.append({
            "step": idx,
            "task_id": cur.id,
            "state": cur.state,
            "info": cur.info
        })
        if cur.children and len(cur.children) > 0:
            cur = cur.children[0]
            idx += 1
        else:
            break
    return steps


@app.get("/result/chain/progress/{chain_id}", tags=["default"])
async def chain_progress(chain_id: str):
    steps = get_chain_steps(chain_id)
    return {"steps": steps}


    
    
