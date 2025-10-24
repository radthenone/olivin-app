#!/bin/bash
set -o errexit
set -o pipefail
set -o nounset

echo "🐍 Python path: $(which python)"
python -c "import django; print('Django version:', django.__version__)" || echo "Django not found!"

echo "⏳ Waiting for PostgreSQL..."
/wait-for/db.sh

echo "⏳ Waiting for Redis..."
/wait-for/redis.sh

echo "⏳ Waiting for MinIO..."
/wait-for/s3.sh

echo "🪣 Setting up MinIO buckets..."
/scripts/init-minio.sh

if [ "${DJANGO_ENVIRONMENT:-development}" == "development" ]; then
    echo "🔧 Development mode..."
    mkdir -p static staticfiles mediafiles

    echo "📊 Running migrations..."
    python manage.py migrate --noinput

    echo "👤 Creating superuser..."
    /scripts/check_superuser.sh

    echo "📁 Collecting static files..."
    python manage.py collectstatic --noinput
fi

echo "🎉 Starting Django server..."
/scripts/runserver.sh