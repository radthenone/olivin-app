import { describe, expect, test } from "bun:test";
import { renderToString } from "react-dom/server";
import type { ProductDetail } from "@olivin/api/generated/apps/schemas";
import { AppIntlProvider } from "@core/i18n";
import { ProductDetailView } from "./ProductDetailView";

describe("ProductDetailView component", () => {
  const mockProductDetail = {
    id: "prod-detail-1",
    slug: "pierscionek-diamentowy",
    name: "Pierścionek z brylantem i szafirem",
    description:
      "Elegancki pierścionek z żółtego złota z naturalnym brylantem.",
    material: "gold",
    fineness: "585",
    averageRating: 4.8,
    isMadeToOrder: true,
    productionTimeDays: 7,
    isEngravable: true,
    engravingPrice: { amount: 5000, currency: "PLN" },
    images: [
      {
        id: "img-main",
        altText: "Widok ogólny",
        urls: { "800": "https://img.example.com/800.webp" },
        isPrimary: true,
        position: 1,
      },
    ],
    variants: [
      {
        id: "var-1",
        sku: "RING-Y-16",
        metalColor: "yellow",
        size: "16",
        stone: "diamond",
        price: { amount: 245000, currency: "PLN" },
        isAvailable: true,
        isLowStock: false,
        images: [],
      },
      {
        id: "var-2",
        sku: "RING-W-16",
        metalColor: "white",
        size: "16",
        stone: "diamond",
        price: { amount: 260000, currency: "PLN" },
        isAvailable: true,
        isLowStock: true,
        images: [],
      },
      {
        id: "var-3",
        sku: "RING-Y-18",
        metalColor: "yellow",
        size: "18",
        stone: "sapphire",
        price: { amount: 280000, currency: "PLN" },
        isAvailable: false,
        isLowStock: false,
        images: [],
      },
    ],
  } as unknown as ProductDetail;

  test("renders gallery, description, material, fineness, stones, rating, production time and engraving", () => {
    const html = renderToString(
      <AppIntlProvider initialLocale="pl">
        <ProductDetailView product={mockProductDetail} />
      </AppIntlProvider>,
    );

    // Nazwa i opis
    expect(html).toContain("Pierścionek z brylantem i szafirem");
    expect(html).toContain("Elegancki pierścionek z żółtego złota");

    // Ocena
    expect(html).toContain("4,8");

    // Parametry
    expect(html).toContain("Złoto");
    expect(html).toContain("585");
    expect(html).toContain("Diament");

    // Czas realizacji i grawer
    expect(html).toContain("7 dni");
    expect(html).toContain("Grawer dostępny");
    expect(html).toContain("50,00");

    // Cena i dostępność aktywnego wariantu
    expect(html).toContain("2450,00");
    expect(html).toContain("Dostępny");
  });

  test("renders in English with translated parameters and currency", () => {
    const html = renderToString(
      <AppIntlProvider initialLocale="en">
        <ProductDetailView product={mockProductDetail} />
      </AppIntlProvider>,
    );

    expect(html).toContain("Pierścionek z brylantem i szafirem");
    expect(html).toContain("Gold");
    expect(html).toContain("Diamond");
    expect(html).toContain("7 days");
    expect(html).toContain("Available");
  });
});
