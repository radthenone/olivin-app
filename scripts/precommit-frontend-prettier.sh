#!/usr/bin/env bash
set -euo pipefail

if [[ "$#" -eq 0 ]]; then
    exit 0
fi

files=()
for file in "$@"; do
    case "$file" in
        frontend/src/api/generated/*)
            ;;
        frontend/*.js|frontend/*.jsx|frontend/*.ts|frontend/*.tsx|frontend/*.json|frontend/*.css|frontend/*.md)
            files+=("${file#frontend/}")
            ;;
    esac
done

if [[ "${#files[@]}" -eq 0 ]]; then
    exit 0
fi

if ! command -v bunx >/dev/null 2>&1; then
    if [[ -x "$HOME/.bun/bin/bunx.exe" || -x "$HOME/.bun/bin/bunx" ]]; then
        export PATH="$HOME/.bun/bin:$PATH"
    elif [[ -n "${USERPROFILE:-}" ]] && command -v cygpath >/dev/null 2>&1; then
        user_home="$(cygpath -u "$USERPROFILE")"
        if [[ -x "$user_home/.bun/bin/bunx.exe" || -x "$user_home/.bun/bin/bunx" ]]; then
            export PATH="$user_home/.bun/bin:$PATH"
        fi
    fi
fi

if ! command -v bunx >/dev/null 2>&1; then
    echo "Nie znaleziono 'bunx' w PATH ani w ~/.bun/bin."
    echo "Dodaj Bun do PATH uzywanego przez Git/VS Code."
    exit 127
fi

cd frontend
if command -v cmd.exe >/dev/null 2>&1; then
    cmd.exe //c bunx.exe prettier --write -- "${files[@]}"
else
    bunx prettier --write -- "${files[@]}"
fi
