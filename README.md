# Drip Marketing Campaign Demo

# Finished
- Setup AI agent, webhook
- Connect everything together
- Now reply on smartlead will trigger the agent to work
- Refactor code for readability and easy maintainence

# TO DO
- Add knowledge base
- Extract payload from webhook to get data such as campaign_id, lead_id, reply_mail and feed to the agent
- D A S H B O A R D

# How to use
- Create ngrok account, follow their instruction and create a domain (They give 1 free domain)
- Start ngrok tunnel service on port 5000: ngrok http 5000 --domain domain-name.ngrok-free.app
- pip install -r requirements.txt
- Run webhook.py, not main.py (Currently using Flask for localhost, may switch to FastAPI)
- Try a webhook trigger on SmartLead, the agent will automatically runs (Currently it fetch from local csv file)