from exa_py import Exa
from dotenv import load_dotenv
from exa_py.websets.types import CreateWebsetParameters, CreateEnrichmentParameters
from langchain_exa import ExaSearchResults
import os
import json
from datetime import datetime

load_dotenv()
# exa = Exa(os.getenv('EXA_API_KEY'))


# result = exa.search_and_contents(
#   "blog post about AI",
#   type = "auto",
#   num_results = 10,
#   text = True,
# #   start_published_date = "2025-07-01T15:00:00.000Z",
# #   end_published_date = "2025-07-04T14:59:59.999Z",
# #   start_crawl_date = "2025-07-01T15:00:02.000Z",
# #   end_crawl_date = "2025-07-03T15:00:01.000Z",
# #   exclude_domains = ["youtube.com"],
# #   exclude_text = ["pdf"],
# #   context = True,
# #   livecrawl = "fallback",
# #   livecrawl_timeout = 1000,
# #   summary = True,
# #   subpages = 1,
# #   extras = {
# #     "links": 1,
# #     "image_links": 1
# #   }
# )

# print(result)



# # Initialize the ExaSearchResults tool
# search_tool = ExaSearchResults(exa_api_key=os.environ["EXA_API_KEY"])

# # 검색 쿼리 수행
# search_results = search_tool._run(
#     # query="When was the last time the New York Knicks won the NBA Championship?",
#     query="AI 프로란?",
#     num_results=5,
#     text_contents_options=True,
#     highlights=True,
# )

# # 결과를 저장할 디렉토리 생성
# if not os.path.exists('search_results'):
#     os.makedirs('search_results')

# # 현재 시간을 파일명에 포함
# timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
# filename = f"exa_search_result_{timestamp}.json"

# # SearchResponse 객체를 dictionary로 변환
# def convert_search_results(results):
#     if isinstance(results, (list, tuple)):
#         return [convert_search_results(item) for item in results]
#     elif isinstance(results, dict):
#         return {k: convert_search_results(v) for k, v in results.items()}
#     elif hasattr(results, '__dict__'):
#         return convert_search_results(results.__dict__)
#     else:
#         return results

# serializable_results = convert_search_results(search_results)

# # 검색 결과를 JSON 파일로 저장
# with open(filename, 'w', encoding='utf-8') as f:
#     json.dump({
#         'query': "When was the last time the New York Knicks won the NBA Championship?",
#         'results': serializable_results,
#         'timestamp': timestamp
#     }, f, ensure_ascii=False, indent=4)

# print(f"검색 결과가 {filename}에 저장되었습니다.")

# Exa-Tavily 변환 테스트
def test_exa_to_tavily_conversion():
    # Exa 클라이언트 초기화
    exa = Exa(os.getenv('EXA_API_KEY'))
    
    query = "chatty에 대해 간단히"
    # Exa 검색 수행
    exa_results = exa.search_and_contents(
        query,
        type="auto",
        num_results=5,
        text=True,
        highlights=True,
        include_domains=[".kr", ".com", ".net", ".org", ".info", ".biz", ".name", ".pro", ".edu", ".gov", ".mil", ".online", ".tech", ".site", ".app", ".blog", ".shop", ".us", ".jp", ".uk", ".de", ".cn", ".fr", ".br", ".in", ".au", ".io", ".ai"]  # 한국 도메인으로 제한
    )
    
    print(f"type(exa_results): {type(exa_results)}")
    # SearchResponse 객체를 dictionary로 변환
    def convert_search_results(results):
        if isinstance(results, (list, tuple)):
            return [convert_search_results(item) for item in results]
        elif isinstance(results, dict):
            return {k: convert_search_results(v) for k, v in results.items()}
        elif hasattr(results, '__dict__'):
            return convert_search_results(results.__dict__)
        else:
            return results
    
    # 검색 결과를 직렬화 가능한 형태로 변환
    serializable_results = convert_search_results(exa_results)
    
    # 결과 구조 확인을 위한 디버그 출력
    print("\nExa 결과 구조:")
    print(json.dumps(serializable_results, ensure_ascii=False, indent=2)[:100] + "...")
    
    # Exa 결과를 Tavily 형식으로 변환
    def convert_to_tavily_format(results):
        tavily_formatted_results = []
        for result in results.get('results', []):
            tavily_formatted_result = {
                "title": result.get("title", ""),
                "url": result.get("url", ""),
                "content": result.get("highlights", []),  # 하이라이트된 부분
                "score": result.get("highlight_scores", 0),  # score 필드명 수정
                "favicon_url": result.get("favicon", ""),
            }
            tavily_formatted_results.append(tavily_formatted_result)
        
        return {"type": "web", "result": tavily_formatted_results}
    
    # 변환 실행
    tavily_results = convert_to_tavily_format(serializable_results)
    
    # 현재 시간을 파일명에 포함
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 원본 Exa 결과 저장
    exa_filename = f"search_result/exa_search_result_{timestamp}.json"
    with open(exa_filename, 'w', encoding='utf-8') as f:
        json.dump({
            'query': query,
            'results': serializable_results,
            'timestamp': timestamp
        }, f, ensure_ascii=False, indent=4)
    
    # Tavily 형식으로 변환된 결과 저장
    tavily_filename = f"search_result/exa_search_result_{timestamp}.json"
    with open(tavily_filename, 'w', encoding='utf-8') as f:
        json.dump(tavily_results, f, ensure_ascii=False, indent=4)
    
    print(f"Exa 검색 결과가 {exa_filename}에 저장되었습니다.")
    print(f"Tavily 형식 결과가 {tavily_filename}에 저장되었습니다.")
    
    # 변환된 결과 출력
    print("\n변환된 Tavily 형식 결과 예시 (첫 번째 항목):")
    if tavily_results["result"]:
        first_result = tavily_results["result"][0]
        print(json.dumps(first_result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    test_exa_to_tavily_conversion()