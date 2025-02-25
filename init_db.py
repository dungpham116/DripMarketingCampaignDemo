from app import create_app, db
from app.models.user import User
from app.models.campaign import Campaign
from app.models.contact import Contact
from app.models.email_template import EmailTemplate, EmailSequence
from app.models.tracking import EmailTracking
import json

def backup_data():
    """Backup existing data"""
    data = {
        'campaigns': [],
        'contacts': [],
        'templates': [],
        'sequences': []
    }
    
    campaigns = Campaign.query.all()
    for c in campaigns:
        campaign_data = {
            'name': c.name,
            'description': c.description,
            'status': c.status,
            'smartlead_id': c.smartlead_id,
            'smartlead_stats_json': c.smartlead_stats_json
        }
        data['campaigns'].append(campaign_data)
    
    # Similar for other models...
    
    return data

def restore_data(data):
    """Restore data from backup"""
    for c_data in data['campaigns']:
        campaign = Campaign(**c_data)
        db.session.add(campaign)
    
    # Similar for other models...
    
    db.session.commit()

def init_db():
    """Initialize the database"""
    app = create_app()
    with app.app_context():
        # Backup existing data
        try:
            backup = backup_data()
        except Exception as e:
            print(f"Backup failed: {e}")
            backup = None
        
        # Recreate tables
        db.drop_all()
        db.create_all()
        
        # Restore data if backup exists
        if backup:
            try:
                restore_data(backup)
                print("Data restored successfully")
            except Exception as e:
                print(f"Restore failed: {e}")
        
        print("Database initialized successfully")

if __name__ == "__main__":
    init_db() 