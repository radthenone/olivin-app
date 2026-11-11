import { getProductsRetrieveUrl } from "@olivin/api/generated/apps/products/products";
import { getCategoriesRetrieveUrl } from "@olivin/api/generated/apps/categories/categories";
import { getCollectionsRetrieveUrl } from "@olivin/api/generated/apps/collections/collections";
import { isLocale, type Locale } from "@olivin/i18n";

import { catalogBaseUrl, isCatalogSlug, isProductSlug } from "./catalog-url";

/**
 * Sprawdzenie, czy encje katalogu (produkt, kategoria, kolekcja) istnieją,
 * zanim strona zacznie streamować.
 *
 * Z Cache Components strona wysyła prerenderowaną powłokę od razu,
 * więc `notFound()` w stronie daje już tylko 200 z `noindex`. Prawdziwe 404
 * musi zapaść w proxy. Pytamy ten sam publiczny endpoint katalogu co strona,
 * bez cookies sesji (ADR 0034).
 */

/** Adres encji katalogu: `/{locale}/{products|categories|collections}/{slug}`. */
const CATALOG_PATH = /^\/([^/]+)\/(products|categories|collections)\/([^/]+)$/;

/** Rodzaj encji katalogu wskazywanej przez adres. */
export type CatalogKind = "product" | "category" | "collection";

const KIND_BY_SEGMENT: Record<string, CatalogKind> = {
  products: "product",
  categories: "category",
  collections: "collection",
};

export type MatchedCatalogPath = {
  kind: CatalogKind;
  locale: Locale;
  slug: string;
};

/**
 * Rodzaj encji, język i slug z adresu karty produktu, kategorii albo kolekcji.
 *
 * Args:
 *     pathname: Ścieżka żądania.
 *
 * Returns:
 *     Rodzaj, język i slug albo `null`, gdy to nie jest adres encji katalogu
 *     (lista `/products`, podścieżki, nieznany język).
 */
export function matchCatalogPath(pathname: string): MatchedCatalogPath | null {
  const match = CATALOG_PATH.exec(pathname);

  if (!match || !isLocale(match[1])) {
    return null;
  }

  return { kind: KIND_BY_SEGMENT[match[2]], locale: match[1], slug: match[3] };
}

type EntityExistenceOptions = {
  fetch?: typeof fetch;
  now?: () => number;
  ttlMs?: number;
  maxEntries?: number;
  timeoutMs?: number;
};

/**
 * Sprawdzenie istnienia encji katalogu z keszem w pamięci procesu.
 *
 * Kesz trzyma wynik per slug, także negatywny i przepuszczenie po błędzie,
 * więc katalog dostaje najwyżej jedno żądanie na slug na TTL. Równoległe
 * żądania o ten sam slug czekają na jedno sprawdzenie. Po przekroczeniu
 * limitu wypada najstarszy wpis.
 *
 * Slug spoza formatu `isCatalogSlug` (np. `a%2Fb`, `złoty`) nie istnieje
 * w katalogu z definicji: wynik `false` zapada od razu, bez żądania i bez
 * wpisu w keszu, więc śmieciowe adresy nie wypychają prawdziwych slugów.
 *
 * shortcut: kesz żyje w jednej instancji serwera, więc każda instancja pyta
 * katalog osobno, a zdjęta encja dostaje 404 dopiero po TTL; przy wielu
 * instancjach albo potrzebie natychmiastowej propagacji przenieść wynik do
 * wspólnego kesza i unieważniać go tagiem `product:<slug>` z ADR 0034.
 *
 * Args:
 *     urlBuilder: Budowniczy ścieżki endpointu szczegółów encji.
 *     options: Zależności i limity; domyślnie globalny `fetch`, TTL 1 minuta
 *         (rewalidacja profilu `cacheLife("minutes")` strony), 1000 wpisów
 *         i 2 s na odpowiedź katalogu.
 *
 * Returns:
 *     Funkcja `(slug, locale)`, która rozstrzyga, czy encja istnieje.
 */
function createExistenceCheck(
  urlBuilder: (slug: string, locale: Locale) => string,
  {
    fetch: fetchImpl = fetch,
    now = Date.now,
    ttlMs = 60_000,
    maxEntries = 1000,
    timeoutMs = 2_000,
  }: EntityExistenceOptions = {},
) {
  const cache = new Map<
    string,
    { expiresAt: number; exists: Promise<boolean> }
  >();

  async function askCatalog(slug: string, locale: Locale): Promise<boolean> {
    try {
      const response = await fetchImpl(
        `${catalogBaseUrl()}${urlBuilder(slug, locale)}`,
        {
          headers: { accept: "application/json" },
          signal: AbortSignal.timeout(timeoutMs),
        },
      );
      await response.body?.cancel();

      // Tylko jednoznaczne 404 katalogu oznacza brak encji.
      return response.status !== 404;
    } catch {
      // Timeout, błąd sieci albo brak adresu: przepuszczamy, strona sama
      // zrobi `notFound()`. Awaria backendu nie może dawać 404 na stronach.
      return true;
    }
  }

  return function checkExists(slug: string, locale: Locale): Promise<boolean> {
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

/**
 * Sprawdzenie istnienia produktu (fabryka z wstrzykiwanymi zależnościami).
 *
 * Args:
 *     options: Zależności i limity, patrz `createExistenceCheck`.
 *
 * Returns:
 *     Funkcja `(slug, locale)`, która rozstrzyga, czy produkt istnieje.
 */
export function createProductExistenceCheck(
  options: EntityExistenceOptions = {},
) {
  return createExistenceCheck(
    (slug, locale) => getProductsRetrieveUrl(slug, { lang: locale }),
    options,
  );
}

/**
 * Sprawdzenie istnienia kategorii (fabryka z wstrzykiwanymi zależnościami).
 *
 * Args:
 *     options: Zależności i limity, patrz `createExistenceCheck`.
 *
 * Returns:
 *     Funkcja `(slug, locale)`, która rozstrzyga, czy kategoria istnieje.
 */
export function createCategoryExistenceCheck(
  options: EntityExistenceOptions = {},
) {
  return createExistenceCheck(
    (slug, locale) => getCategoriesRetrieveUrl(slug, { lang: locale }),
    options,
  );
}

/**
 * Sprawdzenie istnienia kolekcji (fabryka z wstrzykiwanymi zależnościami).
 *
 * Args:
 *     options: Zależności i limity, patrz `createExistenceCheck`.
 *
 * Returns:
 *     Funkcja `(slug, locale)`, która rozstrzyga, czy kolekcja istnieje.
 */
export function createCollectionExistenceCheck(
  options: EntityExistenceOptions = {},
) {
  return createExistenceCheck(
    (slug, locale) => getCollectionsRetrieveUrl(slug, { lang: locale }),
    options,
  );
}

/** Sprawdzenie istnienia produktu. */
export const productExists = createProductExistenceCheck();

/** Sprawdzenie istnienia kategorii. */
export const categoryExists = createCategoryExistenceCheck();

/** Sprawdzenie istnienia kolekcji. */
export const collectionExists = createCollectionExistenceCheck();
