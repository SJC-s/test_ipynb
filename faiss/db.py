import numpy as np
from sentence_transformers import SentenceTransformer

# 1. 한국어 문장 임베딩 모델 로드
print("임베딩 모델을 로드합니다...")
model = SentenceTransformer('jhgan/ko-sroberta-multitask')

# 2. 검색 대상이 될 샘플 문장 데이터
data = [
    "오늘 날씨가 정말 좋네요.",
    "서울의 맛집을 추천해주세요.",
    "파이썬으로 웹 스크래핑하는 방법이 궁금합니다.",
    "내일 비가 올 확률은 얼마나 되나요?",
    "인공지능 기술의 미래 전망에 대해 알려주세요.",
    "가장 인기 있는 프로그래밍 언어는 무엇인가요?",
    "최신 스마트폰 모델 비교 정보를 찾고 있습니다.",
    "근처에 있는 괜찮은 카페를 알려주세요."
]

# 3. 문장들을 벡터로 변환 (임베딩)
print("데이터를 벡터로 변환합니다...")
db_vectors = model.encode(data)

# 벡터의 차원과 데이터 개수 확인
num_vectors, d = db_vectors.shape
print(f"데이터베이스 벡터 수: {num_vectors}")
print(f"벡터 차원: {d}")
# 출력 예시:
# 데이터베이스 벡터 수: 8
# 벡터 차원: 768


import faiss

# 벡터 차원
d = db_vectors.shape[1]

# IndexIVFFlat을 위한 설정
nlist = 5  # 벡터 공간을 몇 개의 셀로 나눌지 결정 (데이터 크기에 따라 조정)
quantizer = faiss.IndexFlatL2(d)  # L2 거리(유클리드 거리) 기반의 기본 인덱스
index = faiss.IndexIVFFlat(quantizer, d, nlist, faiss.METRIC_L2)

# 3. 인덱스 학습 (Training)
# 이 과정에서 Faiss는 벡터 공간의 구조를 학습하여 클러스터(셀)의 중심점을 찾습니다.
print("Faiss 인덱스를 학습시킵니다...")
assert not index.is_trained
index.train(db_vectors)
assert index.is_trained

# 4. 학습된 인덱스에 벡터 추가
print("학습된 인덱스에 벡터를 추가합니다...")
index.add(db_vectors)

print(f"인덱스에 추가된 총 벡터 수: {index.ntotal}")


# 5. 검색 실행

# 검색할 쿼리 문장
query_text = "가장 좋은 프로그래밍 언어는?"

# 쿼리 문장을 벡터로 변환
query_vector = model.encode([query_text])

# 검색할 이웃의 수 (가장 유사한 3개)
k = 3

print(f"\n''{query_text}''와(과) 유사한 문장을 검색합니다...")

# 검색 수행
# D: 쿼리 벡터와 검색된 벡터들 사이의 거리(distance) 배열
# I: 검색된 벡터들의 인덱스(index) 배열
D, I = index.search(query_vector, k)

# 6. 결과 출력
print("--- 검색 결과 ---")
for i, dist in zip(I[0], D[0]):
    print(f"인덱스: {i}, 유사도(거리): {dist:.4f}, 문장: {data[i]}")

# 예상 출력:
# --- 검색 결과 ---
# 인덱스: 5, 유사도(거리): 0.3456, 문장: 가장 인기 있는 프로그래밍 언어는 무엇인가요?
# 인덱스: 2, 유사도(거리): 0.8765, 문장: 파이썬으로 웹 스크래핑하는 방법이 궁금합니다.
# 인덱스: 4, 유사도(거리): 1.1234, 문장: 인공지능 기술의 미래 전망에 대해 알려주세요.


# 인덱스 저장
faiss.write_index(index, "my_faiss_index.bin")

# 인덱스 로드
loaded_index = faiss.read_index("my_faiss_index.bin")

print(f"\n로드된 인덱스의 벡터 수: {loaded_index.ntotal}")

# 로드된 인덱스로 검색 테스트
D, I = loaded_index.search(query_vector, k)
print("--- 로드된 인덱스 검색 결과 ---")
for i in I[0]:
    print(data[i])