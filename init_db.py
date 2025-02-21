from app import create_app, db
from app.models.user import User
from app.models.campaign import Campaign
from app.models.contact import Contact
from app.models.email_template import EmailTemplate, EmailSequence
from app.models.tracking import EmailTracking

def init_db():
    app = create_app()
    with app.app_context():
        # Drop all existing tables
        db.drop_all()
        # Create all tables with new schema
        db.create_all()
        print("Database tables created successfully!")

if __name__ == '__main__':
    init_db() 