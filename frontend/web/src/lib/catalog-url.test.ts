import { describe, expect, test } from "bun:test";

import { isCatalogSlug, isProductSlug } from "./catalog-url";

describe("catalog-url", () => {
  test("isCatalogSlug accepts valid slug characters and rejects invalid", () => {
    expect(isCatalogSlug("valid-slug_123")).toBe(true);
    expect(isCatalogSlug("invalid/slug")).toBe(false);
    expect(isCatalogSlug("../escape")).toBe(false);
    expect(isCatalogSlug("zółty-pierścionek")).toBe(false);
  });

  test("isProductSlug accepts valid product slug and rejects invalid", () => {
    expect(isProductSlug("valid-product-slug_123")).toBe(true);
    expect(isProductSlug("invalid/product/slug")).toBe(false);
    expect(isProductSlug("../escape")).toBe(false);
    expect(isProductSlug("zółty-pierścionek")).toBe(false);
  });
});
