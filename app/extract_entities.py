import os
import json
from datetime import datetime, UTC
from dotenv import load_dotenv
from pyairtable import Api
from openai import OpenAI

# Load environment variables
load_dotenv()

AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
BASE_ID = os.getenv("AIRTABLE_BASE_ID")

# Airtable setup
api = Api(AIRTABLE_API_KEY)
articles_table = api.table(BASE_ID, "Articles")
entities_table = api.table(BASE_ID, "Entities")

# OpenAI client
client = OpenAI()


def extract_entities(article_text):
    prompt = f"""
Extract entities related to K. J. Alphons from this article.

Only include entities directly connected to Alphons.

Allowed entity types:
Person
Organization
Location
Event

Return ONLY valid JSON in this format:

{{
  "entities": [
    {{"name": "K. J. Alphons", "type": "Person"}},
    {{"name": "Kerala", "type": "Location"}}
  ]
}}

Article:
{article_text}
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": "You extract structured entities from news articles."},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )

    content = response.choices[0].message.content.strip()

    try:
        data = json.loads(content)
        return data.get("entities", [])
    except:
        print("⚠ JSON parse error")
        print(content)
        return []


def main():

    # Fetch unprocessed articles
    records = articles_table.all(formula="Processed = FALSE()")

    print(f"Found {len(records)} unprocessed articles")

    for record in records:

        fields = record["fields"]

        title = fields.get("Title", "")
        summary = fields.get("Summary", "")
        text = fields.get("Text", "")
        url = fields.get("URL", "")

        if not title and not text:
            continue

        article_content = f"{title}\n\n{summary}\n\n{text[:6000]}"

        print(f"\nProcessing: {title}")

        entities = extract_entities(article_content)

        for entity in entities:

            entities_table.create({
                "Name": entity["name"],
                "Type": entity["type"],
                "Article URL": url,
                "Article Title": title,
                "Extracted At": datetime.now(UTC).isoformat()
            })

        # Mark article as processed
        articles_table.update(record["id"], {
            "Processed": True
        })

        print(f"Extracted {len(entities)} entities")


if __name__ == "__main__":
    main()