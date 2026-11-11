import createMiddleware from "next-intl/middleware";
import { type NextRequest, NextResponse } from "next/server";

import { routing } from "@/i18n/routing";
import {
  categoryExists,
  collectionExists,
  matchCatalogPath,
  productExists,
  type CatalogKind,
} from "@/lib/product-exists";

/**
 * Przekierowanie `/` na język klienta i obsługa prefiksu `/pl` albo `/en`.
 *
 * Kolejność detekcji: cookie języka, `Accept-Language`, domyślnie `/pl`.
 */
const handleI18nRouting = createMiddleware(routing);

/** Dla każdego rodzaju encji: sprawdzenie istnienia i strona 404 do rewrite'u. */
const CATALOG_CHECKS: Record<
  CatalogKind,
  { check: typeof productExists; notFoundPath: string }
> = {
  product: { check: productExists, notFoundPath: "product-not-found" },
  category: { check: categoryExists, notFoundPath: "category-not-found" },
  collection: { check: collectionExists, notFoundPath: "collection-not-found" },
};

/**
 * Routing języka, a dla encji katalogu (karta produktu, kategoria, kolekcja) dodatkowo prawdziwe 404.
 *
 * Z Cache Components strona streamuje prerenderowaną powłokę od razu, więc
 * nieznany slug musi zostać odrzucony przed renderem (#357, #359). Nieznany slug
 * idzie rewrite'em na statyczną stronę 404 w tym samym języku, a slug
 * w formacie spoza katalogu (np. `a%2Fb`) dostaje to samo bez żądania do
 * katalogu. Nagłówki i ciasteczka next-intl zostają.
 *
 * Args:
 *     request: Żądanie przed renderem strony.
 *
 * Returns:
 *     Odpowiedź next-intl albo rewrite na stronę not-found w odpowiednim języku.
 */
export default async function proxy(request: NextRequest) {
  const response = handleI18nRouting(request);

  if (response.headers.has("location")) {
    return response;
  }

  const matched = matchCatalogPath(request.nextUrl.pathname);
  if (matched) {
    const { check, notFoundPath } = CATALOG_CHECKS[matched.kind];

    if (await check(matched.slug, matched.locale)) {
      return response;
    }
    return NextResponse.rewrite(
      new URL(`/${matched.locale}/${notFoundPath}`, request.url),
      { headers: response.headers },
    );
  }

  return response;
}

/**
 * Poza routingiem językowym zostają adresy techniczne: `/api` i `/api/*`
 * (kontrakt rewalidacji z ADR 0034), `/_allauth/*` (przekazywane do Django
 * przez rewrite, żeby ciasteczka sesji i CSRF były widoczne dla webu),
 * `/_next/*`, `/.well-known/*`, `robots.txt`, `sitemap.xml` i pliki statyczne
 * (kropka w ostatnim segmencie). Lookahead kotwiczy cały segment, żeby
 * `/apiary` czy `/api-docs` nadal dostawały prefiks języka.
 *
 * Matcher musi być literałem w tym pliku: Next czyta `config` statycznie
 * z kodu źródłowego, a importowana stała kończy się błędem kompilacji
 * i odpowiedzią 500 na każdej stronie.
 */
export const config = {
  matcher:
    "/((?!api(?:/|$)|_allauth(?:/|$)|_next/|\\.well-known/|robots\\.txt$|sitemap\\.xml$|.*\\.[^/]+$).*)",
};
