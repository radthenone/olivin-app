import { describe, expect, mock, test } from "bun:test";
import { messages, type Locale } from "@olivin/i18n";
import { NextIntlClientProvider } from "next-intl";
import { renderToStaticMarkup } from "react-dom/server";

mock.module("next/navigation", () => ({
  useRouter: () => ({
    push: () => {},
    replace: () => {},
    prefetch: () => {},
  }),
  usePathname: () => "/pl/products",
  useSearchParams: () => new URLSearchParams(),
}));

import {
  CatalogFiltersPanel,
  CatalogSearch,
  CatalogSort,
} from "./catalog-controls";

function renderWithIntl(ui: React.ReactNode, locale: Locale = "pl"): string {
  return renderToStaticMarkup(
    <NextIntlClientProvider
      locale={locale}
      messages={messages[locale]}
      timeZone="Europe/Warsaw"
    >
      {ui}
    </NextIntlClientProvider>,
  );
}

describe("CatalogControls", () => {
  test("CatalogSearch renders search input and submit button with accessible label", () => {
    const html = renderWithIntl(
      <CatalogSearch initialSearch="pierścionek" basePath="/pl/products" />,
    );

    expect(html).toContain('type="search"');
    expect(html).toContain('value="pierścionek"');
    expect(html).toContain("Szukaj w katalogu");
    expect(html).toContain("Szukaj");
  });

  test("CatalogSort renders select with ordering options", () => {
    const html = renderWithIntl(
      <CatalogSort currentOrdering="price" basePath="/pl/products" />,
    );

    expect(html).toContain("<select");
    expect(html).toContain("Sortowanie");
    expect(html).toContain("Najnowsze");
    expect(html).toContain("Cena: od najniższej");
    expect(html).toContain("Cena: od najwyższej");
    expect(html).toContain("Nazwa: A-Z");
  });

  test("CatalogFiltersPanel renders filter fields and labels with keyboard access", () => {
    const html = renderWithIntl(
      <CatalogFiltersPanel
        basePath="/pl/products"
        currentFilters={{
          material: "gold",
          priceMin: 100,
          priceMax: 1000,
        }}
      />,
    );

    expect(html).toContain("Filtry");
    expect(html).toContain("Kruszec");
    expect(html).toContain("Kolor kruszcu");
    expect(html).toContain("Próba kruszcu");
    expect(html).toContain("Rodzaj kamienia");
    expect(html).toContain("Rozmiar");
    expect(html).toContain("Długość");
    expect(html).toContain("Cena");
    expect(html).toContain("Wyczyść filtry");
    expect(html).toContain('id="filter-material"');
    expect(html).toContain('id="filter-price-min"');
    expect(html).toContain('id="filter-price-max"');
  });

  test("CatalogFiltersPanel groups price fields in a labelled fieldset with currency", () => {
    const html = renderWithIntl(
      <CatalogFiltersPanel basePath="/pl/products" />,
    );

    expect(html).toContain("<fieldset");
    expect(html).toContain("<legend");
    expect(html).toContain("Cena (PLN)");
    expect(html).toContain('step="0.01"');
    expect(html).not.toContain('step="1"');

    const en = renderWithIntl(
      <CatalogFiltersPanel basePath="/en/products" currency="EUR" />,
      "en",
    );
    expect(en).toContain("Price (EUR)");
  });

  test("CatalogFiltersPanel renders length options through i18n", () => {
    const pl = renderWithIntl(<CatalogFiltersPanel basePath="/pl/products" />);
    expect(pl).toContain("45 cm");
  });
});
