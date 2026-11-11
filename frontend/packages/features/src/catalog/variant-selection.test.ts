import { describe, expect, test } from "bun:test";
import type {
  LengthEnum,
  ProductVariant,
  StoneEnum,
} from "@olivin/api/generated/apps/schemas";

import {
  findMatchingVariant,
  getAttributeDefinitions,
  getInitialSelection,
  isCombinationPossible,
  isOptionAvailable,
} from "./variant-selection";

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

describe("variant-selection", () => {
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

  test("getAttributeDefinitions extracts active attributes with unique values", () => {
    const defs = getAttributeDefinitions(variants);
    expect(defs.map((d) => d.name)).toContain("metalColor");
    expect(defs.map((d) => d.name)).toContain("size");

    const metalColors = defs.find((d) => d.name === "metalColor")?.values;
    expect(metalColors).toEqual(["yellow", "white"]);

    const sizes = defs.find((d) => d.name === "size")?.values;
    expect(sizes).toEqual(["16", "17"]);
  });

  test("getAttributeDefinitions ignores empty attributes", () => {
    const ringVariants = [
      mockVariant("R1", {
        size: "17",
        length: "" as unknown as LengthEnum,
        stone: "" as unknown as StoneEnum,
      }),
      mockVariant("R2", {
        size: "18",
        length: "" as unknown as LengthEnum,
        stone: "" as unknown as StoneEnum,
      }),
    ];
    const defs = getAttributeDefinitions(ringVariants);
    expect(defs.map((d) => d.name)).toEqual(["metalColor", "size"]);
  });

  test("findMatchingVariant finds the variant matching all selected attributes", () => {
    expect(
      findMatchingVariant(variants, { metalColor: "yellow", size: "16" })?.sku,
    ).toBe("V1");
    expect(
      findMatchingVariant(variants, { metalColor: "white", size: "17" })?.sku,
    ).toBe("V3");
    expect(
      findMatchingVariant(variants, { metalColor: "white", size: "16" }),
    ).toBeUndefined();
  });

  test("isCombinationPossible verifies whether combination exists in catalog", () => {
    // Current selection is yellow, size 16
    const current = { metalColor: "yellow", size: "16" };

    // With size 16, white is NOT possible because only (white, 17) exists
    expect(
      isCombinationPossible(variants, current, "metalColor", "white"),
    ).toBe(false);

    // With size 16, yellow is possible
    expect(
      isCombinationPossible(variants, current, "metalColor", "yellow"),
    ).toBe(true);

    // With metalColor yellow, size 17 is possible
    expect(isCombinationPossible(variants, current, "size", "17")).toBe(true);
  });

  test("isOptionAvailable checks if existing combination is in stock", () => {
    // Current selection has size 17
    const current = { metalColor: "yellow", size: "17" };

    // For size 17, yellow is available (v2 has isAvailable: true)
    expect(isOptionAvailable(variants, current, "metalColor", "yellow")).toBe(
      true,
    );

    // For size 17, white is unavailable (v3 has isAvailable: false)
    expect(isOptionAvailable(variants, current, "metalColor", "white")).toBe(
      false,
    );
  });

  test("getInitialSelection picks preferred variant or first available variant", () => {
    expect(getInitialSelection(variants, "V3")).toEqual({
      metalColor: "white",
      size: "17",
      length: "45",
      stone: "diamond",
    });

    expect(getInitialSelection(variants)).toEqual({
      metalColor: "yellow",
      size: "16",
      length: "45",
      stone: "diamond",
    });
  });
});
