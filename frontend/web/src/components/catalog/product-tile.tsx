import Link from "next/link";
import type { Route } from "next";
import { Suspense } from "react";
import type { ProductList } from "@olivin/api/generated/apps/schemas";
import type { Locale } from "@olivin/i18n";

import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

import { ProductTilePrice } from "./product-tile-price";

/**
 * Kafelek produktu na liście produktów, w kategorii lub kolekcji.
 *
 * Zdjęcie, nazwa i link są keszowane. Cena najtańszego wariantu to dynamiczny
 * fragment streamowany przez Suspense (ADR 0034).
 */
export function ProductTile({
  product,
  locale,
}: {
  product: ProductList;
  locale: Locale;
}) {
  const primaryImage =
    product.cheapestVariant?.images?.find((img) => img.isPrimary) ??
    product.cheapestVariant?.images?.[0];

  const imageUrl = primaryImage
    ? primaryImage.urls["400"] ??
      primaryImage.urls["800"] ??
      Object.values(primaryImage.urls)[0]
    : undefined;

  return (
    <Card className="group overflow-hidden transition-shadow hover:shadow-md">
      <Link
        className="flex h-full flex-col"
        href={`/${locale}/products/${product.slug}` as Route}
      >
        <div className="relative aspect-square w-full overflow-hidden bg-neutral-100">
          {imageUrl ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              alt={primaryImage?.altText ?? product.name}
              className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
              height={400}
              src={imageUrl}
              width={400}
            />
          ) : (
            <div className="flex h-full w-full items-center justify-center text-neutral-400">
              <span className="text-xs uppercase tracking-wider">Olivin</span>
            </div>
          )}
        </div>
        <CardContent className="flex flex-1 flex-col justify-between gap-3 p-4">
          <h2 className="line-clamp-2 text-base font-medium text-neutral-900 group-hover:text-brand-600">
            {product.name}
          </h2>
          <div className="flex items-baseline justify-between gap-2">
            <Suspense fallback={<Skeleton className="h-6 w-24" />}>
              <ProductTilePrice
                initialPrice={product.cheapestVariant?.price ?? null}
                locale={locale}
                slug={product.slug}
              />
            </Suspense>
          </div>
        </CardContent>
      </Link>
    </Card>
  );
}
