from app import create_app, db
from app.models.campaign import Campaign
from app.smartlead_api import SmartleadAPI

def resync_campaigns():
    """Resync local campaigns with SmartLead"""
    app = create_app()
    with app.app_context():
        smartlead = SmartleadAPI()
        
        try:
            # Get campaigns from SmartLead
            print("Fetching campaigns from SmartLead...")
            smartlead_campaigns = smartlead.get_campaigns()
            print(f"Found {len(smartlead_campaigns)} campaigns in SmartLead")
            
            # Get local campaigns
            local_campaigns = Campaign.query.all()
            print(f"Found {len(local_campaigns)} campaigns in local database")
            
            # Get SmartLead campaign IDs
            smartlead_ids = [c['id'] for c in smartlead_campaigns]
            
            # Remove local campaigns that don't exist in SmartLead
            for campaign in local_campaigns:
                if campaign.smartlead_id and campaign.smartlead_id not in smartlead_ids:
                    print(f"Removing campaign: {campaign.name} (ID: {campaign.smartlead_id})")
                    db.session.delete(campaign)
            
            # Add missing SmartLead campaigns to local database
            for sl_campaign in smartlead_campaigns:
                campaign = Campaign.query.filter_by(smartlead_id=sl_campaign['id']).first()
                if not campaign:
                    print(f"Adding campaign: {sl_campaign['name']} (ID: {sl_campaign['id']})")
                    campaign = Campaign(
                        name=sl_campaign['name'],
                        smartlead_id=sl_campaign['id'], 
                        status=sl_campaign['status'].lower()
                    )
                    db.session.add(campaign)
            
            db.session.commit()
            print("Resync complete")
            
        except Exception as e:
            print(f"Error during resync: {str(e)}")

if __name__ == "__main__":
    resync_campaigns() 