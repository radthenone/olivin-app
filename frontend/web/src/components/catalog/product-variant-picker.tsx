"use client";

import { useEffect } from "react";
import { useLocale, useTranslations } from "next-intl";
import type { ProductDetail } from "@olivin/api/generated/apps/schemas";
import { useProductsRetrieve } from "@olivin/api/generated/apps/products/products";
import {
  getAvailabilityCategory,
  useVariantSelection,
} from "@olivin/features/catalog";
import { formatMoney } from "@olivin/money";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { CatalogCurrency } from "@/lib/catalog-api";
import { cn } from "@/lib/utils";

import { useProductVariant } from "./product-variant-context";
import { VariantSelector } from "./variant-selector";

/**
 * Interaktywna wyspa wyboru wariantu na karcie produktu.
 *
 * Pobiera dane przez hydratację TanStack Query pod kluczami Orvala
 * (`useProductsRetrieve`), bez wykonywania dodatkowego zapytania w przeglądarce.
 * Zmiana wariantu aktualizuje cenę, dostępność oraz (poprzez kontekst) zdjęcia.
 */
export function ProductVariantPicker({
  slug,
  currency,
  initialProduct,
}: {
  slug: string;
  currency?: CatalogCurrency;
  initialProduct?: ProductDetail;
}) {
  const t = useTranslations("catalog");
  const locale = useLocale();
  const query = useProductsRetrieve(
    slug,
    { lang: locale, ...(currency ? { currency } : {}) },
    {
      query: {
        // Dane przychodzą zhydratowane z serwera, więc nic ich nie odświeża:
        // ani upływ czasu, ani powrót do karty, ani odzyskanie sieci.
        staleTime: Infinity,
        refetchOnWindowFocus: false,
        refetchOnReconnect: false,
      },
    },
  );

  const product = query.data?.data ?? initialProduct;
  const { setSelectedVariant } = useProductVariant();

  const { selectedAttributes, selectedVariant, selectAttribute } =
    useVariantSelection({
      variants: product?.variants ?? [],
    });

  // Synchronizacja wybranego wariantu z kontekstem galerii zdjęć
  useEffect(() => {
    if (selectedVariant) {
      setSelectedVariant(selectedVariant);
    }
  }, [selectedVariant, setSelectedVariant]);

  if (!product) {
    return null;
  }

  const activeVariant = selectedVariant ?? product.variants[0];
  const availabilityCategory = activeVariant
    ? getAvailabilityCategory(activeVariant)
    : "unavailable";

  return (
    <Card className="flex flex-col gap-5 p-6">
      <CardHeader className="p-0">
        <div className="flex flex-wrap items-baseline justify-between gap-4">
          <CardTitle className="text-xl font-semibold text-neutral-900">
            {t("product.variants")}
          </CardTitle>
          {activeVariant && (
            <div aria-live="polite" className="flex flex-col items-end gap-1">
              <span className="text-2xl font-bold text-neutral-900">
                {formatMoney(activeVariant.price, locale)}
              </span>
              <span
                className={cn(
                  "text-sm font-medium",
                  availabilityCategory === "available" && "text-success-700",
                  availabilityCategory === "lowStock" && "text-warning-700",
                  availabilityCategory === "unavailable" && "text-danger-700",
                )}
              >
                {t(`product.availability.${availabilityCategory}`)}
              </span>
            </div>
          )}
        </div>
      </CardHeader>

      <CardContent className="flex flex-col gap-6 p-0">
        <VariantSelector
          onSelect={selectAttribute}
          selectedAttributes={selectedAttributes}
          variants={product.variants}
        />

        {product.isEngravable && product.engravingPrice !== null && (
          <p className="border-t border-neutral-200 pt-4 text-sm text-neutral-700">
            {t("product.engravingAvailable", {
              price: formatMoney(product.engravingPrice, locale),
            })}
          </p>
        )}
      </CardContent>
    </Card>
  );
}
