import {
  availabilityMessageKey,
  getAvailabilityCategory,
} from "@olivin/features/catalog";
import type { Locale } from "@olivin/i18n";
import { formatMoney } from "@olivin/money";
import { getTranslations } from "next-intl/server";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { getProductPrice, getRequestCurrency } from "@/lib/catalog-api";

/**
 * Dynamiczny fragment karty: cena, dostępność i cena graweru.
 *
 * Czyta cookie waluty, więc nigdy nie trafia do kesza (ADR 0034). Bez cookie
 * pokazuje złote — taką samą wersję widzą boty wyszukiwarek.
 */
export async function ProductOffer({
  slug,
  locale,
}: {
  slug: string;
  locale: Locale;
}) {
  const currency = await getRequestCurrency();
  const product = await getProductPrice(slug, locale, currency);

  // Produkt mógł zniknąć między keszowanym odczytem a tym żądaniem — wtedy
  // nagłówek strony i tak zaraz zniknie po rewalidacji tagu.
  if (!product) {
    return null;
  }

  const t = await getTranslations({ locale });

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("catalog.product.variants")}</CardTitle>
      </CardHeader>
      <CardContent>
        <ul className="flex flex-col gap-3">
          {product.variants.map((variant) => {
            const category = getAvailabilityCategory(variant);

            return (
              <li
                className="flex flex-wrap items-baseline justify-between gap-2 border-b border-neutral-200 pb-2 last:border-b-0 last:pb-0"
                key={variant.sku}
              >
                <span className="text-sm text-neutral-700">
                  {t(`catalog.metalColor.${variant.metalColor}`)}
                </span>
                <span className="text-base font-semibold text-neutral-900">
                  {formatMoney(variant.price, locale)}
                </span>
                <span className="text-sm text-neutral-600">
                  {t(availabilityMessageKey[category])}
                </span>
              </li>
            );
          })}
        </ul>

        {product.isEngravable && product.engravingPrice !== null && (
          <p className="mt-4 text-sm text-neutral-700">
            {t("catalog.product.engravingAvailable", {
              price: formatMoney(product.engravingPrice, locale),
            })}
          </p>
        )}
      </CardContent>
    </Card>
  );
}
