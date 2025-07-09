"""
Google Custom Search API를 사용한 검색 예제 - requests 사용
"""
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

class GoogleSearchAPI:
    BASE_URL = "https://www.googleapis.com/customsearch/v1"
    
    def __init__(self, api_key: str, search_engine_id: str):
        """
        GoogleSearchAPI 클래스 초기화
        
        Args:
            api_key (str): Google API 키
            search_engine_id (str): Custom Search Engine ID
        """
        self.api_key = api_key
        self.search_engine_id = search_engine_id
        
    def search(self, query: str, num_results: int = 10) -> dict:
        """
        Google Custom Search API를 사용하여 검색 수행
        
        Args:
            query (str): 검색어
            num_results (int): 검색 결과 수 (기본값: 10)
            
        Returns:
            dict: 검색 결과
        """
        try:
            # 검색 매개변수 설정
            params = {
                "key": self.api_key,
                "cx": self.search_engine_id,
                "q": query,
                "num": num_results
            }
            
            # API 요청 실행
            response = requests.get(self.BASE_URL, params=params)
            response.raise_for_status()  # HTTP 오류 체크
            
            # JSON 응답 파싱
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"API 요청 중 오류 발생: {str(e)}")
            return None
        except json.JSONDecodeError as e:
            print(f"JSON 파싱 중 오류 발생: {str(e)}")
            return None

def main():
    # 환경 변수에서 API 키와 검색 엔진 ID 가져오기
    API_KEY = os.getenv("GOOGLE_API_KEY")
    SEARCH_ENGINE_ID = os.getenv("GOOGLE_SEARCH_ENGINE_ID")
    
    if not API_KEY or not SEARCH_ENGINE_ID:
        print("ERROR: GOOGLE_API_KEY 또는 GOOGLE_SEARCH_ENGINE_ID 환경 변수가 설정되지 않았습니다.")
        return
    
    # GoogleSearchAPI 인스턴스 생성
    search_api = GoogleSearchAPI(API_KEY, SEARCH_ENGINE_ID)
    
    # 검색어 설정
    search_query = "파이썬 프로그래밍"
    
    # 검색 실행
    results = search_api.search(search_query)
    
    # 결과 출력
    if results and 'items' in results:
        print(f"\n검색어 '{search_query}'에 대한 결과:")
        print("-" * 50)
        
        for item in results['items']:
            print(f"제목: {item['title']}")
            print(f"링크: {item['link']}")
            print("-" * 50)
            
        # 전체 결과를 JSON 파일로 저장
        with open("search_results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
            print("\n전체 검색 결과가 search_results.json 파일에 저장되었습니다.")
    else:
        print("검색 결과를 가져오는데 실패했습니다.")

if __name__ == "__main__":
    main()
