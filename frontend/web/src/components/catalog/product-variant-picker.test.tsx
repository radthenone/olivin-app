import { describe, expect, test } from "bun:test";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { messages } from "@olivin/i18n";
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

describe("ProductVariantPicker", () => {
  test("hydrates product data from Orval query key without network request", () => {
    const queryClient = new QueryClient();
    const product = mockProductDetail("ring");

    queryClient.setQueryData(
      getProductsRetrieveQueryKey("ring", { lang: "pl", currency: "PLN" }),
      { data: product, status: 200, headers: new Headers() },
    );

    const markup = renderToStaticMarkup(
      <NextIntlClientProvider
        locale="pl"
        messages={messages.pl}
        timeZone="Europe/Warsaw"
      >
        <QueryClientProvider client={queryClient}>
          <ProductVariantProvider>
            <ProductVariantPicker currency="PLN" locale="pl" slug="ring" />
          </ProductVariantProvider>
        </QueryClientProvider>
      </NextIntlClientProvider>,
    );

    expect(markup).toContain("Warianty");
    expect(markup).toMatch(/2.?500,00.?zł/);
    expect(markup).toContain("Dostępny");
    expect(markup).toContain("Żółte złoto");
    expect(markup).toContain("Białe złoto");
    expect(markup).toContain("Grawer dostępny");
  });
});
