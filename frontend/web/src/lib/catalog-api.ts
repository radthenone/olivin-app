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

import { catalogBaseUrl, isCatalogSlug } from "./catalog-url";

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

/**
 * Wspólny GET publicznego API katalogu (bez cookies, ADR 0034).
 *
 * Args:
 *     url: Ścieżka endpointu z zapytaniem, bez adresu bazowego.
 *     allow404: Czy 404 ma oznaczać brak zasobu (`null`) zamiast błędu.
 *
 * Returns:
 *     Ciało odpowiedzi jako JSON albo `null` przy dozwolonym 404.
 *
 * Raises:
 *     Error: Gdy katalog odpowie statusem innym niż 2xx (i dozwolone 404).
 */
async function catalogGet<T>(
  url: string,
  { allow404 = false }: { allow404?: boolean } = {},
): Promise<T | null> {
  const response = await fetch(`${catalogBaseUrl()}${url}`, {
    headers: { accept: "application/json" },
  });

  if (allow404 && response.status === 404) {
    return null;
  }

  if (!response.ok) {
    throw new Error(`Katalog odpowiedział statusem ${response.status}.`);
  }

  return (await response.json()) as T;
}

async function fetchProduct(
  slug: string,
  locale: Locale,
  currency?: CatalogCurrency,
): Promise<ProductDetail | null> {
  // Slug spoza formatu katalogu nie trafia do adresu API (zdekodowany
  // parametr trasy `..%2Fx.y` to `../x.y`): odpowiada jak brak produktu.
  if (!isCatalogSlug(slug)) {
    return null;
  }

  const url = getProductsRetrieveUrl(slug, {
    lang: locale,
    ...(currency ? { currency } : {}),
  });

  // Zdjęty albo nieistniejący produkt to 404 strony, nie błąd katalogu.
  return catalogGet<ProductDetail>(url, { allow404: true });
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
 * Slug kategorii albo kolekcji spoza formatu katalogu daje pustą listę bez
 * żądania do API.
 *
 * Args:
 *     params: Filtry i stronicowanie (kategoria, kolekcja, strona, rozmiar).
 *     locale: Język treści z prefiksu adresu.
 *
 * Returns:
 *     Strona listy produktów albo `null`, gdy katalog odpowiedział 404
 *     (numer strony poza zakresem).
 */
export async function fetchProductsList(
  params: ProductsListFilters,
  locale: Locale,
): Promise<PaginatedProductListList | null> {
  if (params.category && !isCatalogSlug(params.category)) {
    return { count: 0, results: [] };
  }
  if (params.collection && !isCatalogSlug(params.collection)) {
    return { count: 0, results: [] };
  }

  const queryParams: ProductsListParams = {
    lang: locale,
    ...(params.page ? { page: params.page } : {}),
    ...(params.pageSize ? { pageSize: params.pageSize } : {}),
    ...(params.category ? { category: params.category } : {}),
    ...(params.collection ? { collection: params.collection } : {}),
  };

  // DRF zwraca 404 dla `?page=` poza zakresem: to brak strony, nie błąd katalogu.
  return catalogGet<PaginatedProductListList>(getProductsListUrl(queryParams), {
    allow404: true,
  });
}

/**
 * Keszowana lista produktów dla strony.
 *
 * Args:
 *     params: Filtry i stronicowanie.
 *     locale: Język treści z prefiksu adresu.
 *
 * Returns:
 *     Strona listy produktów albo `null` przy numerze strony poza zakresem.
 */
export async function getProductsListForPage(
  params: ProductsListFilters,
  locale: Locale,
): Promise<PaginatedProductListList | null> {
  "use cache";
  cacheTag("catalog");
  cacheLife("minutes");

  return fetchProductsList(params, locale);
}

/**
 * Pobiera całe drzewo kategorii.
 *
 * Args:
 *     locale: Język treści z prefiksu adresu.
 *
 * Returns:
 *     Drzewo kategorii (bez stronicowania).
 */
export async function fetchCategoriesTree(locale: Locale): Promise<Category[]> {
  return (await catalogGet<Category[]>(
    getCategoriesListUrl({ lang: locale }),
  )) as Category[];
}

/**
 * Keszowane drzewo kategorii dla nawigacji.
 *
 * Args:
 *     locale: Język treści z prefiksu adresu.
 *
 * Returns:
 *     Drzewo kategorii.
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
 *
 * Args:
 *     slug: Slug kategorii.
 *     locale: Język treści z prefiksu adresu.
 *
 * Returns:
 *     Kategoria albo `null`, gdy katalog zwrócił 404 lub slug ma niepoprawny
 *     format.
 */
export async function fetchCategory(
  slug: string,
  locale: Locale,
): Promise<Category | null> {
  if (!isCatalogSlug(slug)) {
    return null;
  }

  const url = getCategoriesRetrieveUrl(slug, { lang: locale });

  return catalogGet<Category>(url, { allow404: true });
}

/**
 * Keszowana kategoria dla strony kategorii.
 *
 * Args:
 *     slug: Slug kategorii.
 *     locale: Język treści z prefiksu adresu.
 *
 * Returns:
 *     Kategoria albo `null` przy 404 lub niepoprawnym slugu.
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
 *
 * Returns:
 *     Lista kolekcji z co najmniej jednym opublikowanym produktem.
 */
export async function fetchCollectionsList(): Promise<PaginatedCollectionList> {
  return (await catalogGet<PaginatedCollectionList>(
    getCollectionsListUrl(),
  )) as PaginatedCollectionList;
}

/**
 * Keszowana lista kolekcji.
 *
 * Returns:
 *     Lista kolekcji.
 */
export async function getCollectionsListForPage(): Promise<PaginatedCollectionList> {
  "use cache";
  cacheTag("catalog");
  cacheLife("minutes");

  return fetchCollectionsList();
}

/**
 * Pobiera pojedynczą kolekcję po slugu.
 *
 * Args:
 *     slug: Slug kolekcji.
 *     locale: Język treści z prefiksu adresu.
 *
 * Returns:
 *     Kolekcja albo `null`, gdy katalog zwrócił 404 lub slug ma niepoprawny
 *     format.
 */
export async function fetchCollection(
  slug: string,
  locale: Locale,
): Promise<Collection | null> {
  if (!isCatalogSlug(slug)) {
    return null;
  }

  const url = getCollectionsRetrieveUrl(slug, { lang: locale });

  return catalogGet<Collection>(url, { allow404: true });
}

/**
 * Keszowana kolekcja dla strony kolekcji.
 *
 * Args:
 *     slug: Slug kolekcji.
 *     locale: Język treści z prefiksu adresu.
 *
 * Returns:
 *     Kolekcja albo `null` przy 404 lub niepoprawnym slugu.
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
