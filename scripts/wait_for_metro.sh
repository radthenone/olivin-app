#!/usr/bin/env bash

# Oczekuje dwóch argumentów:
# $1 - host (domyślnie 127.0.0.1)
# $2 - port (domyślnie 8081)
function wait_for_metro() {
    local target_host="${1:-127.0.0.1}"
    local target_port="${2:-8081}"
    local status_url="http://${target_host}:${target_port}/status"
    local timeout="${EXPO_PUBLIC_EXPO_WAIT_TIMEOUT:-180}"
    local elapsed=0
    local interval=2

    echo "Czekam na Metro: ${status_url}"

    while [ "$elapsed" -lt "$timeout" ]; do
        if command -v curl >/dev/null 2>&1; then
            if curl -fsS "$status_url" 2>/dev/null | grep -q "packager-status:running"; then
                echo "Metro gotowe po ${elapsed}s."
                return 0
            fi
        else
            echo "Brak curl w PATH, pomijam aktywne czekanie na Metro."
            return 0
        fi

        sleep "$interval"
        elapsed=$((elapsed + interval))
    done

    echo "Timeout: Metro nie odpowiedziało na ${status_url} w ${timeout}s."
    return 1
}