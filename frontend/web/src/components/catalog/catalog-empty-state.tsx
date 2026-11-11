import Link from "next/link";
import type { Route } from "next";
import { useTranslations } from "next-intl";

import { Button } from "@/components/ui/button";

/**
 * Pusty stan katalogu (#359, #360).
 *
 * Gdy aktywne są filtry, pokazuje komunikat i pozwala wyczyścić filtry jednym ruchem.
 */
export function CatalogEmptyState({
  hasFilters,
  basePath,
}: {
  hasFilters: boolean;
  basePath: string;
}) {
  const t = useTranslations("catalog");

  return (
    <div className="flex flex-col items-center justify-center gap-4 rounded-xl border border-neutral-200 bg-neutral-0 p-8 text-center text-neutral-600">
      <p>{hasFilters ? t("list.emptyFiltered") : t("list.empty")}</p>
      {hasFilters && (
        <Button asChild variant="outline">
          <Link href={basePath as Route}>{t("list.clearFilters")}</Link>
        </Button>
      )}
    </div>
  );
}
