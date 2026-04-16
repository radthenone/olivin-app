#!/bin/bash
set -o errexit
set -o pipefail
set -o nounset

# Default values
S3_PROVIDER=${S3_PROVIDER:-""}
S3_HOST=${S3_HOST:-"olivin-minio"}
S3_PORT=${S3_PORT:-"9000"}
S3_URL=${S3_URL:-"http://${S3_HOST}:${S3_PORT}"}
S3_TIMEOUT=${S3_TIMEOUT:-60}

if [ -z "${S3_PROVIDER}" ] && [ "${S3_HOST}" = "olivin-minio" ]; then
    S3_PROVIDER=minio
fi

if ! [[ "${S3_TIMEOUT}" =~ ^[0-9]+$ ]]; then
    S3_TIMEOUT=60
fi

if [ "${S3_PROVIDER}" = "minio" ]; then
    S3_HEALTH_PATH=${S3_HEALTH_PATH:-"/minio/health/live"}
else
    S3_HEALTH_PATH=${S3_HEALTH_PATH:-"/"}
fi

echo "⏳ Waiting for S3..."

start_time=$SECONDS
while true; do
    if curl -fsS "${S3_URL}${S3_HEALTH_PATH}" > /dev/null 2>&1; then
        echo "✅ S3 ready"
        break
    fi

    if [ $((SECONDS - start_time)) -ge "${S3_TIMEOUT}" ]; then
        echo "⚠️  S3 not responding, continuing anyway..."
        break
    fi

    sleep 1
done
