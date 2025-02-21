from app import db
from datetime import datetime

class EmailTracking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    contact_id = db.Column(db.Integer, db.ForeignKey('contact.id'), nullable=False)
    email_sequence_id = db.Column(db.Integer, db.ForeignKey('email_sequence.id'), nullable=False)
    opened_at = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(200))
    
    contact = db.relationship('Contact', backref='tracking_events')
    email_sequence = db.relationship('EmailSequence') 