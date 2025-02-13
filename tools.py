import os
from crewai.tools.structured_tool import CrewStructuredTool
from pydantic import BaseModel
import requests
from datetime import datetime
current_datetime = datetime.utcnow()

# Email Sender Tool
class EmailSenderToolInput(BaseModel):
    campaign_id: int
    email_stats_id: int
    email_body: str
    reply_message_id: int
    reply_email_body: str
    email : str

# Wrapper function to execute the API call
def email_sender_wrapper(*args, **kwargs):
    SmartLead_API_KEY = os.getenv("SMARTLEAD_API_KEY")
    url = f"https://server.smartlead.ai/api/v1/campaigns/{kwargs['campaign_id']}/reply-email-thread?api_key={kwargs['SmartLead_API_KEY']}"
    data = {
      "email_stats_id": {kwargs['email_stats_id']},
      "email_body": {kwargs['email_body']},
      "reply_message_id": {kwargs['reply_message_id']},
      "reply_email_time": current_datetime.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
      "reply_email_body": {kwargs['reply_email_body']},
      "cc": {kwargs['email']},
    }
    try:
      response = requests.post(url,data=data)
      response = response.json()
      return "Email sent to lead!"
    except requests.exceptions.RequestException as e:
      return f"Error: {e}"

def create_email_sender_tool():
    return CrewStructuredTool.from_function(
        name = 'Email Sender Tool',
        description = "A tool to reply to lead from master inbox via API ",
        args_schema = EmailSenderToolInput,
        func = email_sender_wrapper,
    )


# Company Search Tool
class CompanySearchToolInput(BaseModel):
    email: str

# Wrapper function to execute the API call
def company_search_wrapper(*args, **kwargs):
    data = {
            "api_key":os.getenv("Apollo_API_KEY"),
            "email":{kwargs['email']}
        }
    try:
      response = requests.post(f"https://api.apollo.io/v1/people/match",data=data)
      response = response.json()
      return response["person"]["organization"]["short_description"]
    except requests.exceptions.RequestException as e:
      return f"Error: {e}"

def create_company_search_tool():
    return CrewStructuredTool.from_function(
        name = 'Company Search Tool',
        description = "use this tool when you want to get information about the company of the email sender",
        args_schema = CompanySearchToolInput,
        func = company_search_wrapper,
    )

# # Example usage
# CompanySearchTool = create_company_search_tool()

# result = CompanySearchTool._run(**{
#     "email":  'someone@apollo.ai'
# })
# print(result)  