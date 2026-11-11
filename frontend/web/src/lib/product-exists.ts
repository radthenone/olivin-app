import { getProductsRetrieveUrl } from "@olivin/api/generated/apps/products/products";
import { isLocale, type Locale } from "@olivin/i18n";

import { catalogBaseUrl, isProductSlug } from "./catalog-url";

/**
 * Sprawdzenie, czy slug produktu istnieje, zanim strona zacznie streamować.
 *
 * Z Cache Components karta produktu wysyła prerenderowaną powłokę od razu,
 * więc `notFound()` w stronie daje już tylko 200 z `noindex`. Prawdziwe 404
 * musi zapaść w proxy. Pytamy ten sam publiczny endpoint katalogu co strona,
 * bez cookies sesji (ADR 0034).
 */

/** Adres karty produktu: `/{locale}/products/{slug}`. */
const PRODUCT_PATH = /^\/([^/]+)\/products\/([^/]+)$/;

/**
 * Język i slug z adresu karty produktu.
 *
 * Args:
 *     pathname: Ścieżka żądania.
 *
 * Returns:
 *     Język i slug albo `null`, gdy to nie jest karta produktu.
 */
export function matchProductPath(
  pathname: string,
): { locale: Locale; slug: string } | null {
  const match = PRODUCT_PATH.exec(pathname);

  if (!match || !isLocale(match[1])) {
    return null;
  }

  return { locale: match[1], slug: match[2] };
}

type ProductExistenceOptions = {
  fetch?: typeof fetch;
  now?: () => number;
  ttlMs?: number;
  maxEntries?: number;
  timeoutMs?: number;
};

/**
 * Sprawdzenie istnienia produktu z keszem w pamięci procesu.
 *
 * Kesz trzyma wynik per slug, także negatywny i przepuszczenie po błędzie,
 * więc katalog dostaje najwyżej jedno żądanie na slug na TTL. Równoległe
 * żądania o ten sam slug czekają na jedno sprawdzenie. Po przekroczeniu
 * limitu wypada najstarszy wpis.
 *
 * Slug spoza formatu `isProductSlug` (np. `a%2Fb`, `złoty`) nie istnieje
 * w katalogu z definicji: wynik `false` zapada od razu, bez żądania i bez
 * wpisu w keszu, więc śmieciowe adresy nie wypychają prawdziwych slugów.
 *
 * shortcut: kesz żyje w jednej instancji serwera, więc każda instancja pyta
 * katalog osobno, a zdjęty produkt dostaje 404 dopiero po TTL; przy wielu
 * instancjach albo potrzebie natychmiastowej propagacji przenieść wynik do
 * wspólnego kesza i unieważniać go tagiem `product:<slug>` z ADR 0034.
 *
 * Args:
 *     options: Zależności i limity; domyślnie globalny `fetch`, TTL 1 minuta
 *         (rewalidacja profilu `cacheLife("minutes")` strony), 1000 wpisów
 *         i 2 s na odpowiedź katalogu.
 *
 * Returns:
 *     Funkcja `(slug, locale)`, która rozstrzyga, czy produkt istnieje.
 */
export function createProductExistenceCheck({
  fetch: fetchImpl = fetch,
  now = Date.now,
  ttlMs = 60_000,
  maxEntries = 1000,
  timeoutMs = 2_000,
}: ProductExistenceOptions = {}) {
  const cache = new Map<
    string,
    { expiresAt: number; exists: Promise<boolean> }
  >();

  async function askCatalog(slug: string, locale: Locale): Promise<boolean> {
    try {
      const response = await fetchImpl(
        `${catalogBaseUrl()}${getProductsRetrieveUrl(slug, { lang: locale })}`,
        {
          headers: { accept: "application/json" },
          signal: AbortSignal.timeout(timeoutMs),
        },
      );
      await response.body?.cancel();

      // Tylko jednoznaczne 404 katalogu oznacza brak produktu.
      return response.status !== 404;
    } catch {
      // Timeout, błąd sieci albo brak adresu: przepuszczamy, strona sama
      // zrobi `notFound()`. Awaria backendu nie może dawać 404 na kartach.
      return true;
    }
  }

  return function productExists(
    slug: string,
    locale: Locale,
  ): Promise<boolean> {
    if (!isProductSlug(slug)) {
      return Promise.resolve(false);
    }

    const cached = cache.get(slug);

    if (cached && cached.expiresAt > now()) {
      return cached.exists;
    }

    cache.delete(slug);

    if (cache.size >= maxEntries) {
      const oldest = cache.keys().next().value;
      if (oldest !== undefined) {
        cache.delete(oldest);
      }
    }

    const exists = askCatalog(slug, locale);
    cache.set(slug, { expiresAt: now() + ttlMs, exists });

    return exists;
  };
}

/** Wspólne sprawdzenie dla `proxy.ts`. */
export const productExists = createProductExistenceCheck();
