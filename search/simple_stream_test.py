import requests
import json
import os
def simple_stream_test(api_key: str, query: str = "Python의 특징을 간단히 설명해줘"):
    """
    간단한 Perplexity API 스트림 테스트
    """
    url = "https://api.perplexity.ai/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "sonar",
        "messages": [{"role": "user", "content": query}],
        "stream": True
    }
    
    print(f"질문: {query}\n")
    print("답변: ", end="", flush=True)
    
    try:
        response = requests.post(url, headers=headers, json=data, stream=True)
        
        if response.status_code != 200:
            print(f"오류: {response.status_code} - {response.text}")
            return
        
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                
                if line_str.startswith('data: '):
                    data_part = line_str[6:]
                    
                    if data_part.strip() == '[DONE]':
                        print("\n\n✅ 완료!")
                        break
                    
                    try:
                        chunk = json.loads(data_part)
                        if 'choices' in chunk and chunk['choices']:
                            delta = chunk['choices'][0].get('delta', {})
                            if 'content' in delta and delta['content']:
                                print(delta['content'], end='', flush=True)
                    except json.JSONDecodeError:
                        continue
                        
    except Exception as e:
        print(f"오류 발생: {e}")

if __name__ == "__main__":
    # 여기에 실제 API 키를 입력하세요
    API_KEY = os.getenv("PPLX_API_KEY")
    
    # 테스트 실행
    simple_stream_test(API_KEY) 