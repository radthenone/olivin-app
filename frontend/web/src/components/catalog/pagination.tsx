import Link from "next/link";
import type { Route } from "next";
import type { Locale } from "@olivin/i18n";
import { getTranslations } from "next-intl/server";

/**
 * Komponent stronicowania listy produktów (#359).
 *
 * Wszystkie przejścia stron są zapisane w parametrze `?page=X` w adresie URL.
 */
export async function Pagination({
  currentPage,
  totalPages,
  basePath,
  locale,
}: {
  currentPage: number;
  totalPages: number;
  basePath: string;
  locale: Locale;
}) {
  if (totalPages <= 1) {
    return null;
  }

  const t = await getTranslations({ locale });

  const buildPageHref = (pageNumber: number): Route => {
    return (pageNumber === 1 ? basePath : `${basePath}?page=${pageNumber}`) as Route;
  };

  const hasPrevious = currentPage > 1;
  const hasNext = currentPage < totalPages;

  return (
    <nav
      aria-label={t("catalog.pagination.pageOf", {
        page: currentPage,
        totalPages,
      })}
      className="mt-8 flex items-center justify-between gap-4 border-t border-neutral-200 pt-6"
    >
      <div>
        {hasPrevious ? (
          <Link
            className="inline-flex items-center justify-center rounded-lg border border-neutral-200 bg-neutral-0 px-4 py-2 text-sm font-medium text-neutral-800 transition-colors hover:bg-neutral-100 hover:text-brand-600"
            href={buildPageHref(currentPage - 1)}
          >
            {t("catalog.pagination.previous")}
          </Link>
        ) : (
          <span className="inline-flex items-center justify-center rounded-lg border border-neutral-200 bg-neutral-100 px-4 py-2 text-sm font-medium text-neutral-400 cursor-not-allowed">
            {t("catalog.pagination.previous")}
          </span>
        )}
      </div>

      <span className="text-sm text-neutral-600">
        {t("catalog.pagination.pageOf", {
          page: currentPage,
          totalPages,
        })}
      </span>

      <div>
        {hasNext ? (
          <Link
            className="inline-flex items-center justify-center rounded-lg border border-neutral-200 bg-neutral-0 px-4 py-2 text-sm font-medium text-neutral-800 transition-colors hover:bg-neutral-100 hover:text-brand-600"
            href={buildPageHref(currentPage + 1)}
          >
            {t("catalog.pagination.next")}
          </Link>
        ) : (
          <span className="inline-flex items-center justify-center rounded-lg border border-neutral-200 bg-neutral-100 px-4 py-2 text-sm font-medium text-neutral-400 cursor-not-allowed">
            {t("catalog.pagination.next")}
          </span>
        )}
      </div>
    </nav>
  );
}
