import { describe, expect, test } from "bun:test";
import pl from "@olivin/i18n/messages/pl.json";
import en from "@olivin/i18n/messages/en.json";

describe("Catalog i18n messages", () => {
  const requiredCatalogKeys = [
    "search.label",
    "search.placeholder",
    "search.submit",
    "sort.label",
    "sort.newest",
    "sort.priceAsc",
    "sort.priceDesc",
    "sort.nameAsc",
    "sort.nameDesc",
    "filters.heading",
    "filters.clear",
    "filters.material",
    "filters.fineness",
    "filters.metalColor",
    "filters.stone",
    "filters.size",
    "filters.length",
    "filters.price",
    "filters.priceInCurrency",
    "filters.priceFrom",
    "filters.priceTo",
    "list.emptyFiltered",
    "list.clearFilters",
  ];

  function getNestedKey(obj: { catalog: unknown }, path: string): unknown {
    return path
      .split(".")
      .reduce<unknown>(
        (acc, part) => (acc as Record<string, unknown> | undefined)?.[part],
        obj.catalog,
      );
  }

  for (const key of requiredCatalogKeys) {
    test(`has catalog.${key} in pl.json and en.json`, () => {
      expect(typeof getNestedKey(pl, key)).toBe("string");
      expect(typeof getNestedKey(en, key)).toBe("string");
    });
  }
});
