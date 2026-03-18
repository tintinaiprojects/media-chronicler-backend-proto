from fastapi import FastAPI
from pyairtable import Table
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
BASE_ID = os.getenv("AIRTABLE_BASE_ID")

events_table = Table(AIRTABLE_API_KEY, BASE_ID, "Events")
narratives_table = Table(AIRTABLE_API_KEY, BASE_ID, "Narratives")


@app.get("/events")
def get_events():

    events = events_table.all()
    narratives = narratives_table.all()

    narrative_map = {
        n["fields"]["event_id"]: n["fields"]["Narrative"]
        for n in narratives
        if "event_id" in n["fields"]
    }

    result = []

    for record in events:
        f = record["fields"]

        event_id = f.get("event_id")

        result.append({
            "id": event_id,
            "title": f.get("title"),
            "date": f.get("event_date", ""),
            "description": narrative_map.get(event_id, f.get("sentence", "")),
            "source": f.get("source_article_url")
        })

    result = sorted(result, key=lambda x: x["date"], reverse=True)

    return result