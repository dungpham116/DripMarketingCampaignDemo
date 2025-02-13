from crewai.tools.structured_tool import CrewStructuredTool
from crewai import Agent, Crew, Process
from pydantic import BaseModel
from typing import Type, List
import requests
from datetime import datetime
import openai
current_datetime = datetime.utcnow()

#Email categorization tool
class CategorizeEmailInput(BaseModel):
    conversation: str = Field(description="Email conversation array")

class CategorizeEmailTool(BaseTool):
		# Provide proper name and description for your tool
    name = "email_categorizer_tool"
    description = "use this tool when have email conversation history and you want to categorize this email"
    args_schema: Type[BaseModel] = CategorizeEmailInput

    def _run(self, conversation: str):
      prompt = f"""
        Email Conversation History:
        ---
        {conversation}
        ---
        You have given an array of conversation between Rohan Sawant and a client
        Your goal is to categorize this email based on the conversation history from the given categories:

        1. Meeting_Ready_Lead: they have shown positive intent and are interested in getting on a call
        2. Power: If they’re interested and we want to push for a call
        3. Question: If they have any question regarding anything
        4. Unsubscribe: They want to unsubscribe themselves from our email list
        5. OOO: They are out of office
        6. No_Longer_Works: They no longer works in the company
        7. Not_Interested: They are not interested
        8. Info: these are emails that don't fit into any of the above categories.

        Note: Your final response MUST BE the category name ONLY

        RESPONSE:
      """
      message = openai.chat.completions.create(
          model="gpt-4",
          messages=[
              {"role": "user", "content": prompt}
          ]
      )
      category = message.choices[0].message.content
      return category

    def _arun(self, url: str):
        raise NotImplementedError(
            "categorise_email does not support async")

# Email Sender Tool
class EmailSenderToolInput(BaseModel):
    SmartLead_API_KEY: str
    campaign_id: int
    email_stats_id: int
    email_body: str
    reply_message_id: int
    reply_email_body: str
    email : str

# Wrapper function to execute the API call
def email_sender_wrapper(*args, **kwargs):
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
    Apollo_API_KEY: str

# Wrapper function to execute the API call
def company_search_wrapper(*args, **kwargs):
    data = {
            "api_key":{kwargs['Apollo_API_KEY']},
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
#     "Apollo_API_KEY": "################",
#     "email":  'someone@apollo.ai'
# })
# print(result)  