import { afterEach, beforeEach, describe, expect, test } from "bun:test";

import {
  createCategoryExistenceCheck,
  createCollectionExistenceCheck,
  createProductExistenceCheck,
  matchCatalogPath,
} from "./product-exists";

const originalEnv = process.env.CATALOG_API_URL;

/** Atrapa `fetch`, która liczy żądania i odpowiada podanym statusem. */
function fakeCatalog(status: number) {
  const urls: string[] = [];
  const fetchImpl = (async (input: RequestInfo | URL) => {
    urls.push(String(input));
    return new Response("{}", { status });
  }) as typeof fetch;

  return { fetchImpl, urls };
}

describe("catalog path matching", () => {
  test("reads kind, locale and slug from a product card path", () => {
    expect(matchCatalogPath("/pl/products/ring")).toEqual({
      kind: "product",
      locale: "pl",
      slug: "ring",
    });
  });

  test("reads kind, locale and slug from category and collection paths", () => {
    expect(matchCatalogPath("/pl/categories/pierscionki")).toEqual({
      kind: "category",
      locale: "pl",
      slug: "pierscionki",
    });
    expect(matchCatalogPath("/en/collections/summer-2026")).toEqual({
      kind: "collection",
      locale: "en",
      slug: "summer-2026",
    });
  });

  test("ignores other paths, list pages, subpaths and unknown locales", () => {
    expect(matchCatalogPath("/pl/login")).toBeNull();
    expect(matchCatalogPath("/pl/products")).toBeNull();
    expect(matchCatalogPath("/pl/categories")).toBeNull();
    expect(matchCatalogPath("/pl/collections")).toBeNull();
    expect(matchCatalogPath("/de/products/ring")).toBeNull();
    expect(matchCatalogPath("/pl/products/ring/reviews")).toBeNull();
    expect(matchCatalogPath("/pl/categories/pierscionki/extra")).toBeNull();
  });
});

describe("product existence check", () => {
  beforeEach(() => {
    process.env.CATALOG_API_URL = "http://catalog.internal:8020";
  });

  afterEach(() => {
    if (originalEnv !== undefined) {
      process.env.CATALOG_API_URL = originalEnv;
    } else {
      delete process.env.CATALOG_API_URL;
    }
  });

  test("asks the public catalog endpoint and reports an existing product", async () => {
    const { fetchImpl, urls } = fakeCatalog(200);
    const productExists = createProductExistenceCheck({ fetch: fetchImpl });

    expect(await productExists("ring", "pl")).toBe(true);
    expect(urls).toEqual([
      "http://catalog.internal:8020/products/ring/?lang=pl",
    ]);
  });

  test("reports a missing product only for a catalog 404", async () => {
    const { fetchImpl } = fakeCatalog(404);
    const productExists = createProductExistenceCheck({ fetch: fetchImpl });

    expect(await productExists("unknown", "pl")).toBe(false);
  });

  test("lets the request through when the catalog fails", async () => {
    const serverError = createProductExistenceCheck({
      fetch: fakeCatalog(503).fetchImpl,
    });
    const networkError = createProductExistenceCheck({
      fetch: (async () => {
        throw new TypeError("fetch failed");
      }) as typeof fetch,
    });
    const timeout = createProductExistenceCheck({
      timeoutMs: 10,
      fetch: ((_input: RequestInfo | URL, init?: RequestInit) =>
        new Promise<Response>((_resolve, reject) => {
          init?.signal?.addEventListener("abort", () =>
            reject(init.signal?.reason),
          );
        })) as typeof fetch,
    });

    expect(await serverError("ring", "pl")).toBe(true);
    expect(await networkError("ring", "pl")).toBe(true);
    expect(await timeout("ring", "pl")).toBe(true);
  });

  test("caches both answers until the TTL passes", async () => {
    let clock = 0;
    const missing = fakeCatalog(404);
    const productExists = createProductExistenceCheck({
      fetch: missing.fetchImpl,
      now: () => clock,
      ttlMs: 1_000,
    });

    expect(await productExists("unknown", "pl")).toBe(false);
    clock = 999;
    expect(await productExists("unknown", "en")).toBe(false);
    expect(missing.urls).toHaveLength(1);

    clock = 1_000;
    await productExists("unknown", "pl");
    expect(missing.urls).toHaveLength(2);
  });

  test("evicts the oldest slug above the size limit", async () => {
    const { fetchImpl, urls } = fakeCatalog(200);
    const productExists = createProductExistenceCheck({
      fetch: fetchImpl,
      maxEntries: 2,
    });

    await productExists("a", "pl");
    await productExists("b", "pl");
    await productExists("c", "pl");
    await productExists("b", "pl");
    expect(urls).toHaveLength(3);

    await productExists("a", "pl");
    expect(urls).toHaveLength(4);
  });

  test("does not evict a live slug when an expired one is refreshed", async () => {
    let clock = 0;
    const { fetchImpl, urls } = fakeCatalog(200);
    const productExists = createProductExistenceCheck({
      fetch: fetchImpl,
      now: () => clock,
      ttlMs: 1_000,
      maxEntries: 2,
    });

    await productExists("a", "pl");
    clock = 500;
    await productExists("b", "pl");
    clock = 1_000;
    await productExists("a", "pl");
    expect(urls).toHaveLength(3);

    await productExists("b", "pl");
    expect(urls).toHaveLength(3);
  });

  test.each(["..%2Fx", "a%2Fb", "z%C5%82oty", "złoty", "", " "])(
    "rejects the slug %p without asking the catalog",
    async (slug: string) => {
      const { fetchImpl, urls } = fakeCatalog(200);
      const productExists = createProductExistenceCheck({ fetch: fetchImpl });

      expect(await productExists(slug, "pl")).toBe(false);
      expect(urls).toEqual([]);
    },
  );

  test("keeps rejected slugs out of the cache", async () => {
    const { fetchImpl, urls } = fakeCatalog(200);
    const productExists = createProductExistenceCheck({
      fetch: fetchImpl,
      maxEntries: 1,
    });

    await productExists("ring", "pl");
    await productExists("a%2Fb", "pl");
    await productExists("ring", "pl");

    expect(urls).toHaveLength(1);
  });

  test("still asks the catalog for every allowed slug character", async () => {
    const { fetchImpl, urls } = fakeCatalog(200);
    const productExists = createProductExistenceCheck({ fetch: fetchImpl });

    expect(await productExists("Gold-ring_2", "pl")).toBe(true);
    expect(urls).toEqual([
      "http://catalog.internal:8020/products/Gold-ring_2/?lang=pl",
    ]);
  });
});

describe("category and collection existence check", () => {
  beforeEach(() => {
    process.env.CATALOG_API_URL = "http://catalog.internal:8020";
  });

  afterEach(() => {
    if (originalEnv !== undefined) {
      process.env.CATALOG_API_URL = originalEnv;
    } else {
      delete process.env.CATALOG_API_URL;
    }
  });

  test("checks category existence against categories retrieve URL", async () => {
    const { fetchImpl, urls } = fakeCatalog(200);
    const categoryExists = createCategoryExistenceCheck({ fetch: fetchImpl });

    expect(await categoryExists("pierscionki", "pl")).toBe(true);
    expect(urls).toEqual([
      "http://catalog.internal:8020/categories/pierscionki/?lang=pl",
    ]);
  });

  test("rejects invalid category slug without network call", async () => {
    const { fetchImpl, urls } = fakeCatalog(200);
    const categoryExists = createCategoryExistenceCheck({ fetch: fetchImpl });

    expect(await categoryExists("nie/poprawny", "pl")).toBe(false);
    expect(urls).toHaveLength(0);
  });

  test("checks collection existence against collections retrieve URL", async () => {
    const { fetchImpl, urls } = fakeCatalog(200);
    const collectionExists = createCollectionExistenceCheck({
      fetch: fetchImpl,
    });

    expect(await collectionExists("lato-2026", "pl")).toBe(true);
    expect(urls).toEqual([
      "http://catalog.internal:8020/collections/lato-2026/?lang=pl",
    ]);
  });

  test("returns false for 404 collection", async () => {
    const { fetchImpl } = fakeCatalog(404);
    const collectionExists = createCollectionExistenceCheck({
      fetch: fetchImpl,
    });

    expect(await collectionExists("nie-ma", "pl")).toBe(false);
  });
});
