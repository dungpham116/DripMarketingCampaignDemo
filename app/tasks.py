from celery import Celery
from flask_mail import Message
from app import mail, create_app, db
from app.models.contact import Contact
from app.models.campaign import Campaign
from app.models.email_template import EmailSequence
from datetime import datetime, timedelta
from itsdangerous import URLSafeSerializer
from flask import url_for

app = create_app()
celery = Celery('tasks', 
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0'
)

# Configure Celery
celery.conf.update(
    enable_utc=True,
    timezone='UTC',
    beat_schedule={
        'check-and-send-emails': {
            'task': 'app.tasks.send_campaign_emails',
            'schedule': 30.0,  # Run every 30 seconds
        }
    }
)

def render_template(template_text, contact):
    """Replace placeholders in template with contact details"""
    return template_text.replace(
        '{{first_name}}', contact.first_name
    ).replace(
        '{{last_name}}', contact.last_name
    )

def generate_tracking_token(contact_id, sequence_id):
    s = URLSafeSerializer(app.config['SECRET_KEY'])
    return s.dumps([contact_id, sequence_id])

@celery.task
def send_campaign_emails():
    with app.app_context():
        print("\n=== Starting email check ===")
        now = datetime.utcnow()
        print(f"Current time UTC: {now}")
        
        # Get active campaigns
        campaigns = Campaign.query.filter_by(status='active').all()
        print(f"Found {len(campaigns)} active campaigns")
        
        for campaign in campaigns:
            print(f"\nProcessing campaign: {campaign.name} (ID: {campaign.id})")
            
            # Get pending contacts
            contacts = Contact.query.filter_by(
                campaign_id=campaign.id,
                status='pending'  # Only get pending contacts
            ).all()
            print(f"Found {len(contacts)} pending contacts")
            
            for contact in contacts:
                print(f"\nProcessing contact: {contact.email}")
                print(f"Contact created at: {contact.created_at}")
                
                sequences = EmailSequence.query.filter_by(
                    campaign_id=campaign.id
                ).order_by(EmailSequence.sequence_order).all()
                
                for sequence in sequences:
                    print(f"\nChecking sequence {sequence.sequence_order}")
                    print(f"Delay: {sequence.delay_days}d {sequence.delay_hours}h {sequence.delay_minutes}m")
                    
                    # Calculate send time
                    delay = timedelta(
                        days=sequence.delay_days,
                        hours=sequence.delay_hours,
                        minutes=sequence.delay_minutes
                    )
                    send_time = contact.created_at + delay
                    
                    print(f"Contact created at: {contact.created_at}")
                    print(f"Delay: {delay}")
                    print(f"Send time: {send_time}")
                    print(f"Current time: {now}")
                    print(f"Time until send: {send_time - now}")
                    print(f"Should send: {now >= send_time}")
                    
                    if now >= send_time:
                        try:
                            print(f"Attempting to send email to {contact.email}")
                            msg = Message(
                                subject=render_template(sequence.template.subject, contact),
                                sender=app.config['MAIL_USERNAME'],
                                recipients=[contact.email]
                            )
                            msg.html = render_template(sequence.template.body, contact)
                            
                            mail.send(msg)
                            print("Email sent successfully!")
                            
                            # Update contact status
                            contact.status = 'sent'
                            contact.last_email_sent = now
                            db.session.commit()
                            print("Contact status updated")
                            return  # Exit after sending one email
                            
                        except Exception as e:
                            print(f"Error sending email: {str(e)}")
                            print(f"Full error: {e.__class__.__name__}")
                            import traceback
                            print(traceback.format_exc())

@celery.task
def send_email(contact_id, subject, body, sequence_id):
    """Send an email to a specific contact"""
    with app.app_context():
        try:
            contact = Contact.query.get(contact_id)
            if not contact:
                print(f"Contact {contact_id} not found")  # Debug log
                return
            
            # Generate tracking token
            tracking_token = generate_tracking_token(contact_id, sequence_id)
            tracking_pixel = f'<img src="{url_for("tracking.track_open", token=tracking_token, _external=True)}" width="1" height="1" />'
            
            # Render the template with contact details
            rendered_body = render_template(body, contact) + tracking_pixel
            rendered_subject = render_template(subject, contact)
            
            msg = Message(
                rendered_subject,
                sender=app.config['MAIL_USERNAME'],
                recipients=[contact.email]
            )
            msg.html = rendered_body
            
            mail.send(msg)
            print(f"Email sent successfully to {contact.email}")  # Debug log
            
            # Update contact status
            contact.last_email_sent = datetime.utcnow()
            contact.status = 'sent'
            db.session.commit()
            
        except Exception as e:
            print(f"Error sending email to {contact.email}: {str(e)}")  # Debug log 