import time
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

# 대상 URL (JavaScript로 콘텐츠가 로드됨)
URL = "http://quotes.toscrape.com/js/"

def main():
    with sync_playwright() as p:
        # 1. Playwright로 브라우저 실행 및 페이지 이동
        print("Playwright를 시작합니다...")
        browser = p.chromium.launch(headless=True) # headless=True는 백그라운드에서 실행
        page = browser.new_page()
        page.goto(URL)

        # 2. JavaScript가 콘텐츠를 로드할 때까지 잠시 대기
        # 실제로는 특정 요소가 나타날 때까지 기다리는 것이 더 안정적입니다.
        # 예: page.wait_for_selector("div.quote")
        print(f"{URL}로 이동하여 콘텐츠 로드를 기다립니다...")
        time.sleep(2) # 간단한 예제를 위해 2초 대기

        # 3. Playwright로 최종 렌더링된 HTML 콘텐츠 가져오기 (스냅샷)
        print("페이지의 최종 HTML을 가져옵니다...")
        html_content = page.content()

        # Playwright 브라우저 종료
        browser.close()
        print("Playwright 브라우저를 종료했습니다.")

        # 4. BeautifulSoup으로 HTML 파싱
        print("BeautifulSoup으로 HTML 파싱을 시작합니다...")
        soup = BeautifulSoup(html_content, "lxml")

        # 5. BeautifulSoup을 사용하여 데이터 추출
        quotes = soup.find_all("div", class_="quote")

        if not quotes:
            print("명언을 찾을 수 없습니다.")
            return

        print(f"총 {len(quotes)}개의 명언을 찾았습니다. 결과를 출력합니다.")
        print("-" * 30)

        for quote in quotes:
            text = quote.find("span", class_="text").get_text(strip=True)
            author = quote.find("small", class_="author").get_text(strip=True)
            print(f"명언: {text}")
            print(f"작성자: {author}")
            print("-" * 30)

if __name__ == "__main__":
    main()