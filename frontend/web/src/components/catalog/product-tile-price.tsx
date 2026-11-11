import type { Money, ProductDetail } from "@olivin/api/generated/apps/schemas";
import type { Locale } from "@olivin/i18n";
import { formatMoney } from "@olivin/money";
import { getTranslations } from "next-intl/server";

import { getProductPrice, getRequestCurrency } from "@/lib/catalog-api";

function findCheapestPrice(product: ProductDetail | null): Money | null {
  if (!product || product.variants.length === 0) {
    return null;
  }

  let cheapest = product.variants[0].price;
  for (const variant of product.variants) {
    if (variant.price.amount < cheapest.amount) {
      cheapest = variant.price;
    }
  }

  return cheapest;
}

/**
 * Dynamiczny fragment ceny na kafelku produktu.
 *
 * Czyta cookie waluty klienta, więc nie trafia do kesza listy produktów (ADR 0034).
 */
export async function ProductTilePrice({
  slug,
  locale,
  initialPrice,
}: {
  slug: string;
  locale: Locale;
  initialPrice?: Money | null;
}) {
  const currency = await getRequestCurrency();
  const t = await getTranslations({ locale });

  let price = initialPrice;

  if (currency === "EUR" || !price) {
    const product = await getProductPrice(slug, locale, currency);
    const cheapest = findCheapestPrice(product);
    if (cheapest) {
      price = cheapest;
    }
  }

  if (!price) {
    return null;
  }

  return (
    <span className="text-base font-semibold text-neutral-900">
      {t("catalog.card.fromPrice", {
        price: formatMoney(price, locale),
      })}
    </span>
  );
}
