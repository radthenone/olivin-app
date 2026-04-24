#!/bin/bash
set -o errexit
set -o pipefail
set -o nounset

BACKUP_DIR="/app/backups"
BACKUP_FILE="${BACKUP_DIR}/auto_backup.dump"
TEMP_BACKUP_FILE="${BACKUP_DIR}/auto_backup.tmp.dump"
SLEEP_SECONDS=86400 # 24 godziny

mkdir -p "$BACKUP_DIR"

echo "⏲️ Periodic backup loop started (every ${SLEEP_SECONDS}s)"

while true; do
    echo "💾 Creating automatic backup candidate: ${TEMP_BACKUP_FILE}..."
    
    # Używamy zmiennych środowiskowych Django do połączenia z bazą
    PGPASSWORD="${POSTGRES_PASSWORD}" pg_dump \
        -h "${POSTGRES_HOST}" \
        -U "${POSTGRES_USER}" \
        -d "${POSTGRES_DB}" \
        -Fc -f "$TEMP_BACKUP_FILE"

    if [ -f "$BACKUP_FILE" ]; then
        CURRENT_SIZE=$(wc -c < "$BACKUP_FILE")
        NEW_SIZE=$(wc -c < "$TEMP_BACKUP_FILE")

        if [ "$NEW_SIZE" -gt "$CURRENT_SIZE" ]; then
            mv -f "$TEMP_BACKUP_FILE" "$BACKUP_FILE"
            echo "✅ Backup updated (new file is larger: ${NEW_SIZE}B > ${CURRENT_SIZE}B)."
        else
            rm -f "$TEMP_BACKUP_FILE"
            echo "ℹ️ Backup not updated (new file is not larger: ${NEW_SIZE}B <= ${CURRENT_SIZE}B)."
        fi
    else
        mv -f "$TEMP_BACKUP_FILE" "$BACKUP_FILE"
        echo "✅ Initial backup created: ${BACKUP_FILE}."
    fi
    
    sleep "$SLEEP_SECONDS"
done
