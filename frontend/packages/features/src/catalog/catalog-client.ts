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

/** Format sluga produktu, kategorii i kolekcji: Django `SlugField` bez `allow_unicode`. */
const CATALOG_SLUG = /^[-a-zA-Z0-9_]+$/;

/**
 * Czy slug można bezpiecznie wstawić do adresu API katalogu.
 *
 * Sprawdzamy slug w surowej postaci: znaki `/`, `.` i znaki spoza ASCII
 * są odrzucane, co zapobiega zniekształceniu ścieżki HTTP.
 *
 * Args:
 *     slug: Weryfikowany slug produktu, kategorii lub kolekcji.
 *
 * Returns:
 *     `true`, gdy slug spełnia wymagania formatu katalogu.
 */
export function isCatalogSlug(slug: string): boolean {
  return CATALOG_SLUG.test(slug);
}

export type CatalogCurrency = "PLN" | "EUR";

export type ProductsListFilters = {
  category?: string;
  collection?: string;
  page?: number;
  pageSize?: number;
};

export type CatalogClientOptions = {
  baseUrl?: string | (() => string);
  fetch?: typeof fetch;
};

export interface CatalogClient {
  fetchProduct(
    slug: string,
    locale: Locale,
    currency?: CatalogCurrency,
  ): Promise<ProductDetail | null>;

  fetchProductsList(
    params: ProductsListFilters,
    locale: Locale,
  ): Promise<PaginatedProductListList | null>;

  fetchCategoriesTree(locale: Locale): Promise<Category[]>;

  fetchCategory(slug: string, locale: Locale): Promise<Category | null>;

  fetchCollectionsList(): Promise<PaginatedCollectionList>;

  fetchCollection(slug: string, locale: Locale): Promise<Collection | null>;
}

/**
 * Tworzy klienta API katalogu opartego o transport publiczny (ADR 0034).
 *
 * Klient ten nie przesyła tokenów sesji ani poświadczeń przeglądarkowych,
 * dzięki czemu zapytania trafiają do wspólnego kesza lub stuba API.
 */
export function createCatalogClient(
  options: CatalogClientOptions = {},
): CatalogClient {
  function resolveBaseUrl(): string {
    const raw =
      typeof options.baseUrl === "function"
        ? options.baseUrl()
        : options.baseUrl ?? "";
    return raw.replace(/\/$/, "");
  }

  async function catalogGet<T>(
    path: string,
    locale?: Locale,
    { allow404 = false }: { allow404?: boolean } = {},
  ): Promise<T | null> {
    const activeFetch = options.fetch ?? globalThis.fetch;
    const base = resolveBaseUrl();
    const url = `${base}${path}`;
    const headers: Record<string, string> = {
      accept: "application/json",
    };
    if (locale) {
      headers["accept-language"] = locale;
    }

    const response = await activeFetch(url, {
      method: "GET",
      headers,
    });

    if (allow404 && response.status === 404) {
      return null;
    }

    if (!response.ok) {
      throw new Error(`Katalog odpowiedział statusem ${response.status}.`);
    }

    return (await response.json()) as T;
  }

  return {
    async fetchProduct(
      slug: string,
      locale: Locale,
      currency?: CatalogCurrency,
    ): Promise<ProductDetail | null> {
      if (!isCatalogSlug(slug)) {
        return null;
      }

      const url = getProductsRetrieveUrl(slug, {
        lang: locale,
        ...(currency ? { currency } : {}),
      });

      return catalogGet<ProductDetail>(url, locale, { allow404: true });
    },

    async fetchProductsList(
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

      return catalogGet<PaginatedProductListList>(
        getProductsListUrl(queryParams),
        locale,
        { allow404: true },
      );
    },

    async fetchCategoriesTree(locale: Locale): Promise<Category[]> {
      const url = getCategoriesListUrl({ lang: locale });
      const result = await catalogGet<Category[]>(url, locale);
      return result ?? [];
    },

    async fetchCategory(
      slug: string,
      locale: Locale,
    ): Promise<Category | null> {
      if (!isCatalogSlug(slug)) {
        return null;
      }

      const url = getCategoriesRetrieveUrl(slug, { lang: locale });
      return catalogGet<Category>(url, locale, { allow404: true });
    },

    async fetchCollectionsList(): Promise<PaginatedCollectionList> {
      const url = getCollectionsListUrl();
      const result = await catalogGet<PaginatedCollectionList>(url);
      return result ?? { count: 0, results: [] };
    },

    async fetchCollection(
      slug: string,
      locale: Locale,
    ): Promise<Collection | null> {
      if (!isCatalogSlug(slug)) {
        return null;
      }

      const url = getCollectionsRetrieveUrl(slug, { lang: locale });
      return catalogGet<Collection>(url, locale, { allow404: true });
    },
  };
}
