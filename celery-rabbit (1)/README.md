# Celery + RabbitMQ + FastAPI 분산 작업 시스템

FastAPI와 Celery를 사용한 분산 작업 처리 시스템입니다. RabbitMQ를 메시지 브로커로, Redis를 결과 백엔드로 사용합니다.

## 🏗️ 프로젝트 구조

```
celery-rabbit/
├── app.py                          # FastAPI 웹 애플리케이션
├── background/
│   ├── celery.py                   # Celery 앱 초기화
│   ├── celeryconfig.py             # Celery 설정
│   └── tasks/
│       └── default_tasks.py        # 비동기 작업 정의
├── data/                           # 데이터 볼륨 마운트 포인트
├── docker-compose.yaml             # Docker Compose 설정
├── Dockerfile                      # Docker 이미지 빌드 설정
├── requirements.txt                # Python 의존성
└── README.md                       # 이 파일
```

## 🚀 주요 기능

### 1. FastAPI 웹 서버 (포트: 8001)
- **GET `/`**: 기본 상태 확인
- **GET `/solo/add`**: 단일 비동기 작업 발행 (20초 소요)
- **GET `/solo/chain`**: 연속 작업 실행 (덧셈 → 곱셈)
- **GET `/solo/group`**: 병렬 작업 실행 (덧셈과 곱셈 동시)
- **GET `/result/{task_id}`**: 단일/체인 작업 결과 조회
- **GET `/result/group/{group_id}`**: 그룹 작업 결과 조회

### 2. Celery Worker (기본 큐 사용)
- 모든 큐에서 작업을 처리
- 지원하는 작업 유형:
  - `add_task`: 두 숫자 덧셈 (20초 소요)
  - `multi_task`: 두 숫자 곱셈 (2초 소요)
  - `sum_multiply_task`: 합계와 각 숫자의 곱셈 (2초 소요)
- 동시성: 2개 워커

### 3. Flower 모니터링 (포트: 5555)
- Celery 작업 상태 실시간 모니터링
- 큐 상태, 워커 상태, 작업 이력 확인
- 다양한 작업 패턴별 성능 모니터링

### 4. RabbitMQ (포트: 5672, 관리 UI: 15672)
- 메시지 브로커 역할
- Health Check 기능으로 안정성 보장
- 관리 UI 접속: `http://localhost:15672` (guest/guest)

### 5. Redis (포트: 6379)
- 작업 결과 저장소
- GroupResult 메타데이터 저장

## ⚙️ 기술 스택

- **Web Framework**: FastAPI
- **Task Queue**: Celery 5.5.3
- **Message Broker**: RabbitMQ 4.0
- **Result Backend**: Redis
- **Monitoring**: Flower
- **Containerization**: Docker & Docker Compose

## 🔧 설치 및 실행

### 필수 요구사항
- Docker
- Docker Compose

### 1. 프로젝트 클론 및 실행
```bash
# 프로젝트 디렉토리로 이동
cd celery-rabbit

# Docker Compose로 전체 스택 실행
docker-compose up --build
```

### 2. 서비스 접속 URL
- **FastAPI 앱**: http://localhost:8001
- **Flower 모니터링**: http://localhost:5555
- **RabbitMQ 관리 UI**: http://localhost:15672
- **Redis**: localhost:6379

## 📋 사용 방법

### 1. 작업 패턴별 사용법

#### 🔹 단일 작업 (Solo Task)
```bash
# 단일 덧셈 작업 실행 (20초 소요)
curl http://localhost:8001/solo/add

# 응답 예시:
{
  "message": "FastAPI : a=45, b=23 Published to the queue",
  "task_id": "abc123-def456-ghi789"
}

# 결과 확인
curl http://localhost:8001/result/abc123-def456-ghi789
```

#### ⛓️ 체인 작업 (Chain Task)
```bash
# 연속 작업: 덧셈 → 각 숫자와 합계의 곱셈
curl http://localhost:8001/solo/chain

# 응답 예시:
{
  "message": "Chain task result",
  "task_id": "chain123-456",
  "status_code": 200
}

# 결과 확인 (체인의 최종 결과)
curl http://localhost:8001/result/chain123-456
```

#### 🔀 그룹 작업 (Group Task)
```bash
# 병렬 작업: 덧셈과 곱셈을 동시 실행
curl http://localhost:8001/solo/group

# 응답 예시:
{
  "message": "Group task submitted : a = 20, b = 76",
  "group_id": "group123-456",
  "individual_tasks": ["task1_id", "task2_id"],
  "check_result_url": "/result/group/group123-456"
}

# 그룹 결과 확인
curl http://localhost:8001/result/group/group123-456

# 개별 작업 결과도 확인 가능
curl http://localhost:8001/result/task1_id
```

### 2. 작업 상태 확인
- **Flower UI**: http://localhost:5555 (실시간 모니터링)
- **워커 로그**: `docker logs celery-test-worker -f`
- **RabbitMQ 관리 UI**: http://localhost:15672 (guest/guest)

### 3. 결과 조회 상태 코드
- **200**: 작업 완료 (결과 반환)
- **202**: 작업 진행 중 (아직 완료되지 않음)
- **404**: 작업 ID를 찾을 수 없음
- **500**: 서버 오류

## 🐳 Docker 서비스 구성

### Web Service
- FastAPI 애플리케이션 실행
- 포트: 8001 → 8000

### Worker Service  
- Celery 워커 실행
- `default-sum` 큐에서 작업 처리
- 동시성: 2개 워커

### Flower Service
- Celery 모니터링 대시보드
- 포트: 5555

### RabbitMQ Service
- 메시지 브로커
- 관리 UI 포함
- 데이터 영속성을 위한 볼륨 마운트

### Redis Service
- 작업 결과 저장
- Redis Stack Server 사용

## 🔍 환경 변수

```yaml
CELERY_BROKER_URL=amqp://guest:guest@rabbitmq:5672
CELERY_RESULT_BACKEND=redis://redis:6379
RABBITMQ_DEFAULT_USER=guest
RABBITMQ_DEFAULT_PASS=guest
RABBITMQ_DEFAULT_VHOST=/
```

## 📊 모니터링

### Flower 대시보드에서 확인 가능한 정보:
- 활성 작업 수
- 완료된 작업 수
- 실패한 작업 수
- 워커 상태
- 큐 길이
- 작업 실행 시간

### 로그 확인:
```bash
# 전체 서비스 로그
docker-compose logs -f

# 특정 서비스 로그
docker logs celery-test-worker -f
docker logs celery-test-web -f
docker logs celery-test-flower -f
```

## 🛠️ 개발 모드

### 로컬 개발 환경에서 실행:
```bash
# 의존성 설치
pip install -r requirements.txt

# RabbitMQ와 Redis만 Docker로 실행
docker-compose up rabbitmq redis

# 별도 터미널에서 각각 실행
uvicorn app:app --reload --port 8000
celery -A background.celery.celery_app worker -Q default-sum --loglevel=info
celery -A background.celery.celery_app flower --port=5555
```

## 🎯 Celery 작업 패턴 심화

### 📊 작업 패턴별 특징 비교

| 패턴 | 실행 방식 | 결과 저장 | 적용 사례 |
|------|-----------|-----------|-----------|
| **Solo** | 단일 작업 | 자동 저장 | 파일 업로드, 이메일 발송 |
| **Chain** | 순차 실행 | 자동 저장 (최종 결과) | 데이터 파이프라인, 워크플로 |
| **Group** | 병렬 실행 | 수동 저장 필요 | 배치 처리, 병렬 계산 |

### 🔄 AsyncResult vs GroupResult 저장 차이

#### ✅ 자동 저장 (AsyncResult, Chain)
```python
# 단일 작업 - Worker가 완료 시 자동 저장
result = celery_app.send_task("add_task", kwargs={"a": 1, "b": 2})
# Redis: celery-task-meta-{task_id} ← 자동 생성

# Chain 작업 - 마지막 작업 결과가 전체 결과
task = chain(add_task.s(1, 2), multiply_task.s(10))
result = task.apply_async()
# Redis: celery-task-meta-{chain_id} ← 자동 생성
```

#### ⚠️ 수동 저장 필요 (GroupResult)
```python
# Group 작업 - 메타데이터는 수동 저장 필요
task = group(add_task.s(1, 2), multiply_task.s(3, 4))
result = task.apply_async()
result.save()  # ← 이 단계가 필요!
# Redis: celery-taskset-meta-{group_id} ← 수동 생성

# 이유: Group은 개별 작업들의 "메타데이터 관리자" 역할
#       실제 작업이 아니므로 명시적 저장 필요
```

## 🏥 RabbitMQ Health Check

### 💡 Health Check의 역할
현재 프로젝트는 RabbitMQ가 완전히 준비될 때까지 다른 서비스들이 대기하도록 설정되어 있습니다.

```yaml
# docker-compose.yaml
healthcheck:
  test: ["CMD", "rabbitmq-diagnostics", "ping"]
  interval: 30s    # 30초마다 체크
  timeout: 10s     # 10초 내 응답 필요
  retries: 5       # 5번 실패 시 unhealthy

depends_on:
  rabbitmq:
    condition: service_healthy  # RabbitMQ healthy 후 시작
```

### 🔍 Health Check 명령어
```bash
# 기본 ping 체크
docker exec celery-test-rabbitmq rabbitmq-diagnostics ping

# 상세 상태 확인
docker exec celery-test-rabbitmq rabbitmq-diagnostics status

# 포트 연결 확인
docker exec celery-test-rabbitmq rabbitmq-diagnostics listeners

# Health Check 상태 확인
docker ps  # STATUS 컬럼에서 healthy 상태 확인
```

## 🛠️ Supervisor를 활용한 프로세스 관리

### 📋 Supervisor vs Docker Compose

| 구분 | Docker Compose | Supervisor |
|------|----------------|------------|
| **관리 단위** | 컨테이너 | 프로세스 |
| **적용 환경** | 개발/테스트 | 운영 환경 |
| **재시작 정책** | `restart: always` | `autorestart=true` |
| **로그 관리** | Docker 로그 | 파일 기반 로그 |

### 🚀 Supervisor 설정 예시
프로젝트에 `supervisor.conf` 파일이 포함되어 있습니다:

```ini
[program:celery-worker]
command=celery -A background.celery.celery_app worker --loglevel=info --concurrency=2
autostart=true       # 자동 시작
autorestart=true     # 크래시 시 자동 재시작
startsecs=10        # 10초 후 성공으로 간주
stdout_logfile=/var/log/celery/worker.log
```

### 📊 Supervisor 명령어
```bash
# 모든 프로세스 상태 확인
supervisorctl status

# 특정 프로세스 재시작
supervisorctl restart celery-worker

# 실시간 로그 확인
supervisorctl tail -f celery-worker

# 설정 리로드
supervisorctl reread && supervisorctl update
```

## 🔧 커스터마이징

### 새로운 작업 추가:
1. `background/tasks/` 디렉토리에 새 작업 파일 생성
2. `background/celery.py`의 `include` 리스트에 추가
3. 필요시 큐 설정 추가

### 큐 설정 변경:
```bash
# 특정 큐만 처리하고 싶은 경우
command: celery -A background.celery.celery_app worker -Q high-priority,low-priority

# 모든 큐 처리 (현재 설정)
command: celery -A background.celery.celery_app worker
```

### Group 결과 저장 비활성화:
```python
# default/service.py에서 result.save() 제거
# 단, 이 경우 group 결과 조회 불가
```

## 🚨 문제 해결 (Troubleshooting)

### ❌ Group 결과 조회 시 404 오류
```bash
# 증상: GET /result/group/{group_id} → 404 Not Found

# 원인: GroupResult.save() 호출 누락
# 해결: default/service.py에서 result.save() 추가됨 ✅
```

### ⚠️ RabbitMQ 연결 실패
```bash
# 증상: celery.exceptions.OperationalError: [Errno 111] Connection refused

# 원인: RabbitMQ가 완전히 시작되기 전에 Worker가 시작됨
# 해결: Health Check로 해결됨 ✅
#       depends_on: condition: service_healthy
```

### 🔄 작업이 실행되지 않음
```bash
# 1. 워커 상태 확인
docker logs celery-test-worker

# 2. RabbitMQ 큐 상태 확인
# http://localhost:15672 → Queues 탭

# 3. Redis 연결 확인
docker exec redis redis-cli ping
```

### 📊 Group vs Chain 선택 가이드
```python
# ✅ Chain 사용: 순차적 의존성이 있는 경우
# 예: 이미지 업로드 → 썸네일 생성 → 메타데이터 저장

# ✅ Group 사용: 독립적 병렬 처리가 필요한 경우
# 예: 여러 파일 동시 처리, 여러 API 동시 호출
```

## 🎯 성능 최적화 팁

### 🚀 Worker 동시성 조정
```yaml
# docker-compose.yaml
command: celery -A background.celery.celery_app worker --concurrency=4
# CPU 코어 수에 맞게 조정
```

### ⏱️ 작업 타임아웃 설정
```python
# background/celeryconfig.py
task_soft_time_limit = 600  # 10분 소프트 제한
task_time_limit = 1200      # 20분 하드 제한
```

### 📈 메모리 사용량 모니터링
```bash
# Flower에서 실시간 모니터링
# http://localhost:5555 → Monitor 탭

# 시스템 리소스 확인
docker stats
```

## 📚 참고 자료

- [Celery 공식 문서](https://docs.celeryproject.org/)
- [FastAPI 공식 문서](https://fastapi.tiangolo.com/)
- [RabbitMQ 공식 문서](https://www.rabbitmq.com/documentation.html)
- [Flower 공식 문서](https://flower.readthedocs.io/)
- [Docker Compose Health Check](https://docs.docker.com/compose/compose-file/compose-file-v3/#healthcheck)
- [Supervisor 공식 문서](http://supervisord.org/)

## 🏁 정리

이 프로젝트는 마이크로서비스 아키텍처에서 비동기 작업 처리를 위한 **완전한 스택**을 제공합니다:

### ✅ **핵심 기능**
- **3가지 작업 패턴**: Solo, Chain, Group
- **안정적인 Health Check**: RabbitMQ 준비 완료 후 서비스 시작
- **실시간 모니터링**: Flower 대시보드
- **결과 저장**: Redis 백엔드 with GroupResult 지원

### 🎯 **실무 적용 가능한 기능들**
- **파일 처리**: 업로드 → 변환 → 저장 파이프라인 (Chain)
- **배치 처리**: 대용량 데이터 병렬 처리 (Group)
- **알림 시스템**: 이메일, SMS 등 비동기 발송 (Solo)
- **데이터 ETL**: 추출 → 변환 → 적재 워크플로 (Chain)

### 🚀 **확장 가능성**
- **Kubernetes**: 컨테이너 오케스트레이션 적용 가능
- **Auto Scaling**: Worker 개수 동적 조정
- **모니터링**: Prometheus, Grafana 연동
- **로그 수집**: ELK Stack 통합

웹 애플리케이션에서 **시간이 오래 걸리는 작업을 백그라운드에서 안정적으로 처리**하고, **실시간으로 모니터링**할 수 있는 **프로덕션 레벨의 환경**을 구축할 수 있습니다! 