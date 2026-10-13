#!/bin/bash
set -o errexit
set -o pipefail
set -o nounset

# Gotowość dowolnego magazynu S3 (w dev i teście SeaweedFS z olivin-s3).
# Bez zgadywania dostawcy: adres i ścieżka zdrowia wyłącznie z envu.
S3_HOST=${S3_HOST:-"olivin-s3"}
S3_PORT=${S3_PORT:-"8333"}
S3_URL=${S3_URL:-"http://${S3_HOST}:${S3_PORT}"}
S3_TIMEOUT=${S3_TIMEOUT:-60}
S3_HEALTH_PATH=${S3_HEALTH_PATH:-"/healthz"}

if ! [[ "${S3_TIMEOUT}" =~ ^[0-9]+$ ]]; then
    S3_TIMEOUT=60
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
