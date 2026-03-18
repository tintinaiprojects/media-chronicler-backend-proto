import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("PPLX_API_KEY")

URL = "https://api.perplexity.ai/chat/completions"


PROMPT = """
List news articles mentioning K. J. Alphons (Alphons Kannanthanam).

Include:
- articles about him
- interviews
- opinion pieces
- controversies
- political coverage
- stories where he is mentioned

Return up to 20 results.

Return ONLY JSON:

[
  {
    "title": "...",
    "url": "...",
    "source": "...",
    "published_date": "...",
    "summary": "..."
  }
]
"""


def discover_articles(query):

    payload = {
        "model": "sonar",
        "messages": [
            {"role": "user", "content": f"{PROMPT}\nSearch focus: {query}"}
        ]
    }

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    response = requests.post(URL, json=payload, headers=headers)

    print("Status:", response.status_code)
    print("Raw response:", response.text)
    
    data = response.json()

    return data["choices"][0]["message"]["content"]