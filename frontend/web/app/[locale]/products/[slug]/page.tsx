import type { Locale } from "@olivin/i18n";
import { hasLocale } from "next-intl";
import { notFound } from "next/navigation";
import { Suspense } from "react";

import { ProductView } from "@/components/catalog/product-view";
import { routing } from "@/i18n/routing";
import { getProductForPage } from "@/lib/catalog-api";

/**
 * Karta produktu pod prefiksem języka.
 *
 * Część z treścią produktu jest keszowana (`product:<slug>`), a cena i
 * dostępność streamują się jako dynamiczny fragment w tym samym żądaniu —
 * dlatego `params` czytamy dopiero wewnątrz `<Suspense>` (ADR 0034).
 */
export default function ProductPage({
  params,
}: {
  params: Promise<{ locale: string; slug: string }>;
}) {
  return (
    <main className="mx-auto w-full max-w-3xl px-6 py-16">
      <Suspense
        fallback={
          <div
            aria-hidden
            className="h-96 w-full animate-pulse rounded-xl bg-neutral-100"
          />
        }
      >
        <ProductContent params={params} />
      </Suspense>
    </main>
  );
}

async function ProductContent({
  params,
}: {
  params: Promise<{ locale: string; slug: string }>;
}) {
  const { locale, slug } = await params;

  if (!hasLocale(routing.locales, locale)) {
    notFound();
  }

  const product = await getProductForPage(slug, locale as Locale);

  // Zdjęty albo nieistniejący produkt daje 404 w języku strony.
  if (!product) {
    notFound();
  }

  return <ProductView locale={locale} product={product} />;
}
