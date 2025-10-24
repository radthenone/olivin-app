#!/bin/bash
set -o errexit
set -o pipefail
set -o nounset

echo "Starting iOS frontend..."
docker-compose up olivin-frontend-ios