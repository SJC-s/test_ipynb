import requests
import json
import os

# API 키 설정
pplx_api_key = os.getenv("PPLX_API_KEY")

def simple_search_with_count(query: str, result_count: int = 5):
    """
    간단한 웹검색 - 결과 개수 제어
    
    Args:
        query: 검색할 쿼리
        result_count: 반환할 검색 결과 수
    """
    url = "https://api.perplexity.ai/chat/completions"
    
    payload = {
        "model": "sonar",
        "messages": [
            {
                "content": f"""
You are a web search assistant. Search for the user's query and return EXACTLY {result_count} results.

Return only a JSON array with these fields for each result:
- title: Document title
- url: Document URL  
- snippet: Summary (minimum 100 characters)
- score: Relevance score (0.0-1.0)

Return exactly {result_count} results, no more, no less.
If fewer results exist, fill with empty objects to reach {result_count} total.

Example format:
[
  {{
    "title": "Result 1 Title",
    "url": "https://example1.com",
    "snippet": "Detailed summary of the first result...",
    "score": 0.95
  }},
  {{
    "title": "Result 2 Title", 
    "url": "https://example2.com",
    "snippet": "Detailed summary of the second result...",
    "score": 0.88
  }}
]
                """,
                "role": "system"
            },
            {
                "role": "user",
                "content": query
            }
        ],
        "search_mode": "web",
        "stream": True,
        "temperature": 0.3
    }
    
    headers = {
        "Authorization": f"Bearer {pplx_api_key}",
        "Content-Type": "application/json"
    }
    
    print(f"🔍 검색: {query}")
    print(f"📊 요청 결과 수: {result_count}개")
    print("-" * 50)
    
    try:
        response = requests.post(url, json=payload, headers=headers, stream=True)
        
        if response.status_code != 200:
            print(f"❌ 오류: {response.status_code}")
            return None
        
        full_content = ""
        print("📡 검색 중... ", end="", flush=True)
        
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                
                if line_str.startswith('data: '):
                    data_part = line_str[6:]
                    
                    if data_part.strip() == '[DONE]':
                        break
                    
                    try:
                        chunk_data = json.loads(data_part)
                        
                        if 'choices' in chunk_data and chunk_data['choices']:
                            choice = chunk_data['choices'][0]
                            
                            if 'delta' in choice and 'content' in choice['delta']:
                                content = choice['delta']['content']
                                if content:
                                    print(".", end="", flush=True)
                                    full_content += content
                            
                            if choice.get('finish_reason'):
                                break
                        
                    except json.JSONDecodeError:
                        continue
        
        print(" 완료!")
        
        # JSON 파싱
        try:
            results = json.loads(full_content)
            
            if isinstance(results, list):
                print(f"✅ {len(results)}개 결과 반환")
                
                # 결과 출력
                for i, result in enumerate(results, 1):
                    print(f"\n{i}. {result.get('title', 'N/A')}")
                    print(f"   URL: {result.get('url', 'N/A')}")
                    print(f"   점수: {result.get('score', 'N/A')}")
                    
                    snippet = result.get('snippet', '')
                    if snippet:
                        print(f"   요약: {snippet[:100]}...")
                
                return results
            else:
                print("⚠️ 배열 형식이 아닌 결과")
                return full_content
                
        except json.JSONDecodeError:
            print("⚠️ JSON 파싱 실패")
            print(f"원시 응답: {full_content[:200]}...")
            return None
            
    except Exception as e:
        print(f"❌ 오류: {e}")
        return None


def test_multiple_counts():
    """다양한 결과 개수로 테스트"""
    query = "Python 머신러닝 라이브러리"
    counts = [3, 5, 8]
    
    print("🧪 결과 개수별 테스트\n")
    print("=" * 60)
    
    for count in counts:
        print(f"\n🔢 {count}개 결과 테스트")
        print("-" * 30)
        
        results = simple_search_with_count(query, count)
        
        if results:
            print(f"📈 성공: {len(results)}개 결과 획득")
        else:
            print("❌ 실패")
        
        print("-" * 30)


if __name__ == "__main__":
    # 기본 테스트
    print("1️⃣ 기본 검색 테스트 (5개 결과)")
    simple_search_with_count("Perplexity API 사용법", 5)
    
    print("\n" + "=" * 60)
    
    # 다양한 개수 테스트
    print("\n2️⃣ 다양한 결과 개수 테스트")
    test_multiple_counts()
    
    print("\n🎉 테스트 완료!") 