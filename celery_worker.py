from app.tasks import celery

if __name__ == '__main__':
    argv = [
        'worker',
        '--loglevel=info',
        '--pool=solo'
    ]
    celery.worker_main(argv) 