import requests
import json
import os
from flask import current_app
from app import db
from app.models.campaign import Campaign
import datetime

class SmartleadAPI:
    BASE_URL = "https://server.smartlead.ai/api/v1"
    
    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get("SMARTLEAD_API_KEY")
        if not self.api_key:
            raise ValueError("SmartLead API key is required")
    
    def _get_headers(self):
        return {"Content-Type": "application/json"}
    
    def _get_url(self, endpoint):
        return f"{self.BASE_URL}/{endpoint}?api_key={self.api_key}"
    
    def get_campaigns(self):
        """Get all campaigns from SmartLead"""
        response = requests.get(self._get_url("campaigns"))
        return response.json()
    
    def create_campaign(self, name, client_id=None):
        """Create a new campaign on SmartLead"""
        data = {
            "name": name,
            "client_id": client_id
        }
        response = requests.post(self._get_url("campaigns/create"), data=data)
        return response.json()
    
    def upload_leads(self, campaign_id, leads, settings=None):
        """Upload leads to a campaign"""
        if settings is None:
            settings = {
                "ignore_global_block_list": False,
                "ignore_unsubscribe_list": False,
                "ignore_community_bounce_list": False,
                "ignore_duplicate_leads_in_other_campaign": False
            }
        
        data = {
            "lead_list": leads,
            "settings": settings
        }
        
        response = requests.post(
            self._get_url(f"campaigns/{campaign_id}/leads"),
            data=json.dumps(data),
            headers=self._get_headers()
        )
        return response.json()
    
    def create_sequences(self, campaign_id, sequences_data):
        """Create email sequences for a campaign"""
        response = requests.post(
            self._get_url(f"campaigns/{campaign_id}/sequences"),
            data=json.dumps(sequences_data),
            headers=self._get_headers()
        )
        return response.json()
    
    def setup_schedule(self, campaign_id, schedule_data):
        """Set up a schedule for a campaign"""
        response = requests.post(
            self._get_url(f"campaigns/{campaign_id}/schedule"),
            data=json.dumps(schedule_data),
            headers=self._get_headers()
        )
        return response.json()
    
    def get_email_accounts(self):
        """Get all email accounts"""
        response = requests.get(self._get_url("email-accounts"))
        return response.json()
    
    def add_email_accounts_to_campaign(self, campaign_id, email_account_ids):
        """Add email accounts to a campaign"""
        data = {"email_account_ids": email_account_ids}
        response = requests.post(
            self._get_url(f"campaigns/{campaign_id}/email-accounts"),
            data=json.dumps(data),
            headers=self._get_headers()
        )
        return response.json()
    
    def start_campaign(self, campaign_id):
        """Start a campaign"""
        data = {"status": "START"}
        response = requests.post(
            self._get_url(f"campaigns/{campaign_id}/status"),
            data=json.dumps(data),
            headers=self._get_headers()
        )
        return response.json()
    
    def pause_campaign(self, campaign_id):
        """Pause a campaign"""
        data = {"status": "PAUSE"}
        response = requests.post(
            self._get_url(f"campaigns/{campaign_id}/status"),
            data=json.dumps(data),
            headers=self._get_headers()
        )
        return response.json()
    
    def get_campaign_stats(self, campaign_id, max_age_minutes=30):
        """Get campaign statistics with caching"""
        # Check if we have recent stats cached
        campaign = Campaign.query.filter_by(smartlead_id=campaign_id).first()
        if campaign and campaign.smartlead_stats:
            # Check if stats have updated_at field and are recent enough
            stats = campaign.smartlead_stats
            if 'updated_at' in stats:
                last_update = datetime.datetime.fromisoformat(stats['updated_at'])
                age = datetime.datetime.utcnow() - last_update
                if age.total_seconds() < max_age_minutes * 60:
                    return stats  # Use cached stats
        
        # If we reach here, we need to fetch fresh stats
        try:
            response = requests.get(self._get_url(f"campaigns/{campaign_id}/stats"))
            # Check if response is successful and has content
            if response.status_code == 200 and response.text.strip():
                stats = response.json()
                # Add timestamp
                stats['updated_at'] = datetime.datetime.utcnow().isoformat()
                # Cache the result if we have a campaign
                if campaign:
                    campaign.smartlead_stats = stats
                    db.session.commit()
                return stats
            elif response.status_code != 200:
                print(f"API error for campaign {campaign_id}: Status code {response.status_code}")
                return {
                    "error": f"API returned status code {response.status_code}",
                    "total_leads": 0,
                    "total_email_sent": 0,
                    "total_opened": 0,
                    "total_replied": 0,
                    "updated_at": datetime.datetime.utcnow().isoformat()
                }
            else:
                print(f"Empty response for campaign {campaign_id}")
                return {
                    "error": "Empty response from API",
                    "total_leads": 0,
                    "total_email_sent": 0,
                    "total_opened": 0,
                    "total_replied": 0,
                    "updated_at": datetime.datetime.utcnow().isoformat()
                }
        except Exception as e:
            print(f"Exception getting stats for campaign {campaign_id}: {str(e)}")
            return {
                "error": str(e),
                "total_leads": 0,
                "total_email_sent": 0,
                "total_opened": 0,
                "total_replied": 0,
                "updated_at": datetime.datetime.utcnow().isoformat()
            }
    
    def create_advanced_sequence(self, campaign_id, sequence_data):
        """Create an advanced email sequence with conditional logic
        
        sequence_data should contain:
        - steps: list of sequence steps (emails)
        - conditions: rules for branching based on recipient behavior
        - branches: alternative paths in the sequence
        """
        response = requests.post(
            self._get_url(f"campaigns/{campaign_id}/advanced-sequences"),
            data=json.dumps(sequence_data),
            headers=self._get_headers()
        )
        return response.json()
    
    def get_sequence_conditions(self):
        """Get available condition types for email sequences"""
        response = requests.get(self._get_url("sequence-conditions"))
        return response.json()
    
    def create_sequence_step(self, campaign_id, step_data):
        """Create a single step in an email sequence"""
        response = requests.post(
            self._get_url(f"campaigns/{campaign_id}/sequence-steps"),
            data=json.dumps(step_data),
            headers=self._get_headers()
        )
        return response.json()
    
    def create_sequence_branch(self, campaign_id, branch_data):
        """Create a branch in an email sequence based on conditions"""
        response = requests.post(
            self._get_url(f"campaigns/{campaign_id}/sequence-branches"),
            data=json.dumps(branch_data),
            headers=self._get_headers()
        )
        return response.json()
    
    def get_campaign_sequence(self, campaign_id):
        """Get the full sequence with all steps and branches for a campaign"""
        response = requests.get(self._get_url(f"campaigns/{campaign_id}/sequence"))
        return response.json() 