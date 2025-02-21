from celery.apps.beat import Beat
from app.tasks import celery

if __name__ == '__main__':
    beat = Beat(
        app=celery,
        loglevel='INFO'
    )
    beat.run() 