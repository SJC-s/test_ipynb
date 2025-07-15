import requests
import json
import os
from typing import Dict, List, Optional

def perplexity_web_search_fixed(query: str, api_key: str) -> Optional[Dict]:
    """
    Perplexity API 웹 검색 - 오류 수정 버전
    
    Args:
        query: 검색 쿼리
        api_key: Perplexity API 키
    
    Returns:
        Dict: 검색 결과 또는 None (오류 시)
    """
    url = "https://api.perplexity.ai/chat/completions"
    
    # 올바른 payload 구조
    payload = {
        "model": "sonar",
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful web search assistant. Provide accurate and comprehensive answers based on real-time web search."
            },
            {
                "role": "user",
                "content": query
            }
        ],
        "search_mode": "web",
        "stream": False,
        "temperature": 0.3,
        "max_tokens": 1000
    }
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json; charset=utf-8"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        # 응답 상태 코드 확인
        if response.status_code != 200:
            print(f"❌ API 오류: {response.status_code}")
            print(f"오류 내용: {response.text}")
            return None
        
        # UTF-8 인코딩 설정 (중요!)
        response.encoding = 'utf-8'
        
        # 응답이 비어있는지 확인
        if not response.text or response.text.strip() == "":
            print("❌ 빈 응답 수신")
            return None
        
        # JSON 파싱 시도
        try:
            data = response.json()
            
            # API 응답 구조 확인
            if "choices" not in data or not data["choices"]:
                print("❌ 유효하지 않은 응답 구조")
                return None
            
            # 응답 내용 추출
            content = data["choices"][0]["message"]["content"]
            
            return {
                "success": True,
                "content": content,
                "usage": data.get("usage", {}),
                "citations": data.get("citations", []),
                "search_results": data.get("search_results", [])
            }
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON 파싱 오류: {e}")
            print(f"응답 내용 (처음 200자): {response.text[:200]}")
            return None
        
    except requests.exceptions.Timeout:
        print("❌ 요청 시간 초과")
        return None
    except requests.exceptions.ConnectionError:
        print("❌ 연결 오류")
        return None
    except requests.exceptions.RequestException as e:
        print(f"❌ 요청 오류: {e}")
        return None
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")
        return None


def perplexity_structured_search(query: str, api_key: str, max_results: int = 5) -> Optional[List[Dict]]:
    """
    구조화된 검색 결과를 반환하는 Perplexity API 함수
    
    Args:
        query: 검색 쿼리
        api_key: Perplexity API 키
        max_results: 반환할 최대 결과 수
    
    Returns:
        List[Dict]: 구조화된 검색 결과 리스트
    """
    url = "https://api.perplexity.ai/chat/completions"
    
    payload = {
        "model": "sonar",
        "messages": [
            {
                "role": "system",
                "content": f"""
You are WebSearchBot, an AI assistant specialized in performing natural-language web searches and returning structured results.

When a user asks a question in natural language:
1. Treat the entire user input as a search query.
2. Perform a real-time web search.
3. Return EXACTLY {max_results} search results.
4. For each result, return a JSON object with these fields:
   - title: 문서 제목 (UTF-8 텍스트, HTML 태그 제거)
   - url: 문서 URL
   - snippet: 검색어와 연관된 요약문(최소 200자)
   - score: 검색 결과의 유사도 점수(0.0-1.0)
   - favicon: 문서의 파비콘 URL

5. Return the overall answer as a JSON 배열만, 다른 설명 없이 출력하세요.
6. 응답은 반드시 UTF-8 인코딩으로 처리하고, 모든 비ASCII 문자를 그대로 유지해야 합니다.
7. 결과가 {max_results}개 미만이면 빈 객체로 채워서 정확히 {max_results}개를 반환하세요.

Example response:
[
  {{
    "title": "검색 결과 제목",
    "url": "https://example.com/article",
    "snippet": "검색어와 관련된 상세한 요약 내용...",
    "score": 0.95,
    "favicon": "https://example.com/favicon.ico"
  }}
]
                """
            },
            {
                "role": "user",
                "content": query
            }
        ],
        "search_mode": "web",
        "stream": False,
        "temperature": 0.3,
        "web_search_options": {"search_context_size": "medium"}
    }
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json; charset=utf-8"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ API 오류: {response.status_code} - {response.text}")
            return None
        
        # UTF-8 인코딩 설정
        response.encoding = 'utf-8'
        
        # 빈 응답 확인
        if not response.text.strip():
            print("❌ 빈 응답 수신")
            return None
        
        # API 응답 파싱
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        
        # JSON 배열 파싱 시도
        try:
            results = json.loads(content)
            
            if isinstance(results, list):
                # 결과 정리 및 변환
                formatted_results = []
                for result in results:
                    if result.get("title") or result.get("url"):  # 빈 객체 필터링
                        formatted_results.append({
                            "title": result.get("title", ""),
                            "url": result.get("url", ""),
                            "content": result.get("snippet", ""),
                            "score": result.get("score", 0.0),
                            "favicon": result.get("favicon", "")
                        })
                
                return formatted_results
            else:
                print("⚠️ 응답이 배열 형식이 아닙니다")
                return None
                
        except json.JSONDecodeError as e:
            print(f"❌ 콘텐츠 JSON 파싱 오류: {e}")
            print(f"콘텐츠 내용: {content[:200]}...")
            return None
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return None


# 사용 예시
if __name__ == "__main__":
    # 환경변수에서 API 키 가져오기
    api_key = os.getenv("PPLX_API_KEY")
    
    if not api_key:
        print("❌ PPLX_API_KEY 환경변수가 설정되지 않았습니다")
        exit(1)
    
    # 기본 검색 테스트
    print("🔍 기본 웹 검색 테스트")
    result = perplexity_web_search_fixed("파이썬 프로그래밍 입문", api_key)
    
    if result:
        print("✅ 검색 성공!")
        print(f"응답 길이: {len(result['content'])} 문자")
        print(f"인용 수: {len(result.get('citations', []))}")
    else:
        print("❌ 검색 실패")
    
    print("\n" + "="*50 + "\n")
    
    # 구조화된 검색 테스트
    print("🔍 구조화된 검색 테스트")
    structured_results = perplexity_structured_search("인공지능 최신 동향", api_key, max_results=3)
    
    if structured_results:
        print(f"✅ {len(structured_results)}개 결과 반환")
        for i, result in enumerate(structured_results, 1):
            print(f"\n{i}. {result['title']}")
            print(f"   URL: {result['url']}")
            print(f"   점수: {result['score']}")
            print(f"   요약: {result['content'][:100]}...")
    else:
        print("❌ 구조화된 검색 실패") 