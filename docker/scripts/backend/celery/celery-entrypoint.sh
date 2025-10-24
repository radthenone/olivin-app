#!/bin/bash
set -o errexit
set -o pipefail
set -o nounset

echo "Python path: $(which python)"
python -c "import django; print('Django version:', django.__version__)"

echo "Waiting for PostgreSQL..."
/wait-for/db.sh

echo "Waiting for Redis..."
/wait-for/redis.sh

if [ "${ENVIRONMENT:-development}" == "development" ]; then
    echo "Running migrations..."
    python manage.py migrate --noinput
fi

mkdir -p logs
exec "$@"