import html2text
from config import Config
from openai import OpenAI

client = OpenAI(api_key=Config.OPENAI_KEY)

class EmailProcessor:
    @staticmethod
    def extract_latest_email(message_history,row):
        conversation_history = []
        for message in message_history:
            plain_text = html2text.html2text(message['email_body'])
            prompt = f"""
                Email Thread:
                ---
                {plain_text}
                ---
                You have given a email thread as a plain text and you have to return the latest email from it

                You have to follow these steps to do it:
                Step-1: Get the text which don't starts with '>' because every other text which starts with '>' is a old message in thread
                (It will be at the starting of text and older messages will be at below this latest message)

                The email thread format typically look like this:
                ---
                Hey john,
                I am interested
                Thanks,
                shivam
                > sentence 1 ....
                > sentence 2 ....
                > ...
                >> sentence from older emails ...
                >> sentence from older emails ....
                >> ....
                ---
                For above example, the email message content will be:
                Hey john,
                I am interested
                Thanks,
                Shivam

                Note: Please note that the above message content was just an example and your respond must be related to given plain text

                Step-2: Once you got the latest email then get the message content from it and remove any extra blank space or unnecessary content from email
                After these steps, Return the email message content in response

                RESPONSE (Don't return anything except email message):
            """
            email_content = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            email_content = email_content.choices[0].message.content
            convo = {
                "sender": "info mation" if message["type"] == "SENT" else row[0],
                "message": email_content
            }
            conversation_history.append(convo)
        return conversation_history