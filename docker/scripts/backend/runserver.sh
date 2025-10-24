#!/bin/bash
set -o errexit
set -o pipefail
set -o nounset

echo "🚀 Starting Django server..."
python manage.py runserver "${DJANGO_HOST}":"${DJANGO_PORT}"