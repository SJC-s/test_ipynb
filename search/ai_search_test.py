import asyncio
import json
import os
from datetime import datetime
from dotenv import load_dotenv
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage


load_dotenv()

# SystemMessage 클래스 정의
class SystemMessage:
    def __init__(self, content):
        self.content = content

# get_agent_with_rag_ingredient_v3 함수 정의
async def get_agent_with_rag_ingredient_v3(
    query: str,
):
    today = datetime.now().strftime("%Y-%m-%d")
    weekday_korean = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]
    current_weekday = weekday_korean[datetime.now().weekday()]

    answer_prompt = SystemMessage(
        content = f"""
You are an interactive chatbot that answers your questions, Multilingual assistants who answer user questions with searches from multiple tools (RAG, web, image, etc.).  
Today is {today}, {current_weekday}.  

query: {query}  

Strictly follow these rules:  
1. Use available tools to generate a response to the user's question.  
2. Detect the user's input language and always reply in the same language.  
3. When expressing time ranges or any other ranges, include a space on both sides of the tilde (~) symbol, for example: 07:00 ~ 16:00    
"""
    )

    logging_prompt = SystemMessage(
        content = f"""
너는 출처 정보를 생성하는 에이전트야. 

🔒 필수 소스 로깅 - 중요한 규칙:  
retrievers 리스트를 참고하여, 각 검색 결과의 title(대표 제목)과 snippet(대표 인용문)을 직접 생성하라.
반드시 답변과 함께 출처 정보를 명확하게 포함하라.
title, snippet은 retrievers에서 직접 추출하지 말고, LLM이 요약/생성해서 넣어라.
필드에서 [출처:], [Chunk_number:], [Title:], [Chunk:]와 같은 메타 정보를 절대 사용하지 마십시오.  
스니펫을 추출할 때 인용문을 200자로 제한하고 인용된 구절 주변에 최대 100자의 문맥을 포함시킵니다. 원문이 200자를 초과하는 경우, 이에 따라 잘라내고 앞첨부/첨부합니다.  

제목 및 스니펫 필드에 대한 🔒 중요한 형식 규칙:  
   → title: 20자 이하이어야 하며, 제목, 출처, 청크_넘버 등과 같은 메타데이터 접두사를 제거해야 합니다.  
   → snippet: 텍스트만 정리하고, 한국어, 영어, 숫자, 공백, 마침표, 쉼표를 제외한 모든 메타데이터 마커와 특수 문자를 제거합니다.  
   → 제목과 스니펫 모두: 콜론, 괄호, 백슬래시 또는 괄호는 절대 포함하지 않습니다.  

🚨 JSON 안전 규정 - 모든 반환된 텍스트 필드에 필수:  
   → 콜론, 단일 따옴표, 이중 따옴표, 백슬래시, 곱슬 괄호, 사각 괄호 등 JSON을 깨는 문자는 절대 포함하지 마세요.  
   → 따옴표를 제거하거나 공백으로 대체하거나 완전히 생략합니다.  
   → 콜론을 공백이나 하이픈으로 대체합니다.  
   → 모든 백슬래시, 곱슬 브레이스, 사각 괄호를 제거합니다.  
   → 텍스트에 이러한 문자가 포함되어 있는 경우, 반환하기 전에 정리하세요.  

        """
    )

    return answer_prompt, logging_prompt

# 답변 생성(스트리밍) 함수 정의 (OpenAI API 필요)
import openai

async def ai_search_answer_streaming(llm, prompt, retrievers):
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    loop = asyncio.get_event_loop()
    try:
        def sync_stream():
            return client.chat.completions.create(
                model=llm,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": retrievers}
                ],
                stream=True,
                temperature=0.2
            )
        response = await loop.run_in_executor(None, sync_stream)
        for chunk in response:
            delta = chunk.choices[0].delta
            if delta and hasattr(delta, "content"):
                yield {"content": delta.content, "done": False, "description": "main_content"}
    except Exception as e:
        print(f"Error during streaming: {e}")

# retrivers.txt 파일에서 검색 결과 불러오기
def load_retrievers_from_txt(filepath="retrivers.json"):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read().strip()
        if not content:
            raise ValueError("retrivers.txt 파일이 비어 있습니다.")
        try:
            retrievers = json.loads(content)
        except json.JSONDecodeError as e:
            print("retrivers.txt 파일의 JSON 형식이 올바르지 않습니다.")
            raise e
    return retrievers

# 테스트 실행 함수
async def test_answer_and_source():
    retrievers = load_retrievers_from_txt()

    llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0, openai_api_key=os.getenv("OPENAI_API_KEY"))

    query = "나라원시스템의 연혁을 알려줘"

    answer_prompt, logging_prompt = await get_agent_with_rag_ingredient_v3(
        query=query,
    )

    # ReAct agent에서 tool 없이 동작
    graph_v3 = create_react_agent(
        llm,
        tools=[],
        prompt = logging_prompt.content
    )

    print("\n=== 출처 정보 생성 및 답변 생성 테스트 ===")
    # LLM이 retrievers를 보고 직접 title, snippet을 생성해서 답변에 포함하도록 유도
    result = await graph_v3.ainvoke(
        {
            "messages": [
                {"role": "user", "content": str(retrievers) + "의 title과 snippet를 리스트로 생성해줘"}
            ],
        }
    )
    print(result.get["AIMessage"])

    print("=== 답변 생성(스트리밍) 테스트 ===")
    answer = []
    # async for chunk in ai_search_answer_streaming(
    #     llm="gpt-4o-mini",
    #     prompt=answer_prompt.content,
    #     retrievers=json.dumps(retrievers, ensure_ascii=False)
    # ):
    #     answer.append(chunk.get('content', ''))
        
    print(answer)

if __name__ == "__main__":
    asyncio.run(test_answer_and_source())
