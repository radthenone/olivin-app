#!/bin/bash
set -o errexit
set -o pipefail
set -o nounset

VERBOSE=${VERBOSE:-false}

if [ "$VERBOSE" = "true" ]; then
    echo "🐍 Python path: $(which python)"
    python -c "import django; print('Django version:', django.__version__)" || echo "Django not found!"
fi

/wait-for/db.sh
/wait-for/redis.sh
/wait-for/s3.sh

/scripts/init-minio.sh

if [ "${DJANGO_ENVIRONMENT:-development}" == "development" ]; then
    mkdir -p static staticfiles mediafiles

    echo "📊 Running migrations..."
    python manage.py migrate --noinput 2>&1 | grep -v "No migrations to apply" || true

    /scripts/check_superuser.sh

    echo "📁 Collecting static files..."
    python manage.py collectstatic --noinput > /dev/null 2>&1 || true
fi

echo "🎉 Starting Django server..."
/scripts/runserver.sh