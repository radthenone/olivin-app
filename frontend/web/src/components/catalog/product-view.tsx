import type { ProductDetail } from "@olivin/api/generated/apps/schemas";
import type { Locale } from "@olivin/i18n";
import { getTranslations } from "next-intl/server";

import { Suspense } from "react";

import { uniqueStones } from "@/lib/product-stones";

import { ProductGallery } from "./product-gallery";
import { ProductOffer } from "./product-offer";
import { ProductVariantProvider } from "./product-variant-context";

/**
 * Keszowana część karty produktu.
 *
 * Treść nie zależy od waluty ani sesji, więc pochodzi z kesza z tagiem
 * `product:<slug>`. Cena i dostępność są osobnym, dynamicznym fragmentem
 * streamowanym w tym samym żądaniu (ADR 0034).
 */
export async function ProductView({
  product,
  locale,
}: {
  product: ProductDetail;
  locale: Locale;
}) {
  const t = await getTranslations({ locale });
  const stones = uniqueStones(product.variants);
  const initialVariant =
    product.variants.find((v) => v.isAvailable) ?? product.variants[0] ?? null;

  return (
    <ProductVariantProvider initialVariant={initialVariant}>
      <article className="flex flex-col gap-8">
        <header className="flex flex-col gap-2">
          <h1 className="text-3xl font-semibold text-brand-600">
            {product.name}
          </h1>
          {product.averageRating !== null && (
            <p className="text-sm text-neutral-600">
              {t("catalog.product.rating", { rating: product.averageRating })}
            </p>
          )}
        </header>

        <ProductGallery defaultImages={product.images} />

        <section className="flex flex-col gap-2">
          <h2 className="text-lg font-semibold text-neutral-800">
            {t("catalog.product.description")}
          </h2>
          <p className="text-base text-neutral-700">{product.description}</p>
        </section>

        <dl className="grid grid-cols-2 gap-x-6 gap-y-2 text-sm">
          <dt className="text-neutral-500">{t("catalog.product.material")}</dt>
          <dd className="text-neutral-800">
            {t(`catalog.material.${product.material}`)}
          </dd>
          <dt className="text-neutral-500">{t("catalog.product.fineness")}</dt>
          <dd className="text-neutral-800">{product.fineness}</dd>
          {stones.length > 0 && (
            <>
              <dt className="text-neutral-500">
                {t("catalog.product.stones")}
              </dt>
              <dd className="text-neutral-800">
                {stones.map((stone) => t(`catalog.stone.${stone}`)).join(", ")}
              </dd>
            </>
          )}
        </dl>

        {product.isMadeToOrder && product.productionTimeDays !== null && (
          <p className="text-sm text-neutral-700">
            {t("catalog.product.productionTime", {
              days: product.productionTimeDays,
            })}
          </p>
        )}

        <Suspense
          fallback={
            <p className="text-sm text-neutral-500">
              {t("catalog.product.priceLoading")}
            </p>
          }
        >
          <ProductOffer locale={locale} slug={product.slug} />
        </Suspense>
      </article>
    </ProductVariantProvider>
  );
}
