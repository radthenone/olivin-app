#!/usr/bin/env bash
set -euo pipefail

if [[ "$#" -eq 0 ]]; then
    exit 0
fi

# Jak w wariancie ESLint: sciezki przychodza od korzenia repo, a Prettier
# uruchamiamy w katalogu workspace'a, zeby zlapal jego .prettierignore.
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
    [[ "$workspace" == "$rest" ]] && continue
    [[ -f "frontend/$workspace/package.json" ]] || continue

    relative="${rest#"$workspace"/}"

    case "$relative" in
        src/api/generated/*) continue ;;
    esac

    case "$relative" in
        *.js|*.jsx|*.ts|*.tsx|*.json|*.css|*.md) grouped["$workspace"]+=" $relative" ;;
    esac
done

if [[ "${#grouped[@]}" -eq 0 ]]; then
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

for workspace in "${!grouped[@]}"; do
    read -r -a files <<<"${grouped[$workspace]}"
    (
        cd "frontend/$workspace"
        if command -v cmd.exe >/dev/null 2>&1; then
            cmd.exe //c bunx.exe prettier --write -- "${files[@]}"
        else
            bunx prettier --write -- "${files[@]}"
        fi
    )
done
