import { useQuery } from "@tanstack/react-query";
import type { ProductDetail } from "@olivin/api/generated/apps/schemas";
import { isCatalogSlug } from "@olivin/features/catalog";
import { getActiveLocale } from "@core/i18n";
import { mobileCatalogClient } from "../services/catalog.service";

/**
 * Pobiera szczegóły produktu dla karty produktu na mobile.
 *
 * Zapytanie jest blokowane, jeśli slug nie spełnia wymogów formatu katalogu
 * (`isCatalogSlug`), co zapobiega zniekształceniu ścieżki HTTP.
 */
export function useCatalogProduct(slug?: string) {
  const locale = getActiveLocale();
  const isValidSlug = typeof slug === "string" && isCatalogSlug(slug);

  return useQuery<ProductDetail | null, Error>({
    queryKey: ["catalog", "product", slug, { locale }] as const,
    enabled: isValidSlug,
    queryFn: async () => {
      if (!slug || !isCatalogSlug(slug)) {
        return null;
      }
      return mobileCatalogClient.fetchProduct(slug, locale);
    },
  });
}
