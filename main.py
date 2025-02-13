from crew import email_writing_agent

def run():
    result = email_writing_agent.kickoff(
        inputs = {
            'client_mail': 'abc@gmail.com', # Mail to which have to reply
            'conversation_history': '', # Fetch from smartlead API, need more preprocessing
            'sender_name': 'abc',
            'company_decs': 'None', # From company search tool
            }
        )