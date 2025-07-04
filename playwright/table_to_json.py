import asyncio
import json
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from datetime import datetime
import re
import os
from urllib.parse import urlparse
import time

async def extract_tables_from_urls(urls_file="urls.txt"):
    """txt 파일에서 URL 목록을 읽어서 각각의 테이블을 추출"""
    # URL 목록 읽기
    urls = read_urls_from_file(urls_file)
    
    if not urls:
        print(f"❌ {urls_file} 파일이 없거나 URL이 없습니다.")
        return
    
    print(f"📋 총 {len(urls)}개의 URL을 처리합니다.")
    
    # 결과 저장용 폴더 생성
    results_dir = "extracted_results"
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)
    
    # 전체 결과 요약
    all_results = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        
        for i, url in enumerate(urls, 1):
            print(f"\n{'='*60}")
            print(f"🌐 [{i}/{len(urls)}] {url} 처리 중...")
            print(f"{'='*60}")
            
            try:
                result = await extract_tables_from_single_url(browser, url, results_dir)
                all_results.append(result)
                
                # 각 URL 처리 후 잠시 대기 (서버 부하 방지)
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"❌ URL 처리 중 오류 발생: {e}")
                error_result = {
                    "url": url,
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
                all_results.append(error_result)
        
        await browser.close()
    
    # 전체 결과 요약 저장
    summary_file = os.path.join(results_dir, "extraction_summary.json")
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump({
            "total_urls": len(urls),
            "processed_at": datetime.now().isoformat(),
            "results": all_results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n🎉 모든 URL 처리 완료!")
    print(f"📁 결과 파일들이 '{results_dir}' 폴더에 저장되었습니다.")
    print(f"📊 전체 요약: {summary_file}")

def read_urls_from_file(filename):
    """txt 파일에서 URL 목록을 읽어오는 함수"""
    urls = []
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # 빈 줄이나 주석(#으로 시작) 제외
                if line and not line.startswith('#'):
                    # http로 시작하지 않으면 추가
                    if not line.startswith(('http://', 'https://')):
                        line = 'https://' + line
                    urls.append(line)
    except FileNotFoundError:
        print(f"❌ {filename} 파일을 찾을 수 없습니다.")
        # 기본 URL 파일 생성
        create_sample_urls_file(filename)
        return []
    
    return urls

def create_sample_urls_file(filename):
    """샘플 URL 파일 생성"""
    sample_urls = [
        "# URL 목록 파일 - 한 줄에 하나씩 입력하세요",
        "# 주석은 #으로 시작합니다",
        "",
        "https://kr.youme.com/sub_people/peopleopen.aspx?idx=204&tidx=0&dir=people",
        "https://tago.kr/service/ioniq6_monthly.htm",
        "# 추가 URL들을 여기에 입력하세요",
    ]
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write('\n'.join(sample_urls))
    
    print(f"📝 샘플 {filename} 파일을 생성했습니다. URL을 추가하고 다시 실행하세요.")

def get_safe_filename(url):
    """URL에서 안전한 파일명 생성"""
    # URL 파싱
    parsed = urlparse(url)
    domain = parsed.netloc
    path = parsed.path
    
    # 특수문자 제거 및 변환
    safe_name = f"{domain}{path}".replace('/', '_').replace('\\', '_')
    safe_name = re.sub(r'[<>:"|?*]', '_', safe_name)
    safe_name = re.sub(r'[^\w\-_.]', '_', safe_name)
    safe_name = re.sub(r'_+', '_', safe_name).strip('_')
    
    # 길이 제한 (최대 100자)
    if len(safe_name) > 100:
        safe_name = safe_name[:100]
    
    return safe_name

async def extract_tables_from_single_url(browser, url, results_dir):
    """단일 URL에서 테이블 추출"""
    page = await browser.new_page()
    
    try:
        # 웹페이지 로드
        await page.goto(url, timeout=30000)
        await page.wait_for_load_state('networkidle', timeout=30000)
        
        # HTML 내용 가져오기
        html_content = await page.content()
        
        # BeautifulSoup으로 HTML 파싱
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 다양한 테이블 형식 찾기
        table_candidates = find_table_candidates(soup)
        
        # 데이터 구조 생성
        extracted_data = {
            "extraction_info": {
                "url": url,
                "timestamp": datetime.now().isoformat(),
                "total_tables": len(table_candidates),
                "page_title": soup.title.string if soup.title else "제목 없음"
            },
            "tables": []
        }
        
        print(f"📊 총 {len(table_candidates)}개의 테이블 형식을 발견했습니다.")
        
        # 각 테이블 처리
        for i, table_info in enumerate(table_candidates):
            print(f"  └─ 테이블 {i+1}: {table_info['type']}")
            
            table_data = extract_table_data(table_info, i + 1)
            extracted_data["tables"].append(table_data)
        
        # 파일명 생성
        safe_filename = get_safe_filename(url)
        json_filename = f"{safe_filename}.json"
        json_filepath = os.path.join(results_dir, json_filename)
        
        # JSON 파일 저장
        with open(json_filepath, 'w', encoding='utf-8') as f:
            json.dump(extracted_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 저장 완료: {json_filename}")
        
        return {
            "url": url,
            "status": "success",
            "filename": json_filename,
            "tables_found": len(table_candidates),
            "page_title": extracted_data["extraction_info"]["page_title"]
        }
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        raise e
    finally:
        await page.close()

async def extract_tables_to_json():
    """웹페이지에서 다양한 형태의 테이블 데이터를 추출하여 JSON으로 저장"""
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        try:
            # 웹페이지 로드
            url = "https://kr.youme.com/sub_people/peopleopen.aspx?idx=204&tidx=0&dir=people"
            await page.goto(url)
            await page.wait_for_load_state('networkidle')
            
            # HTML 내용 가져오기
            html_content = await page.content()
            
            # BeautifulSoup으로 HTML 파싱
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 다양한 테이블 형식 찾기
            table_candidates = find_table_candidates(soup)
            
            # 전체 데이터 구조
            extracted_data = {
                "extraction_info": {
                    "url": url,
                    "timestamp": datetime.now().isoformat(),
                    "total_tables": len(table_candidates)
                },
                "tables": []
            }
            
            print(f"총 {len(table_candidates)}개의 테이블 형식을 발견했습니다.")
            
            for i, table_info in enumerate(table_candidates):
                print(f"\n=== 테이블 {i+1} 처리 중 ===")
                print(f"유형: {table_info['type']}")
                
                table_data = extract_table_data(table_info, i + 1)
                extracted_data["tables"].append(table_data)
                
                print(f"제목: {table_data['title']}")
                print(f"  - 헤더 행: {len(table_data['headers'])}")
                print(f"  - 데이터 행: {len(table_data['rows'])}")
                print(f"  - 컬럼 수: {len(table_data['rows'][0]) if table_data['rows'] else 0}")
                print(f"  - 테이블 유형: {table_data['table_type']}")
            
            # JSON 파일로 저장
            with open('extracted_tables.json', 'w', encoding='utf-8') as f:
                json.dump(extracted_data, f, ensure_ascii=False, indent=2)
            
            print(f"\n✅ 모든 테이블 데이터가 'extracted_tables.json'에 저장되었습니다!")
            
            return extracted_data
            
        except Exception as e:
            print(f"오류 발생: {e}")
            return None
        finally:
            await browser.close()

def find_table_candidates(soup):
    """다양한 형태의 테이블 후보를 찾는 함수"""
    candidates = []
    
    # 1. 표준 HTML 테이블
    html_tables = soup.find_all('table')
    for table in html_tables:
        candidates.append({
            'type': 'html_table',
            'element': table,
            'confidence': 1.0
        })
    
    # 2. div 기반 테이블 (CSS Grid/Flexbox)
    div_tables = soup.find_all('div', class_=re.compile(r'table|grid|data-table', re.I))
    for div in div_tables:
        if has_table_structure(div):
            candidates.append({
                'type': 'div_table',
                'element': div,
                'confidence': 0.8
            })
    
    # 3. ul/ol 기반 리스트 테이블
    list_tables = soup.find_all(['ul', 'ol'], class_=re.compile(r'table|list-table|data-list', re.I))
    for list_elem in list_tables:
        if has_list_table_structure(list_elem):
            candidates.append({
                'type': 'list_table',
                'element': list_elem,
                'confidence': 0.7
            })
    
    # 4. dl (Definition List) 기반 테이블
    dl_tables = soup.find_all('dl')
    for dl in dl_tables:
        if has_dl_table_structure(dl):
            candidates.append({
                'type': 'dl_table',
                'element': dl,
                'confidence': 0.6
            })
    
    # 5. 반복되는 div 패턴 (카드 형태)
    card_patterns = find_card_patterns(soup)
    for pattern in card_patterns:
        candidates.append({
            'type': 'card_table',
            'element': pattern,
            'confidence': 0.5
        })
    
    # 신뢰도 순으로 정렬
    candidates.sort(key=lambda x: x['confidence'], reverse=True)
    
    return candidates

def has_table_structure(div):
    """div 요소가 테이블 구조를 가지는지 확인"""
    # 행을 나타내는 하위 요소들이 있는지 확인
    rows = div.find_all('div', class_=re.compile(r'row|tr|table-row', re.I))
    if len(rows) >= 2:  # 최소 2개 행
        # 각 행에 셀들이 있는지 확인
        for row in rows[:3]:  # 처음 3개 행만 확인
            cells = row.find_all(['div', 'span'], class_=re.compile(r'cell|td|col', re.I))
            if len(cells) >= 2:  # 최소 2개 셀
                return True
    return False

def has_list_table_structure(list_elem):
    """리스트 요소가 테이블 구조를 가지는지 확인"""
    items = list_elem.find_all('li')
    if len(items) >= 2:
        # 각 항목이 일정한 패턴을 가지는지 확인
        first_item_structure = get_element_structure(items[0])
        similar_count = sum(1 for item in items[1:3] 
                          if is_similar_structure(first_item_structure, get_element_structure(item)))
        return similar_count >= 1
    return False

def has_dl_table_structure(dl):
    """dl 요소가 테이블 구조를 가지는지 확인"""
    dt_elements = dl.find_all('dt')
    dd_elements = dl.find_all('dd')
    # dt와 dd가 쌍을 이루는지 확인
    return len(dt_elements) >= 2 and len(dd_elements) >= 2

def find_card_patterns(soup):
    """반복되는 카드 패턴을 찾는 함수"""
    patterns = []
    
    # 같은 클래스를 가진 반복 요소들 찾기
    potential_cards = soup.find_all('div', class_=True)
    class_counts = {}
    
    for card in potential_cards:
        classes = ' '.join(card.get('class', []))
        if classes and len(classes.split()) <= 3:  # 너무 복잡한 클래스는 제외
            class_counts[classes] = class_counts.get(classes, 0) + 1
    
    # 3개 이상 반복되는 패턴 찾기
    for class_name, count in class_counts.items():
        if count >= 3:
            cards = soup.find_all('div', class_=class_name.split())
            if all(has_structured_content(card) for card in cards[:3]):
                patterns.append({
                    'class': class_name,
                    'elements': cards,
                    'count': count
                })
    
    return patterns

def has_structured_content(element):
    """요소가 구조화된 내용을 가지는지 확인"""
    # 텍스트 노드와 하위 요소들의 비율 확인
    text_content = element.get_text(strip=True)
    child_elements = element.find_all(True)
    
    return len(text_content) > 10 and len(child_elements) >= 2

def get_element_structure(element):
    """요소의 구조를 분석하여 패턴 반환"""
    return {
        'tag_count': len(element.find_all(True)),
        'text_length': len(element.get_text(strip=True)),
        'child_tags': [child.name for child in element.find_all(True, recursive=False)]
    }

def is_similar_structure(struct1, struct2):
    """두 구조가 유사한지 확인"""
    tag_diff = abs(struct1['tag_count'] - struct2['tag_count'])
    text_diff = abs(struct1['text_length'] - struct2['text_length'])
    
    return tag_diff <= 2 and text_diff <= 50

def extract_table_data(table_info, table_id):
    """테이블 정보에서 데이터를 추출하는 함수"""
    table_type = table_info['type']
    element = table_info['element']
    
    if table_type == 'html_table':
        return extract_html_table(element, table_id)
    elif table_type == 'div_table':
        return extract_div_table(element, table_id)
    elif table_type == 'list_table':
        return extract_list_table(element, table_id)
    elif table_type == 'dl_table':
        return extract_dl_table(element, table_id)
    elif table_type == 'card_table':
        return extract_card_table(table_info, table_id)
    else:
        return create_empty_table(table_id)

def extract_html_table(table, table_id):
    """표준 HTML 테이블에서 데이터 추출"""
    # 기존 로직 사용
    caption = table.find('caption')
    table_title = caption.get_text(strip=True) if caption else f"테이블 {table_id}"
    
    table_data = {
        "table_id": table_id,
        "title": table_title,
        "headers": [],
        "rows": [],
        "table_type": "html_table"
    }
    
    # 헤더 추출
    thead = table.find('thead')
    if thead:
        header_rows = thead.find_all('tr')
        for header_row in header_rows:
            headers = []
            for th in header_row.find_all(['th', 'td']):
                headers.append(th.get_text(strip=True))
            table_data["headers"].append(headers)
    
    # 데이터 행 추출
    tbody = table.find('tbody')
    if tbody:
        rows = tbody.find_all('tr')
    else:
        rows = table.find_all('tr')
        if not thead and rows:
            first_row = rows[0]
            if first_row.find('th'):
                headers = []
                for th in first_row.find_all(['th', 'td']):
                    headers.append(th.get_text(strip=True))
                table_data["headers"].append(headers)
                rows = rows[1:]
    
    # 행 헤더 감지
    has_row_headers = False
    if rows:
        th_first_count = sum(1 for row in rows 
                           if row.find(['td', 'th']) and row.find(['td', 'th']).name == 'th')
        has_row_headers = (th_first_count / len(rows)) >= 0.8
    
    table_data["has_row_headers"] = has_row_headers
    
    # 데이터 행 처리
    for row in rows:
        row_data = []
        all_cells = row.find_all(['td', 'th'])
        for cell in all_cells:
            cell_text = cell.get_text(strip=True)
            row_data.append(cell_text)
        table_data["rows"].append(row_data)
    
    return table_data

def extract_div_table(div, table_id):
    """div 기반 테이블에서 데이터 추출"""
    table_data = {
        "table_id": table_id,
        "title": f"Div 테이블 {table_id}",
        "headers": [],
        "rows": [],
        "table_type": "div_table"
    }
    
    # 헤더 찾기
    header_row = div.find('div', class_=re.compile(r'header|thead', re.I))
    if header_row:
        headers = []
        header_cells = header_row.find_all(['div', 'span'], class_=re.compile(r'cell|col', re.I))
        for cell in header_cells:
            headers.append(cell.get_text(strip=True))
        table_data["headers"].append(headers)
    
    # 데이터 행 찾기
    rows = div.find_all('div', class_=re.compile(r'row|tr', re.I))
    for row in rows:
        if header_row and row == header_row:
            continue
        
        row_data = []
        cells = row.find_all(['div', 'span'], class_=re.compile(r'cell|col', re.I))
        for cell in cells:
            row_data.append(cell.get_text(strip=True))
        
        if row_data:
            table_data["rows"].append(row_data)
    
    return table_data

def extract_list_table(list_elem, table_id):
    """리스트 기반 테이블에서 데이터 추출"""
    table_data = {
        "table_id": table_id,
        "title": f"리스트 테이블 {table_id}",
        "headers": [],
        "rows": [],
        "table_type": "list_table"
    }
    
    items = list_elem.find_all('li')
    for item in items:
        row_data = []
        
        # 각 항목에서 구조화된 데이터 추출
        labels = item.find_all(['strong', 'b', 'label'])
        values = item.find_all(['span', 'div'])
        
        if labels and values:
            for label, value in zip(labels, values):
                row_data.extend([label.get_text(strip=True), value.get_text(strip=True)])
        else:
            # 단순 텍스트 분할
            text = item.get_text(strip=True)
            if ':' in text:
                parts = text.split(':', 1)
                row_data.extend([part.strip() for part in parts])
            else:
                row_data.append(text)
        
        if row_data:
            table_data["rows"].append(row_data)
    
    return table_data

def extract_dl_table(dl, table_id):
    """dl 기반 테이블에서 데이터 추출"""
    table_data = {
        "table_id": table_id,
        "title": f"정의 목록 테이블 {table_id}",
        "headers": ["항목", "설명"],
        "rows": [],
        "table_type": "dl_table"
    }
    
    dt_elements = dl.find_all('dt')
    dd_elements = dl.find_all('dd')
    
    for dt, dd in zip(dt_elements, dd_elements):
        row_data = [
            dt.get_text(strip=True),
            dd.get_text(strip=True)
        ]
        table_data["rows"].append(row_data)
    
    return table_data

def extract_card_table(table_info, table_id):
    """카드 패턴에서 테이블 데이터 추출"""
    pattern = table_info['element']
    elements = pattern['elements']
    
    table_data = {
        "table_id": table_id,
        "title": f"카드 테이블 {table_id}",
        "headers": [],
        "rows": [],
        "table_type": "card_table"
    }
    
    # 첫 번째 카드에서 헤더 구조 추출
    if elements:
        first_card = elements[0]
        headers = []
        
        # 라벨들을 헤더로 사용
        labels = first_card.find_all(['strong', 'b', 'label', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        for label in labels:
            headers.append(label.get_text(strip=True))
        
        if headers:
            table_data["headers"].append(headers)
    
    # 각 카드에서 데이터 추출
    for card in elements:
        row_data = []
        
        # 구조화된 데이터 추출
        data_elements = card.find_all(['span', 'div', 'p'])
        for elem in data_elements:
            text = elem.get_text(strip=True)
            if text and len(text) > 0:
                row_data.append(text)
        
        if row_data:
            table_data["rows"].append(row_data)
    
    return table_data

def create_empty_table(table_id):
    """빈 테이블 생성"""
    return {
        "table_id": table_id,
        "title": f"테이블 {table_id}",
        "headers": [],
        "rows": [],
        "table_type": "unknown"
    }

# 실행
if __name__ == "__main__":
    import sys
    
    # 명령행 인자 확인
    if len(sys.argv) > 1:
        if sys.argv[1] == "multi":
            # 다중 URL 모드
            urls_file = sys.argv[2] if len(sys.argv) > 2 else "urls.txt"
            result = asyncio.run(extract_tables_from_urls(urls_file))
        elif sys.argv[1] == "single":
            # 단일 URL 모드
            result = asyncio.run(extract_tables_to_json())
        else:
            print("❌ 잘못된 인자입니다.")
            print("사용법:")
            print("  python table_to_json.py multi [urls.txt]  # 다중 URL 처리")
            print("  python table_to_json.py single           # 단일 URL 처리")
    else:
        # 기본값: urls.txt 파일이 있으면 다중 모드, 없으면 단일 모드
        if os.path.exists("urls.txt"):
            print("📋 urls.txt 파일이 발견되었습니다. 다중 URL 모드로 실행합니다.")
            print("💡 단일 URL 모드로 실행하려면: python table_to_json.py single")
            result = asyncio.run(extract_tables_from_urls())
        else:
            print("🌐 단일 URL 모드로 실행합니다.")
            print("💡 다중 URL 모드로 실행하려면: python table_to_json.py multi")
            result = asyncio.run(extract_tables_to_json())
    
    if result:
        print(f"\n🎉 처리 완료!") 