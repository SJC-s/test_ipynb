import asyncio
import json
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from datetime import datetime

async def extract_tables_to_json():
    """웹페이지에서 표 형태의 데이터를 추출하여 JSON으로 저장"""
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        try:
            # 웹페이지 로드
            url = "https://tago.kr/service/ioniq6_monthly.htm"
            await page.goto(url)
            await page.wait_for_load_state('networkidle')
            
            # HTML 내용 가져오기
            html_content = await page.content()
            
            # BeautifulSoup으로 HTML 파싱
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 모든 테이블 찾기
            tables = soup.find_all('table')
            
            # 전체 데이터 구조
            extracted_data = {
                "extraction_info": {
                    "url": url,
                    "timestamp": datetime.now().isoformat(),
                    "total_tables": len(tables)
                },
                "tables": []
            }
            
            print(f"총 {len(tables)}개의 테이블을 발견했습니다.")
            
            for i, table in enumerate(tables):
                print(f"\n=== 테이블 {i+1} 처리 중 ===")
                
                # 테이블 캡션 추출
                caption = table.find('caption')
                table_title = caption.get_text(strip=True) if caption else f"테이블 {i+1}"
                print(f"제목: {table_title}")
                
                # 테이블 데이터 구조 초기화
                table_data = {
                    "table_id": i + 1,
                    "title": table_title,
                    "headers": [],
                    "rows": []
                }
                
                # 헤더 추출 (thead 또는 첫 번째 tr)
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
                    # tbody가 없으면 table 직하위의 tr들을 사용
                    rows = table.find_all('tr')
                    # 헤더가 있다면 첫 번째 행 제외
                    if not thead and rows:
                        # 첫 번째 행이 헤더인지 확인
                        first_row = rows[0]
                        if first_row.find('th'):
                            headers = []
                            for th in first_row.find_all(['th', 'td']):
                                headers.append(th.get_text(strip=True))
                            table_data["headers"].append(headers)
                            rows = rows[1:]  # 첫 번째 행 제외
                
                # 첫 번째 열이 헤더인지 확인 (행 헤더 감지)
                has_row_headers = False
                if rows:
                    # 모든 행의 첫 번째 셀이 th인지 확인
                    first_cells_are_th = all(
                        row.find(['td', 'th']) and row.find(['td', 'th']).name == 'th'
                        for row in rows if row.find(['td', 'th'])
                    )
                    
                    # 또는 대부분의 행(80% 이상)의 첫 번째 셀이 th인지 확인
                    if not first_cells_are_th and len(rows) > 0:
                        th_first_count = sum(
                            1 for row in rows 
                            if row.find(['td', 'th']) and row.find(['td', 'th']).name == 'th'
                        )
                        first_cells_are_th = (th_first_count / len(rows)) >= 0.8
                    
                    has_row_headers = first_cells_are_th
                
                # 테이블 구조 정보 업데이트
                table_data["has_row_headers"] = has_row_headers
                
                # 데이터 행 처리
                for row_idx, row in enumerate(rows):
                    row_data = []
                    
                    # 행 내의 모든 셀을 순서대로 처리
                    all_cells = row.find_all(['td', 'th'])
                    
                    for cell in all_cells:
                        # 셀 텍스트만 추출
                        cell_text = cell.get_text(strip=True)
                        row_data.append(cell_text)
                    
                    table_data["rows"].append(row_data)
                
                extracted_data["tables"].append(table_data)
                
                print(f"  - 헤더 행: {len(table_data['headers'])}")
                print(f"  - 데이터 행: {len(table_data['rows'])}")
                print(f"  - 컬럼 수: {len(table_data['rows'][0]) if table_data['rows'] else 0}")
                print(f"  - 테이블 유형: {'both_headers' if has_row_headers else 'normal'}")
                print(f"  - 열 헤더: {'있음' if table_data['headers'] else '없음'}")
                print(f"  - 행 헤더: {'있음' if has_row_headers else '없음'}")
            
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

# 실행
if __name__ == "__main__":
    result = asyncio.run(extract_tables_to_json())
    if result:
        print(f"\n🎉 데이터 추출 완료! 총 {result['extraction_info']['total_tables']}개 테이블 처리됨") 