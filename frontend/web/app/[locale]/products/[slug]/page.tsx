import type { Locale } from "@olivin/i18n";
import { hasLocale } from "next-intl";
import { notFound } from "next/navigation";

import { ProductView } from "@/components/catalog/product-view";
import { routing } from "@/i18n/routing";
import { getProductForPage } from "@/lib/catalog-api";

/**
 * Karta produktu pod prefiksem języka.
 *
 * Slug sprawdzamy przed jakimkolwiek `<Suspense>`, żeby nieznany albo zdjęty
 * produkt dawał prawdziwy status 404 w języku strony. Treść jest keszowana
 * (`product:<slug>`), a cena i dostępność streamują się dalej jako dynamiczny
 * fragment w `ProductView` (ADR 0034).
 */
export default async function ProductPage({
  params,
}: {
  params: Promise<{ locale: string; slug: string }>;
}) {
  const { locale, slug } = await params;

  if (!hasLocale(routing.locales, locale)) {
    notFound();
  }

  const product = await getProductForPage(slug, locale as Locale);

  if (!product) {
    notFound();
  }

  return (
    <main className="mx-auto w-full max-w-3xl px-6 py-16">
      <ProductView locale={locale} product={product} />
    </main>
  );
}
