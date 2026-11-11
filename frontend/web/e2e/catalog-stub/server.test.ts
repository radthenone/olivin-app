import { describe, expect, test } from "bun:test";
import {
  filterAndSortFixtures,
  initialFixtures,
} from "./server";

describe("Catalog stub filter and search logic", () => {
  const fixtures = Object.values(initialFixtures());

  test("filters products by search keyword in name and description", () => {
    const params = new URLSearchParams({ search: "pierścionek" });
    const results = filterAndSortFixtures(fixtures, params, "pl");

    expect(results.length).toBeGreaterThan(0);
    for (const r of results) {
      const match =
        r.name.pl.toLowerCase().includes("pierścionek") ||
        r.description.pl.toLowerCase().includes("pierścionek");
      expect(match).toBe(true);
    }
  });

  test("filters products by material", () => {
    const params = new URLSearchParams({ material: "silver" });
    const results = filterAndSortFixtures(fixtures, params, "pl");

    expect(results.length).toBeGreaterThan(0);
    expect(results.every((r) => r.product.material === "silver")).toBe(true);
  });

  test("filters products by variant metalColor", () => {
    const params = new URLSearchParams({ metalColor: "rose" });
    const results = filterAndSortFixtures(fixtures, params, "pl");

    expect(results.length).toBe(1);
    expect(results[0].product.slug).toBe("ring");
  });

  test("filters products by variant stone", () => {
    const params = new URLSearchParams({ stone: "diamond" });
    const results = filterAndSortFixtures(fixtures, params, "pl");

    expect(results.length).toBeGreaterThan(0);
    expect(
      results.every((r) =>
        r.product.variants.some((v) => v.stone === "diamond"),
      ),
    ).toBe(true);
  });

  test("filters products by price range in grosze", () => {
    // ring: min variant 245_000 groszy (2450 zł)
    // necklace: 189_000 groszy (1890 zł)
    // earrings-gold: 120_000 groszy (1200 zł)
    const params = new URLSearchParams({
      priceMin: "200000",
      priceMax: "300000",
    });
    const results = filterAndSortFixtures(fixtures, params, "pl");

    expect(results.map((r) => r.product.slug)).toContain("ring");
    expect(results.map((r) => r.product.slug)).not.toContain("earrings-gold");
  });

  test("sorts products by price ascending and descending", () => {
    const ascParams = new URLSearchParams({ ordering: "price" });
    const ascResults = filterAndSortFixtures(fixtures, ascParams, "pl");
    const getCheapest = (r: typeof fixtures[0]) =>
      Math.min(...r.product.variants.map((v) => v.price.amount));

    for (let i = 0; i < ascResults.length - 1; i++) {
      expect(getCheapest(ascResults[i])).toBeLessThanOrEqual(
        getCheapest(ascResults[i + 1]),
      );
    }

    const descParams = new URLSearchParams({ ordering: "-price" });
    const descResults = filterAndSortFixtures(fixtures, descParams, "pl");
    for (let i = 0; i < descResults.length - 1; i++) {
      expect(getCheapest(descResults[i])).toBeGreaterThanOrEqual(
        getCheapest(descResults[i + 1]),
      );
    }
  });

  test("sorts products by name A-Z and Z-A", () => {
    const ascParams = new URLSearchParams({ ordering: "name" });
    const ascResults = filterAndSortFixtures(fixtures, ascParams, "pl");
    for (let i = 0; i < ascResults.length - 1; i++) {
      expect(
        ascResults[i].name.pl.localeCompare(ascResults[i + 1].name.pl, "pl"),
      ).toBeLessThanOrEqual(0);
    }
  });
});
