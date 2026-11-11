import type {
  Category,
  Collection,
  PaginatedCollectionList,
  PaginatedProductListList,
  ProductDetail,
} from "@olivin/api/generated/apps/schemas";
import type { Locale } from "@olivin/i18n";
import {
  createCatalogClient,
  type CatalogCurrency,
  type ProductsListFilters,
} from "@olivin/features/catalog/server";
import { cacheLife, cacheTag } from "next/cache";
import { cookies } from "next/headers";

import { catalogBaseUrl } from "./catalog-url";

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

export type { CatalogCurrency, ProductsListFilters };

const catalogClient = createCatalogClient({
  baseUrl: catalogBaseUrl,
});

export const fetchProduct = catalogClient.fetchProduct;
export const fetchProductsList = catalogClient.fetchProductsList;
export const fetchCategoriesTree = catalogClient.fetchCategoriesTree;
export const fetchCategory = catalogClient.fetchCategory;
export const fetchCollectionsList = catalogClient.fetchCollectionsList;
export const fetchCollection = catalogClient.fetchCollection;

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
