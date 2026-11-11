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
  resolveSelection,
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

  describe("sparse catalog", () => {
    // Istnieją tylko żółte 14 i białe 16 — brak kombinacji (białe, 14) i (żółte, 16).
    const y14 = mockVariant("Y14", { metalColor: "yellow", size: "14" });
    const w16 = mockVariant("W16", { metalColor: "white", size: "16" });
    const sparse = [y14, w16];

    test("resolveSelection jumps to the nearest existing variant instead of blocking", () => {
      const start = getInitialSelection(sparse);
      expect(start.metalColor).toBe("yellow");

      const next = resolveSelection(sparse, start, "metalColor", "white");

      expect(next).toEqual({
        metalColor: "white",
        size: "16",
        length: "45",
        stone: "diamond",
      });
      expect(findMatchingVariant(sparse, next ?? {})?.sku).toBe("W16");
    });

    test("resolveSelection keeps the selection when the combination exists", () => {
      const current = { metalColor: "yellow", size: "16" };

      // (białe, 16) nie istnieje, więc skok do V3 (białe, 17)
      const jumped = resolveSelection(variants, current, "metalColor", "white");
      expect(jumped?.metalColor).toBe("white");
      expect(jumped?.size).toBe("17");

      expect(resolveSelection(variants, current, "size", "16")).toEqual(
        current,
      );
    });

    test("resolveSelection preserves as many selected attributes as possible", () => {
      const a = mockVariant("A", {
        metalColor: "yellow",
        size: "16",
        stone: "ruby",
      });
      const b = mockVariant("B", {
        metalColor: "white",
        size: "17",
        stone: "diamond",
      });
      const c = mockVariant("C", {
        metalColor: "white",
        size: "16",
        stone: "ruby",
      });
      const all = [a, b, c];

      // Z A (żółte, 16, rubin) klik „białe": C zachowuje dwa atrybuty, B tylko jeden
      const next = resolveSelection(
        all,
        getInitialSelection(all, "A"),
        "metalColor",
        "white",
      );
      expect(findMatchingVariant(all, next ?? {})?.sku).toBe("C");
    });

    test("resolveSelection prefers an available variant on a tie", () => {
      const out = mockVariant("OUT", {
        metalColor: "white",
        size: "18",
        isAvailable: false,
      });
      const inStock = mockVariant("IN", {
        metalColor: "white",
        size: "19",
        isAvailable: true,
      });
      const all = [y14, out, inStock];

      const next = resolveSelection(
        all,
        getInitialSelection(all, "Y14"),
        "metalColor",
        "white",
      );
      expect(findMatchingVariant(all, next ?? {})?.sku).toBe("IN");
    });

    test("resolveSelection returns undefined for a value no variant has", () => {
      expect(
        resolveSelection(sparse, {}, "metalColor", "rose"),
      ).toBeUndefined();
    });

    test("isOptionAvailable reports the variant the click would select", () => {
      const start = getInitialSelection(sparse);
      expect(isOptionAvailable(sparse, start, "metalColor", "white")).toBe(
        true,
      );

      const soldOut = [y14, { ...w16, isAvailable: false }];
      expect(isOptionAvailable(soldOut, start, "metalColor", "white")).toBe(
        false,
      );
      expect(isOptionAvailable(sparse, start, "metalColor", "rose")).toBe(
        false,
      );
    });
  });

  describe("attribute present in only some variants", () => {
    const withStone = mockVariant("A", { stone: "diamond" });
    const withoutStone = mockVariant("B", {
      stone: "" as unknown as StoneEnum,
    });
    const mixed = [withStone, withoutStone];

    test("getAttributeDefinitions adds an empty value for the missing attribute", () => {
      const stone = getAttributeDefinitions(mixed).find(
        (d) => d.name === "stone",
      );
      expect(stone?.values).toEqual(["diamond", ""]);
    });

    test("getAttributeDefinitions trims values from variants", () => {
      const padded = [
        mockVariant("P", { size: " 17 " as ProductVariant["size"] }),
      ];
      const size = getAttributeDefinitions(padded).find(
        (d) => d.name === "size",
      );
      expect(size?.values).toEqual(["17"]);
    });

    test("getInitialSelection records the missing attribute as an empty value", () => {
      expect(getInitialSelection(mixed, "B").stone).toBe("");
    });

    test("findMatchingVariant does not treat a missing attribute as a wildcard", () => {
      const noStone = {
        metalColor: "yellow",
        size: "17",
        length: "45",
        stone: "",
      };
      expect(findMatchingVariant(mixed, noStone)?.sku).toBe("B");
      expect(
        findMatchingVariant(mixed, { ...noStone, stone: "diamond" })?.sku,
      ).toBe("A");
    });

    test("isCombinationPossible distinguishes a variant without the attribute", () => {
      const current = {
        metalColor: "yellow",
        size: "17",
        length: "45",
        stone: "diamond",
      };
      expect(isCombinationPossible(mixed, current, "stone", "")).toBe(true);
      expect(isCombinationPossible([withStone], current, "stone", "")).toBe(
        false,
      );
    });

    test("resolveSelection moves between a variant with and without the attribute", () => {
      const next = resolveSelection(
        mixed,
        getInitialSelection(mixed, "A"),
        "stone",
        "",
      );
      expect(findMatchingVariant(mixed, next ?? {})?.sku).toBe("B");
    });
  });
});
