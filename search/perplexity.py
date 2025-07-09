import os
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_perplexity import ChatPerplexity
from typing import List, Optional

# .env 파일 로드
load_dotenv()

class ChatPerplexityTest:
    def __init__(self, temperature: float = 0, model: str = "sonar"):
        """
        ChatPerplexity 테스트를 위한 클래스 초기화
        
        Args:
            temperature (float): 생성 텍스트의 무작위성 정도 (0: 결정적, 1: 매우 창의적)
            model (str): 사용할 모델 이름 (예: "sonar")
        """
        self.api_key = os.getenv("PPLX_API_KEY")
        if not self.api_key:
            raise ValueError("API 키가 필요합니다. 환경변수 PPLX_API_KEY를 설정해주세요.")
        
        self.chat = ChatPerplexity(
            temperature=temperature,
            pplx_api_key=self.api_key,
            model=model
        )
    
    def simple_query(self, query: str) -> str:
        """
        간단한 질의를 수행하는 메서드
        
        Args:
            query (str): 검색할 질문
            
        Returns:
            str: API 응답 결과
        """
        prompt = ChatPromptTemplate.from_messages([
            ("human", "{input}")
        ])
        chain = prompt | self.chat
        response = chain.invoke({"input": query})
        return response.content
    
    def search_with_context(self, query: str, context: List[str]) -> str:
        """
        컨텍스트를 포함한 질의를 수행하는 메서드
        
        Args:
            query (str): 검색할 질문
            context (List[str]): 추가 컨텍스트 목록
            
        Returns:
            str: API 응답 결과
        """
        context_str = "\n".join(context)
        prompt = ChatPromptTemplate.from_messages([
            ("system", "다음 컨텍스트를 기반으로 질문에 답변해주세요:\n{context}"),
            ("human", "{input}")
        ])
        chain = prompt | self.chat
        response = chain.invoke({
            "context": context_str,
            "input": query
        })
        return response.content

def main():
    # 테스트 실행 예제
    try:
        # ChatPerplexity 인스턴스 생성
        chat_test = ChatPerplexityTest(temperature=0)
        
        # 간단한 질의 테스트
        query = "파이썬의 장점에 대해 설명해주세요."
        result = chat_test.simple_query(query)
        print(f"질문: {query}")
        print(f"응답: {result}\n")
        
        # 컨텍스트를 포함한 질의 테스트
        context = [
            "파이썬은 1991년에 만들어졌습니다.",
            "파이썬은 가독성이 높은 프로그래밍 언어입니다.",
            "파이썬은 풍부한 라이브러리 생태계를 가지고 있습니다."
        ]
        query_with_context = "이 언어의 특징을 설명해주세요."
        result_with_context = chat_test.search_with_context(query_with_context, context)
        print(f"컨텍스트가 있는 질문: {query_with_context}")
        print(f"응답: {result_with_context}")
        
    except Exception as e:
        print(f"오류 발생: {str(e)}")

if __name__ == "__main__":
    main()
