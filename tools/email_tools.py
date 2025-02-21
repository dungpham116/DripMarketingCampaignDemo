from pydantic import BaseModel, Field
from typing import Type
from langchain.tools import BaseTool
from config import Config
from openai import OpenAI
from langchain.document_loaders import CSVLoader
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma

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
        You have given an array of conversations between Jamie and a client.
        Your goal is to categorize this email based on the conversation history from the given categories:

        1. Interested_Needs_Further_Discussion: Prospects who show positive engagement with your offering, asking questions or expressing clear interest in learning more.
        2. Request_For_More_Information: When a prospect asks for additional details about your product or service to make an informed decision.
        3. Positive_Feedback: Emails where the recipient expresses appreciation for your outreach or provides positive comments about your company.
        4. Open_To_A_Call: When the prospect indicates they're willing to schedule a call to discuss further.
        5. Needs_Immediate_Follow_Up: Urgent situations where a prospect needs a quick response due to a time-sensitive need.
        6. Not_Interested_Politely_Decline: Prospects who clearly state they are not interested in your offering but do so in a respectful manner.
        7. Out_Of_Scope: Emails from individuals or companies that fall outside your target market or service area.
        8. Wrong_Contact: Emails sent to the wrong person within a company or an outdated contact.
        9. Auto_Reply: Generic replies indicating the recipient is out of office or not currently monitoring their email.
        10. Spam_Indicator: Emails with suspicious subject lines, excessive exclamation points, or other signs of spam.
        11. Negative_Response: Aggressive or hostile replies, personal attacks, or clear disinterest in your offering.
        12. Unsubscribed: Individuals who have opted out of receiving further communication from your company.
        13. Info: These are emails that don't fit into any of the above categories.

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
    description: str = "Use this tool to construct a reply to an email."
    args_schema: Type[BaseModel] = EmailWriterToolInput

    def __init__(self):
        super().__init__()

        # Load past emails and FAQs into ChromaDB
        embedding_function = OpenAIEmbeddings()

        # Load past replies
        email_loader = CSVLoader("./final.csv", encoding="utf-8")
        email_documents = email_loader.load()

        # Load FAQs
        faq_loader = CSVLoader("./faq.csv", encoding="utf-8")
        faq_documents = faq_loader.load()

        # Store in ChromaDB
        self.email_db = Chroma.from_documents(email_documents, embedding_function)
        self.faq_db = Chroma.from_documents(faq_documents, embedding_function)

    def retrieve_relevant_knowledge(self, query: str):
        """Retrieve past emails & FAQs relevant to the latest reply."""
        past_emails = self.email_db.similarity_search(query, k=3)
        faqs = self.faq_db.similarity_search(query, k=3)

        past_emails_text = "\n".join([doc.page_content for doc in past_emails])
        faqs_text = "\n".join([doc.page_content for doc in faqs])

        return past_emails_text, faqs_text

    def _run(self, latest_reply: str, conversation_history: str, sender: str):
        # Retrieve relevant past emails & FAQs
        past_emails, faqs = self.retrieve_relevant_knowledge(latest_reply)

        prompt = f"""
        You are the email inbox manager for Jamie, a recruiter at Hyred.
        He has sent cold emails to prospects, and they have replied.
        Your task is to draft responses that mimic Jamie’s past replies.

        **PAST EMAIL EXAMPLES:**
        {past_emails}

        **USE THIS AS YOUR KNOWLEDGE BASE:**
        {faqs}

        **CONVERSATION HISTORY:**
        {conversation_history}

        **NEW EMAIL FROM PROSPECT:**
        {latest_reply}

        **SENDER NAME:** {sender}

        **INSTRUCTIONS:**
        - If the email from prospect cannot be found in the knowledge base, DON'T construct the reply
        - Reply in the same style Jamie used in his past emails.
        - Avoid repeating what the client said.
        - Do not defer topics to another email—respond fully now.
        - Keep it short and easy to understand.
        """

        message = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )

        return message.choices[0].message.content

    def _arun(self, url: str):
        raise NotImplementedError("Email writer tool does not support async.")