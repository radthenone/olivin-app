import { describe, expect, test } from "bun:test";
import type { ProductVariant } from "@olivin/api/generated/apps/schemas";
import { renderToStaticMarkup } from "react-dom/server";

import { VariantSelector } from "./variant-selector";

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
    price: { amount: 100_000, currency: "PLN" },
    vatRate: "0.2300",
    isVatExempt: false,
    vatExemptionBasis: "",
    images: [],
    gemstones: [],
    ...overrides,
  };
}

describe("VariantSelector", () => {
  const v1 = mockVariant("V1", {
    metalColor: "yellow",
    size: "16",
    isAvailable: true,
  });
  const v2 = mockVariant("V2", {
    metalColor: "yellow",
    size: "17",
    isAvailable: true,
  });
  const v3 = mockVariant("V3", {
    metalColor: "white",
    size: "17",
    isAvailable: false,
  });
  const variants = [v1, v2, v3];

  test("renders radiogroups for active attributes", () => {
    const markup = renderToStaticMarkup(
      <VariantSelector
        locale="pl"
        selectedAttributes={{ metalColor: "yellow", size: "16" }}
        variants={variants}
      />,
    );

    expect(markup).toContain('role="radiogroup"');
    expect(markup).toContain('role="radio"');
    expect(markup).toContain("Żółte złoto");
    expect(markup).toContain("Białe złoto");
  });

  test("marks selected option with aria-checked=true", () => {
    const markup = renderToStaticMarkup(
      <VariantSelector
        locale="pl"
        selectedAttributes={{ metalColor: "yellow", size: "16" }}
        variants={variants}
      />,
    );

    expect(markup).toContain('aria-checked="true"');
  });

  test("disables unavailable combination that does not exist in catalog", () => {
    // Current selection is yellow, size 16. (white, 16) does not exist!
    const markup = renderToStaticMarkup(
      <VariantSelector
        locale="pl"
        selectedAttributes={{ metalColor: "yellow", size: "16" }}
        variants={variants}
      />,
    );

    // White button should be disabled
    expect(markup).toContain('disabled=""');
  });

  test("marks out-of-stock variant as unavailable", () => {
    // Current selection is yellow, size 17. (white, 17) exists but isAvailable=false.
    const markup = renderToStaticMarkup(
      <VariantSelector
        locale="pl"
        selectedAttributes={{ metalColor: "yellow", size: "17" }}
        variants={variants}
      />,
    );

    // White exists for size 17, so it's not disabled, but marked as unavailable
    expect(markup).toContain("Niedostępny");
  });
});
