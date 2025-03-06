# %%
import requests
import pandas as pd
import csv
import json
from dotenv import load_dotenv
import os
load_dotenv('example.env')
API_KEY = os.getenv("SMARTLEAD_API_KEY")


# %% [markdown]
# ## CREATE A CAMPAIGN

# %%
data = {
    "name": "Campaign created via API",
    "client_id": None,
}
create_campaign = requests.post(f"https://server.smartlead.ai/api/v1/campaigns/create?api_key={API_KEY}", data=data)

# %%
# leads = pd.read_csv("First 100 - Sheet2.csv")
# leads = leads.drop(['Unnamed: 6', 'Unnamed: 7', 'Last Name'], axis=1)
# leads_deliverable = leads[leads['result'] == 'deliverable']
# leads_deliverable.reset_index(drop=True, inplace=True)
# leads_deliverable.to_csv("leads_deliverable.csv", index=False)

# %% [markdown]
# GET CAMPAIGN ID WITH NAME

# %%
campaigns = requests.get(f"https://server.smartlead.ai/api/v1/campaigns?api_key={API_KEY}")
campaigns = campaigns.json()
for i in campaigns:
    if i['name'] == "Campaign created via API":
        campaign_id = i['id']
        break
print(campaign_id)

# %% [markdown]
# ## CONVERT DATA FROM CSV TO JSON FILE WITH THE FOLLOWING FORMAT

# %%
def convert_csv_to_json(csv_file_path, json_file_path):
    lead_list = []
    
    with open(csv_file_path, 'r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        
        for row in csv_reader:
            # Create the lead dictionary with the required structure
            lead = {
                "first_name": row.get("First Name", ""),
                "last_name": row.get("Last Name", ""),
                "email": row.get("Email", ""),
                "phone_number": row.get("Phone Number", ""),
                "company_name": row.get("Company Name", ""),
                "website": row.get("Website", ""),
                "location": row.get("Country", ""),
                "linkedin_profile": row.get("Linkedin Profile", ""),
                "company_url": row.get("Company Url", ""),
            }
            
            # # Add any additional columns as custom fields
            # for key, value in row.items():
            #     if key not in lead.keys() and value:
            #         lead["custom_fields"][key] = value
            
            lead_list.append(lead)
    
    # Write the JSON output
    with open(json_file_path, 'w') as json_file:
        json.dump({"lead_list": lead_list}, json_file, indent=2)

    return lead_list

# Usage
csv_file_path = 'test_campaign 2 Lead List.csv'
json_file_path = 'lead_list.json'
leads = convert_csv_to_json(csv_file_path, json_file_path)
print(f"Converted {len(leads)} leads to JSON format")

# %% [markdown]
# ## UPLOAD LEADS TO CAMPAIGN

# %%
data = {
    "lead_list": leads[:50],
    "settings": {
    "ignore_global_block_list": False, # If true, uploaded leads will BYPASS the global block list and be uploaded to the campaign.
    "ignore_unsubscribe_list": False, # If true, leads will BYPASS the comparison with unsubscribed leads and be uploaded to the campaign.
    "ignore_community_bounce_list": False, # If true, uploaded leads will BYPASS any leads that bounced across smartleads entire userbase and be uploaded to the campaign.
    # *Pay attention to below*
    "ignore_duplicate_leads_in_other_campaign": False # If true, leads will NOT BYPASS the comparison with other campaigns and NOT be added to the campaign if they are part of any other campaign. 
  }
}
leads_uploaded = requests.post(f"https://server.smartlead.ai/api/v1/campaigns/{campaign_id}/leads?api_key={API_KEY}", data=json.dumps(data), headers={"Content-Type": "application/json"})

# %%
leads_uploaded.json()

# %% [markdown]
# ## CREATE SEQUENCE FOR CAMPAIGN

# %%
# --- Example, can replace with AI Agent Writer Tools ---
sequences_data = {
    "sequences": [
        {
            "seq_number": 1,
            "seq_delay_details": {
                "delay_in_days": 1
            },
            "variant_distribution_type": "MANUAL_EQUAL",
            "lead_distribution_percentage": 40,
            "winning_metric_property": "OPEN_RATE",
            "seq_variants": [
                {
                    "subject": "Subject",
                    "email_body": "<p>Hi<br><br>How are you?<br><br>Hope you're doing good</p>",
                    "variant_label": "A",
                    "variant_distribution_percentage": 20
                },
                {
                    "subject": "Ema a",
                    "email_body": "<p>This is a new game a</p>",
                    "variant_label": "B",
                    "variant_distribution_percentage": 60
                },
                {
                    "subject": "C emsil",
                    "email_body": "<p>Hiii C</p>",
                    "variant_label": "C",
                    "variant_distribution_percentage": 20
                }
            ]
        },
        {
            "seq_number": 2,
            "seq_delay_details": {
                "delay_in_days": 1
            },
            "subject": "",
            "email_body": "Hi there, this is a follow up email",
        }
    ]
}

response = requests.post(
    f"https://server.smartlead.ai/api/v1/campaigns/{campaign_id}/sequences?api_key={API_KEY}",
    data=json.dumps(sequences_data),
    headers={"Content-Type": "application/json"}
)

# %%
response.json()

# %% [markdown]
# ## SCHEDULE TO RUN CAMPAIGN

# %%
schedule_data = {
    "timezone": "Asia/Saigon",  # Changed to Hanoi timezone
    "days_of_the_week": [0,1,2,3,4,5,6],
    "start_hour": "09:00",
    "end_hour": "17:00",
    "min_time_btw_emails": 5,
    "max_new_leads_per_day": 20,
    "schedule_start_time": None,
}

schedule_response = requests.post(
    f"https://server.smartlead.ai/api/v1/campaigns/{campaign_id}/schedule?api_key={API_KEY}",
    data=json.dumps(schedule_data),
    headers={"Content-Type": "application/json"}
)
schedule_response.json()

# %% [markdown]
# ## ADD EMAIL ACCOUNT FOR SENDING EMAIL CAMPAIGN 

# %%
email_accounts = requests.get(f"https://server.smartlead.ai/api/v1/campaigns/1485611/email-accounts?api_key={API_KEY}")
email_accounts.json()

# %%
data = {
    "email_account_ids": [5730600]
}

email_accounts_response = requests.post(
    f"https://server.smartlead.ai/api/v1/campaigns/{campaign_id}/email-accounts?api_key={API_KEY}",
    data=json.dumps(data),
    headers={"Content-Type": "application/json"}
)
email_accounts_response.json()

# %% [markdown]
# ## START THE CAMPAIGN

# %%
data = {
    "status": "START"
}

status_response = requests.post(
    f"https://server.smartlead.ai/api/v1/campaigns/{campaign_id}/status?api_key={API_KEY}",
    data=json.dumps(data),
    headers={"Content-Type": "application/json"}
)
status_response.json()


