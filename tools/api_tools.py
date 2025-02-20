import requests
from datetime import datetime
from config import Config

class SmartLeadAPIClient:
    def __init__(self):
        self.base_url = Config.SMARTLEAD_BASE_URL
        self.api_key = Config.SMARTLEAD_API_KEY
    
    def get_campaigns(self):
        response = requests.get(f"{self.base_url}/campaigns?api_key={self.api_key}")
        response.raise_for_status()
        return response.json()
    
    def EmailSenderTool(self, campaign_id, email_data):
        url = f"{self.base_url}/campaigns/{campaign_id}/reply-email-thread"
        data = {
            **email_data,
            "api_key": self.api_key,
            "reply_email_time": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        }
        response = requests.post(url, json=data)
        response.raise_for_status()
        return response.json()