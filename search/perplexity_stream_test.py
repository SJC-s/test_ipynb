import requests
import json
import time
import os

def perplexity_stream_test(query: str, api_key: str) -> None:
    """
    Perplexity API 스트림 기능 테스트
    
    Args:
        query: 검색할 쿼리
        api_key: Perplexity API 키
    """
    url = "https://api.perplexity.ai/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "sonar-pro",
        "messages": [{
            "role": "user", 
            "content": query
        }],
        "stream": True,  # 스트림 활성화
        "max_tokens": 1000,
        "temperature": 0.2
    }

    print(f"🔍 검색 쿼리: {query}")
    print("📡 스트림 응답 시작...\n")
    print("-" * 50)

    try:
        # 스트림 요청
        response = requests.post(url, headers=headers, json=data, stream=True)
        
        if response.status_code != 200:
            print(f"❌ API 오류: {response.status_code}")
            print(f"오류 내용: {response.text}")
            return

        # 스트림 데이터 처리
        full_content = ""
        chunk_count = 0
        
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                
                # SSE(Server-Sent Events) 형식 처리
                if line_str.startswith('data: '):
                    data_part = line_str[6:]  # 'data: ' 제거
                    
                    # 스트림 종료 신호
                    if data_part.strip() == '[DONE]':
                        print("\n\n✅ 스트림 완료!")
                        break
                    
                    try:
                        # JSON 파싱
                        chunk_data = json.loads(data_part)
                        chunk_count += 1
                        
                        # 응답 내용 추출
                        if 'choices' in chunk_data and len(chunk_data['choices']) > 0:
                            choice = chunk_data['choices'][0]
                            
                            if 'delta' in choice and 'content' in choice['delta']:
                                content = choice['delta']['content']
                                if content:
                                    print(content, end='', flush=True)
                                    full_content += content
                            
                            # 완료 상태 확인
                            if choice.get('finish_reason'):
                                print(f"\n\n✅ 완료 사유: {choice['finish_reason']}")
                                break
                        
                        # 디버깅 정보 (선택사항)
                        # print(f"\n[DEBUG] Chunk {chunk_count}: {json.dumps(chunk_data, indent=2)}")
                        
                    except json.JSONDecodeError as e:
                        print(f"\n❌ JSON 파싱 오류: {e}")
                        print(f"문제 데이터: {data_part}")
                        continue
                        
    except requests.exceptions.RequestException as e:
        print(f"❌ 요청 오류: {e}")
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")
    
    print(f"\n\n📊 통계:")
    print(f"총 청크 수: {chunk_count}")
    print(f"전체 응답 길이: {len(full_content)} 문자")


def perplexity_openai_stream_test(query: str, api_key: str) -> None:
    """
    OpenAI 클라이언트를 사용한 스트림 테스트
    """
    try:
        from openai import OpenAI
        
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.perplexity.ai"
        )
        
        print(f"🔍 검색 쿼리: {query}")
        print("📡 OpenAI 클라이언트 스트림 시작...\n")
        print("-" * 50)
        
        stream = client.chat.completions.create(
            model="sonar-pro",
            messages=[
                {"role": "user", "content": query}
            ],
            stream=True,
            max_tokens=1000,
            temperature=0.2
        )
        
        full_content = ""
        chunk_count = 0
        
        for chunk in stream:
            chunk_count += 1
            
            if chunk.choices[0].delta.content is not None:
                content = chunk.choices[0].delta.content
                print(content, end='', flush=True)
                full_content += content
                
            if chunk.choices[0].finish_reason:
                print(f"\n\n✅ 완료 사유: {chunk.choices[0].finish_reason}")
                break
        
        print(f"\n\n📊 통계:")
        print(f"총 청크 수: {chunk_count}")
        print(f"전체 응답 길이: {len(full_content)} 문자")
        
    except ImportError:
        print("❌ OpenAI 라이브러리가 설치되지 않았습니다. 'pip install openai'로 설치하세요.")
    except Exception as e:
        print(f"❌ OpenAI 클라이언트 오류: {e}")


def compare_stream_vs_non_stream(query: str, api_key: str) -> None:
    """
    스트림과 비스트림 응답 시간 비교
    """
    print("🆚 스트림 vs 비스트림 비교 테스트\n")
    
    # 비스트림 테스트
    print("1️⃣ 비스트림 테스트:")
    start_time = time.time()
    
    url = "https://api.perplexity.ai/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "sonar-pro",
        "messages": [{"role": "user", "content": query}],
        "stream": False
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        non_stream_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            print(f"응답 길이: {len(content)} 문자")
            print(f"소요 시간: {non_stream_time:.2f}초")
        else:
            print(f"오류: {response.status_code}")
            
    except Exception as e:
        print(f"오류: {e}")
    
    print("\n" + "-" * 30 + "\n")
    
    # 스트림 테스트
    print("2️⃣ 스트림 테스트:")
    start_time = time.time()
    first_chunk_time = None
    
    data["stream"] = True
    
    try:
        response = requests.post(url, headers=headers, json=data, stream=True)
        
        if response.status_code == 200:
            full_content = ""
            
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    
                    if line_str.startswith('data: '):
                        data_part = line_str[6:]
                        
                        if data_part.strip() == '[DONE]':
                            break
                        
                        try:
                            chunk_data = json.loads(data_part)
                            
                            if 'choices' in chunk_data and len(chunk_data['choices']) > 0:
                                choice = chunk_data['choices'][0]
                                
                                if 'delta' in choice and 'content' in choice['delta']:
                                    content = choice['delta']['content']
                                    if content and first_chunk_time is None:
                                        first_chunk_time = time.time() - start_time
                                    
                                    if content:
                                        full_content += content
                                
                                if choice.get('finish_reason'):
                                    break
                                    
                        except json.JSONDecodeError:
                            continue
            
            total_stream_time = time.time() - start_time
            
            print(f"응답 길이: {len(full_content)} 문자")
            print(f"첫 청크까지: {first_chunk_time:.2f}초" if first_chunk_time else "첫 청크 시간 측정 실패")
            print(f"전체 소요 시간: {total_stream_time:.2f}초")
            
            print(f"\n📊 비교 결과:")
            print(f"비스트림: {non_stream_time:.2f}초")
            print(f"스트림: {total_stream_time:.2f}초")
            if first_chunk_time:
                print(f"첫 응답까지: {first_chunk_time:.2f}초 (스트림의 장점!)")
                
        else:
            print(f"오류: {response.status_code}")
            
    except Exception as e:
        print(f"오류: {e}")


if __name__ == "__main__":
    # API 키 설정 (실제 사용 시 환경변수 사용 권장)
    API_KEY = os.getenv("PPLX_API_KEY")
    
    # 테스트 쿼리
    test_query = "Python에서 비동기 프로그래밍을 하는 방법을 자세히 설명해줘."
    
    print("🚀 Perplexity API 스트림 테스트 시작\n")
    print("=" * 60)
    
    # 1. 기본 스트림 테스트
    print("\n1️⃣ 기본 스트림 테스트")
    perplexity_stream_test(test_query, API_KEY)
    
    print("\n" + "=" * 60)
    
    # 2. OpenAI 클라이언트 스트림 테스트
    print("\n2️⃣ OpenAI 클라이언트 스트림 테스트")
    perplexity_openai_stream_test(test_query, API_KEY)
    
    print("\n" + "=" * 60)
    
    # 3. 스트림 vs 비스트림 비교
    print("\n3️⃣ 성능 비교 테스트")
    compare_stream_vs_non_stream(test_query, API_KEY)
    
    print("\n🎉 모든 테스트 완료!") 