# Bugbot — reguły projektu

Sekcje Tierów (backend, web/mobile) Bootstrap zostawia tylko dla Tierów wybranych w `.ai/project.profile.yaml`.
Stack każdego Tieru: MCP `get_bundle`. Dostosuj ścieżki i taski do `.ai/project.md` (sekcja `## Ścieżki`). Bugbot ładuje ten plik przy review PR.

## Reguły projektu

<!-- project:rules -->
<!-- Reguły olivin ponad szablon kita — ten blok przechodzi przez `kit-ai reload` bez zmian. -->

If the diff adds or renames a class, function, method, variable or test (`test_*`, `class Test*`) whose name is not in English (e.g. `test_pusty_koszyk_jest_odrzucony`, `TestSkladanieZamowienia`):

- Add a blocking bug titled "Non-English identifier"
- Body: "Nazwy w kodzie po angielsku, także testy; opis zachowania po polsku w docstringu (`.ai/project.md`, Nazewnictwo w kodzie)."

Flag `permission_classes = []` on new DRF viewsets without justification.

If the PR modifies `frontend/`, flag imports from `react-native` in `.web.tsx` files (`task lints:frontend:typecheck` must pass).

If the diff changes files under `frontend/web/src/components/ui/` and they import `@olivin/api`, `@olivin/features`, `next-intl` or `next/navigation`, or contain hex colors (`#[0-9a-fA-F]{3,6}`) or Tailwind arbitrary values with a number or color (e.g. `p-[13px]`, `bg-[#fff]`; `data-[...]` and `aria-[...]` variants are allowed):

- Add a blocking bug titled "Impure UI library component"
- Body: "Komponenty `ui/` są czyste: bez danych, nawigacji i i18n, style wyłącznie z tokenów `@olivin/tokens` (`.ai/project.md`, Biblioteka komponentów UI)."
<!-- /project:rules -->

## Ogólne

- Odpowiedzi agentów po polsku; kod po angielsku; docstringi po polsku.
- Nie commituj `.env`, kluczy API, haseł, tokenów CI.
- Preferuj minimalny diff — flaguj drive-by refactory poza zakresem PR.

If the diff adds or renames a function, class, or test (`test_*`, `class Test*`; strings in `describe`/`it` are prose, not names) with a non-English name:

- Add a blocking bug titled "Non-English identifier"
- Body: "Nazwy funkcji, klas i testów po angielsku (terminy z nagłówków `CONTEXT.md`, jeśli istnieje); opis zachowania w docstringu."

## Backend

If the PR modifies backend files (`backend/` — key `backend:` in `.ai/project.md` → `## Ścieżki`) and there are no changes in backend test files (`**/test*.py`, `**/tests/**`, `**/*_test.py`):

- Add a blocking bug titled "Missing tests for backend changes"
- Body: "Dodaj lub zaktualizuj testy dla zmian w backendzie."

If changed files include API schema, endpoints, routes, or models affecting API
**and** the project uses Orval (`codegen: orval` in `.ai/project.profile.yaml`; MCP `get_codegen`):

- Add a blocking bug unless the generated API client (`frontend/packages/api/generated/` — key `api-generated:` or `codegen-output:` in `.ai/project.md` → `## Ścieżki`) was regenerated.
- Body: "Po zmianie kontraktu API uruchom `task ovral:generate` i commituj wygenerowany klient."

If profile says `codegen: manual` or `codegen: none`: do **not** require Orval regeneration.

If any changed Python file lacks type hints on new public functions:

- Add a non-blocking finding per `core:typing-python`.

Flag `eval(`, `exec(`, raw SQL string concatenation with user input, and new endpoints open to everyone without justification.

## Frontend (web / mobile)

If the PR modifies client code (`frontend/web/`, `frontend/mobile/` — keys `web:` / `mobile:` in `.ai/project.md` → `## Ścieżki`) without the typecheck task passing (assume CI will catch — flag risky patterns):

- Flag native-only imports in web-only files (and DOM-only APIs in native files), if the Stack splits platforms.
- Flag `any` on new public interfaces without `@ts-expect-error` justification.

If the PR changes UI library components (`frontend/web/src/components/ui/` — key `ui:` in `.ai/project.md` → `## Ścieżki`) and they import the API client, stores, or feature code:

- Add a non-blocking finding titled "Impure UI library component"
- Body: "Komponenty biblioteki UI są czyste — dane i logika przychodzą przez propsy."

If native modules, Expo app config (`**/app.json`, `**/app.config.js`, `**/app.config.ts`) or config plugins change without a native-build note in PR description:

- Add a non-blocking finding: "Zmiana native — wymaga nowego buildu natywnego, nie tylko OTA."

## Auth, ACL, płatności

If changed paths match `**/auth/**`, `**/permissions/**`, `**/acl/**`, `**/payments/**`, `**/stripe/**`:

- Add a blocking bug if webhook handlers skip signature verification.
- Recommend `/review-security` in PR description if not already run locally.

## Sekrety i compliance

If dependency files change (`package.json`, `bun.lock`, `pyproject.toml`, `uv.lock`, `requirements.txt`):

- Flag new dependencies with copyleft licenses (GPL, AGPL) if project policy forbids them.

If diff contains patterns like `sk_live_`, `pk_live_`, `AWS_SECRET`, `password = "`:

- Add a blocking bug titled "Possible hardcoded secret."

## Taskfile

When suggesting fixes, prefer `task <namespace>:<nazwa>` from `.ai/project.md` over raw docker/bash commands.

## Lokalny workflow

Przed pushem developer powinien uruchomić `/review-bugbot` w Cursor (przypomina o tym `/git-end`). Guard `git-guard.mjs` blokuje push bezpośrednio na main/master/dev.
