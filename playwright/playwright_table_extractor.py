import asyncio
import pandas as pd
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import json
import csv

async def extract_table_data():
    """웹페이지에서 표 형태의 데이터를 추출하고 다양한 형태로 저장"""
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        # 웹페이지 로드
        await page.goto("https://tago.kr/service/ioniq6_monthly.htm")
        
        # 페이지가 완전히 로드될 때까지 대기
        await page.wait_for_load_state('networkidle')
        
        # HTML 내용 가져오기
        html_content = await page.content()
        
        # BeautifulSoup으로 HTML 파싱
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 모든 테이블 찾기
        tables = soup.find_all('table')
        
        all_table_data = []
        
        for i, table in enumerate(tables):
            print(f"\n=== 테이블 {i+1} ===")
            
            # 테이블 캡션 추출
            caption = table.find('caption')
            table_title = caption.get_text(strip=True) if caption else f"테이블 {i+1}"
            print(f"제목: {table_title}")
            
            # 테이블 데이터 추출
            table_data = {
                'title': table_title,
                'headers': [],
                'rows': []
            }
            
            # 헤더 추출
            thead = table.find('thead')
            if thead:
                header_rows = thead.find_all('tr')
                for header_row in header_rows:
                    headers = []
                    for th in header_row.find_all(['th', 'td']):
                        headers.append(th.get_text(strip=True))
                    table_data['headers'].append(headers)
            
            # 데이터 행 추출
            tbody = table.find('tbody')
            if tbody:
                rows = tbody.find_all('tr')
                for row in rows:
                    row_data = []
                    for cell in row.find_all(['td', 'th']):
                        cell_text = cell.get_text(strip=True)
                        row_data.append(cell_text)
                    table_data['rows'].append(row_data)
            
            all_table_data.append(table_data)
            
            # 테이블 내용 출력
            print("헤더:", table_data['headers'])
            print("데이터 행 수:", len(table_data['rows']))
            for j, row in enumerate(table_data['rows'][:5]):  # 처음 5행만 출력
                print(f"  행 {j+1}: {row}")
            if len(table_data['rows']) > 5:
                print(f"  ... (총 {len(table_data['rows'])}행)")
        
        # 데이터를 다양한 형태로 저장
        
        # 1. JSON 형태로 저장
        with open('table_data.json', 'w', encoding='utf-8') as f:
            json.dump(all_table_data, f, ensure_ascii=False, indent=2)
        print(f"\n✓ JSON 파일로 저장: table_data.json")
        
        # 2. 각 테이블을 CSV로 저장
        for i, table_data in enumerate(all_table_data):
            if table_data['rows']:
                filename = f"table_{i+1}_{table_data['title'][:20]}.csv"
                # 파일명에서 특수문자 제거
                filename = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_', '.')).rstrip()
                
                with open(filename, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    
                    # 헤더 작성
                    if table_data['headers']:
                        for header_row in table_data['headers']:
                            writer.writerow(header_row)
                    
                    # 데이터 행 작성
                    for row in table_data['rows']:
                        writer.writerow(row)
                
                print(f"✓ CSV 파일로 저장: {filename}")
        
        # 3. 가격표 테이블을 pandas DataFrame으로 변환하여 분석
        price_table = None
        for table_data in all_table_data:
            if '가격표' in table_data['title']:
                price_table = table_data
                break
        
        if price_table:
            print(f"\n=== 가격표 분석 ===")
            # DataFrame 생성
            df = pd.DataFrame(price_table['rows'], 
                            columns=price_table['headers'][0] if price_table['headers'] else None)
            
            # DataFrame 저장
            df.to_excel('ioniq6_price_table.xlsx', index=False)
            print("✓ Excel 파일로 저장: ioniq6_price_table.xlsx")
            
            # 기본 통계 정보
            print("\n가격표 데이터 구조:")
            print(df.head())
            print(f"\n행 수: {len(df)}")
            print(f"열 수: {len(df.columns)}")
        
        # 4. 원본 HTML 테이블 구존
        with open('original_tables.html', 'w', encoding='utf-8') as f:
            f.write("<html><head><meta charset='utf-8'></head><body>")
            for i, table in enumerate(tables):
                f.write(f"<h2>테이블 {i+1}</h2>")
                f.write(str(table))
                f.write("<br><br>")
            f.write("</body></html>")
        print("✓ 원본 HTML 테이블 구조 저장: original_tables.html")
        
        await browser.close()
        
        return all_table_data

# 실행
if __name__ == "__main__":
    asyncio.run(extract_table_data()) 