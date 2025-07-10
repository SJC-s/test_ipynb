import requests
import json
import time
import os

# API 키 설정 (실제 사용 시 환경변수에서 가져오기)
pplx_api_key = os.getenv("PPLX_API_KEY")

def websearch_with_stream(query: str, stream: bool = True):
    """
    Perplexity API를 사용한 웹검색 - 스트림 모드 지원
    
    Args:
        query: 검색할 쿼리
        stream: 스트림 모드 사용 여부
    """
    url = "https://api.perplexity.ai/chat/completions"
    
    payload = {
        "model": "sonar",  # sonar 대신 sonar-pro 사용
        "messages": [
            {
                "content": """
You are WebSearchBot, an AI assistant specialized in performing natural-language web searches and returning structured results.  

When a user asks a question in natural language:
1. Treat the entire user input as a search query.
2. Perform a real-time web search (e.g., via an API or search engine).
3. For each result, return a JSON object with these fields:
   - title: 문서 제목 (UTF-8 텍스트, HTML 태그 제거)
   - url: 문서 URL
   - snippet: 검색어와 연관된 요약문(최소 200자), 문맥 뒤 "…"로 트렁케이트
   - score: 검색 결과의 유사도 점수(소수점 3자리)
   - favicon: 문서의 파비콘 URL
4. Return the overall answer as a JSON 배열만, 다른 설명 없이 출력하세요.
5. 응답은 반드시 UTF-8 인코딩으로 처리하고, 모든 비ASCII 문자를 그대로 유지해야 합니다.
6. 결과가 없거나 오류가 발생하면 빈 배열 `[]`을 반환하세요.

Example response:
[
  {
    "title": "직장인 업무 필수 툴 참고자료 검색은 퍼플렉시티 AI로 해결하는 법",
    "url": "https://example.com/article",
    "snippet": "…직장인들이 주로 사용하는 업무 도구와 그 꿀팁을 퍼플렉시티 AI 검색을 통해 한눈에 정리하는 방법을 소개합니다.…",
    "score": 0.952,
    "favicon": "https://example.com/favicon.ico"
  }
]
                """,
                "role": "system"
            },
            {
                "role": "user",
                "content": query
            }
        ],
        "search_domain_filter": ["-youtube.com", "-youtube.be"],
        "search_mode": "web",
        "reasoning_effort": "medium",
        "temperature": 0.5,
        "top_p": 0.2,
        "stream": stream,  # 스트림 설정
        "web_search_options": {"search_context_size": "medium"},
    }
    
    headers = {
        "Authorization": f"Bearer {pplx_api_key}",
        "Content-Type": "application/json"
    }
    
    print(f"🔍 검색 쿼리: {query}")
    print(f"📡 스트림 모드: {'ON' if stream else 'OFF'}")
    print("-" * 60)
    
    if stream:
        return _handle_stream_response(url, payload, headers)
    else:
        return _handle_non_stream_response(url, payload, headers)


def _handle_stream_response(url, payload, headers):
    """스트림 응답 처리"""
    try:
        response = requests.post(url, json=payload, headers=headers, stream=True)
        
        if response.status_code != 200:
            print(f"❌ API 오류: {response.status_code}")
            print(f"오류 내용: {response.text}")
            return None
        
        print("📡 스트림 응답 시작...\n")
        
        full_content = ""
        chunk_count = 0
        start_time = time.time()
        first_chunk_time = None
        
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                
                if line_str.startswith('data: '):
                    data_part = line_str[6:]
                    
                    if data_part.strip() == '[DONE]':
                        print("\n\n✅ 스트림 완료!")
                        break
                    
                    try:
                        chunk_data = json.loads(data_part)
                        chunk_count += 1
                        
                        if chunk_count == 1:
                            first_chunk_time = time.time() - start_time
                            print("🚀 첫 번째 청크 도착!\n")
                        
                        if 'choices' in chunk_data and len(chunk_data['choices']) > 0:
                            choice = chunk_data['choices'][0]
                            
                            if 'delta' in choice and 'content' in choice['delta']:
                                content = choice['delta']['content']
                                if content:
                                    print(content, end='', flush=True)
                                    full_content += content
                            
                            if choice.get('finish_reason'):
                                print(f"\n\n✅ 완료 사유: {choice['finish_reason']}")
                                break
                        
                    except json.JSONDecodeError as e:
                        print(f"\n❌ JSON 파싱 오류: {e}")
                        continue
        
        total_time = time.time() - start_time
        
        print(f"\n\n📊 스트림 통계:")
        print(f"총 청크 수: {chunk_count}")
        print(f"첫 청크까지: {first_chunk_time:.2f}초" if first_chunk_time else "첫 청크 시간 측정 실패")
        print(f"전체 소요 시간: {total_time:.2f}초")
        print(f"응답 길이: {len(full_content)} 문자")
        
        # JSON 파싱 시도
        try:
            parsed_result = json.loads(full_content)
            return parsed_result
        except json.JSONDecodeError:
            print("⚠️ 응답이 유효한 JSON 형식이 아닙니다.")
            return full_content
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 요청 오류: {e}")
        return None
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")
        return None


def _handle_non_stream_response(url, payload, headers):
    """비스트림 응답 처리"""
    try:
        start_time = time.time()
        response = requests.post(url, json=payload, headers=headers)
        total_time = time.time() - start_time
        
        response.encoding = 'utf-8'
        
        if response.status_code == 200:
            data = response.json()
            content = data['choices'][0]['message']['content']
            
            print(f"📄 응답 내용:\n{content}")
            
            print(f"\n📊 비스트림 통계:")
            print(f"소요 시간: {total_time:.2f}초")
            print(f"응답 길이: {len(content)} 문자")
            
            # JSON 파싱 시도
            try:
                parsed_result = json.loads(content)
                return parsed_result
            except json.JSONDecodeError:
                print("⚠️ 응답이 유효한 JSON 형식이 아닙니다.")
                return content
        else:
            print(f"❌ API 오류: {response.status_code}")
            print(f"오류 내용: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return None


def compare_stream_vs_non_stream(query: str):
    """스트림과 비스트림 비교 테스트"""
    # print("🆚 스트림 vs 비스트림 웹검색 비교\n")
    print("=" * 80)
    
    # # 비스트림 테스트
    # print("\n1️⃣ 비스트림 웹검색 테스트")
    # print("-" * 40)
    # non_stream_result = websearch_with_stream(query, stream=False)
    
    print("\n" + "=" * 80)
    
    # 스트림 테스트
    print("\n2️⃣ 스트림 웹검색 테스트")
    print("-" * 40)
    
    stream_result = websearch_with_stream(query, stream=True)
    print(f"\n📋 스트림 첫 번째 결과:")
    print(f"제목: {stream_result[0].get('title', 'N/A')}")
    print(f"URL: {stream_result[0].get('url', 'N/A')}")
    
    # 결과 비교
    print("\n" + "=" * 80)
    # print("\n🔍 결과 분석:")
    
    # if non_stream_result and stream_result:
    #     if isinstance(non_stream_result, list) and isinstance(stream_result, list):
    #         print(f"비스트림 결과 수: {len(non_stream_result)}개")
    #         print(f"스트림 결과 수: {len(stream_result)}개")
            
    #         if len(non_stream_result) > 0:
    #             print(f"\n📋 비스트림 첫 번째 결과:")
    #             print(f"제목: {non_stream_result[0].get('title', 'N/A')}")
    #             print(f"URL: {non_stream_result[0].get('url', 'N/A')}")
            
    #         if len(stream_result) > 0:
    #             print(f"\n📋 스트림 첫 번째 결과:")
    #             print(f"제목: {stream_result[0].get('title', 'N/A')}")
    #             print(f"URL: {stream_result[0].get('url', 'N/A')}")
    #     else:
    #         print("⚠️ 결과가 예상된 JSON 배열 형식이 아닙니다.")
    # else:
    #     print("❌ 하나 이상의 테스트에서 결과를 얻지 못했습니다.")


def debug_stream_response(query: str):
    """스트림 응답 디버깅"""
    print("🔧 스트림 응답 디버깅 모드\n")
    
    url = "https://api.perplexity.ai/chat/completions"
    
    payload = {
        "model": "sonar-pro",
        "messages": [
            {
                "content": "간단한 웹검색을 수행하고 결과를 JSON 형식으로 반환해주세요.",
                "role": "system"
            },
            {
                "role": "user",
                "content": query
            }
        ],
        "stream": True,
        "search_mode": "web"
    }
    
    headers = {
        "Authorization": f"Bearer {pplx_api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, stream=True)
        
        print(f"상태 코드: {response.status_code}")
        print(f"응답 헤더: {dict(response.headers)}")
        print("-" * 50)
        
        chunk_count = 0
        for line in response.iter_lines():
            if line:
                chunk_count += 1
                line_str = line.decode('utf-8')
                print(f"[청크 {chunk_count}] {line_str}")
                
                if chunk_count > 10:  # 처음 10개 청크만 출력
                    print("... (더 많은 청크가 있습니다)")
                    break
                    
    except Exception as e:
        print(f"디버깅 중 오류: {e}")


if __name__ == "__main__":
    # 테스트 쿼리
    test_queries = [
        "perplexity web검색 도구로 쓰는 방법",
        "Python 머신러닝 라이브러리 추천",
        "최신 AI 뉴스"
    ]
    
    print("🚀 Perplexity API 웹검색 스트림 테스트 시작\n")
    
    # 1. 기본 스트림 테스트
    print("1️⃣ 기본 스트림 웹검색 테스트")
    result = websearch_with_stream(test_queries[0], stream=True)
    
    print("\n" + "=" * 80)
    
    # 2. 비교 테스트
    print("\n2️⃣ 스트림 vs 비스트림 비교")
    compare_stream_vs_non_stream(test_queries[1])
    
    print("\n" + "=" * 80)
    
    # 3. 디버깅 테스트
    print("\n3️⃣ 스트림 응답 디버깅")
    debug_stream_response(test_queries[2])
    
    print("\n🎉 모든 테스트 완료!") 