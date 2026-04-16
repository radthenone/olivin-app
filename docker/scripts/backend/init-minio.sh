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

result = sync_buckets("${S3_BUCKETS_NAMES}")

if result.created:
    print(f"✅ Utworzono buckety: {', '.join(result.created)}")
if result.deleted:
    print(f"🗑️  Usunięto buckety: {', '.join(result.deleted)}")
if result.success and not result.created and not result.deleted:
    print("✅ Wszystkie buckety są aktualne, brak zmian.")

result.exit_on_failure()
END
