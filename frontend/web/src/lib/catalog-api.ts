import type {
  Category,
  Collection,
  PaginatedCollectionList,
  PaginatedProductListList,
  ProductDetail,
  ProductsListParams,
} from "@olivin/api/generated/apps/schemas";
import {
  getProductsListUrl,
  getProductsRetrieveUrl,
} from "@olivin/api/generated/apps/products/products";
import {
  getCategoriesListUrl,
  getCategoriesRetrieveUrl,
} from "@olivin/api/generated/apps/categories/categories";
import {
  getCollectionsListUrl,
  getCollectionsRetrieveUrl,
} from "@olivin/api/generated/apps/collections/collections";
import type { Locale } from "@olivin/i18n";
import { cacheLife, cacheTag } from "next/cache";
import { cookies } from "next/headers";

import { catalogBaseUrl, isProductSlug } from "./catalog-url";

/**
 * Publiczny transport serwerowy katalogu (ADR 0034).
 *
 * Komponenty serwerowe katalogu nie mogą czytać cookies sesji, bo ich wynik
 * trafia do wspólnego kesza. Dlatego katalog rozmawia z backendem osobnym
 * adresem ze zmiennej `CATALOG_API_URL` (fallback: publiczny adres backendu)
 * i bez poświadczeń przeglądarki. Ten sam adres jest szwem testowym: w CI
 * wskazuje stub, a przy `E2E_LIVE_BACKEND=1` prawdziwy backend.
 */

/** Cookie waluty z kraju dostawy (ADR 0035). Brak cookie oznacza złote. */
export const currencyCookieName = "currency";

export type CatalogCurrency = "PLN" | "EUR";

async function fetchProduct(
  slug: string,
  locale: Locale,
  currency?: CatalogCurrency,
): Promise<ProductDetail | null> {
  // Slug spoza formatu katalogu nie trafia do adresu API (zdekodowany
  // parametr trasy `..%2Fx.y` to `../x.y`): odpowiada jak brak produktu.
  if (!isProductSlug(slug)) {
    return null;
  }

  const url = getProductsRetrieveUrl(slug, {
    lang: locale,
    ...(currency ? { currency } : {}),
  });
  const response = await fetch(`${catalogBaseUrl()}${url}`, {
    headers: { accept: "application/json" },
  });

  // Zdjęty albo nieistniejący produkt to 404 strony, nie błąd katalogu.
  if (response.status === 404) {
    return null;
  }

  if (!response.ok) {
    throw new Error(`Katalog odpowiedział statusem ${response.status}.`);
  }

  return (await response.json()) as ProductDetail;
}

/**
 * Produkt do keszowanej części karty.
 *
 * Args:
 *     slug: Stały slug produktu.
 *     locale: Język treści z prefiksu adresu.
 *
 * Returns:
 *     Produkt albo `null`, gdy backend zwrócił 404 albo slug ma niepoprawny
 *     format.
 */
export async function getProductForPage(
  slug: string,
  locale: Locale,
): Promise<ProductDetail | null> {
  "use cache";
  // Zapisy produktu i przeliczenie cen unieważniają tag z ADR 0034.
  cacheTag(`product:${slug}`);
  // Krótkie wygasanie jako siatka bezpieczeństwa, gdy rewalidacja nie dojdzie.
  cacheLife("minutes");

  return fetchProduct(slug, locale);
}

/**
 * Produkt z ceną w walucie cookie — dynamiczna dziura, nigdy nie keszowana.
 *
 * Args:
 *     slug: Stały slug produktu.
 *     locale: Język treści z prefiksu adresu.
 *     currency: Waluta z cookie; `PLN`, gdy cookie nie ma albo jest inne.
 *
 * Returns:
 *     Produkt z przeliczonymi cenami albo `null` przy 404 lub niepoprawnym
 *     slugu.
 */
export async function getProductPrice(
  slug: string,
  locale: Locale,
  currency: CatalogCurrency,
): Promise<ProductDetail | null> {
  return fetchProduct(slug, locale, currency);
}

/**
 * Waluta bieżącego żądania. Waluta nie trafia do adresu ani do kesza.
 *
 * Returns:
 *     `EUR` tylko przy jawnym cookie euro; inaczej `PLN`.
 */
export async function getRequestCurrency(): Promise<CatalogCurrency> {
  const value = (await cookies()).get(currencyCookieName)?.value;

  return value === "EUR" ? "EUR" : "PLN";
}

export type ProductsListFilters = {
  category?: string;
  collection?: string;
  page?: number;
  pageSize?: number;
};

/**
 * Pobiera listę produktów z API katalogu.
 *
 * Sprawdza poprawność slugów parametrów category i collection.
 */
export async function fetchProductsList(
  params: ProductsListFilters,
  locale: Locale,
): Promise<PaginatedProductListList> {
  if (params.category && !isProductSlug(params.category)) {
    return { count: 0, results: [] };
  }
  if (params.collection && !isProductSlug(params.collection)) {
    return { count: 0, results: [] };
  }

  const queryParams: ProductsListParams = {
    lang: locale,
    ...(params.page ? { page: params.page } : {}),
    ...(params.pageSize ? { pageSize: params.pageSize } : {}),
    ...(params.category ? { category: params.category } : {}),
    ...(params.collection ? { collection: params.collection } : {}),
  };

  const url = getProductsListUrl(queryParams);
  const response = await fetch(`${catalogBaseUrl()}${url}`, {
    headers: { accept: "application/json" },
  });

  if (!response.ok) {
    throw new Error(`Katalog odpowiedział statusem ${response.status}.`);
  }

  return (await response.json()) as PaginatedProductListList;
}

/**
 * Keszowana lista produktów dla strony.
 */
export async function getProductsListForPage(
  params: ProductsListFilters,
  locale: Locale,
): Promise<PaginatedProductListList> {
  "use cache";
  cacheTag("catalog");
  cacheLife("minutes");

  return fetchProductsList(params, locale);
}

/**
 * Pobiera całe drzewo kategorii.
 */
export async function fetchCategoriesTree(locale: Locale): Promise<Category[]> {
  const url = getCategoriesListUrl({ lang: locale });
  const response = await fetch(`${catalogBaseUrl()}${url}`, {
    headers: { accept: "application/json" },
  });

  if (!response.ok) {
    throw new Error(`Katalog odpowiedział statusem ${response.status}.`);
  }

  return (await response.json()) as Category[];
}

/**
 * Keszowane drzewo kategorii dla nawigacji.
 */
export async function getCategoriesTreeForPage(
  locale: Locale,
): Promise<Category[]> {
  "use cache";
  cacheTag("catalog");
  cacheLife("minutes");

  return fetchCategoriesTree(locale);
}

/**
 * Pobiera gałąź pojedynczej kategorii po slugu.
 */
export async function fetchCategory(
  slug: string,
  locale: Locale,
): Promise<Category | null> {
  if (!isProductSlug(slug)) {
    return null;
  }

  const url = getCategoriesRetrieveUrl(slug, { lang: locale });
  const response = await fetch(`${catalogBaseUrl()}${url}`, {
    headers: { accept: "application/json" },
  });

  if (response.status === 404) {
    return null;
  }

  if (!response.ok) {
    throw new Error(`Katalog odpowiedział statusem ${response.status}.`);
  }

  return (await response.json()) as Category;
}

/**
 * Keszowana kategoria dla strony kategorii.
 */
export async function getCategoryForPage(
  slug: string,
  locale: Locale,
): Promise<Category | null> {
  "use cache";
  cacheTag("catalog");
  cacheLife("minutes");

  return fetchCategory(slug, locale);
}

/**
 * Pobiera listę kolekcji z API katalogu.
 */
export async function fetchCollectionsList(): Promise<PaginatedCollectionList> {
  const url = getCollectionsListUrl();
  const response = await fetch(`${catalogBaseUrl()}${url}`, {
    headers: { accept: "application/json" },
  });

  if (!response.ok) {
    throw new Error(`Katalog odpowiedział statusem ${response.status}.`);
  }

  return (await response.json()) as PaginatedCollectionList;
}

/**
 * Keszowana lista kolekcji.
 */
export async function getCollectionsListForPage(): Promise<PaginatedCollectionList> {
  "use cache";
  cacheTag("catalog");
  cacheLife("minutes");

  return fetchCollectionsList();
}

/**
 * Pobiera pojedynczą kolekcję po slugu.
 */
export async function fetchCollection(
  slug: string,
  locale: Locale,
): Promise<Collection | null> {
  if (!isProductSlug(slug)) {
    return null;
  }

  const url = getCollectionsRetrieveUrl(slug, { lang: locale });
  const response = await fetch(`${catalogBaseUrl()}${url}`, {
    headers: { accept: "application/json" },
  });

  if (response.status === 404) {
    return null;
  }

  if (!response.ok) {
    throw new Error(`Katalog odpowiedział statusem ${response.status}.`);
  }

  return (await response.json()) as Collection;
}

/**
 * Keszowana kolekcja dla strony kolekcji.
 */
export async function getCollectionForPage(
  slug: string,
  locale: Locale,
): Promise<Collection | null> {
  "use cache";
  cacheTag("catalog");
  cacheLife("minutes");

  return fetchCollection(slug, locale);
}
