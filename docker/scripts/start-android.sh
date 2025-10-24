#!/bin/bash
set -o errexit
set -o pipefail
set -o nounset

echo "Starting Android frontend..."
docker-compose up olivin-frontend-android