#!/bin/bash
set -o errexit
set -o pipefail
set -o nounset

# Default values
REDIS_HOST=${REDIS_HOST:-"olivin-redis"}
REDIS_PORT=${REDIS_PORT:-"6379"}
TIMEOUT=${REDIS_TIMEOUT:-30}

redis_ready() {
    python << END
import sys
import redis
from redis.exceptions import ConnectionError, TimeoutError

try:
    r = redis.Redis(host="${REDIS_HOST}", port=${REDIS_PORT}, decode_responses=True)
    r.ping()
    sys.exit(0)
except (ConnectionError, TimeoutError, Exception):
    sys.exit(1)
END
}

echo "⏳ Waiting for Redis..."
start_time=$(date +%s)

until redis_ready; do
    current_time=$(date +%s)
    elapsed_time=$((current_time - start_time))

    if [ $elapsed_time -gt $TIMEOUT ]; then
        echo "❌ Redis not available after ${TIMEOUT} seconds"
        exit 1
    fi

    sleep 1
done

echo "✅ Redis ready"