#!/bin/bash
set -o errexit
set -o pipefail
set -o nounset

# Default values
POSTGRES_HOST=${POSTGRES_HOST:-"olivin-postgres"}
POSTGRES_PORT=${POSTGRES_PORT:-"5432"}
POSTGRES_DB=${POSTGRES_DB:-"olivin_db"}
POSTGRES_USER=${POSTGRES_USER:-"postgres"}
TIMEOUT=${DB_TIMEOUT:-30}

db_ready() {
    python << END
import sys
import psycopg2
from psycopg2 import OperationalError

try:
    conn = psycopg2.connect(
        host="${POSTGRES_HOST}",
        port="${POSTGRES_PORT}",
        database="${POSTGRES_DB}",
        user="${POSTGRES_USER}",
        password="${POSTGRES_PASSWORD}"
    )
    conn.close()
    print("✅ Database is ready!")
    sys.exit(0)
except OperationalError as e:
    sys.stderr.write(f"❌ Database not ready: {e}\n")
    sys.exit(1)
except Exception as e:
    sys.stderr.write(f"❌ Database error: {e}\n")
    sys.exit(1)
END
}

echo "🔍 Waiting for PostgreSQL at ${POSTGRES_HOST}:${POSTGRES_PORT}..."
start_time=$(date +%s)

until db_ready; do
    current_time=$(date +%s)
    elapsed_time=$((current_time - start_time))

    if [ $elapsed_time -gt $TIMEOUT ]; then
        echo "❌ Database not available after ${TIMEOUT} seconds"
        exit 1
    fi

    echo "⏳ Waiting for database... (${elapsed_time}s/${TIMEOUT}s)"
    sleep 1
done

echo "🎉 Database is ready!"