#!/bin/bash
cd /var/app/current
nohup celery -A app.celery beat --loglevel=info > /var/log/celery_beat.log 2>&1 &
