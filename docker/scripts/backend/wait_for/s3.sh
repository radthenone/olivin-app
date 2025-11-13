#!/bin/bash
set -o errexit
set -o pipefail
set -o nounset

echo "⏳ Waiting for MinIO..."

if curl -f "http://localhost:9000/" > /dev/null 2>&1; then
    echo "✅ MinIO ready"
else
    echo "⚠️  MinIO not responding, continuing anyway..."
fi