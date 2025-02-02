#!/bin/bash
cd /var/app/current
nohup celery -A app.celery worker --loglevel=info > /var/log/celery_worker.log 2>&1 &
