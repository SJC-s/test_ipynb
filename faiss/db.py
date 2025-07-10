import numpy as np
import faiss
import pickle
import os
import logging
from typing import List, Tuple, Optional
from sentence_transformers import SentenceTransformer

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FaissKnowledgeBase:
    """
    Faiss를 이용한 한국어 지식 베이스 클래스
    벡터 검색을 통한 유사 문서 검색 기능 제공
    """
    
    def __init__(self, model_name: str = 'jhgan/ko-sroberta-multitask', index_type: str = 'IVFFlat'):
        """
        초기화
        
        Args:
            model_name: 사용할 임베딩 모델명
            index_type: Faiss 인덱스 타입 ('Flat', 'IVFFlat', 'HNSW')
        """
        self.model_name = model_name
        self.index_type = index_type
        self.model = None
        self.index = None
        self.data = []
        self.is_trained = False
        
        logger.info(f"FaissKnowledgeBase 초기화 - 모델: {model_name}, 인덱스: {index_type}")
        
    def _load_model(self):
        """임베딩 모델 로드"""
        if self.model is None:
            logger.info("임베딩 모델을 로드합니다...")
            try:
                self.model = SentenceTransformer(self.model_name)
                logger.info("모델 로드 완료")
            except Exception as e:
                logger.error(f"모델 로드 실패: {e}")
                raise
    
    def _create_index(self, dimension: int, num_vectors: int):
        """
        Faiss 인덱스 생성
        
        Args:
            dimension: 벡터 차원
            num_vectors: 벡터 개수
        """
        logger.info(f"Faiss 인덱스 생성 - 타입: {self.index_type}, 차원: {dimension}")
        
        if self.index_type == 'Flat':
            # 정확한 검색, 작은 데이터셋용
            self.index = faiss.IndexFlatL2(dimension)
            
        elif self.index_type == 'IVFFlat':
            # 빠른 검색, 중간 크기 데이터셋용
            nlist = min(max(int(np.sqrt(num_vectors)), 1), num_vectors)  # 적응적 nlist 설정
            quantizer = faiss.IndexFlatL2(dimension)
            self.index = faiss.IndexIVFFlat(quantizer, dimension, nlist, faiss.METRIC_L2)
            
        elif self.index_type == 'HNSW':
            # 매우 빠른 검색, 큰 데이터셋용
            M = 16  # 연결 수
            self.index = faiss.IndexHNSWFlat(dimension, M)
            self.index.hnsw.efConstruction = 200
            self.index.hnsw.efSearch = 50
            
        else:
            raise ValueError(f"지원하지 않는 인덱스 타입: {self.index_type}")
    
    def add_documents(self, documents: List[str], batch_size: int = 100):
        """
        문서들을 지식 베이스에 추가
        
        Args:
            documents: 추가할 문서 리스트
            batch_size: 배치 처리 크기
        """
        self._load_model()
        
        if not documents:
            logger.warning("추가할 문서가 없습니다.")
            return
        
        logger.info(f"{len(documents)}개의 문서를 추가합니다...")
        
        # 기존 데이터에 새 문서 추가
        self.data.extend(documents)
        
        # 배치별로 임베딩 생성
        all_vectors = []
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            logger.info(f"배치 {i//batch_size + 1} 처리 중... ({len(batch)}개 문서)")
            
            try:
                batch_vectors = self.model.encode(batch, convert_to_numpy=True)
                all_vectors.append(batch_vectors)
            except Exception as e:
                logger.error(f"임베딩 생성 실패: {e}")
                raise
        
        # 모든 벡터 결합
        db_vectors = np.vstack(all_vectors)
        
        # 인덱스가 없으면 생성
        if self.index is None:
            self._create_index(db_vectors.shape[1], len(self.data))
        
        # 학습이 필요한 인덱스 타입인 경우 학습 수행
        if hasattr(self.index, 'is_trained') and not self.index.is_trained:
            logger.info("인덱스 학습을 시작합니다...")
            self.index.train(db_vectors)
            logger.info("인덱스 학습 완료")
        
        # 벡터 추가
        self.index.add(db_vectors)
        self.is_trained = True
        
        logger.info(f"총 {self.index.ntotal}개의 벡터가 인덱스에 저장되었습니다.")
    
    def search(self, query: str, k: int = 5, return_distances: bool = True) -> List[Tuple]:
        """
        유사 문서 검색
        
        Args:
            query: 검색 쿼리
            k: 반환할 결과 수
            return_distances: 거리 정보 포함 여부
            
        Returns:
            검색 결과 리스트 [(문서, 거리), ...]
        """
        if not self.is_trained or self.index is None:
            logger.error("인덱스가 학습되지 않았습니다. add_documents()를 먼저 호출하세요.")
            return []
        
        self._load_model()
        
        print(f"🔍 쿼리 검색 중: '{query}'")
        
        try:
            # 쿼리 벡터화
            query_vector = self.model.encode([query], convert_to_numpy=True)
            
            # 검색 수행
            distances, indices = self.index.search(query_vector, k)
            
            # 결과 정리
            results = []
            for idx, dist in zip(indices[0], distances[0]):
                if idx < len(self.data):  # 유효한 인덱스인지 확인
                    if return_distances:
                        results.append((self.data[idx], float(dist)))
                    else:
                        results.append(self.data[idx])
            
            print(f"✅ {len(results)}개의 검색 결과를 찾았습니다.")
            return results
            
        except Exception as e:
            print(f"❌ 검색 중 오류 발생: {e}")
            return []
    
    def save(self, filepath: str):
        """
        인덱스와 데이터 저장
        
        Args:
            filepath: 저장할 파일 경로 (확장자 제외)
        """
        if not self.is_trained:
            logger.warning("학습되지 않은 인덱스입니다.")
            return
        
        try:
            # Faiss 인덱스 저장
            index_path = f"{filepath}.faiss"
            faiss.write_index(self.index, index_path)
            
            # 메타데이터 저장
            metadata = {
                'data': self.data,
                'model_name': self.model_name,
                'index_type': self.index_type,
                'is_trained': self.is_trained
            }
            
            metadata_path = f"{filepath}.pkl"
            with open(metadata_path, 'wb') as f:
                pickle.dump(metadata, f)
            
            logger.info(f"인덱스 저장 완료: {index_path}, {metadata_path}")
            
        except Exception as e:
            logger.error(f"저장 중 오류 발생: {e}")
            raise
    
    def load(self, filepath: str):
        """
        저장된 인덱스와 데이터 로드
        
        Args:
            filepath: 로드할 파일 경로 (확장자 제외)
        """
        try:
            # Faiss 인덱스 로드
            index_path = f"{filepath}.faiss"
            if not os.path.exists(index_path):
                raise FileNotFoundError(f"인덱스 파일을 찾을 수 없습니다: {index_path}")
            
            self.index = faiss.read_index(index_path)
            
            # 메타데이터 로드
            metadata_path = f"{filepath}.pkl"
            if not os.path.exists(metadata_path):
                raise FileNotFoundError(f"메타데이터 파일을 찾을 수 없습니다: {metadata_path}")
            
            with open(metadata_path, 'rb') as f:
                metadata = pickle.load(f)
            
            self.data = metadata['data']
            self.model_name = metadata['model_name']
            self.index_type = metadata['index_type']
            self.is_trained = metadata['is_trained']
            
            logger.info(f"인덱스 로드 완료: {self.index.ntotal}개 벡터")
            
        except Exception as e:
            logger.error(f"로드 중 오류 발생: {e}")
            raise
    
    def get_stats(self) -> dict:
        """인덱스 통계 정보 반환"""
        stats = {
            'total_vectors': self.index.ntotal if self.index else 0,
            'total_documents': len(self.data),
            'model_name': self.model_name,
            'index_type': self.index_type,
            'is_trained': self.is_trained
        }
        
        if self.index and hasattr(self.index, 'd'):
            stats['vector_dimension'] = self.index.d
            
        return stats


def main():
    """테스트 및 데모 함수"""
    # 샘플 데이터
    sample_documents = [
        "오늘 날씨가 정말 좋네요.",
        "서울의 맛집을 추천해주세요.",
        "파이썬으로 웹 스크래핑하는 방법이 궁금합니다.",
        "내일 비가 올 확률은 얼마나 되나요?",
        "인공지능 기술의 미래 전망에 대해 알려주세요.",
        "가장 인기 있는 프로그래밍 언어는 무엇인가요?",
        "최신 스마트폰 모델 비교 정보를 찾고 있습니다.",
        "근처에 있는 괜찮은 카페를 알려주세요.",
        "머신러닝 알고리즘 성능 비교 분석",
        "딥러닝 모델 최적화 기법들",
        "자연어 처리 기술의 현재와 미래",
        "컴퓨터 비전 기술 발전 동향"
    ]
    
    # 1. 지식 베이스 생성 및 문서 추가
    print("=== Faiss 지식 베이스 테스트 ===")
    kb = FaissKnowledgeBase(index_type='IVFFlat')
    
    # 문서 추가
    kb.add_documents(sample_documents)
    
    # 통계 출력
    stats = kb.get_stats()
    print(f"\n📊 인덱스 통계:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # 2. 검색 테스트
    test_queries = [
        "가장 좋은 프로그래밍 언어는?",
        "오늘 날씨 어때요?",
        "딥러닝에 대해 알려주세요"
    ]
    
    print(f"\n🔍 검색 테스트:")
    for query in test_queries:
        print(f"\n쿼리: '{query}'")
        results = kb.search(query, k=3)
        
        for i, (doc, distance) in enumerate(results, 1):
            print(f"  {i}. [{distance:.4f}] {doc}")
    
    # 3. 저장/로드 테스트
    print(f"\n💾 저장/로드 테스트:")
    save_path = "knowledge_base"
    
    # 저장
    kb.save(save_path)
    
    # 새로운 인스턴스로 로드
    kb_loaded = FaissKnowledgeBase()
    kb_loaded.load(save_path)
    
    # 로드된 인덱스로 검색 테스트
    print(f"로드된 인덱스 검색 테스트:")
    results = kb_loaded.search("프로그래밍 언어", k=2)
    for i, (doc, distance) in enumerate(results, 1):
        print(f"  {i}. [{distance:.4f}] {doc}")
    
    print(f"\n✅ 모든 테스트 완료!")


if __name__ == "__main__":
    main()