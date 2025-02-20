import csv
import json
import requests
from agents.email_agent import EmailAgent
from tools.api_tools import SmartLeadAPIClient
from utils.email_formating import EmailProcessor
from config import Config

def process_leads(campaign_id, csv_path):
    api_client = SmartLeadAPIClient()
    email_agent = EmailAgent()
    
    with open(csv_path, 'r', encoding='utf-8') as file:
        csv_reader = csv.reader(file)
        for index,row in enumerate(csv_reader):
            if index == 0:
                continue
            # Get lead ID
            lead_info = requests.get(f"https://server.smartlead.ai/api/v1/leads/?api_key={Config.SMARTLEAD_API_KEY}&email={row[2]}")
            lead_info = lead_info.json()
            # Get conversation history of lead
            message_history = requests.get(f"https://server.smartlead.ai/api/v1/campaigns/{campaign_id}/leads/{lead_info['id']}/message-history?api_key={Config.SMARTLEAD_API_KEY}")
            message_history = message_history.json()
            message_history = message_history["history"]
            # print(message_history)
            conversation_history = EmailProcessor.extract_latest_email(message_history,row)
            # Prompt for our agent
            prompt = f"""
                Email conversation history:
                ---
                {conversation_history}
                ---
                Lead Name: {row[0]}
                Lead Email: {row[2]}

                Sender of last message: {conversation_history[len(conversation_history) - 1]["sender"]}
            """
            # print(type(email_agent))
            response = email_agent({"input": prompt})
            response = json.loads(response["output"])
            history = message_history[len(message_history)-1]
            print('Finished processing lead')
            # If there is reply which needs to be send then use email sender tool to send email
            # if response['reply'] != "":
            #     res = api_client.EmailSenderTool(campaign_id=campaign_id,email_stats_id=history["stats_id"],email_body=response['reply'],reply_message_id=history["message_id"],reply_email_body=history["email_body"],email=row[2])

if __name__ == "__main__":
    process_leads(1501858, 'Campaign_Leads.csv')