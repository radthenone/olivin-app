#!/usr/bin/env bash
set -o errexit
set -o pipefail
set -o nounset

# Usage: ./scripts/open-expo-dev-client-android.sh [ADB_SERIAL]
# Otwiera aktualny Expo LAN bundle w development buildzie na konkretnym
# urządzeniu ADB. To nie jest Expo Go.

# shellcheck disable=SC1091
source ./scripts/load_env.sh
# shellcheck disable=SC1091
source ./scripts/wait_for_metro.sh

serial="${1:-${ANDROID_SERIAL:-emulator-5554}}"
load_env_file ".envs/dev/expo.env"

host="${EXPO_PUBLIC_EXPO_HOST:-}"
port="${EXPO_PUBLIC_EXPO_PORT:-8081}"
wait_host="${host:-127.0.0.1}"

if [ -z "$host" ]; then
    android_url="${EXPO_PUBLIC_ANDROID_URL:-${EXPO_PUBLIC_EMULATOR_URL:-10.0.2.2:8020}}"
    android_url="${android_url#http://}"
    android_url="${android_url#https://}"
    host="${android_url%%:*}"
fi

wait_for_metro "$wait_host" "$port"

device_host="$host"

adb -s "$serial" reverse --remove "tcp:${port}" >/dev/null 2>&1 || true

if adb -s "$serial" reverse "tcp:${port}" "tcp:${port}" >/dev/null 2>&1; then
    device_host="127.0.0.1"
    echo "ADB reverse aktywne: urządzenie użyje ${device_host}:${port} dla Metro."
else
    echo "ADB reverse niedostępne, używam adresu LAN: ${device_host}:${port}."
fi

bundle_url="http://${device_host}:${port}"
encoded_bundle_url="${bundle_url//:/%3A}"
encoded_bundle_url="${encoded_bundle_url//\//%2F}"
url="exp+frontend://expo-development-client/?url=${encoded_bundle_url}"

echo "Resetuję dev client na urządzeniu ${serial}..."
adb -s "$serial" shell am force-stop com.olivin.frontend >/dev/null 2>&1 || true

echo "Otwieram dev client na urządzeniu ${serial}: ${url}"
adb -s "$serial" shell am start -W -a android.intent.action.VIEW -d "$url" >/dev/null
