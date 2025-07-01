import json
from bs4 import BeautifulSoup
import aiohttp
import asyncio

async def create_search_snippets(soup: BeautifulSoup, search_query: str, max_snippets: int = 3, snippet_length: int = 150) -> list[dict]:
    """
    웹사이트에서 검색어와 관련된 텍스트 스니펫을 추출하는 함수
    
    Args:
        soup: BeautifulSoup 객체
        search_query: 검색어
        max_snippets: 반환할 최대 스니펫 수
        snippet_length: 각 스니펫의 최대 길이
        
    Returns:
        list[dict]: [
            {
                "text": "스니펫 텍스트",
                "source": "텍스트 출처 (예: title, description, heading 등)",
                "relevance_score": 점수
            },
            ...
        ]
    """
    snippets = []
    search_terms = search_query.lower().split()
    
    try:
        # 1단계: 메타 데이터에서 관련 텍스트 추출
        meta_selectors = {
            'title': 'title',
            'description': 'meta[name="description"]',
            'keywords': 'meta[name="keywords"]',
            'og:title': 'meta[property="og:title"]',
            'og:description': 'meta[property="og:description"]'
        }
        
        for source, selector in meta_selectors.items():
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text().strip() if source == 'title' else element.get('content', '').strip()
                if text:
                    score = _calculate_relevance_score(text, search_terms)
                    if score > 0:
                        snippet = _create_snippet(text, search_terms, snippet_length)
                        snippets.append({
                            "text": snippet,
                            "source": source,
                            "relevance_score": score
                        })
        
        # 2단계: 주요 텍스트 컨텐츠에서 추출
        content_selectors = {
            'heading': ['h1', 'h2', 'h3'],
            'paragraph': ['p'],
            'article': ['article'],
            'section': ['section'],
            'list': ['li']
        }
        
        for source, selectors in content_selectors.items():
            for selector in selectors:
                elements = soup.select(selector)
                for element in elements:
                    text = element.get_text().strip()
                    if text and len(text) >= 10:  # 너무 짧은 텍스트 제외
                        score = _calculate_relevance_score(text, search_terms)
                        if score > 0:
                            snippet = _create_snippet(text, search_terms, snippet_length)
                            snippets.append({
                                "text": snippet,
                                "source": f"{source}",
                                "relevance_score": score
                            })
        
        # 3단계: JSON-LD 데이터에서 추출
        json_ld_scripts = soup.find_all('script', type='application/ld+json')
        for script in json_ld_scripts:
            try:
                if script.string:
                    data = json.loads(script.string)
                    if isinstance(data, list):
                        data = data[0] if data else {}
                    
                    text_fields = [
                        data.get('description', ''),
                        data.get('articleBody', ''),
                        data.get('text', '')
                    ]
                    
                    for text in text_fields:
                        if isinstance(text, str) and text.strip():
                            score = _calculate_relevance_score(text, search_terms)
                            if score > 0:
                                snippet = _create_snippet(text, search_terms, snippet_length)
                                snippets.append({
                                    "text": snippet,
                                    "source": "structured_data",
                                    "relevance_score": score
                                })
            except (json.JSONDecodeError, AttributeError):
                continue
        
        # 결과 정렬 및 필터링
        snippets.sort(key=lambda x: x['relevance_score'], reverse=True)
        return snippets[:max_snippets]
    
    except Exception as e:
        print(f"스니펫 생성 중 오류 발생: {str(e)}")
        return []

def _calculate_relevance_score(text: str, search_terms: list[str]) -> float:
    """
    텍스트와 검색어의 관련성 점수를 계산
    
    Args:
        text: 대상 텍스트
        search_terms: 검색어 리스트
        
    Returns:
        float: 관련성 점수 (0.0 ~ 1.0)
    """
    text_lower = text.lower()
    score = 0.0
    
    # 1. 정확한 구문 매칭
    exact_phrase = ' '.join(search_terms)
    if exact_phrase in text_lower:
        score += 1.0
    
    # 2. 개별 검색어 매칭
    matched_terms = sum(1 for term in search_terms if term in text_lower)
    score += (matched_terms / len(search_terms)) * 0.5
    
    # 3. 검색어 근접성 보너스
    words = text_lower.split()
    term_positions = []
    for term in search_terms:
        positions = [i for i, word in enumerate(words) if term in word]
        if positions:
            term_positions.extend(positions)
    
    if term_positions:
        term_positions.sort()
        if len(term_positions) > 1:
            max_gap = term_positions[-1] - term_positions[0]
            proximity_score = 1.0 / (max_gap + 1)
            score += proximity_score * 0.3
    
    # 4. 텍스트 위치 가중치
    if len(words) > 0:
        first_match = min(term_positions) if term_positions else len(words)
        position_weight = 1.0 - (first_match / len(words))
        score += position_weight * 0.2
    
    return min(1.0, score)

def _create_snippet(text: str, search_terms: list[str], max_length: int) -> str:
    """
    검색어를 포함하는 문맥 있는 스니펫 생성
    
    Args:
        text: 원본 텍스트
        search_terms: 검색어 리스트
        max_length: 최대 스니펫 길이
        
    Returns:
        str: 생성된 스니펫
    """
    text_lower = text.lower()
    
    # 검색어와 가장 관련있는 부분 찾기
    best_start = 0
    best_score = -1
    
    words = text.split()
    for i in range(len(words)):
        window = ' '.join(words[i:i + max_length // 10])  # 단어 기준으로 윈도우 생성
        score = sum(term in window.lower() for term in search_terms)
        if score > best_score:
            best_score = score
            best_start = i
    
    # 스니펫 추출
    start_pos = max(0, best_start)
    end_pos = min(len(words), start_pos + max_length // 5)
    snippet = ' '.join(words[start_pos:end_pos])
    
    # 스니펫이 문장 중간에서 시작하거나 끝나는 경우 처리
    if start_pos > 0:
        snippet = f"...{snippet}"
    if end_pos < len(words):
        snippet = f"{snippet}..."
    
    return snippet

async def search_naver_content(search_query: str, max_snippets: int = 3) -> None:
    """
    네이버 웹사이트에서 검색어와 관련된 텍스트를 추출하고 검색하는 함수
    
    Args:
        search_query: 검색어
        max_snippets: 반환할 최대 스니펫 수
    """
    url = "https://www.naver.com"
    
    try:
        # 커스텀 헤더 설정 (네이버는 User-Agent 확인)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    print(f"네이버 접근 실패: 상태 코드 {response.status}")
                    return
                
                html_content = await response.text()
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # 검색 스니펫 생성
                snippets = await create_search_snippets(
                    soup=soup,
                    search_query=search_query,
                    max_snippets=max_snippets,
                    snippet_length=200  # 네이버는 좀 더 긴 스니펫이 유용할 수 있음
                )
                
                # 결과 출력
                if snippets:
                    print(f"\n[네이버 검색 결과: '{search_query}']\n")
                    for i, snippet in enumerate(snippets, 1):
                        print(f"[스니펫 {i}]")
                        print(f"텍스트: {snippet['text']}")
                        print(f"출처: {snippet['source']}")
                        print(f"관련성 점수: {snippet['relevance_score']:.2f}")
                        print("-" * 50)
                else:
                    print(f"\n검색어 '{search_query}'에 대한 결과를 찾을 수 없습니다.")

    except aiohttp.ClientError as e:
        print(f"네트워크 오류: {str(e)}")
    except Exception as e:
        print(f"검색 중 오류 발생: {str(e)}")

# 실행 예제
async def main():
    # 검색어 예시
    search_queries = [
        "뉴스",
        "쇼핑",
        "메일"
    ]
    
    # 각 검색어에 대해 검색 실행
    for query in search_queries:
        await search_naver_content(query)
        print("\n" + "=" * 70 + "\n")

if __name__ == "__main__":
    # Windows에서 실행할 때 필요한 설정
    if asyncio.get_event_loop().is_closed():
        asyncio.set_event_loop(asyncio.new_event_loop())
    
    # 비동기 실행
    asyncio.run(main())