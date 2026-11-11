import { getProductsRetrieveUrl } from "@olivin/api/generated/apps/products/products";
import { getCategoriesRetrieveUrl } from "@olivin/api/generated/apps/categories/categories";
import { getCollectionsRetrieveUrl } from "@olivin/api/generated/apps/collections/collections";
import { isLocale, type Locale } from "@olivin/i18n";

import { catalogBaseUrl, isProductSlug } from "./catalog-url";

/**
 * Sprawdzenie, czy encje katalogu (produkt, kategoria, kolekcja) istnieją,
 * zanim strona zacznie streamować.
 *
 * Z Cache Components strona wysyła prerenderowaną powłokę od razu,
 * więc `notFound()` w stronie daje już tylko 200 z `noindex`. Prawdziwe 404
 * musi zapaść w proxy. Pytamy ten sam publiczny endpoint katalogu co strona,
 * bez cookies sesji (ADR 0034).
 */

/** Adres karty produktu: `/{locale}/products/{slug}`. */
const PRODUCT_PATH = /^\/([^/]+)\/products\/([^/]+)$/;
/** Adres strony kategorii: `/{locale}/categories/{slug}`. */
const CATEGORY_PATH = /^\/([^/]+)\/categories\/([^/]+)$/;
/** Adres strony kolekcji: `/{locale}/collections/{slug}`. */
const COLLECTION_PATH = /^\/([^/]+)\/collections\/([^/]+)$/;

export type MatchedCatalogPath = {
  locale: Locale;
  slug: string;
};

/**
 * Język i slug z adresu karty produktu.
 */
export function matchProductPath(
  pathname: string,
): MatchedCatalogPath | null {
  const match = PRODUCT_PATH.exec(pathname);

  if (!match || !isLocale(match[1])) {
    return null;
  }

  return { locale: match[1], slug: match[2] };
}

/**
 * Język i slug z adresu strony kategorii.
 */
export function matchCategoryPath(
  pathname: string,
): MatchedCatalogPath | null {
  const match = CATEGORY_PATH.exec(pathname);

  if (!match || !isLocale(match[1])) {
    return null;
  }

  return { locale: match[1], slug: match[2] };
}

/**
 * Język i slug z adresu strony kolekcji.
 */
export function matchCollectionPath(
  pathname: string,
): MatchedCatalogPath | null {
  const match = COLLECTION_PATH.exec(pathname);

  if (!match || !isLocale(match[1])) {
    return null;
  }

  return { locale: match[1], slug: match[2] };
}

type EntityExistenceOptions = {
  fetch?: typeof fetch;
  now?: () => number;
  ttlMs?: number;
  maxEntries?: number;
  timeoutMs?: number;
};

function createGenericExistenceCheck(
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

      return response.status !== 404;
    } catch {
      return true;
    }
  }

  return async function checkExists(
    slug: string,
    locale: Locale,
  ): Promise<boolean> {
    if (!isProductSlug(slug)) {
      return false;
    }

    const cached = cache.get(slug);

    if (cached && cached.expiresAt > now()) {
      return cached.exists;
    }

    if (cache.size >= maxEntries) {
      const oldestKey = cache.keys().next().value;
      if (oldestKey !== undefined) {
        cache.delete(oldestKey);
      }
    }

    const exists = askCatalog(slug, locale);
    cache.set(slug, { expiresAt: now() + ttlMs, exists });

    return exists;
  };
}

export function createProductExistenceCheck(options: EntityExistenceOptions = {}) {
  return createGenericExistenceCheck(
    (slug, locale) => getProductsRetrieveUrl(slug, { lang: locale }),
    options,
  );
}

export function createCategoryExistenceCheck(options: EntityExistenceOptions = {}) {
  return createGenericExistenceCheck(
    (slug, locale) => getCategoriesRetrieveUrl(slug, { lang: locale }),
    options,
  );
}

export function createCollectionExistenceCheck(options: EntityExistenceOptions = {}) {
  return createGenericExistenceCheck(
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
