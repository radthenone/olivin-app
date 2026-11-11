import type { Locale } from "@olivin/i18n";
import { hasLocale } from "next-intl";
import { getTranslations } from "next-intl/server";
import { notFound } from "next/navigation";

import { CategoryNav } from "@/components/catalog/category-nav";
import { Pagination } from "@/components/catalog/pagination";
import { ProductTile } from "@/components/catalog/product-tile";
import { routing } from "@/i18n/routing";
import {
  getCategoriesTreeForPage,
  getProductsListForPage,
} from "@/lib/catalog-api";
import { calculateTotalPages, parsePageNumber } from "@/lib/catalog-pagination";

export const instant = false;

const PAGE_SIZE = 12;

export default async function ProductsPage({
  params,
  searchParams,
}: {
  params: Promise<{ locale: string }>;
  searchParams: Promise<{ page?: string }>;
}) {
  const { locale } = await params;

  if (!hasLocale(routing.locales, locale)) {
    notFound();
  }

  const { page: rawPage } = await searchParams;
  const currentPage = parsePageNumber(rawPage);

  const [productsData, categories] = await Promise.all([
    getProductsListForPage(
      { page: currentPage, pageSize: PAGE_SIZE },
      locale as Locale,
    ),
    getCategoriesTreeForPage(locale as Locale),
  ]);

  // `?page=` poza zakresem: katalog odpowiada 404, strona też.
  if (!productsData) {
    notFound();
  }

  const t = await getTranslations({ locale });
  const totalPages = calculateTotalPages(productsData.count, PAGE_SIZE);

  return (
    <main className="mx-auto flex w-full max-w-7xl flex-col gap-8 px-6 py-8">
      <header className="flex flex-col gap-2">
        <h1 className="text-3xl font-semibold text-brand-600">
          {t("catalog.list.title")}
        </h1>
        <p className="text-base text-neutral-600">
          {t("catalog.list.description")}
        </p>
        <p className="text-sm text-neutral-500">
          {t("catalog.list.productCount", { count: productsData.count })}
        </p>
      </header>

      <div className="grid grid-cols-1 gap-8 md:grid-cols-4">
        <aside className="md:col-span-1">
          <CategoryNav categories={categories} locale={locale as Locale} />
        </aside>

        <section className="md:col-span-3">
          {productsData.results.length === 0 ? (
            <div className="rounded-xl border border-neutral-200 bg-neutral-0 p-8 text-center text-neutral-600">
              {t("catalog.list.empty")}
            </div>
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
                basePath={`/${locale}/products`}
                currentPage={currentPage}
                locale={locale as Locale}
                totalPages={totalPages}
              />
            </>
          )}
        </section>
      </div>
    </main>
  );
}
