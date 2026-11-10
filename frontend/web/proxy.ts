import createMiddleware from "next-intl/middleware";
import { type NextRequest, NextResponse } from "next/server";

import { routing } from "@/i18n/routing";
import { matchProductPath, productExists } from "@/lib/product-exists";

/**
 * Przekierowanie `/` na język klienta i obsługa prefiksu `/pl` albo `/en`.
 *
 * Kolejność detekcji: cookie języka, `Accept-Language`, domyślnie `/pl`.
 */
const handleI18nRouting = createMiddleware(routing);

/**
 * Routing języka, a dla karty produktu dodatkowo prawdziwe 404.
 *
 * Z Cache Components karta streamuje prerenderowaną powłokę od razu, więc
 * nieznany slug musi zostać odrzucony przed renderem (#357). Nieznany slug
 * idzie rewrite'em na statyczną stronę 404 w tym samym języku. Nagłówki
 * i ciasteczka next-intl zostają.
 *
 * Args:
 *     request: Żądanie przed renderem strony.
 *
 * Returns:
 *     Odpowiedź next-intl albo rewrite na `/{locale}/product-not-found`.
 */
export default async function proxy(request: NextRequest) {
  const response = handleI18nRouting(request);
  const product = matchProductPath(request.nextUrl.pathname);

  if (!product || response.headers.has("location")) {
    return response;
  }

  if (await productExists(product.slug, product.locale)) {
    return response;
  }

  return NextResponse.rewrite(
    new URL(`/${product.locale}/product-not-found`, request.url),
    { headers: response.headers },
  );
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
