#!/bin/sh
# Entrypoint kontenera olivin-s3 (SeaweedFS, issue #303).
#
# Generuje /etc/seaweedfs/s3.json z AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY
# i startuje `weed server` (master + volume + filer + bramka S3) oraz w tle
# `weed admin` (UI). Brak credentiali = kontener nie startuje, a nie otwarty
# magazyn. Plik s3.json nie trafia do repo — powstaje tu, przy starcie.
set -eu

if [ -z "${AWS_ACCESS_KEY_ID:-}" ] || [ -z "${AWS_SECRET_ACCESS_KEY:-}" ]; then
    echo "❌ olivin-s3: brak credentiali — ustaw AWS_ACCESS_KEY_ID i AWS_SECRET_ACCESS_KEY." >&2
    echo "❌ Bez nich magazyn nie startuje (odmowa startu zamiast otwartego magazynu)." >&2
    exit 1
fi

mkdir -p /etc/seaweedfs
# Minimalny escape do JSON (klucze S3 to zwykle tekst bez cudzysłowów).
ACCESS_KEY_ESCAPED=$(printf '%s' "$AWS_ACCESS_KEY_ID" | sed 's/\\/\\\\/g; s/"/\\"/g')
SECRET_ESCAPED=$(printf '%s' "$AWS_SECRET_ACCESS_KEY" | sed 's/\\/\\\\/g; s/"/\\"/g')
cat > /etc/seaweedfs/s3.json <<EOF
{"identities":[{"name":"admin","credentials":[{"accessKey":"$ACCESS_KEY_ESCAPED","secretKey":"$SECRET_ESCAPED"}],"actions":["Admin","Read","Write","List","Tagging"]}]}
EOF
chmod 600 /etc/seaweedfs/s3.json
echo "🔑 Zapisano /etc/seaweedfs/s3.json (uprawnienia 600)."

# UI: w dev nasłuch na wszystkich interfejsach (port publikowany przez
# compose), na prod tylko loopback (tunel SSH) — steruje S3_ADMIN_IP.
ADMIN_IP=${S3_ADMIN_IP:-0.0.0.0}
ADMIN_ARGS="-master=localhost:9333 -port=23646 -ip=$ADMIN_IP -dataDir=/data/admin"
case "$ADMIN_IP" in
    127.0.0.1 | localhost) ;;
    *) ADMIN_ARGS="$ADMIN_ARGS -allowInsecureBind" ;;
esac
# shellcheck disable=SC2086
weed admin $ADMIN_ARGS &
echo "🖥️  weed admin na $ADMIN_IP:23646 (w tle)."

exec weed server -dir=/data -ip.bind=0.0.0.0 -master.port=9333 -volume.port=8080 -master.telemetry=false -volume.max=100 -filer -filer.port=8888 -s3 -s3.port=8333 -s3.config=/etc/seaweedfs/s3.json
