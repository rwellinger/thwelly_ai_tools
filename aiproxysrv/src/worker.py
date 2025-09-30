"""
Celery Worker Starter
"""
from celery_app import celery_app

if __name__ == '__main__':
    # Worker kann direkt gestartet werden mit:
    # python worker.py
    celery_app.start()
