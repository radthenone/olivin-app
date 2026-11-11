import { describe, expect, test } from "bun:test";

import {
  buildPaginationHref,
  calculateTotalPages,
  parsePageNumber,
} from "./catalog-pagination";

describe("catalog pagination helpers", () => {
  test("parsePageNumber returns 1 for undefined, null, non-numeric or values < 1", () => {
    expect(parsePageNumber(undefined)).toBe(1);
    expect(parsePageNumber("")).toBe(1);
    expect(parsePageNumber("abc")).toBe(1);
    expect(parsePageNumber("-5")).toBe(1);
    expect(parsePageNumber("0")).toBe(1);
    expect(parsePageNumber("1")).toBe(1);
    expect(parsePageNumber("3")).toBe(3);
  });

  test("calculateTotalPages calculates pages correctly", () => {
    expect(calculateTotalPages(0, 12)).toBe(1);
    expect(calculateTotalPages(5, 12)).toBe(1);
    expect(calculateTotalPages(12, 12)).toBe(1);
    expect(calculateTotalPages(13, 12)).toBe(2);
    expect(calculateTotalPages(25, 12)).toBe(3);
  });

  test("buildPaginationHref preserves filters and manages page parameter", () => {
    expect(buildPaginationHref("/pl/products", 1)).toBe("/pl/products");
    expect(buildPaginationHref("/pl/products", 2)).toBe("/pl/products?page=2");

    const params = new URLSearchParams({
      material: "gold",
      ordering: "price",
      page: "1",
    });
    expect(buildPaginationHref("/pl/products", 2, params)).toBe(
      "/pl/products?material=gold&ordering=price&page=2",
    );
    expect(buildPaginationHref("/pl/products", 1, params)).toBe(
      "/pl/products?material=gold&ordering=price",
    );
  });
});
