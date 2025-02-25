import csv
import json
import requests
from agents.email_agent import EmailAgent
from tools.api_tools import SmartLeadAPIClient
from utils.email_formating import EmailProcessor
from config import Config

def process_leads(_campaign_id, lead_email, lead_name):
    api_client = SmartLeadAPIClient()
    email_agent = EmailAgent()
    
    message_history = api_client.get_lead_message_history(lead_email,_campaign_id)
    # print(message_history)
    if message_history is not None:
        conversation_history = EmailProcessor.extract_latest_email(message_history,lead_name)
        # Prompt for our agent
        prompt = f"""
            Email conversation history:
            ---
            {conversation_history}
            ---
            Lead Name: {lead_name}
            Lead Email: {lead_email}

            Sender of last message: {conversation_history[len(conversation_history) - 1]["sender"]}
        """
        # print(type(email_agent))
        response = email_agent({"input": prompt})
        response = json.loads(response["output"])
        history = message_history[len(message_history)-1]
        print('Finished processing lead')
        # If there is reply which needs to be send then use email sender tool to send email
        if response['reply'] != "":
            res = api_client.EmailSenderTool(campaign_id=_campaign_id,email_stats_id=history["stats_id"],email_body=response['reply'],reply_message_id=history["message_id"],reply_email_body=history["email_body"],email=lead_email)
            print(res)

# if __name__ == "__main__":
#     process_leads(1501858, 'Campaign_Leads.csv')