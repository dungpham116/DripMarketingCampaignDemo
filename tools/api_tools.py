import requests
from config import Config
from datetime import datetime
current_datetime = datetime.utcnow()

class SmartLeadAPIClient:
    def __init__(self):
        self.base_url = Config.SMARTLEAD_BASE_URL
        self.api_key = Config.SMARTLEAD_API_KEY
    
    def get_campaigns(self):
        response = requests.get(f"{self.base_url}/campaigns?api_key={self.api_key}")
        response.raise_for_status()
        return response.json()
    

    def EmailSenderTool(self,campaign_id,email_stats_id,email_body,reply_message_id,reply_email_body,email):
        url = f"https://server.smartlead.ai/api/v1/campaigns/{campaign_id}/reply-email-thread?api_key={self.api_key}"
        data = {
            "email_stats_id": email_stats_id,
            "email_body": email_body,
            "reply_message_id": reply_message_id,
            "reply_email_time": current_datetime.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
            "reply_email_body": reply_email_body,
            "to_email": email,
        }

        headers = {
            "accept": "application/json",
            "content-type": "application/json"
        }
            
        # Send the request
        try:
            response = requests.post(url, json=data, headers= headers)  # Use `json=data` for JSON payloads
            response.raise_for_status()  # Raise an error for bad status codes (4xx, 5xx)
            response_data = response.json()  # Parse the JSON response
            print("Response:", response_data)
            return response_data
        except requests.exceptions.RequestException as e:
            print(f"An error occurred: {e}")
            return None

