from pyairtable import Table

import os
from dotenv import load_dotenv

load_dotenv()

AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

table = Table(API_KEY, BASE_ID, "Articles")

table.create({
    "URL": "https://example.com",
    "Title": "Test Article from Media Chronicler"
})

print("Article successfully sent to Airtable!")