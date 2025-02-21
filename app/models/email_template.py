from app import db
from datetime import datetime

class EmailTemplate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<EmailTemplate {self.name}>'

class EmailSequence(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=False)
    template_id = db.Column(db.Integer, db.ForeignKey('email_template.id'), nullable=False)
    delay_days = db.Column(db.Integer, default=0)
    delay_hours = db.Column(db.Integer, default=0)
    delay_minutes = db.Column(db.Integer, default=0)
    sequence_order = db.Column(db.Integer, nullable=False)
    
    template = db.relationship('EmailTemplate')

    def __repr__(self):
        return f'<EmailSequence {self.sequence_order}>' 