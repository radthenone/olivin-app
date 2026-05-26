#!/usr/bin/env bash
set -euo pipefail

if [[ "$#" -eq 0 ]]; then
    exit 0
fi

files=()
for file in "$@"; do
    case "$file" in
        backend/*.py)
            files+=("${file#backend/}")
            ;;
    esac
done

if [[ "${#files[@]}" -eq 0 ]]; then
    exit 0
fi

cd backend
uv run ruff check --no-cache --fix -- "${files[@]}"
uv run ruff format --no-cache -- "${files[@]}"
