import json
from newspaper import Article
from pyairtable import Table
from datetime import datetime

import os
from dotenv import load_dotenv

load_dotenv()

AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
BASE_ID = os.getenv("AIRTABLE_BASE_ID")

table = Table(API_KEY, BASE_ID, "Articles")

def url_exists(url):
    records = table.all(formula=f"{{URL}} = '{url}'")
    return len(records) > 0

# load discovered URLs
with open("data/articles.json", "r", encoding="utf-8") as f:
    data = json.load(f)
    articles = data["articles"]

for item in articles:

    if isinstance(item, dict):
        url = item["url"]
    else:
        url = item

    # prevent duplicates
    if url_exists(url):
        print("Skipping (already exists):", url)
        continue

    try:
        article = Article(url)
        article.download()
        article.parse()
        article.nlp()

        record = {
            "URL": url,
            "Title": article.title,
            "Source": article.source_url,
            "Author": ", ".join(article.authors),
            "Published Date": article.publish_date.isoformat() if article.publish_date else None,
            "Summary": article.summary,
            "Keywords": ", ".join(article.keywords),
            "Images": ", ".join(article.images),
            "Text": article.text,
            "Extracted At": datetime.now().strftime("%Y-%m-%d")
        }

        table.create(record)

        print("Saved:", url)

    except Exception as e:
        print("Failed:", url, e)