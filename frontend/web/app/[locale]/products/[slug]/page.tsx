import type { Locale } from "@olivin/i18n";
import { hasLocale } from "next-intl";
import { notFound } from "next/navigation";

import { ProductView } from "@/components/catalog/product-view";
import { routing } from "@/i18n/routing";
import { getProductForPage } from "@/lib/catalog-api";

/**
 * Karta produktu pod prefiksem języka.
 *
 * Status 404 dla nieznanego albo zdjętego produktu daje `proxy.ts`: rewrite
 * na statyczną stronę `product-not-found`, zanim ruszy render. `notFound()`
 * w stronie pokrywa tylko okno, w którym produkt zniknął po sprawdzeniu
 * w proxy (jego kesz trzyma wynik do 60 s); powłoka karty wychodzi wtedy
 * od razu, więc odpowiedź to 200 z `noindex`. Treść jest keszowana
 * (`product:<slug>`), a cena i dostępność streamują się dalej jako dynamiczny
 * fragment w `ProductView` (ADR 0034).
 */

// Trasa blokuje na `params` i odczycie z kesza (bez `<Suspense>`), a o statusie
// 404 decyduje proxy, nie to blokowanie. `false` wyłącza tylko walidację
// natychmiastowej nawigacji i pustej powłoki statycznej, nie zmienia modelu
// renderowania.
export const instant = false;

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
