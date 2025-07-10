from db import FaissKnowledgeBase

# 간단한 테스트
def simple_test():
    print("=== 간단한 Faiss 테스트 ===")
    
    # 샘플 데이터
    documents = [
        "파이썬은 프로그래밍 언어입니다.",
        "자바는 인기있는 언어입니다.",
        "오늘 날씨가 좋네요.",
        "딥러닝은 인공지능 기술입니다."
    ]
    
    # 지식 베이스 생성
    kb = FaissKnowledgeBase(index_type='Flat')  # 작은 데이터용 Flat 인덱스
    
    # 문서 추가
    print("문서 추가 중...")
    kb.add_documents(documents)
    
    # 검색 테스트
    print("\n검색 테스트:")
    query = "프로그래밍 언어"
    results = kb.search(query, k=2)
    
    for i, (doc, distance) in enumerate(results, 1):
        print(f"  {i}. [{distance:.4f}] {doc}")
    
    # 저장/로드 테스트
    print("\n저장/로드 테스트:")
    kb.save("test_kb")
    
    # 새 인스턴스로 로드
    kb2 = FaissKnowledgeBase()
    kb2.load("test_kb")
    
    results2 = kb2.search("날씨", k=1)
    print(f"로드된 KB 검색 결과: {results2[0][0] if results2 else '없음'}")
    
    print("✅ 테스트 완료!")

if __name__ == "__main__":
    simple_test() 