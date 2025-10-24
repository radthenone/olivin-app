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
    print("✅ Redis is ready!")
    sys.exit(0)
except ConnectionError as e:
    sys.stderr.write(f"❌ Cannot connect to Redis at ${REDIS_HOST}:${REDIS_PORT}: {e}\n")
    sys.exit(1)
except TimeoutError as e:
    sys.stderr.write(f"❌ Redis connection timeout: {e}\n")
    sys.exit(1)
except Exception as e:
    sys.stderr.write(f"❌ Redis error: {e}\n")
    sys.exit(1)
END
}

echo "🔍 Waiting for Redis at ${REDIS_HOST}:${REDIS_PORT}..."
start_time=$(date +%s)

until redis_ready; do
    current_time=$(date +%s)
    elapsed_time=$((current_time - start_time))

    if [ $elapsed_time -gt $TIMEOUT ]; then
        echo "❌ Redis not available after ${TIMEOUT} seconds"
        exit 1
    fi

    echo "⏳ Waiting for Redis... (${elapsed_time}s/${TIMEOUT}s)"
    sleep 1
done

echo "🎉 Redis is ready!"