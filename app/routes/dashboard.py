from flask import Blueprint, render_template
from flask_login import login_required
from app.models.campaign import Campaign
from app.models.contact import Contact
from sqlalchemy import func
from app import db

bp = Blueprint('dashboard', __name__)

@bp.route('/')
@login_required
def index():
    # Get campaign statistics
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
    
    # Get recent campaigns
    recent_campaigns = Campaign.query.order_by(Campaign.created_at.desc()).limit(5).all()
    
    return render_template('dashboard/index.html',
                         total_campaigns=total_campaigns,
                         active_campaigns=active_campaigns,
                         total_contacts=total_contacts,
                         stats=stats,
                         recent_campaigns=recent_campaigns) 