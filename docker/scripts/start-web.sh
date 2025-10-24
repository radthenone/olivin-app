#!/bin/bash
set -o errexit
set -o pipefail
set -o nounset

echo "Starting Web frontend..."
docker-compose up olivin-frontend-web