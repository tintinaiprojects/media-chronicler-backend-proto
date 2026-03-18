import re
import uuid
import json
from pathlib import Path
from fastapi import APIRouter
from app.discovery.perplexity_client import discover_articles

router = APIRouter()

DB_PATH = Path("db.json")


def load_db():
    if not DB_PATH.exists():
        return {"articles": []}

    with open(DB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_db(db):
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2)


def extract_urls(text):

    url_pattern = r"https?://[^\s\)\]\>\"']+"

    raw_urls = re.findall(url_pattern, text)

    cleaned = []

    for u in raw_urls:

        u = u.strip().rstrip(".,);:]\"'")

        if "google.com" in u:
            continue

        if len(u) < 30:
            continue

        cleaned.append(u)

    return list(set(cleaned))


@router.post("/discover")
def discover():

    queries = [
    "KJ Alphons news",
    "Alphons Kannanthanam news",
    "KJ Alphons politics",
    "KJ Alphons IAS officer"
    ]
    
    db = load_db()

    seen_urls = set(a["url"] for a in db["articles"])

    added = 0

    for q in queries:

        print(f"Running query: {q}")

        response_text = discover_articles(q)

        if not response_text:
            print("Empty response from Perplexity")
            continue

        # remove markdown code fences
        response_text = response_text.replace("```json", "").replace("```", "").strip()

        # extract JSON array if extra text exists
        import re
        match = re.search(r'\[\s*\{.*?\}\s*\]', response_text, re.DOTALL)

        if not match:
            print("No JSON found in response")
            print("Raw response:", response_text[:500])
            continue

        try:
            articles = json.loads(match.group(0))
        except Exception as e:
            print("JSON parse failed:", e)
            print("Raw response:", response_text[:500])
            continue

        print(f"Found {len(articles)} URLs")

        for article in articles:

            url = article.get("url")

            if not url:
                continue

            if "/tag/" in url or "/topic/" in url or "/author/" in url:
                continue

            if url in seen_urls:
                continue

            seen_urls.add(url)

            aid = str(uuid.uuid4())

            db["articles"].append({
                "id": aid,
                "url": url,
                "title": article.get("title"),
                "source": article.get("source"),
                "published_date": article.get("published_date"),
                "summary": article.get("summary"),
                "query": q
             })

            added += 1

    save_db(db)

    return {
        "bootstrap_complete": True,
        "articles_added": added,
        "total_articles": len(db["articles"])
    }