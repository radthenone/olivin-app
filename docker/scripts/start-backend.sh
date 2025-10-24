#!/bin/bash
set -o errexit
set -o pipefail
set -o nounset

echo "Starting backend services..."
docker-compose up olivin-django olivin-postgres olivin-redis olivin-minio olivin-mailhog