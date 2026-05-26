#!/usr/bin/env bash

load_env_file() {
    local env_path="$1"

    if [[ "$env_path" == *":"* ]] && command -v cygpath >/dev/null 2>&1; then
        env_path=$(cygpath "$env_path")
    fi

    if [ ! -f "$env_path" ]; then
        echo "Uwaga: plik env nie istnieje: ${env_path}" >&2
        return 0
    fi

    set -o allexport
    # shellcheck disable=SC1090
    source "$env_path"
    set +o allexport
}
