import { afterEach, beforeEach, describe, expect, test } from "bun:test";

import {
  createProductExistenceCheck,
  matchProductPath,
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

describe("product path matching", () => {
  test("reads locale and slug from a product card path", () => {
    expect(matchProductPath("/pl/products/ring")).toEqual({
      locale: "pl",
      slug: "ring",
    });
  });

  test("ignores other paths and unknown locales", () => {
    expect(matchProductPath("/pl/login")).toBeNull();
    expect(matchProductPath("/de/products/ring")).toBeNull();
    expect(matchProductPath("/pl/products/ring/reviews")).toBeNull();
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
});
