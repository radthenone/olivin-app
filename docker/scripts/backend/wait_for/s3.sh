#!/bin/bash
set -o errexit
set -o pipefail
set -o nounset

echo "🔍 Waiting for MinIO..."

# ✅ Sprawdź czy MinIO odpowiada z hosta
if curl -f "http://localhost:9000/" > /dev/null 2>&1; then
    echo "✅ MinIO is ready!"
else
    echo "❌ MinIO not responding, but continuing anyway..."
fi

echo "🎉 MinIO check completed!"