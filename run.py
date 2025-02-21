from app import create_app
from celery.schedules import crontab
from app.tasks import celery

app = create_app()

# Configure Celery beat schedule to run every 30 seconds
celery.conf.beat_schedule = {
    'check-and-send-emails': {
        'task': 'app.tasks.send_campaign_emails',
        'schedule': 30.0  # Run every 30 seconds
    }
}

if __name__ == '__main__':
    app.run(debug=True) 