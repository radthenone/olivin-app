import { afterEach, beforeEach, describe, expect, test } from "bun:test";

import { currencyCookieName, getProductPrice } from "./catalog-api";

const originalFetch = globalThis.fetch;
const originalEnv = process.env.CATALOG_API_URL;

describe("catalog server transport", () => {
  beforeEach(() => {
    process.env.CATALOG_API_URL = "http://catalog.internal:8020";
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
    if (originalEnv !== undefined) {
      process.env.CATALOG_API_URL = originalEnv;
    } else {
      delete process.env.CATALOG_API_URL;
    }
  });

  test("defines currency cookie name", () => {
    expect(currencyCookieName).toBe("currency");
  });

  test("fetches product with language and currency query parameters", async () => {
    let requestedUrl = "";
    globalThis.fetch = (async (input) => {
      requestedUrl = String(input);
      return new Response(
        JSON.stringify({
          id: "1",
          slug: "ring",
          name: "Pierścionek",
          variants: [],
        }),
        { status: 200, headers: { "content-type": "application/json" } },
      );
    }) as typeof fetch;

    const product = await getProductPrice("ring", "pl", "PLN");

    expect(requestedUrl).toBe(
      "http://catalog.internal:8020/products/ring/?lang=pl&currency=PLN",
    );
    expect(product?.slug).toBe("ring");
  });

  test("returns null when catalog responds with 404", async () => {
    globalThis.fetch = (async () => {
      return new Response("Nie znaleziono", { status: 404 });
    }) as typeof fetch;

    const product = await getProductPrice("nieznany", "pl", "PLN");
    expect(product).toBeNull();
  });

  test("throws an error on non-404 unexpected status code", async () => {
    globalThis.fetch = (async () => {
      return new Response("Internal Server Error", { status: 500 });
    }) as typeof fetch;

    await expect(getProductPrice("ring", "pl", "PLN")).rejects.toThrow(
      "Katalog odpowiedział statusem 500.",
    );
  });
});
