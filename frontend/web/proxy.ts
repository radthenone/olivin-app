import createMiddleware from "next-intl/middleware";

import { routing } from "@/i18n/routing";

/**
 * Przekierowanie `/` na język klienta i obsługa prefiksu `/pl` albo `/en`.
 *
 * Kolejność detekcji: cookie języka, `Accept-Language`, domyślnie `/pl`.
 */
export default createMiddleware(routing);

/**
 * Poza routingiem językowym zostają adresy techniczne: `/api` i `/api/*`
 * (kontrakt rewalidacji z ADR 0034), `/_next/*`, `/.well-known/*`,
 * `robots.txt`, `sitemap.xml` i pliki statyczne (kropka w ostatnim segmencie).
 * Lookahead kotwiczy cały segment, żeby `/apiary` czy `/api-docs` nadal
 * dostawały prefiks języka.
 *
 * Matcher musi być literałem w tym pliku: Next czyta `config` statycznie
 * z kodu źródłowego, a importowana stała kończy się błędem kompilacji
 * i odpowiedzią 500 na każdej stronie.
 */
export const config = {
  matcher:
    "/((?!api(?:/|$)|_next/|\\.well-known/|robots\\.txt$|sitemap\\.xml$|.*\\.[^/]+$).*)",
};
