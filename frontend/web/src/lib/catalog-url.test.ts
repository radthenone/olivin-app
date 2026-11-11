import { describe, expect, test } from "bun:test";

import { catalogBaseUrl, isCatalogSlug, isProductSlug } from "./catalog-url";

describe("catalog-url", () => {
  test("catalogBaseUrl strips trailing slash and falls back to backend url", () => {
    const prevCatalog = process.env.CATALOG_API_URL;
    const prevBackend = process.env.NEXT_PUBLIC_BACKEND_URL;

    try {
      process.env.CATALOG_API_URL = "https://catalog.example.com/";
      expect(catalogBaseUrl()).toBe("https://catalog.example.com");

      delete process.env.CATALOG_API_URL;
      process.env.NEXT_PUBLIC_BACKEND_URL = "https://backend.example.com/";
      expect(catalogBaseUrl()).toBe("https://backend.example.com");
    } finally {
      process.env.CATALOG_API_URL = prevCatalog;
      process.env.NEXT_PUBLIC_BACKEND_URL = prevBackend;
    }
  });

  test("isCatalogSlug accepts valid slug characters and rejects invalid", () => {
    expect(isCatalogSlug("valid-slug_123")).toBe(true);
    expect(isCatalogSlug("invalid/slug")).toBe(false);
    expect(isCatalogSlug("../escape")).toBe(false);
    expect(isCatalogSlug("zółty-pierścionek")).toBe(false);
  });

  test("isProductSlug validates product slug format", () => {
    expect(isProductSlug("ring")).toBe(true);
    expect(isProductSlug("gold-ring_18k")).toBe(true);
    expect(isProductSlug("invalid/product")).toBe(false);
    expect(isProductSlug("..%2Fescape")).toBe(false);
  });
});
