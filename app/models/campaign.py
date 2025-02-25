from app import db
from datetime import datetime
import json

class Campaign(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='draft')  # draft, active, paused, completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # SmartLead information
    smartlead_id = db.Column(db.Integer, unique=True)
    smartlead_stats_json = db.Column(db.Text)  # Store stats as JSON
    
    # Relationships
    contacts = db.relationship('Contact', backref='campaign', lazy=True)
    email_sequences = db.relationship('EmailSequence', backref='campaign', lazy=True)

    # Add this to the Campaign model class
    branch_data_json = db.Column(db.Text)  # Store branch data as JSON

    @property
    def smartlead_stats(self):
        if self.smartlead_stats_json:
            return json.loads(self.smartlead_stats_json)
        return {}
        
    @smartlead_stats.setter
    def smartlead_stats(self, stats):
        self.smartlead_stats_json = json.dumps(stats)

    @property
    def branch_data(self):
        if self.branch_data_json:
            return json.loads(self.branch_data_json)
        return []
    
    @branch_data.setter
    def branch_data(self, data):
        self.branch_data_json = json.dumps(data)

    def __repr__(self):
        return f'<Campaign {self.name}>' 