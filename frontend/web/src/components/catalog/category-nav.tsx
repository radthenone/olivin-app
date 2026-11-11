import Link from "next/link";
import type { Route } from "next";
import type { Category } from "@olivin/api/generated/apps/schemas";
import type { Locale } from "@olivin/i18n";
import { getTranslations } from "next-intl/server";

import { cn } from "@/lib/utils";

/**
 * Drzewo kategorii w nawigacji katalogu (#359).
 */
export async function CategoryNav({
  categories,
  locale,
  currentSlug,
}: {
  categories: Category[];
  locale: Locale;
  currentSlug?: string;
}) {
  const t = await getTranslations({ locale });

  return (
    <nav
      aria-label={t("catalog.category.heading")}
      className="flex flex-col gap-3 rounded-xl border border-neutral-200 bg-neutral-0 p-4"
    >
      <h2 className="text-sm font-semibold uppercase tracking-wider text-neutral-500">
        {t("catalog.category.heading")}
      </h2>

      <ul className="flex flex-col gap-1 text-sm">
        <li>
          <Link
            className={cn(
              "block rounded-md px-2 py-1.5 transition-colors hover:bg-neutral-100 hover:text-brand-600",
              !currentSlug
                ? "font-semibold text-brand-600 bg-neutral-100"
                : "text-neutral-700",
            )}
            href={`/${locale}/products` as Route}
          >
            {t("catalog.list.allProducts")}
          </Link>
        </li>

        {categories.map((cat) => {
          const isSelected = currentSlug === cat.slug;
          const hasChildren = cat.children && cat.children.length > 0;

          return (
            <li key={cat.id} className="flex flex-col gap-1">
              <Link
                className={cn(
                  "block rounded-md px-2 py-1.5 transition-colors hover:bg-neutral-100 hover:text-brand-600",
                  isSelected
                    ? "font-semibold text-brand-600 bg-neutral-100"
                    : "text-neutral-700",
                )}
                href={`/${locale}/categories/${cat.slug}` as Route}
              >
                {cat.name}
              </Link>

              {hasChildren && (
                <ul className="ml-4 flex flex-col gap-1 border-l border-neutral-200 pl-2">
                  {cat.children.map((sub) => {
                    const isSubSelected = currentSlug === sub.slug;

                    return (
                      <li key={sub.id}>
                        <Link
                          className={cn(
                            "block rounded-md px-2 py-1 transition-colors hover:bg-neutral-100 hover:text-brand-600",
                            isSubSelected
                              ? "font-semibold text-brand-600 bg-neutral-100"
                              : "text-neutral-600",
                          )}
                          href={`/${locale}/categories/${sub.slug}` as Route}
                        >
                          {sub.name}
                        </Link>
                      </li>
                    );
                  })}
                </ul>
              )}
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
