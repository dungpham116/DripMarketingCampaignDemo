from pydantic import BaseModel, Field
from typing import Type
from langchain.tools import BaseTool
from config import Config
from openai import OpenAI

client = OpenAI(api_key=Config.OPENAI_KEY)

class CategorizeEmailInput(BaseModel):
    conversation: str = Field(description="Email conversation array")

class CategorizeEmailTool(BaseTool):
		# Provide proper name and description for your tool
    name: str = "email_categorizer_tool"
    description: str = "use this tool when have email conversation history and you want to categorize this email"
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
        2. Power: If they’re interested in our emails
        3. Question: If they have any question regarding anything
        4. Unsubscribe: They want to unsubscribe themselves from our email list
        5. OOO: They are out of office
        6. No_Longer_Works: They no longer works in the company
        7. Not_Interested: They are not interested
        8. Info: these are emails that don't fit into any of the above categories.

        Note: Your final response MUST BE the category name ONLY 

        RESPONSE:
      """
      message = client.chat.completions.create(
          model="gpt-4o-mini",
          messages=[
              {"role": "user", "content": prompt}
          ]
      )
      category = message.choices[0].message.content
      return category

    def _arun(self, url: str):
        raise NotImplementedError(
            "categorise_email does not support async")
    
class EmailWriterToolInput(BaseModel):
    latest_reply: str = Field(description="Latest reply from the prospect")
    conversation_history: str = Field(description="Array of conversation history")
    sender: str = Field(description="Name of sender")

class EmailWriterTool(BaseTool):
    name: str = "email_writer_tool"
    description: str = "use this tool when you have given a email and you have to construct a reply for it"
    args_schema: Type[BaseModel] = EmailWriterToolInput

    def _run(self, latest_reply: str, conversation_history: str, sender: str):
        prompt = f"""
        You are the email inbox manager for Ron who is CEO of Hyred. He have sent an cold emails to some people and they have replied to Ron and now its your job to help draft email response for Jason that mimic the past reply. Jason is a millenial so please talk in his tone only.
        Use this conversation history as a context:
        {conversation_history}

        Here is the new email for which you have to generate a reply:
        {latest_reply}

        Sender Name: 
        {sender}

        While generating reply YOU MUST FOLLOW these instructions:

        - Try to reply in a way Ron replied in his past emails
        - Don't repeat anything which client said and add everything in this reply only, don't postpone anything to next email.
        - Make the reply short and easy to understand without adding any unnecessary information
      """
        message = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        reply = message.choices[0].message.content
        return reply

    def _arun(self, url: str):
        raise NotImplementedError(
            "email writer tool does not support async")