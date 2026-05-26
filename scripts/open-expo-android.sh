#!/usr/bin/env bash
set -o errexit
set -o pipefail
set -o nounset

# Usage: ./scripts/open-expo-android.sh [ADB_SERIAL]
# Otwiera aktualny Expo LAN bundle na konkretnym urządzeniu ADB.
# Jeśli Metro jeszcze startuje, czeka aż endpoint /status odpowie poprawnie.

# shellcheck disable=SC1091
source ./scripts/load_env.sh
# shellcheck disable=SC1091
source ./scripts/wait_for_metro.sh

serial="${1:-${ANDROID_SERIAL:-emulator-5554}}"
load_env_file ".envs/dev/expo.env"

host="${EXPO_PUBLIC_EXPO_HOST:-}"
port="${EXPO_PUBLIC_EXPO_PORT:-8081}"

if [ -z "$host" ]; then
    android_url="${EXPO_PUBLIC_ANDROID_URL:-${EXPO_PUBLIC_EMULATOR_URL:-10.0.2.2:8020}}"
    android_url="${android_url#http://}"
    android_url="${android_url#https://}"
    host="${android_url%%:*}"
fi

wait_for_metro "$host" "$port"

url="exp://${host}:${port}"

echo "Resetuję Expo Go na urządzeniu ${serial}..."
adb -s "$serial" shell am force-stop host.exp.exponent >/dev/null 2>&1 || true

echo "Otwieram Expo na urządzeniu ${serial}: ${url}"
adb -s "$serial" shell am start -W -a android.intent.action.VIEW -d "$url" >/dev/null
