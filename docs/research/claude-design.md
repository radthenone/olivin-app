# Claude Design i `/design-sync`: co monorepo frontendu musi mieć, żeby dało się je zsynchronizować później

Stan na 2026-10-14. Zakres: `frontend/` (`packages/tokens`, `web`, `mobile`). Narzędzia DesignSync nie uruchamiano. Ten dokument zbiera wiedzę z dokumentacji i opisuje konwencje.

Oznaczenia wiarygodności:

- **[P]**: źródło pierwotne Anthropic (code.claude.com, support.claude.com, claude.com).
- **[T]**: opis narzędzia DesignSync wyciągnięty z promptów Claude Code przez repozytorium społeczności. To nie jest oficjalna dokumentacja, ale jest bliżej źródła niż blogi.
- **[W]**: wpis na blogu lub cudze repo. **Niezweryfikowane** w źródle pierwotnym.

## 1. Czym to jest

| Element | Co robi | Źródło |
|---|---|---|
| Claude Design (design system) | Przechowuje kolory, typografię, komponenty i wzorce layoutu marki. Claude stosuje je w nowych projektach i deckach. | [P] [support: Set up your design system][s1] |
| `/design-sync [hint]` | Bundled skill Claude Code: *"Convert your repo's React design system and upload it to Claude Design, so designs it produces use your real components."* Pierwsza synchronizacja weryfikuje każdy komponent i na dużym repo *"can take a few hours"*. | [P] [Commands][s2] |
| `/design-login` | *"Authorize design-system access for `/design-sync` with your claude.ai account"* | [P] [Commands][s2] |
| `/design [brief]` | Rysuje artboardy (mockupy, ekrany) jako artefakt Claude Design. Eksport do PNG/PDF. Nie służy do synchronizacji biblioteki. | [P] [Commands][s2], [Artifacts][s3] |
| Narzędzie DesignSync | Narzędzie, którego używa skill `/design-sync`. Synchronizuje lokalną bibliotekę *"incrementally, one component at a time, never as a wholesale replace"*. | [T] [Piebald][s6] |

Według supportu `/design-sync` *"reads your tokens and components directly"* i najlepiej pasuje do *"product design systems that live in code"*. Systemy marki (logo, deck, Figma) buduje się czatem lub uploadem [P][s1].

## 2. Setup

Potwierdzone w źródłach pierwotnych [P]:

1. Plan Pro, Max, Team lub Enterprise. Design systems są w becie. Na Enterprise owner musi je włączyć w *Organization settings > Artifacts* [s1]. Artykuł z 2026-10-08 podany na [blogu][s4] mówi o wyjściu z bety i dostępności na każdym planie. Źródła się rozjeżdżają, więc trzeba to sprawdzić w ustawieniach konta.
2. Sesja Claude Code zalogowana kontem claude.ai, nie kluczem API. `/design-sync` nie działa na Bedrock, Vertex, Foundry ani przez Claude apps gateway [s2][s7].
3. `/design-login`, potem `/design-sync [nazwa DS]` uruchomiony w repo z biblioteką komponentów [s2].
4. W Claude Design trzeba przejrzeć wynik i przełączyć toggle *Published*, żeby nowe projekty organizacji używały tego systemu [s1].
5. Uwaga: samodzielna strona claude.ai/design zostanie zamknięta 2026-12-14. Systemy migrują się do artefaktów w Claude i są wtedy dostępne także w Claude Code [P][s5].

Przebieg narzędzia [T][s6]:

- Najpierw odczyt: `list_projects` (tylko projekty design-system z prawem zapisu), `get_project` (sprawdza `type: PROJECT_TYPE_DESIGN_SYSTEM`; typu nie da się zmienić po utworzeniu), `list_files` i `get_file` (limit 256 KiB na plik).
- Potem `finalize_plan`. Plan zamyka dokładną listę ścieżek do zapisu i usunięcia oraz `localDir`, a uruchamia się dopiero **po akceptacji użytkownika**.
- Na końcu `write_files` (maks. 256 plików na wywołanie, tylko z wnętrza `localDir`) i `delete_files`.
- Karty podglądu: aplikacja buduje indeks kart z komentarza `<!-- @dsCard group="…" -->` w **pierwszej linii** każdego pliku preview HTML. Starsze `register_assets` jest potrzebne tylko w projektach pisanych ręcznie.

## 3. Jakie pliki są w projekcie design-system

Z dokumentacji pierwotnej wynika tylko tyle: tokeny (kolory, typografia, spacing), komponenty i wzorce layoutu [P][s1], a do tego przynajmniej jeden plik preview HTML na kartę z markerem `@dsCard` [T][s6]. **Anthropic nie publikuje specyfikacji układu plików.**

Opis z blogów i cudzych repo **[W], niezweryfikowane**:

- `/design-sync` **kompiluje** bibliotekę do bundla (z `dist/` albo Storybooka), który renderer Claude Design wykonuje w przeglądarce. Repo nie jest wysyłane wprost [wmedia][s8].
- Każdy komponent dostaje: `.d.ts` (kontrakt API), `.prompt.md` (instrukcja użycia z przykładami) i `.html` preview (karta w pickerze). Do tego `_ds_sync.json` z hashami, żeby niezmienione komponenty były pomijane [s8].
- W repo powstaje katalog `.design-sync/`, który się commituje: `config.json` (przypięty projekt), `NOTES.md` (czego sync się nauczył), `previews/`, `docs/` i `conventions.md`. Ten ostatni jest doklejany do README czytanego przez agenta designu [s8], [KlassApp PR #547][s9].
- CSS, tokeny i fonty są wciągane przez `styles.css`. Według [s8] to najczęstsze źródło awarii. Tokeny są szukane w `node_modules/<pkg>` przez `tokensPkg`/`tokensGlob`, a `@import` z pliku obok kończył się błędami `[CSS_IMPORT_MISSING]` i `[TOKENS_MISSING]`. Karta może wyglądać dobrze, mimo że bundle nie ma tokenów.
- Weryfikacja wizualna wymaga przeglądarki: Playwright (ok. 200 MB) albo własnego Chrome przez `DS_CHROMIUM_PATH` [s8].

## 4. Kierunek synchronizacji

- **Kod → Design**: główny kierunek, opisany wprost przez Anthropic (*"convert … and upload"*) [P][s2].
- **Design → kod**: Anthropic opisuje przekazanie projektu do Claude Code (*"Send to local coding agent"*, *"Send to Claude Code Web"*), po którym Claude *"continues from your existing work instead of starting over from a screenshot"*. Według bloga `/design` służy też do *"create, edit, and sync design projects"* [P][s4][s10]. To przekazuje **projekty/ekrany**, a nie zmiany z powrotem do biblioteki komponentów.
- Blogi piszą o „sync both ways” i powołują się na wpis @ClaudeDevs z 2026-06-17 [W][s11]. Według Serverworks kierunek Design → kod to ręczne skopiowanie promptu z menu *Share* i wdrożenie go przez MCP `claude_design` [W][s12]. Blog Anthropic nie używa słów „two-way sync” [P][s4]. **Wniosek: biblioteka w repo jest źródłem prawdy, a Design jest jej odbiorcą.**

## 5. React Native

- Oficjalnie obsługiwany jest *"React design system"* [P][s2]. Żadne źródło pierwotne nie wspomina o React Native.
- [W][s8]: działa tylko React renderowany w przeglądarce, Vue, Angular i Svelte nie mają wsparcia. O RN nic nie ma.
- Wniosek własny, **niezweryfikowany**: `mobile` ma `react-native-web ~0.21` (`frontend/mobile/package.json`) i już używa rozszerzeń `.web.tsx` (`TotpQrCode.web.tsx`). Teoretycznie komponenty RNR + NativeWind dałoby się zbundlować dla przeglądarki przez RNW. Wymagałoby to jednak konfiguracji bundla (aliasy `react-native` → `react-native-web`, Babel NativeWind), a nie wiadomo, czy pipeline `/design-sync` na to pozwala. KlassApp z komponentami nie-Reactowymi zrobił ręczny „shim”, czyli cienki port Reactowy w `.design-sync/shim/` [W][s9].
- Realistyczna ścieżka: synchronizować **web (shadcn)** jako system referencyjny. ADR 0003 zakłada, że RNR powiela nazwy i anatomię shadcn, więc projekt z Design przekłada się na mobile przez te same nazwy komponentów i te same tokeny.

## 6. Limity

| Limit | Źródło |
|---|---|
| Tylko React design system | [P][s2] |
| Pierwszy sync weryfikuje wszystko, na dużym repo nawet godziny | [P][s2] |
| Zużycie jest liczone ze wspólnej puli z Claude Code. Po wyczerpaniu Design jest niedostępny do resetu | [P][s10][s4] |
| Jakość importu zależy od źródła: *"A messy codebase … will show up in the output"* | [P][s1] |
| Brak historii wersji w Claude Design | [P][s1] (wg streszczenia wyszukiwarki, nie sprawdzono na stronie) |
| Live preview niedostępne z klawiatury (Tab) | [P][s1] |
| `get_file` maks. 256 KiB, `write_files` maks. 256 plików na wywołanie, zapis tylko według zatwierdzonego planu | [T][s6] |
| Typ projektu (design system) niezmienny po utworzeniu | [T][s6] |
| Bardzo duże repo lepiej linkować z Claude Code niż z przeglądarki | [P][s10] |
| Wymaga zalogowanego claude.ai, bez Bedrock/Vertex/Foundry/gateway | [P][s2][s7] |

## 7. Stan repo vs. wymagania

| Obszar | Stan | Ocena |
|---|---|---|
| `packages/tokens` | Obiekt JS + `index.d.ts` (`colors`, `fontFamily`, `fontSize`, `spacing`, `borderRadius`, `boxShadow`, `screens`), pakiet `@olivin/tokens` bez builda (ADR 0002, 0005) | Dobre źródło prawdy. Pakiet jest w `node_modules` przez workspace, co pasuje do `tokensPkg` [W]. |
| `web/app/tokens.css` | Generowany (`scripts/generate-tokens-css.mjs`), `@theme` Tailwind v4 | Dobrze. To kandydat na wejście CSS dla bundla. Ryzyko z [W][s8]: `@import` z pliku obok może nie zostać znaleziony. |
| `web` komponenty | Brak `components.json` i katalogu komponentów. shadcn jest jeszcze niezainstalowany | Najlepszy moment, żeby ustalić konwencję, zanim powstanie kod. |
| `mobile/src/ui/primitives/Button` | Folder na komponent, `Button.tsx` + `button.variants.ts` (cva) + `index.ts` | Wzorzec dobry. Brakuje preview i opisu użycia. |
| Brak builda (ADR 0005) | Pakiety jako źródło TS | [W][s8] mówi, że `/design-sync` bierze `dist/` albo Storybook. Może być potrzebny build tylko dla synca (np. w `.design-sync/`), bez zmiany ADR 0005. **Niezweryfikowane.** |

## 8. Konwencje dla slice'ów UI od teraz

Cel: później uruchomić `/design-sync` na gotowym katalogu i niczego nie przenosić.

1. **Jedna biblioteka na platformę, w jednym miejscu.** Web: `web/components/ui/` (domyślne miejsce shadcn). Mobile: `mobile/src/ui/` (już istnieje). Ekrany i feature'y (`features/*/components`) tylko **składają** komponenty z biblioteki i nie definiują własnych prymitywów. Sync obejmuje wtedy tylko katalog biblioteki.
2. **Jeden komponent = jeden folder** z tą samą anatomią na obu platformach, z nazwą jak w shadcn/RNR (ADR 0003): `Button/Button.tsx`, `Button/button.variants.ts`, `Button/index.ts`. Mobile już tak ma. Na webie warto przyjąć ten sam układ, mimo że shadcn domyślnie tworzy płaskie `button.tsx`. Alternatywa: płaskie pliki i pełna zgodność z CLI shadcn. Decyzja w pytaniach.
3. **Style tylko z tokenów.** Nie wpisywać hexów, pikseli ani arbitralnych wartości Tailwinda (`bg-[#…]`, `p-[13px]`) w komponentach. Tylko klasy z `@olivin/tokens` przez adaptery. Warianty w `cva`, nie przez warunkowe stringi w JSX. Wtedy tokeny w Design i w kodzie to te same nazwy.
4. **Tokeny zawsze z pakietu, CSS generowany, nie pisany.** `tokens.css` zostaje wynikiem generatora. Nie dodawać ręcznych custom properties poza nim.
5. **Typowane, małe API.** Eksplicytny typ propsów (eksportowany z `index.ts`) bez `any` i spreadu nieopisanych propsów. Według [W] z typów powstaje `.d.ts`, czyli kontrakt dla agenta designu.
6. **Komponent biblioteki jest czysty.** Bez fetchowania, React Query, nawigacji, i18n ani kontekstu aplikacji w środku. Dane i teksty przychodzą w propsach. Wtedy komponent da się wyrenderować w izolacji (preview, bundle).
7. **Rozwidlenia platformowe przez `.web.tsx`/`.native.tsx`, nie `Platform.OS` w środku.** Zostawia to otwartą drogę do bundla przez react-native-web.
8. **JSDoc na komponencie:** jedno zdanie, kiedy go użyć, kiedy nie, i krótki przykład. Mobile już ma docstringi („Dlaczego istnieje”). Według [W] taki opis trafia do `.prompt.md`.
9. **Preview: na razie nie pisać.** Ponytail/YAGNI: `/design-sync` generuje previews sam, a format poza markerem `@dsCard` w pierwszej linii nie jest publicznie opisany. Jeśli kiedyś pisane ręcznie, to jeden plik HTML na komponent, w pierwszej linii `<!-- @dsCard group="Primitives" -->`, a grupy odpowiadają podkatalogom `ui/` (`primitives`, `layout`, `feedback`).
10. **Fonty jako pliki w repo albo z Google Fonts**, nazwane w `fontFamily` tokenów, żeby bundle i preview miały je pod ręką.

Czego **nie** robić teraz: nie dodawać Storybooka, nie budować `dist/`, nie tworzyć `.design-sync/`. Wszystkie trzy da się dodać w dniu synca i nie wymuszają zmian w komponentach, jeśli zachowa się punkty 1–6.

## Rekomendacja

Przyjąć konwencje 1–8 jako regułę dla slice'ów UI. Kosztują niewiele: mobile już w dużej mierze je spełnia, a web nie ma jeszcze komponentów. Pierwszy `/design-sync` zrobić na **web** (React + shadcn, czyli oficjalnie wspierany przypadek), gdy będzie tam ok. 5–10 komponentów. Mobile synchronizować najwyżej eksperymentalnie, przez react-native-web albo shim. Przed pierwszym syncem zrobić próbę na małej kopii i sprawdzić, czy tokeny z `@olivin/tokens` / `tokens.css` trafiają do bundla (ryzyko `[TOKENS_MISSING]` z [s8]).

## Pytania otwarte dla właściciela

1. Web: folder na komponent (spójnie z mobile) czy płaskie pliki shadcn (zgodność z `npx shadcn add`)?
2. Czy synchronizujemy tylko web jako referencję, czy mobile też jest wymagane? Od tego zależy, czy warto inwestować w bundle RNW lub shim.
3. Czy dopuszczamy osobny krok builda wyłącznie dla synca, mimo ADR 0005 (pakiety bez builda)? Może być potrzebny nowy ADR.
4. Plan i konto: czy organizacja ma Design systems włączone, i kto publikuje oraz zatwierdza system (rola admina na Team/Enterprise)?
5. Czy Claude Design ma być źródłem decyzji wizualnych (zmiany tokenów wracają do `@olivin/tokens` ręcznie), czy tylko konsumentem biblioteki?

## Źródła

- [s1]: support.claude.com, *Set up your design system in Claude Design*: https://support.claude.com/en/articles/14604397-set-up-your-design-system-in-claude-design [P]
- [s2]: code.claude.com, *Commands* (`/design`, `/design-sync`, `/design-login`): https://code.claude.com/docs/en/commands [P]
- [s3]: code.claude.com, *Share session output as artifacts*: https://code.claude.com/docs/en/artifacts [P]
- [s4]: claude.com blog, *Claude Design now stays on brand for daily work* (2026-06-17, aktualizacja 09.2026): https://claude.com/blog/claude-design-stays-on-brand-for-daily-work [P]
- [s5]: support.claude.com, *Migrate from standalone Claude Design to Claude*: https://support.claude.com/en/articles/17440474-migrate-from-standalone-claude-design-to-claude [P] (sprawdzono tylko streszczenie z wyszukiwarki)
- [s6]: Piebald-AI, *tool-description-designsync.md*: https://github.com/Piebald-AI/claude-code-system-prompts/blob/main/system-prompts/tool-description-designsync.md [T]
- [s7]: code.claude.com, *Feature availability*: https://code.claude.com/docs/en/feature-availability [P] (według streszczenia z wyszukiwarki)
- [s8]: wmedia.es, *Claude Code design-sync your components*: https://wmedia.es/en/tips/claude-code-design-sync-your-components [W]
- [s9]: KlassApp PR #547, *commit durable Claude Design sync inputs*: https://github.com/KlassApp-Foundation/KlassApp/pull/547 [W]
- [s10]: support.claude.com, *Get started with Claude Design*: https://support.claude.com/en/articles/14604416-get-started-with-claude-design [P]
- [s11]: pasqualepillitteri.it, *Claude Code and Claude Design Now Sync Both Ways*: https://pasqualepillitteri.it/en/news/5308/claude-code-claude-design-two-way-sync-design-sync [W]
- [s12]: Serverworks blog, *design-sync*: https://blog.serverworks.co.jp/claude-design-sync [W]

Uwaga metodyczna: tekstu skilla `/design-sync` nie ma w lokalnym binarium Claude Code 2.1.292 (szukano `@dsCard`, `tokensGlob`, `_ds_sync`, bez wyników). Prawdopodobnie jest pobierany zdalnie. Dlatego układ plików z sekcji 3 pozostaje niezweryfikowany.
