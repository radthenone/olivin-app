import Link from "next/link";
import type { Route } from "next";
import type { Locale } from "@olivin/i18n";
import { getTranslations } from "next-intl/server";

import { Button } from "@/components/ui/button";

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
    return (
      pageNumber === 1 ? basePath : `${basePath}?page=${pageNumber}`
    ) as Route;
  };

  const hasPrevious = currentPage > 1;
  const hasNext = currentPage < totalPages;

  return (
    <nav
      aria-label={t("catalog.pagination.label")}
      className="mt-8 flex items-center justify-between gap-4 border-t border-neutral-200 pt-6"
    >
      {hasPrevious ? (
        <Button asChild variant="outline">
          <Link href={buildPageHref(currentPage - 1)}>
            {t("catalog.pagination.previous")}
          </Link>
        </Button>
      ) : (
        <Button disabled type="button" variant="outline">
          {t("catalog.pagination.previous")}
        </Button>
      )}

      <span className="text-sm text-neutral-600">
        {t("catalog.pagination.pageOf", {
          page: currentPage,
          totalPages,
        })}
      </span>

      {hasNext ? (
        <Button asChild variant="outline">
          <Link href={buildPageHref(currentPage + 1)}>
            {t("catalog.pagination.next")}
          </Link>
        </Button>
      ) : (
        <Button disabled type="button" variant="outline">
          {t("catalog.pagination.next")}
        </Button>
      )}
    </nav>
  );
}
