import { afterEach, beforeEach, describe, expect, test } from "bun:test";

import {
  currencyCookieName,
  fetchCategoriesTree,
  fetchCategory,
  fetchCollection,
  fetchProductsList,
  getProductPrice,
} from "./catalog-api";

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

  test.each(["../x.y", "a/b", "złoty"])(
    "returns null for the slug %p without calling the catalog",
    async (slug: string) => {
      let calls = 0;
      globalThis.fetch = (async () => {
        calls += 1;
        return new Response("{}", { status: 200 });
      }) as typeof fetch;

      expect(await getProductPrice(slug, "pl", "PLN")).toBeNull();
      expect(calls).toBe(0);
    },
  );

  test("fetches products list with page and category", async () => {
    let requestedUrl = "";
    globalThis.fetch = (async (input) => {
      requestedUrl = String(input);
      return new Response(
        JSON.stringify({
          count: 1,
          results: [
            {
              id: "1",
              slug: "ring",
              name: "Pierścionek",
            },
          ],
        }),
        { status: 200, headers: { "content-type": "application/json" } },
      );
    }) as typeof fetch;

    const list = await fetchProductsList(
      { page: 2, category: "pierscionki" },
      "pl",
    );

    expect(requestedUrl).toContain("/products/");
    expect(requestedUrl).toContain("page=2");
    expect(requestedUrl).toContain("category=pierscionki");
    expect(requestedUrl).toContain("lang=pl");
    expect(list?.count).toBe(1);
  });

  test("returns empty list if category or collection has invalid slug", async () => {
    let calls = 0;
    globalThis.fetch = (async () => {
      calls += 1;
      return new Response("{}", { status: 200 });
    }) as typeof fetch;

    const res1 = await fetchProductsList({ category: "../invalid" }, "pl");
    expect(res1).toEqual({ count: 0, results: [] });

    const res2 = await fetchProductsList({ collection: "nie/poprawny" }, "pl");
    expect(res2).toEqual({ count: 0, results: [] });

    expect(calls).toBe(0);
  });

  test("fetches categories tree with language", async () => {
    let requestedUrl = "";
    globalThis.fetch = (async (input) => {
      requestedUrl = String(input);
      return new Response(
        JSON.stringify([
          { id: "1", name: "Pierścionki", slug: "pierscionki", children: [] },
        ]),
        { status: 200, headers: { "content-type": "application/json" } },
      );
    }) as typeof fetch;

    const tree = await fetchCategoriesTree("en");
    expect(requestedUrl).toBe(
      "http://catalog.internal:8020/categories/?lang=en",
    );
    expect(tree).toHaveLength(1);
    expect(tree[0].slug).toBe("pierscionki");
  });

  test("fetches single category and returns null on 404 or invalid slug", async () => {
    let requestedUrl = "";
    globalThis.fetch = (async (input) => {
      requestedUrl = String(input);
      return new Response(
        JSON.stringify({
          id: "1",
          name: "Pierścionki",
          slug: "pierscionki",
          children: [],
        }),
        { status: 200, headers: { "content-type": "application/json" } },
      );
    }) as typeof fetch;

    const cat = await fetchCategory("pierscionki", "pl");
    expect(requestedUrl).toBe(
      "http://catalog.internal:8020/categories/pierscionki/?lang=pl",
    );
    expect(cat?.slug).toBe("pierscionki");

    expect(await fetchCategory("../invalid", "pl")).toBeNull();
  });

  test("fetches single collection and returns null on 404 or invalid slug", async () => {
    let requestedUrl = "";
    globalThis.fetch = (async (input) => {
      requestedUrl = String(input);
      return new Response(
        JSON.stringify({
          id: "1",
          name: "Lato 2026",
          slug: "lato-2026",
          description: "Letnia kolekcja",
          productCount: 5,
        }),
        { status: 200, headers: { "content-type": "application/json" } },
      );
    }) as typeof fetch;

    const col = await fetchCollection("lato-2026", "pl");
    expect(requestedUrl).toBe(
      "http://catalog.internal:8020/collections/lato-2026/?lang=pl",
    );
    expect(col?.slug).toBe("lato-2026");

    expect(await fetchCollection("../invalid", "pl")).toBeNull();
  });
});
