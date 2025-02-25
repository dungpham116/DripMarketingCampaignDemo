from app import create_app, db
from app.models.campaign import Campaign

def cleanup_missing_campaigns():
    """Remove campaigns that return 404 from SmartLead"""
    app = create_app()
    with app.app_context():
        # Get all campaigns with SmartLead IDs
        campaigns = Campaign.query.filter(Campaign.smartlead_id.isnot(None)).all()
        
        print(f"Found {len(campaigns)} campaigns with SmartLead IDs")
        
        # Clean up campaigns based on your error messages
        problem_ids = [1495393, 1542316, 1541958, 1541976, 1542000, 
                      1542001, 1542682, 1501858, 1485611, 1543311, 1502660]
        
        for campaign in campaigns:
            if campaign.smartlead_id in problem_ids:
                print(f"Removing campaign: {campaign.name} (ID: {campaign.smartlead_id})")
                db.session.delete(campaign)
        
        db.session.commit()
        print("Cleanup complete")

if __name__ == "__main__":
    cleanup_missing_campaigns() 