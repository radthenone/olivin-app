#!/bin/bash
set -o errexit
set -o pipefail
set -o nounset

echo "Starting all services..."
docker-compose up