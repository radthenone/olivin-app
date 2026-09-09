#!/usr/bin/env bash
set -euo pipefail

if [[ "$#" -eq 0 ]]; then
    exit 0
fi

# Pliki przychodza jako sciezki od korzenia repo: frontend/<workspace>/<reszta>.
# ESLint uruchamiamy w katalogu workspace'a, bo tam lezy jego flat config,
# wiec grupujemy pliki po workspacie i robimy jedno wywolanie na kazdy.
declare -A grouped=()

for file in "$@"; do
    rest="${file#frontend/}"
    [[ "$rest" == "$file" ]] && continue

    workspace="${rest%%/*}"
    # plik lezacy bezposrednio w frontend/ nie nalezy do zadnego workspace'a
    [[ "$workspace" == "$rest" ]] && continue

    relative="${rest#*/}"

    case "$relative" in
        src/api/generated/*) continue ;;
    esac

    case "$relative" in
        *.js|*.jsx|*.ts|*.tsx) grouped["$workspace"]+=" $relative" ;;
    esac
done

if [[ "${#grouped[@]}" -eq 0 ]]; then
    exit 0
fi

if ! command -v bun >/dev/null 2>&1; then
    if [[ -x "$HOME/.bun/bin/bun.exe" || -x "$HOME/.bun/bin/bun" ]]; then
        export PATH="$HOME/.bun/bin:$PATH"
    elif [[ -n "${USERPROFILE:-}" ]] && command -v cygpath >/dev/null 2>&1; then
        user_home="$(cygpath -u "$USERPROFILE")"
        if [[ -x "$user_home/.bun/bin/bun.exe" || -x "$user_home/.bun/bin/bun" ]]; then
            export PATH="$user_home/.bun/bin:$PATH"
        fi
    fi
fi

if ! command -v bun >/dev/null 2>&1; then
    echo "Nie znaleziono 'bun' w PATH ani w ~/.bun/bin."
    echo "Dodaj Bun do PATH uzywanego przez Git/VS Code albo uruchom: task packages:frontend:add -- <pkg>"
    exit 127
fi

for workspace in "${!grouped[@]}"; do
    read -r -a files <<<"${grouped[$workspace]}"
    (
        cd "frontend/$workspace"
        if command -v cmd.exe >/dev/null 2>&1; then
            cmd.exe //c bun.exe run lint --fix -- "${files[@]}"
        else
            bun run lint --fix -- "${files[@]}"
        fi
    )
done
