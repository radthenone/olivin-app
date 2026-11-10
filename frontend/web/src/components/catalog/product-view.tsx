import type { ProductDetail } from "@olivin/api/generated/apps/schemas";
import type { Locale } from "@olivin/i18n";
import { getTranslations } from "next-intl/server";

import { Suspense } from "react";

import { uniqueStones } from "@/lib/product-stones";

import { ProductOffer } from "./product-offer";

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

  return (
    <article className="flex flex-col gap-8">
      <header className="flex flex-col gap-2">
        <h1 className="text-3xl font-semibold text-brand-600">{product.name}</h1>
        {product.averageRating !== null && (
          <p className="text-sm text-neutral-600">
            {t("catalog.product.rating", { rating: product.averageRating })}
          </p>
        )}
      </header>

      <div className="flex flex-col gap-3">
        {product.images.map((image) => {
          const url =
            image.urls["800"] ??
            image.urls["400"] ??
            Object.values(image.urls)[0];

          if (!url) {
            return null;
          }

          return (
            // Zdjęcia katalogu przychodzą z backendu o zmiennym adresie, więc
            // optymalizator Next nie zna ich z góry.
            // eslint-disable-next-line @next/next/no-img-element
            <img
              alt={image.altText}
              className="w-full rounded-xl border border-neutral-200 object-cover"
              height={800}
              key={image.id}
              src={url}
              width={800}
            />
          );
        })}
      </div>

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
            <dt className="text-neutral-500">{t("catalog.product.stones")}</dt>
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
  );
}
