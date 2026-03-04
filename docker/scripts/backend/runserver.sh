#!/bin/bash
set -o errexit
set -o pipefail
set -o nounset

echo "🚀 Starting Django server..."
python manage.py runserver "${DJANGO_HOST:-0.0.0.0}:${DJANGO_PORT:-8000}"
