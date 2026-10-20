<!-- BEGIN:nextjs-agent-rules -->

## This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` (resolved from this file's directory; in monorepos the `next` package may not be visible from the repo root) before writing any code. Heed deprecation notices.

This block is written and re-added by `next dev` — verify at `node_modules/next/dist/server/lib/generate-agent-files.js`. Removing it from a diff only re-creates the uncommitted change; committing it with your work keeps the tree clean.

<!-- END:nextjs-agent-rules -->

# Biblioteka komponentów `src/components/ui/`

Komponenty w `src/components/ui/` są czyste: nie pobierają danych, nie nawigują i nie wołają i18n. Teksty dostają przez propsy, a style biorą wyłącznie z tokenów według modułu `stack:frontend:ui-structure` z bundla. Dowolne wartości Tailwinda z liczbą albo kolorem (`-[...]`) też są literałami. Warianty `data-[state=open]:` i `aria-[...]` z shadcn są dozwolone. Układ plików jest płaski, taki jak generuje CLI shadcn. Zmieniamy go, jeśli pierwszy `/design-sync` wymusi foldery. Komponenty złożone z domeny mieszkają w `src/components/<obszar>/` i nie trafiają do synchronizacji z Claude Design. Mobile (RNR) trzyma te same nazwy komponentów, warianty i tokeny (ADR 0003). Tor designu jest opisany w `docs/open-decisions.md`.
