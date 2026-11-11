import { describe, expect, test } from "bun:test";

import { isCatalogSlug } from "./catalog-url";

describe("catalog-url", () => {
  test("isCatalogSlug accepts valid slug characters and rejects invalid", () => {
    expect(isCatalogSlug("valid-slug_123")).toBe(true);
    expect(isCatalogSlug("invalid/slug")).toBe(false);
    expect(isCatalogSlug("../escape")).toBe(false);
    expect(isCatalogSlug("zółty-pierścionek")).toBe(false);
  });
});
