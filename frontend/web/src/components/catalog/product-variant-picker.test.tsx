import { describe, expect, mock, test } from "bun:test";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { messages, type Locale } from "@olivin/i18n";
import { NextIntlClientProvider } from "next-intl";
import { getProductsRetrieveQueryKey } from "@olivin/api/generated/apps/products/products";
import type {
  ProductDetail,
  ProductVariant,
} from "@olivin/api/generated/apps/schemas";
import { renderToStaticMarkup } from "react-dom/server";

import { ProductVariantProvider } from "./product-variant-context";
import { ProductVariantPicker } from "./product-variant-picker";

function mockVariant(
  sku: string,
  overrides: Partial<ProductVariant> = {},
): ProductVariant {
  return {
    id: sku,
    sku,
    available: 5,
    isAvailable: true,
    isLowStock: false,
    metalColor: "yellow",
    size: "17",
    length: "45",
    stone: "diamond",
    metalWeightGrams: "3.5",
    price: { amount: 250_000, currency: "PLN" },
    vatRate: "0.2300",
    isVatExempt: false,
    vatExemptionBasis: "",
    images: [],
    gemstones: [],
    ...overrides,
  };
}

function mockProductDetail(slug: string): ProductDetail {
  return {
    id: `prod-${slug}`,
    name: "Złoty pierścionek",
    slug,
    description: "Opis pierścionka.",
    category: "pierscionki",
    material: "gold",
    fineness: "585",
    isMadeToOrder: false,
    productionTimeDays: null,
    isEngravable: true,
    engravingPrice: { amount: 5000, currency: "PLN" },
    images: [],
    variants: [
      mockVariant("RING-Y-17", {
        metalColor: "yellow",
        price: { amount: 250_000, currency: "PLN" },
        isAvailable: true,
      }),
      mockVariant("RING-W-17", {
        metalColor: "white",
        price: { amount: 260_000, currency: "PLN" },
        isAvailable: true,
        isLowStock: true,
      }),
    ],
    averageRating: 4.8,
    isFavorite: false,
  };
}

/** Renderuje wyspę z danymi zhydratowanymi pod kluczem Orvala dla danego języka. */
function renderPicker(locale: Locale): string {
  const queryClient = new QueryClient();

  queryClient.setQueryData(
    getProductsRetrieveQueryKey("ring", { lang: locale, currency: "PLN" }),
    {
      data: mockProductDetail("ring"),
      status: 200,
      headers: new Headers(),
    },
  );

  return renderToStaticMarkup(
    <NextIntlClientProvider
      locale={locale}
      messages={messages[locale]}
      timeZone="Europe/Warsaw"
    >
      <QueryClientProvider client={queryClient}>
        <ProductVariantProvider>
          <ProductVariantPicker currency="PLN" slug="ring" />
        </ProductVariantProvider>
      </QueryClientProvider>
    </NextIntlClientProvider>,
  );
}

describe("ProductVariantPicker", () => {
  test("hydrates product data from Orval query key without network request", () => {
    const originalFetch = globalThis.fetch;
    const fetchSpy = mock(() => Promise.reject(new Error("unexpected fetch")));
    globalThis.fetch = fetchSpy as unknown as typeof fetch;

    let markup: string;
    try {
      markup = renderPicker("pl");
    } finally {
      globalThis.fetch = originalFetch;
    }

    expect(fetchSpy).not.toHaveBeenCalled();
    expect(markup).toContain("Warianty");
    expect(markup).toMatch(/2.?500,00.?zł/);
    expect(markup).toContain("Dostępny");
    expect(markup).toContain("Żółte złoto");
    expect(markup).toContain("Białe złoto");
    expect(markup).toContain("Grawer dostępny");
  });

  test("announces price and availability changes in a polite live region", () => {
    expect(renderPicker("pl")).toContain('aria-live="polite"');
  });

  test("colours availability with semantic status tokens", () => {
    const markup = renderPicker("pl");

    expect(markup).toContain("text-success-700");
    expect(markup).not.toMatch(/text-(emerald|amber|rose)-/);
  });

  test("reads the language from next-intl, including the hydration key", () => {
    const markup = renderPicker("en");

    expect(markup).toContain("Variants");
    expect(markup).toContain("Available");
    expect(markup).toContain("Engraving available");
    expect(markup).toContain("Yellow gold");
  });
});
