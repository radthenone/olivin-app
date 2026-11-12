import { describe, expect, test } from "bun:test";
import { messages, type Locale } from "@olivin/i18n";
import { NextIntlClientProvider } from "next-intl";
import { renderToStaticMarkup } from "react-dom/server";

import { CatalogEmptyState } from "./catalog-empty-state";

function render(
  hasFilters: boolean,
  basePath = "/pl/products",
  locale: Locale = "pl",
): string {
  return renderToStaticMarkup(
    <NextIntlClientProvider
      locale={locale}
      messages={messages[locale]}
      timeZone="Europe/Warsaw"
    >
      <CatalogEmptyState basePath={basePath} hasFilters={hasFilters} />
    </NextIntlClientProvider>,
  );
}

describe("CatalogEmptyState", () => {
  test("shows general empty message when there are no filters", () => {
    const html = render(false);
    expect(html).toContain("Brak produktów do wyświetlenia.");
    expect(html).not.toContain("Wyczyść filtry");
  });

  test("announces the empty state to screen readers", () => {
    expect(render(true)).toContain('role="status"');
  });

  test("shows filtered empty message and clear filters action when filters are active", () => {
    const html = render(true, "/pl/categories/kolczyki");
    expect(html).toContain("Brak produktów spełniających wybrane kryteria.");
    expect(html).toContain("Wyczyść filtry");
    expect(html).toContain('href="/pl/categories/kolczyki"');
  });

  test("renders in English when locale is en", () => {
    const html = render(true, "/en/products", "en");
    expect(html).toContain("No products match the selected criteria.");
    expect(html).toContain("Clear filters");
  });
});
