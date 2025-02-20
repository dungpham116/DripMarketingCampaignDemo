import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SMARTLEAD_API_KEY = os.getenv('SMARTLEAD_API_KEY')
    OPENAI_KEY = os.getenv('OPENAI_KEY')
    APOLLO_API_KEY = os.getenv('APOLLO_API_KEY')
    SMARTLEAD_BASE_URL = "https://server.smartlead.ai/api/v1"
    OPENAI_MODEL = "gpt-4o-mini"