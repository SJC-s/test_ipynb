"""
웹 사이트 자동화 테스트
테스트 목적: 각 도메인의 검색 기능 테스트 (탭 방식)
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import logging
import os
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor
from functools import partial

# 환경 변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='domain_test_results.log',
    encoding='utf-8'  # UTF-8 인코딩 설정
)

class DomainTester:
    def __init__(self):
        # 환경 변수에서 설정 로드
        self.user_id = os.getenv('USER_ID', 'default_id')
        self.user_pw = os.getenv('USER_PW', 'default_pw')
        self.max_workers = int(os.getenv('MAX_WORKERS', 4))
        
        # 테스트할 도메인 리스트
        self.domains = [
            'dev.han.kr/chat/search.htm',
            'test.han.kr/chat/search.htm',
            'ipet.han.kr/chat/search.htm',
            'gwangjin.han.kr/chat/search.htm',
            'oka.han.kr/chat/search.htm',
            'gwi.asadal.com/workmanage/chat/search.htm',
            'nara1.kr/art/search.htm',
            'chatty.kr/search.htm',
            'asadal.com/search.htm',
            'tago.kr/search.htm',
            'admin88.asadal.com/chat/search.htm',
            'admin.asadal.com/chat/search.htm',
            'admin.nara1.kr/chat/search.htm',
            'admin.tago.kr/chat/search.htm',
            'admin.hash.kr/chat/search.htm'
        ]
        
        # 검색할 텍스트
        self.search_text = "나라원 시스템"
        
        # 드라이버 초기화
        self.driver = None

    def setup_driver(self):
        """웹드라이버 설정"""
        if not self.driver:
            options = webdriver.ChromeOptions()
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.page_load_strategy = 'eager'  # DOM이 준비되면 바로 진행
            self.driver = webdriver.Chrome(options=options)
            self.driver.implicitly_wait(2)  # 전역 대기 시간 2초로 설정
        return self.driver

    def create_new_tab(self):
        """새 탭 생성"""
        self.driver.execute_script("window.open('');")
        self.driver.switch_to.window(self.driver.window_handles[-1])

    def close_tab(self):
        """현재 탭 닫기"""
        if len(self.driver.window_handles) > 1:
            self.driver.close()
            self.driver.switch_to.window(self.driver.window_handles[-1])

    def login(self, driver):
        """로그인 시도"""
        try:
            # ID 입력
            id_input = WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[name="userID"]'))
            )
            id_input.clear()
            if "gwi" in driver.current_url or "admin" in driver.current_url:
                id_input.send_keys(os.getenv('shin'))
                pw_input = driver.find_element(By.CSS_SELECTOR, 'input[name="userPW"]')
                pw_input.clear()
                pw_input.send_keys(os.getenv('shinp'))
            else:
                id_input.send_keys(self.user_id)
                pw_input = driver.find_element(By.CSS_SELECTOR, 'input[name="userPW"]')
                pw_input.clear()
                pw_input.send_keys(self.user_pw)
            pw_input.send_keys(Keys.RETURN)

            # 로그인 후 최소 대기
            time.sleep(1)
            return True

        except Exception as e:
            logging.error(f"로그인 실패: {str(e)}")
            return False

    def find_search_input(self, driver):
        """다양한 선택자로 검색 입력창 찾기"""
        selectors = [
            'input[v-model="searchText"]',  # v-model without trim
            'input[v-model\\.trim="searchText"]',  # v-model with trim
            'input[placeholder="12345"]',  # placeholder
            'input[type="text"][ref="searchText"]',  # ref attribute
            'input.inp[type="text"]',  # class and type
            'input[type="text"]',  # just type
            '#searchText',  # id
            'input[name="searchText"]'  # name
        ]
        
        for selector in selectors:
            try:
                element = WebDriverWait(driver, 1).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                logging.info(f"검색창 발견 (선택자: {selector})")
                return element
            except:
                continue
        
        # 모든 input 요소 로깅
        try:
            all_inputs = driver.find_elements(By.TAG_NAME, 'input')
            logging.info(f"페이지의 모든 input 태그:")
            for inp in all_inputs:
                attrs = driver.execute_script(
                    'var items = {}; for (var i = 0; i < arguments[0].attributes.length; i++) { items[arguments[0].attributes[i].name] = arguments[0].attributes[i].value }; return items;',
                    inp
                )
                logging.info(f"Input 속성들: {attrs}")
        except Exception as e:
            logging.error(f"Input 태그 분석 중 오류: {str(e)}")
        
        raise NoSuchElementException("검색 입력창을 찾을 수 없습니다.")

    def open_all_domains(self):
        """모든 도메인을 탭으로 엽니다."""
        domain_to_handle = {}  # 도메인과 핸들을 매핑
        
        for domain in self.domains:
            url = f"https://{domain}"
            if not self.driver.current_url or self.driver.current_url == "about:blank":
                # 첫 번째 탭 사용
                self.driver.get(url)
            else:
                # 새 탭 생성
                self.create_new_tab()
                self.driver.get(url)
            
            # 현재 탭의 핸들 저장
            domain_to_handle[domain] = self.driver.current_window_handle
            logging.info(f"도메인 열기: {url}")
        
        return domain_to_handle

    def test_domain(self, domain, handle):
        """각 도메인에 대한 테스트를 수행합니다."""
        try:
            # 해당 도메인의 탭으로 전환
            self.driver.switch_to.window(handle)
            logging.info(f"테스트 시작: {domain}")
            
            # 로그인 시도
            if not self.login(self.driver):
                logging.warning(f"{domain}: 로그인 실패")
            
            # 페이지 새로고침
            self.driver.get(f"https://{domain}")
            
            # 검색 입력창 찾기
            try:
                search_input = self.find_search_input(self.driver)
                
                # 검색어 입력 및 엔터 키 전송
                search_input.clear()
                search_input.send_keys(self.search_text)
                search_input.send_keys(Keys.RETURN)
                
                # 검색 결과 로딩 최소 대기
                time.sleep(1)
                
                logging.info(f"{domain}: 검색 테스트 완료")
                return True
                
            except NoSuchElementException as e:
                logging.error(f"{domain}: {str(e)}")
                return False
            
        except Exception as e:
            logging.error(f"{domain} 테스트 중 오류 발생: {str(e)}")
            return False

    def run_tests(self):
        """탭을 사용하여 도메인 테스트를 실행합니다."""
        self.setup_driver()
        results = {
            'success': [],
            'failed': []
        }
        
        try:
            # 모든 도메인을 먼저 탭으로 엽니다
            print("모든 도메인을 탭으로 여는 중...")
            domain_to_handle = self.open_all_domains()
            
            # 잠시 대기하여 모든 페이지가 로드되도록 합니다
            time.sleep(2)
            
            # 각 탭을 순회하면서 테스트 실행
            print("\n각 도메인 테스트 시작...")
            for domain, handle in domain_to_handle.items():
                success = self.test_domain(domain, handle)
                if success:
                    results['success'].append(domain)
                else:
                    results['failed'].append(domain)
            
            # 결과 출력
            self.print_results(results)
            
            # 테스트 완료 메시지
            print("\n테스트가 완료되었습니다. 브라우저는 계속 열려있습니다.")
            print("브라우저를 종료하려면 Ctrl+C를 누르세요.")
            
            # 무한 대기
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n프로그램을 종료합니다.")
                if self.driver:
                    self.driver.quit()
                    
        except Exception as e:
            logging.error(f"테스트 실행 중 오류 발생: {str(e)}")
            if self.driver:
                self.driver.quit()
            raise

    def print_results(self, results):
        """테스트 결과를 출력합니다."""
        logging.info("\n=== 테스트 결과 ===")
        logging.info(f"성공한 도메인 ({len(results['success'])}):")
        for domain in results['success']:
            logging.info(f"✓ {domain}")
        
        logging.info(f"\n실패한 도메인 ({len(results['failed'])}):")
        for domain in results['failed']:
            logging.info(f"✗ {domain}")

if __name__ == "__main__":
    try:
        tester = DomainTester()
        tester.run_tests()
    except KeyboardInterrupt:
        print("\n프로그램을 종료합니다.")
        if hasattr(tester, 'driver') and tester.driver:
            tester.driver.quit()
    except Exception as e:
        print(f"\n오류 발생: {str(e)}")
        if hasattr(tester, 'driver') and tester.driver:
            tester.driver.quit()
