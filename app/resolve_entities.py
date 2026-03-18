import re
from datetime import datetime
from pyairtable import Api
from rapidfuzz import fuzz

import os
from dotenv import load_dotenv

load_dotenv()

AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

api = Api(AIRTABLE_API_KEY)

entities_table = api.table(BASE_ID, "Entities")
canonical_table = api.table(BASE_ID, "Canonical_Entities")


def normalize(text):
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def load_canonical_entities():
    records = canonical_table.all()

    entities = []

    for r in records:
        fields = r["fields"]

        if not fields.get("entity_id"):
            continue

        canonical = fields.get("canonical_name", "")
        aliases = fields.get("aliases", "")
        entity_type = fields.get("type")

        alias_list = [normalize(canonical)]

        for a in aliases.split("\n"):
            if a.strip():
                alias_list.append(normalize(a))

        entities.append({
            "entity_id": fields.get("entity_id"),
            "canonical": canonical,
            "type": entity_type,
            "aliases": alias_list
        })

    return entities


def resolve(name, entity_type, entity_map):

    n = normalize(name)

    for entity in entity_map:

        if entity["type"] != entity_type:
            continue

        for alias in entity["aliases"]:

            if n == alias:
                return entity

            if fuzz.ratio(n, alias) > 90:
                return entity

    return None


def create_entity(name, entity_type):

    if not entity_type:
        entity_type = "entity"

    entity_count = len(canonical_table.all()) + 1
    entity_id = f"{entity_type}_{entity_count:03d}"

    canonical_table.create({
        "entity_id": entity_id,
        "canonical_name": name,
        "aliases": name,
        "entity_type": entity_type,
        "created_at": datetime.now().strftime("%Y-%m-%d")
    })

    return {
        "entity_id": entity_id,
        "canonical": name
    }


def run():

    canonical_entities = load_canonical_entities()

    mentions = entities_table.all()

    for m in mentions:

        fields = m["fields"]
        print(fields)

        if fields.get("canonical_entity_id"):
            continue

        name = fields.get("Name")
        type_field = fields.get("Type")

        if isinstance(type_field, dict):
            entity_type = type_field.get("name")
        else:
            entity_type = type_field

        if entity_type:
            entity_type = entity_type.lower()

        if not name:
            continue

        if not entity_type:
            continue

        entity = resolve(name, entity_type, canonical_entities)

        if not entity:
            entity = create_entity(name, entity_type)

        canonical_entities.append({
            "entity_id": entity["entity_id"],
            "canonical": name,
            "type": entity_type,
            "aliases": [normalize(name)]
        })

        entities_table.update(m["id"], {
            "canonical_entity_id": entity["entity_id"]
        })

        print(f"{name} → {entity['entity_id']}")


if __name__ == "__main__":
    run()