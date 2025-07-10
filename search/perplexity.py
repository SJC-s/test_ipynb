import requests
import os
from dotenv import load_dotenv

load_dotenv()

pplx_api_key = os.getenv("PPLX_API_KEY")

url2 = "https://api.perplexity.ai/chat/completions"

payload2 = {"request": {
        "model": "sonar-pro",
        "messages": [
            {
                "role": "system",
                "content": "Be precise and concise."
            },
            {
                "role": "user",
                "content": "Perplexity API로 웹검색하는 방법을 알려줘."
            }
        ],
        "search_mode": "web",
        "stream": False,
        # "reasoning_effort": "medium",
        # "max_tokens": 123,
        # "temperature": 0.2,
        # "top_p": 0.9,
        # "search_domain_filter": ["<any>"],
        # "return_images": False,
        # "return_related_questions": False,
        # "search_recency_filter": "<string>",
        # "search_after_date_filter": "<string>",
        # "search_before_date_filter": "<string>",
        # "last_updated_after_filter": "<string>",
        # "last_updated_before_filter": "<string>",
        # "top_k": 0,
        # "stream": False,
        # "presence_penalty": 0,
        # "frequency_penalty": 0,
        # "response_format": {},
        # "web_search_options": {"search_context_size": "high"}
    }}
headers2 = {
    "Authorization": f"Bearer {pplx_api_key}",
    "Content-Type": "application/json"
}

response2 = requests.request("POST", url2, json=payload2, headers=headers2)

print(response2.text)