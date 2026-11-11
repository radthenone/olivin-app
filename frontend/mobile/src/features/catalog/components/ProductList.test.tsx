import { describe, expect, test } from "bun:test";
import { renderToString } from "react-dom/server";
import type { ProductList } from "@olivin/api/generated/apps/schemas";
import { CatalogError } from "@olivin/features/catalog";
import { AppIntlProvider } from "@core/i18n";
import { ProductTile } from "./ProductTile";
import { ProductErrorView } from "./ProductErrorView";
import { ProductListSkeleton } from "./ProductListSkeleton";

describe("ProductTile component", () => {
  const mockProduct = {
    id: "prod-1",
    slug: "pierscionek-diamentowy",
    name: "Pierścionek z brylantem",
    isAvailable: true,
    cheapestVariant: {
      id: "var-1",
      sku: "RING-1",
      price: { amount: 245000, currency: "PLN" },
      isAvailable: true,
      images: [
        {
          id: "img-1",
          altText: "Widok z góry",
          urls: { "400": "https://img.example.com/400.webp" },
          isPrimary: true,
          position: 1,
        },
      ],
    },
  } as unknown as ProductList;

  test("renders product name, price with fromPrice prefix, and accessibility label", () => {
    const html = renderToString(
      <AppIntlProvider initialLocale="pl">
        <ProductTile product={mockProduct} onPress={() => {}} />
      </AppIntlProvider>,
    );

    expect(html).toContain("Pierścionek z brylantem");
    expect(html).toContain("2450,00");
    expect(html).toContain("zł");
    expect(html).toContain("od");
  });

  test("renders in English with correct formatting and currency", () => {
    const html = renderToString(
      <AppIntlProvider initialLocale="en">
        <ProductTile product={mockProduct} onPress={() => {}} />
      </AppIntlProvider>,
    );

    expect(html).toContain("Pierścionek z brylantem");
    expect(html).toContain("from");
    expect(html).toContain("PLN");
  });
});

describe("ProductErrorView component", () => {
  function renderError(error: unknown, locale: "pl" | "en" = "pl") {
    return renderToString(
      <AppIntlProvider initialLocale={locale}>
        <ProductErrorView error={error} onRetry={() => {}} />
      </AppIntlProvider>,
    );
  }

  test("renders network error message and retry button", () => {
    const html = renderError(new CatalogError(0, "Network request failed"));

    expect(html).toContain("Brak połączenia z siecią");
    expect(html).toContain("Spróbuj ponownie");
    expect(html).not.toContain("Network request failed");
  });

  test("renders the general error key instead of the server message", () => {
    const html = renderError(
      new CatalogError(503, "Katalog odpowiedział statusem 503."),
    );

    expect(html).toContain("Wystąpił błąd podczas ładowania danych");
    expect(html).not.toContain("Katalog odpowiedział statusem 503.");
    expect(html).not.toContain("Brak połączenia z siecią");
  });

  test("renders the general error key in English for an unknown error", () => {
    const html = renderError(new Error("boom"), "en");

    expect(html).toContain("An error occurred while loading data");
    expect(html).not.toContain("boom");
  });
});

describe("ProductListSkeleton component", () => {
  test("renders placeholder skeleton cards", () => {
    const html = renderToString(
      <AppIntlProvider initialLocale="pl">
        <ProductListSkeleton count={4} />
      </AppIntlProvider>,
    );

    expect(html).toBeDefined();
    expect(html.length).toBeGreaterThan(50);
  });
});
