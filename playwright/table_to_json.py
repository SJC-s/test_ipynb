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
                    "structure": {
                        "headers": [],
                        "data_rows": []
                    },
                    "metadata": {
                        "row_count": 0,
                        "column_count": 0,
                        "has_header": False,
                        "has_row_headers": False,
                        "table_type": "normal"
                    }
                }
                
                # 헤더 추출 (thead 또는 첫 번째 tr)
                thead = table.find('thead')
                if thead:
                    header_rows = thead.find_all('tr')
                    for header_row in header_rows:
                        headers = []
                        for th in header_row.find_all(['th', 'td']):
                            cell_data = {
                                "text": th.get_text(strip=True),
                                "colspan": int(th.get('colspan', 1)),
                                "rowspan": int(th.get('rowspan', 1))
                            }
                            headers.append(cell_data)
                        table_data["structure"]["headers"].append(headers)
                    table_data["metadata"]["has_header"] = True
                
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
                                cell_data = {
                                    "text": th.get_text(strip=True),
                                    "colspan": int(th.get('colspan', 1)),
                                    "rowspan": int(th.get('rowspan', 1))
                                }
                                headers.append(cell_data)
                            table_data["structure"]["headers"].append(headers)
                            table_data["metadata"]["has_header"] = True
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
                table_data["metadata"]["has_row_headers"] = has_row_headers
                table_data["metadata"]["table_type"] = "normal"
                
                if table_data["metadata"]["has_header"] and has_row_headers:
                    table_data["metadata"]["table_type"] = "both_headers"
                elif table_data["metadata"]["has_header"]:
                    table_data["metadata"]["table_type"] = "column_headers"
                elif has_row_headers:
                    table_data["metadata"]["table_type"] = "row_headers"
                
                # 데이터 행 처리
                for row_idx, row in enumerate(rows):
                    row_data = {
                        "row_id": row_idx + 1,
                        "cells": []
                    }
                    
                    # 행 내의 모든 셀을 순서대로 처리 (th, td 혼재 가능)
                    all_cells = row.find_all(['td', 'th'])
                    
                    for cell_idx, cell in enumerate(all_cells):
                        cell_data = {
                            "cell_id": cell_idx + 1,
                            "text": cell.get_text(strip=True),
                            "html": str(cell),
                            "tag_name": cell.name,  # 'th' 또는 'td'
                            "is_header": cell.name == 'th',
                            "colspan": int(cell.get('colspan', 1)),
                            "rowspan": int(cell.get('rowspan', 1)),
                            "classes": cell.get('class', []),
                            "style": cell.get('style', ''),
                            "attributes": dict(cell.attrs)  # 모든 속성 저장
                        }
                        row_data["cells"].append(cell_data)
                    
                    # 행 내 th와 td 통계 추가
                    th_count = sum(1 for cell in all_cells if cell.name == 'th')
                    td_count = sum(1 for cell in all_cells if cell.name == 'td')
                    
                    row_data["cell_statistics"] = {
                        "total_cells": len(all_cells),
                        "th_count": th_count,
                        "td_count": td_count,
                        "has_mixed_tags": th_count > 0 and td_count > 0
                    }
                    
                    table_data["structure"]["data_rows"].append(row_data)
                
                # 메타데이터 업데이트
                table_data["metadata"]["row_count"] = len(table_data["structure"]["data_rows"])
                if table_data["structure"]["data_rows"]:
                    table_data["metadata"]["column_count"] = len(table_data["structure"]["data_rows"][0]["cells"])
                
                extracted_data["tables"].append(table_data)
                
                print(f"  - 헤더 행: {len(table_data['structure']['headers'])}")
                print(f"  - 데이터 행: {table_data['metadata']['row_count']}")
                print(f"  - 컬럼 수: {table_data['metadata']['column_count']}")
                print(f"  - 테이블 유형: {table_data['metadata']['table_type']}")
                print(f"  - 열 헤더: {'있음' if table_data['metadata']['has_header'] else '없음'}")
                print(f"  - 행 헤더: {'있음' if table_data['metadata']['has_row_headers'] else '없음'}")
            
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