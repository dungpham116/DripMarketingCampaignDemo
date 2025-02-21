from app import db
from datetime import datetime

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    email = db.Column(db.String(120), unique=True, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, sent, seen, responded
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_email_sent = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<Contact {self.email}>' 