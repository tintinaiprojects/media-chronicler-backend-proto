import re
from datetime import datetime, UTC
from pyairtable import Api
import openai
import os
from dotenv import load_dotenv

load_dotenv()

AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

from openai import OpenAI

client = OpenAI()

def generate_event_title_llm(event):
    prompt = f"""
Rewrite the following event into a clear, specific news-style headline.

Rules:
- Must be self-contained
- Include who did what
- Replace weak verbs like "said", "stated" with the actual action
- Keep it concise (max 12 words)

Event:
Actor: {event.get("actor", "")}
Action: {event.get("action", "")}
Object: {event.get("object", "")}
Context: {event.get("context", "")}

Return only the title.
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.3
    )

    return response.choices[0].message.content.strip()

    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    return response.choices[0].message.content.strip()

def extract_event_date_llm(sentence):
    prompt = f"""
Extract the date of the event from this sentence.

Rules:
- Return in YYYY-MM-DD format
- If exact date not available, infer best possible (year or month)
- If completely unknown, return "UNKNOWN"

Sentence:
{sentence}

Return only the date.
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )

    return response.choices[0].message.content.strip()


api = Api(AIRTABLE_API_KEY)

articles_table = api.table(BASE_ID, "Articles")
entities_table = api.table(BASE_ID, "Entities")
events_table = api.table(BASE_ID, "Events")

ACTION_VERBS = [
    "said",
    "announced",
    "criticized",
    "accused",
    "met",
    "visited",
    "launched",
    "inaugurated",
    "appointed",
    "resigned",
    "joined",
    "supported",
    "opposed"
]


def load_entities():
    records = entities_table.all()
    entity_map = {}

    for r in records:
        fields = r["fields"]

        if "Name" in fields and "canonical_entity_id" in fields:
            entity_map[fields["Name"].lower()] = fields["canonical_entity_id"]

    return entity_map


def split_sentences(text):

    text = text.replace("\n", " ")
    sentences = re.split(r'[.!?]', text)

    return [s.strip() for s in sentences if s.strip()]


def detect_entities(sentence, entity_map):
    found = []

    for name, eid in entity_map.items():
        if name in sentence.lower():
            found.append(eid)

    return list(set(found))


def detect_action(sentence):
    for verb in ACTION_VERBS:
        if f" {verb} " in sentence.lower():
            return verb
    return None

def event_exists(sentence):

    formula = f"{{sentence}}='{sentence}'"

    records = events_table.all(formula=formula)

    return len(records) > 0

def save_event(actor, action, target, article, sentence):

    event = {
        "event_id": f"event_{int(datetime.now(UTC).timestamp())}",
        "actor": actor,
        "action": action,
        "object": target,
        "context": sentence,
        "actor_entity_id": actor,
        "target_entity_id": target,
        "source_article_url": article["fields"]["URL"],
        "sentence": sentence,
        "created_at": datetime.now(UTC).strftime("%Y-%m-%d")
    }

    event["title"] = generate_event_title_llm(event)
    event["event_date"] = extract_event_date_llm(sentence)

    if event_exists(sentence):
        return

    events_table.create(event)


def run():

    entity_map = load_entities()
    articles = articles_table.all()
    print("Articles found:", len(articles))

    for article in articles:

        content = article["fields"].get("Text", "")
        

        sentences = split_sentences(content)

        for s in sentences:
            print("Sentence:", s)
            action = detect_action(s)

            if not action:
                continue

            entities = detect_entities(s, entity_map)

            if len(entities) < 2:
                continue

            actor = entities[0]
            target = entities[1]

        

            save_event(actor, action, target, article, s)

            print("Event created:", actor, action, target)


if __name__ == "__main__":
    run()