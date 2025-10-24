#!/bin/bash
set -o errexit
set -o pipefail
set -o nounset

# wait for redis
echo "Checking Redis connection..."
/wait-for/redis.sh

echo "Starting Celery worker..."
# logs exists
mkdir -p logs

# run celery worker
exec celery -A core.celery worker -l info