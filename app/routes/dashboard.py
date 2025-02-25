from flask import Blueprint, render_template, flash
from flask_login import login_required
from app.models.campaign import Campaign
from app.models.contact import Contact
from sqlalchemy import func
from app import db
from app.smartlead_api import SmartleadAPI

bp = Blueprint('dashboard', __name__)
smartlead = SmartleadAPI()

@bp.route('/')
@login_required
def index():
    # Initialize stats
    total_campaigns = 0
    active_campaigns = 0
    total_contacts = 0
    stats = {'pending': 0, 'sent': 0, 'seen': 0, 'responded': 0}
    
    # Try to get data from SmartLead API
    try:
        # Sync campaigns from SmartLead
        smartlead_campaigns = smartlead.get_campaigns()
        
        # Update local database with SmartLead campaigns
        for sl_campaign in smartlead_campaigns:
            campaign = Campaign.query.filter_by(smartlead_id=sl_campaign['id']).first()
            if not campaign:
                campaign = Campaign(
                    name=sl_campaign['name'],
                    smartlead_id=sl_campaign['id'], 
                    status=sl_campaign['status'].lower()
                )
                db.session.add(campaign)
                
        db.session.commit()
        
        # Count campaigns
        total_campaigns = len(smartlead_campaigns)
        active_campaigns = sum(1 for c in smartlead_campaigns if c['status'] == 'ACTIVE')
        
        # Get contact statistics from SmartLead campaigns
        for sl_campaign in smartlead_campaigns:
            try:
                campaign_stats = smartlead.get_campaign_stats(sl_campaign['id'])
                if campaign_stats and 'error' not in campaign_stats:
                    total_contacts += campaign_stats.get('total_leads', 0)
                    stats['sent'] += campaign_stats.get('total_email_sent', 0)
                    stats['seen'] += campaign_stats.get('total_opened', 0)
                    stats['responded'] += campaign_stats.get('total_replied', 0)
                    
                    # Store stats in local campaign
                    campaign = Campaign.query.filter_by(smartlead_id=sl_campaign['id']).first()
                    if campaign:
                        campaign.smartlead_stats = campaign_stats
                        db.session.commit()
                else:
                    print(f"Skipping invalid stats for campaign {sl_campaign['id']}")
            except Exception as e:
                print(f"Error getting stats for campaign {sl_campaign['id']}: {str(e)}")
                
        # Calculate pending
        stats['pending'] = total_contacts - stats['sent']
        
    except Exception as e:
        flash(f"Could not connect to SmartLead API: {str(e)}", "warning")
        # Fallback to local database if API fails
        campaigns = Campaign.query.all()
        total_campaigns = len(campaigns)
        active_campaigns = Campaign.query.filter_by(status='active').count()
        
        # Get contact statistics
        total_contacts = Contact.query.count()
        contact_stats = db.session.query(
            Contact.status,
            func.count(Contact.id)
        ).group_by(Contact.status).all()
        
        stats = {status: count for status, count in contact_stats}
    
    # Get recent campaigns from local database
    recent_campaigns = Campaign.query.order_by(Campaign.created_at.desc()).limit(5).all()
    
    return render_template('dashboard/index.html',
                         total_campaigns=total_campaigns,
                         active_campaigns=active_campaigns,
                         total_contacts=total_contacts,
                         stats=stats,
                         recent_campaigns=recent_campaigns) 