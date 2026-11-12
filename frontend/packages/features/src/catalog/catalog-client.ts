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

/**
 * Błąd pobierania danych z API katalogu.
 *
 * Widoki mapują go na komunikat z i18n po `isNetworkError`, a `message`
 * zostaje wyłącznie do logów i testów — nie trafia do interfejsu.
 *
 * Args:
 *     status: Status HTTP odpowiedzi; `0`, gdy żądanie nie dotarło do serwera.
 *     message: Opis techniczny błędu.
 */
export class CatalogError extends Error {
  readonly status: number;
  readonly isNetworkError: boolean;

  constructor(status: number, message: string) {
    super(message);
    this.name = "CatalogError";
    this.status = status;
    this.isNetworkError = status === 0;
  }
}

export type CatalogCurrency = "PLN" | "EUR";

export type ProductsListFilters = {
  category?: string;
  collection?: string;
  page?: number;
  pageSize?: number;
  material?: ProductsListParams["material"];
  fineness?: ProductsListParams["fineness"];
  metalColor?: ProductsListParams["metalColor"];
  stone?: ProductsListParams["stone"];
  size?: ProductsListParams["size"];
  length?: ProductsListParams["length"];
  /** Cena minimalna w groszach, jak w API (nie w PLN jak w `CatalogFilterState`). */
  priceMin?: number;
  /** Cena maksymalna w groszach, jak w API (nie w PLN jak w `CatalogFilterState`). */
  priceMax?: number;
  search?: string;
  ordering?: string;
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
        : (options.baseUrl ?? "");
    return raw.replace(/\/$/, "");
  }

  async function catalogGet<T>(
    path: string,
    locale?: Locale,
    {
      allow404 = false,
      onBadRequest,
    }: { allow404?: boolean; onBadRequest?: T } = {},
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

    let response: Response;
    try {
      response = await activeFetch(url, {
        method: "GET",
        headers,
        // Transport publiczny (ADR 0034): bez ciasteczek sesji.
        credentials: "omit",
      });
    } catch (cause) {
      throw new CatalogError(
        0,
        cause instanceof Error
          ? cause.message
          : "Brak połączenia z katalogiem.",
      );
    }

    if (allow404 && response.status === 404) {
      return null;
    }

    if (onBadRequest !== undefined && response.status === 400) {
      return onBadRequest;
    }

    if (!response.ok) {
      throw new CatalogError(
        response.status,
        `Katalog odpowiedział statusem ${response.status}.`,
      );
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
        ...(params.material ? { material: params.material } : {}),
        ...(params.fineness ? { fineness: params.fineness } : {}),
        ...(params.metalColor ? { metalColor: params.metalColor } : {}),
        ...(params.stone ? { stone: params.stone } : {}),
        ...(params.size ? { size: params.size } : {}),
        ...(params.length ? { length: params.length } : {}),
        ...(params.priceMin !== undefined ? { priceMin: params.priceMin } : {}),
        ...(params.priceMax !== undefined ? { priceMax: params.priceMax } : {}),
        ...(params.search ? { search: params.search } : {}),
        ...(params.ordering ? { ordering: params.ordering } : {}),
      };

      // 400 oznacza niepoprawny filtr: pusty wynik zamiast błędu strony.
      return catalogGet<PaginatedProductListList>(
        getProductsListUrl(queryParams),
        locale,
        {
          allow404: true,
          onBadRequest: { count: 0, results: [] },
        },
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
