import type { Locale } from "@olivin/i18n";
import {
  hasActiveFilters,
  parseCatalogFilters,
  toProductsListParams,
} from "@olivin/features/catalog";
import { hasLocale } from "next-intl";
import { getTranslations } from "next-intl/server";
import { notFound } from "next/navigation";

import {
  CatalogFiltersPanel,
  CatalogSearch,
  CatalogSort,
} from "@/components/catalog/catalog-controls";
import { CatalogEmptyState } from "@/components/catalog/catalog-empty-state";
import { CategoryNav } from "@/components/catalog/category-nav";
import { Pagination } from "@/components/catalog/pagination";
import { ProductTile } from "@/components/catalog/product-tile";
import { routing } from "@/i18n/routing";
import {
  getCategoriesTreeForPage,
  getCollectionForPage,
  getProductsListForPage,
} from "@/lib/catalog-api";
import { calculateTotalPages, parsePageNumber } from "@/lib/catalog-pagination";

export const instant = false;

const PAGE_SIZE = 12;

export default async function CollectionPage({
  params,
  searchParams,
}: {
  params: Promise<{ locale: string; slug: string }>;
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const { locale, slug } = await params;

  if (!hasLocale(routing.locales, locale)) {
    notFound();
  }

  const collection = await getCollectionForPage(slug, locale as Locale);
  if (!collection) {
    notFound();
  }

  const rawSearchParams = await searchParams;
  const filters = parseCatalogFilters(rawSearchParams);
  const currentPage = filters.page ?? parsePageNumber(rawSearchParams.page);

  const queryParams = toProductsListParams(
    { ...filters, page: currentPage },
    { collection: slug, pageSize: PAGE_SIZE },
  );

  const [productsData, categories] = await Promise.all([
    getProductsListForPage(queryParams, locale as Locale),
    getCategoriesTreeForPage(locale as Locale),
  ]);

  // `?page=` poza zakresem: katalog odpowiada 404, strona też.
  if (!productsData) {
    notFound();
  }

  const t = await getTranslations({ locale });
  const totalPages = calculateTotalPages(productsData.count, PAGE_SIZE);
  const basePath = `/${locale}/collections/${slug}`;

  return (
    <main className="mx-auto flex w-full max-w-7xl flex-col gap-8 px-6 py-8">
      <header className="flex flex-col gap-2">
        <h1 className="text-3xl font-semibold text-brand-600">
          {collection.name}
        </h1>
        {collection.description && (
          <p className="text-base text-neutral-600">{collection.description}</p>
        )}
        <p className="text-sm text-neutral-500">
          {t("catalog.list.productCount", { count: productsData.count })}
        </p>
      </header>

      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <CatalogSearch
          basePath={basePath}
          currentFilters={filters}
          initialSearch={filters.search}
        />
        <CatalogSort
          basePath={basePath}
          currentFilters={filters}
          currentOrdering={filters.ordering}
        />
      </div>

      <div className="grid grid-cols-1 gap-8 md:grid-cols-4">
        <aside className="flex flex-col gap-6 md:col-span-1">
          <CategoryNav categories={categories} locale={locale as Locale} />
          <CatalogFiltersPanel basePath={basePath} currentFilters={filters} />
        </aside>

        <section className="md:col-span-3">
          {productsData.results.length === 0 ? (
            <CatalogEmptyState
              basePath={basePath}
              hasFilters={hasActiveFilters(filters)}
            />
          ) : (
            <>
              <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
                {productsData.results.map((product) => (
                  <ProductTile
                    key={product.id}
                    locale={locale as Locale}
                    product={product}
                  />
                ))}
              </div>

              <Pagination
                basePath={basePath}
                currentPage={currentPage}
                locale={locale as Locale}
                searchParams={rawSearchParams}
                totalPages={totalPages}
              />
            </>
          )}
        </section>
      </div>
    </main>
  );
}
