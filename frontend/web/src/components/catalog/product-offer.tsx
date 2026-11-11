import {
  dehydrate,
  HydrationBoundary,
  QueryClient,
} from "@tanstack/react-query";
import { getProductsRetrieveQueryKey } from "@olivin/api/generated/apps/products/products";
import type { Locale } from "@olivin/i18n";

import { getProductPrice, getRequestCurrency } from "@/lib/catalog-api";

import { ProductVariantPicker } from "./product-variant-picker";

/**
 * Dynamiczny fragment karty: cena, dostępność i interaktywny wybór wariantu.
 *
 * Czyta cookie waluty, więc nigdy nie trafia do kesza (ADR 0034). Dane
 * przekazywane są do interaktywnej wyspy klienta przez hydratację TanStack Query
 * pod kluczami Orvala, bez osobnego pobierania po stronie przeglądarki.
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

  const queryClient = new QueryClient();
  const queryKey = getProductsRetrieveQueryKey(slug, {
    lang: locale,
    ...(currency ? { currency } : {}),
  });

  queryClient.setQueryData(queryKey, {
    data: product,
    status: 200,
    headers: new Headers(),
  });

  return (
    <HydrationBoundary state={dehydrate(queryClient)}>
      <ProductVariantPicker
        currency={currency}
        initialProduct={product}
        locale={locale}
        slug={slug}
      />
    </HydrationBoundary>
  );
}
