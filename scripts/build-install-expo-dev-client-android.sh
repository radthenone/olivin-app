#!/usr/bin/env bash
set -o errexit
set -o pipefail
set -o nounset

# Usage: ./scripts/build-install-expo-dev-client-android.sh [ADB_SERIAL]
# Buduje development clienta dla ABI konkretnego urządzenia ADB i instaluje APK.

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
frontend_dir="${repo_root}/frontend"
serial="${1:-${ANDROID_SERIAL:-emulator-5554}}"
package_name="com.olivin.frontend"

if ! adb -s "$serial" get-state >/dev/null 2>&1; then
    echo "Nie widzę urządzenia ADB: ${serial}"
    echo "Dostępne urządzenia:"
    adb devices
    exit 1
fi

abi="$(adb -s "$serial" shell getprop ro.product.cpu.abi | tr -d '\r')"

if [ -z "$abi" ]; then
    echo "Nie udało się odczytać ABI z urządzenia ${serial}."
    exit 1
fi

echo "Buduję dev client dla ${serial} (${abi})..."

cd "${frontend_dir}/android"

if [ -x "./gradlew" ]; then
    gradle_cmd=(./gradlew)
elif [ -f "./gradlew.bat" ]; then
    gradle_cmd=(cmd.exe /c gradlew.bat)
else
    echo "Brakuje gradlew lub gradlew.bat w frontend/android. Uruchom najpierw prebuild dev clienta."
    exit 1
fi

NODE_ENV="${NODE_ENV:-development}" "${gradle_cmd[@]}" app:assembleDebug \
    -x lint \
    -x test \
    --configure-on-demand \
    --build-cache \
    -PreactNativeDevServerPort=8081 \
    -PreactNativeArchitectures="$abi"

apk_path="app/build/outputs/apk/debug/app-debug.apk"

echo "Zatrzymuję poprzedni dev client na ${serial}..."
adb -s "$serial" shell am force-stop "$package_name" >/dev/null 2>&1 || true

echo "Instaluję ${apk_path} na ${serial}..."
adb -s "$serial" install -r "$apk_path"
