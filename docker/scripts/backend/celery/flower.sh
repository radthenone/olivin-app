#!/bin/bash
set -o errexit
set -o pipefail
set -o nounset

# Function to check if Celery workers are ready
worker_ready() {
    celery -A core.celery inspect ping
}

# Wait until workers are available
until worker_ready; do
    >&2 echo 'Celery workers not available'
    sleep 1
done
>&2 echo 'Celery workers is available'

echo "========== STARTING CELERY FLOWER =========="

# Wait for other services to be fully operational
sleep 5

# Start Flower - Web-based tool for monitoring and administrating Celery clusters
exec celery \
    -A core.celery \
    -b "${CELERY_BROKER_URL}" \
    flower \
    --basic_auth="${CELERY_FLOWER_USER}:${CELERY_FLOWER_PASSWORD}"