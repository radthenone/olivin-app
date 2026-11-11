import { describe, expect, test } from "bun:test";
import { isCatalogSlug } from "@olivin/features/catalog";
import { getNextProductsPageParam } from "./use-catalog-products";

describe("catalog hooks and pagination logic", () => {
  test("getNextProductsPageParam calculates next page or undefined when finished", () => {
    // 25 elementów łącznie, strona 1 ma 10
    const page1 = { count: 25, results: new Array(10).fill({ id: "1" }) };
    const allPages1 = [page1];
    expect(getNextProductsPageParam(page1, allPages1)).toBe(2);

    // Strona 2 ma kolejne 10 (łącznie 20)
    const page2 = { count: 25, results: new Array(10).fill({ id: "2" }) };
    const allPages2 = [page1, page2];
    expect(getNextProductsPageParam(page2, allPages2)).toBe(3);

    // Strona 3 ma ostatnie 5 (łącznie 25)
    const page3 = { count: 25, results: new Array(5).fill({ id: "3" }) };
    const allPages3 = [page1, page2, page3];
    expect(getNextProductsPageParam(page3, allPages3)).toBeUndefined();
  });

  test("getNextProductsPageParam returns undefined for null or empty page", () => {
    expect(getNextProductsPageParam(null, [])).toBeUndefined();
    expect(
      getNextProductsPageParam({ count: 0, results: [] }, []),
    ).toBeUndefined();
  });

  test("slug validation prevents requests for malformed product slugs", () => {
    expect(isCatalogSlug("gold-necklace")).toBe(true);
    expect(isCatalogSlug("ring_14k")).toBe(true);
    expect(isCatalogSlug("invalid/slug")).toBe(false);
    expect(isCatalogSlug("..%2Fescape")).toBe(false);
  });
});
