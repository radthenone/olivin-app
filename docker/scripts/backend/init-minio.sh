#!/bin/bash
set -o errexit
set -o pipefail
set -o nounset

echo "🪣 Setting up MinIO buckets..."

python << END
import sys
import os

sys.path.insert(0, "/app/src")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

from core.storage.utils import sync_buckets

result = sync_buckets()

if result.created:
    print(f"✅ Utworzono buckety: {', '.join(result.created)}")
if result.updated:
    print(f"✅ Odświeżono polityki bucketów: {', '.join(result.updated)}")

result.exit_on_failure()
END
