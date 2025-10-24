#!/bin/bash
set -o errexit
set -o pipefail
set -o nounset

# wait for redis
until celery -A core.celery inspect ping; do
    >&2 echo "Redis is unavailable - waiting"
    sleep 1
done

# rm old PID
rm -f './celerybeat.pid'

# run celery beat
exec celery -A core.celery beat \
    --loglevel=info \
    --scheduler="django_celery_beat.schedulers:DatabaseScheduler"