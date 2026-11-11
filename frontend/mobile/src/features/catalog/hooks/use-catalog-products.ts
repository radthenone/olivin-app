import { useInfiniteQuery } from "@tanstack/react-query";
import type {
  PaginatedProductListList,
  ProductList,
} from "@olivin/api/generated/apps/schemas";
import type { ProductsListFilters } from "@olivin/features/catalog";
import { getActiveLocale } from "@core/i18n";
import { mobileCatalogClient } from "../services/catalog.service";

const DEFAULT_PAGE_SIZE = 10;

/**
 * Oblicza numer kolejnej strony paginacji lub undefined, gdy pobrano wszystkie produkty.
 */
export function getNextProductsPageParam(
  lastPage: { count: number; results: unknown[] } | null | undefined,
  allPages: Array<{ count: number; results: unknown[] } | null | undefined>,
): number | undefined {
  if (!lastPage || !lastPage.results || lastPage.results.length === 0) {
    return undefined;
  }

  const totalLoaded = allPages.reduce(
    (acc, page) => acc + (page?.results?.length ?? 0),
    0,
  );

  if (totalLoaded >= lastPage.count) {
    return undefined;
  }

  return allPages.length + 1;
}

export function useCatalogProductsInfinite(
  filters: Omit<ProductsListFilters, "page"> = {},
) {
  const locale = getActiveLocale();

  return useInfiniteQuery<
    PaginatedProductListList | null,
    Error,
    { pages: (PaginatedProductListList | null)[]; pageParams: number[] },
    readonly [string, string, { locale: string; category?: string; collection?: string }],
    number
  >({
    queryKey: [
      "catalog",
      "products",
      {
        locale,
        category: filters.category,
        collection: filters.collection,
      },
    ] as const,
    initialPageParam: 1,
    queryFn: async ({ pageParam }) => {
      return mobileCatalogClient.fetchProductsList(
        {
          ...filters,
          page: pageParam,
          pageSize: filters.pageSize ?? DEFAULT_PAGE_SIZE,
        },
        locale,
      );
    },
    getNextPageParam: (lastPage, allPages) =>
      getNextProductsPageParam(lastPage, allPages),
  });
}
