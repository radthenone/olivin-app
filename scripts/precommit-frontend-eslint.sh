#!/usr/bin/env bash
set -euo pipefail

if [[ "$#" -eq 0 ]]; then
    exit 0
fi

# Pliki przychodza jako sciezki od korzenia repo: frontend/<workspace>/<reszta>.
# ESLint uruchamiamy w katalogu workspace'a, bo tam lezy jego flat config,
# wiec grupujemy pliki po workspacie i robimy jedno wywolanie na kazdy.
# Workspace to albo pierwszy segment (mobile, web), albo dwa segmenty pod
# packages/. Branie zawsze pierwszego segmentu trafialoby w frontend/packages,
# gdzie nie ma manifestu, i bun wspinalby sie do korzenia uruchamiajac zadanie
# Turborepo zamiast lintera aplikacji.
workspace_of() {
    case "$1" in
        packages/*/*)
            local without_prefix="${1#packages/}"
            echo "packages/${without_prefix%%/*}"
            ;;
        *)
            echo "${1%%/*}"
            ;;
    esac
}

declare -A grouped=()

for file in "$@"; do
    rest="${file#frontend/}"
    [[ "$rest" == "$file" ]] && continue

    workspace="$(workspace_of "$rest")"
    # plik lezacy bezposrednio w frontend/ nie nalezy do zadnego workspace'a
    [[ "$workspace" == "$rest" ]] && continue
    [[ -f "frontend/$workspace/package.json" ]] || continue
    # workspace bez zadania lint (np. pakiet z sama konfiguracja) nie ma czego
    # uruchomic — bun run wspiąłby sie wtedy do korzenia i odpalil Turborepo
    grep -q '"lint"[[:space:]]*:' "frontend/$workspace/package.json" || continue

    relative="${rest#"$workspace"/}"

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
