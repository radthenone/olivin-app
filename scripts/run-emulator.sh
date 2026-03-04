#!/usr/bin/env bash
set -o errexit
set -o pipefail
set -o nounset

# shellcheck disable=SC1091
source ./scripts/convert_path.sh

if [ ! -d "$ANDROID_HOME" ]; then
    echo "Error: Android SDK nie znaleziony w $ANDROID_HOME"
    exit 1
fi

export PATH="$ANDROID_HOME/emulator:$PATH"
export PATH="$ANDROID_HOME/platform-tools:$PATH"
export PATH="$ANDROID_HOME/cmdline-tools/latest/bin:$PATH"

#Usage: ./run-emulator.sh [AVD_NAME]
#This script starts the specified Android emulator (default: S23) and waits until it is fully booted.
#Example: ./run-emulator.sh S23

function wait_for_adb() {
    local timeout=300
    local elapsed=0
    local interval=15

    # Logi idą na stderr żeby nie psuć podstawienia $()
    echo "Czekam aż emulator pojawi się w ADB (max ${timeout}s)..." >&2
    while [ $elapsed -lt $timeout ]; do
        local serial
        serial=$(adb devices | grep "emulator" | grep -v "offline" | awk '{print $1}' || true)
        if [ -n "$serial" ]; then
            echo "Emulator wykryty: $serial" >&2
            echo "$serial"  # jedyna linia na stdout
            return 0
        fi
        sleep $interval
        elapsed=$((elapsed + interval))
        echo "  ...czekam na emulator w ADB ($elapsed/${timeout}s)" >&2
    done
    echo "Błąd: emulator nie pojawił się w ADB w ciągu ${timeout}s." >&2
    adb devices >&2
    return 1
}

function wait_for_boot() {
    local serial="$1"
    local max_wait=300
    local elapsed=0
    local interval=15

    local existing
    existing=$(adb devices | grep "emulator" | grep -v "offline" | awk '{print $1}' || true)
    if [ -n "$existing" ]; then
        echo "Emulator już działa: $existing"
        serial="$existing"
    fi

    echo "Czekam na boot emulatora (max ${max_wait}s)..."
    while [ $elapsed -lt $max_wait ]; do
        local status
        status=$(adb -s "$serial" shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')
        if [ "$status" = "1" ]; then
            echo "Emulator zabootowany po ${elapsed}s."
            return 0
        fi
        sleep $interval
        elapsed=$((elapsed + interval))
        echo "  ...czekam na boot ($elapsed/${max_wait}s)"
    done
    echo "Timeout: emulator nie zabootował w ciągu ${max_wait}s."
    return 1
}

function run-emulator() {
    local avd_name="${1:-S23}"

    echo "Uruchamiam emulator: $avd_name..."
    emulator -avd "$avd_name" -no-snapshot-load > /dev/null 2>&1 &

    local serial
    serial=$(wait_for_adb)

    wait_for_boot "$serial"

    echo "Dostępne urządzenia:"
    adb devices

    echo "Emulator $avd_name gotowy!"
}

run-emulator "$@"