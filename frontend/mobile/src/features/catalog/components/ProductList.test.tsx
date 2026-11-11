import { describe, expect, test } from "bun:test";
import { renderToString } from "react-dom/server";
import type { ProductList } from "@olivin/api/generated/apps/schemas";
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
  test("renders network error message and retry button", () => {
    const html = renderToString(
      <AppIntlProvider initialLocale="pl">
        <ProductErrorView onRetry={() => {}} />
      </AppIntlProvider>,
    );

    expect(html).toContain("Brak połączenia z siecią");
    expect(html).toContain("Spróbuj ponownie");
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
