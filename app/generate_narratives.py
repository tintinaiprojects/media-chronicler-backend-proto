import os
from pyairtable import Api
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv("../../.env")

import os
from dotenv import load_dotenv

load_dotenv()

AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


api = Api(AIRTABLE_API_KEY)

events_table = api.table(AIRTABLE_BASE_ID, "Events")
narratives_table = api.table(AIRTABLE_BASE_ID, "Narratives")

client = OpenAI(api_key=OPENAI_API_KEY)


def narrative_exists(event_id):
    records = narratives_table.all(
        formula=f"{{event_id}}='{event_id}'"
    )
    return len(records) > 0


def build_prompt(event):

    sentence = event.get("sentence", "")
    source = event.get("source_article_url", "")

    return f"""
Write a short factual summary of the following news event.

Event sentence:
{sentence}

Source article:
{source}

Rules:
- Only describe the event in the sentence.
- Do NOT invent historical events.
- Do NOT add unrelated information.
- Keep it 2–3 sentences.
"""


def generate_narrative(prompt):

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )

    return response.choices[0].message.content.strip()


def run():

    events = events_table.all()

    for record in events:

        fields = record["fields"]
        event_id = fields.get("event_id")

        if not event_id:
            continue

        if narrative_exists(event_id):
            print("Skipping existing narrative:", event_id)
            continue

        prompt = build_prompt(fields)

        narrative_text = generate_narrative(prompt)

        narratives_table.create({
            "event_id": event_id,
            "Narrative": narrative_text
        })

        print("Narrative generated:", event_id)


if __name__ == "__main__":
    run()