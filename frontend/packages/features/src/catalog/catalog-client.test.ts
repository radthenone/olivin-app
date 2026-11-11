import { describe, expect, test } from "bun:test";
import type {
  PaginatedProductListList,
  ProductDetail,
} from "@olivin/api/generated/apps/schemas";

import {
  CatalogError,
  createCatalogClient,
  isCatalogSlug,
} from "./catalog-client";

describe("catalog slug validation", () => {
  test("isCatalogSlug accepts valid slug characters and rejects invalid", () => {
    expect(isCatalogSlug("gold-ring_18k")).toBe(true);
    expect(isCatalogSlug("emerald-necklace")).toBe(true);
    expect(isCatalogSlug("ring123")).toBe(true);
    expect(isCatalogSlug("ring")).toBe(true);

    expect(isCatalogSlug("invalid/slug")).toBe(false);
    expect(isCatalogSlug("../escape")).toBe(false);
    expect(isCatalogSlug("zółty-pierścionek")).toBe(false);
    expect(isCatalogSlug("")).toBe(false);
  });
});

describe("catalog client (public transport without session)", () => {
  const baseUrl = "https://catalog.example.com";

  test("fetchProduct validates slug and returns null for invalid slug without request", async () => {
    let called = false;
    const fetchFn = async () => {
      called = true;
      return new Response(null, { status: 200 });
    };

    const client = createCatalogClient({ baseUrl, fetch: fetchFn });
    const result = await client.fetchProduct("invalid/slug", "pl");

    expect(result).toBeNull();
    expect(called).toBe(false);
  });

  test("fetchProduct requests public endpoint without session headers and returns null on 404", async () => {
    let capturedHeaders: Headers | undefined;
    let capturedUrl: string | undefined;

    const fetchFn = async (input: RequestInfo | URL, init?: RequestInit) => {
      capturedUrl = String(input);
      capturedHeaders = new Headers(init?.headers);
      return new Response(null, { status: 404 });
    };

    const client = createCatalogClient({ baseUrl, fetch: fetchFn });
    const result = await client.fetchProduct("diamond-ring", "pl", "PLN");

    expect(result).toBeNull();
    expect(capturedUrl).toContain("/products/diamond-ring/");
    expect(capturedUrl).toContain("lang=pl");
    expect(capturedUrl).toContain("currency=PLN");
    expect(capturedHeaders?.get("accept")).toBe("application/json");
    expect(capturedHeaders?.get("x-session-token")).toBeNull();
  });

  test("fetchProduct returns product details on 200", async () => {
    const mockProduct = {
      id: "prod-1",
      slug: "diamond-ring",
      name: "Pierścionek z diamentem",
      variants: [],
    } as unknown as ProductDetail;

    const fetchFn = async () =>
      new Response(JSON.stringify(mockProduct), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });

    const client = createCatalogClient({ baseUrl, fetch: fetchFn });
    const result = await client.fetchProduct("diamond-ring", "pl");

    expect(result).toEqual(mockProduct);
  });

  test("fetchProductsList returns empty list for invalid category or collection slug", async () => {
    let called = false;
    const fetchFn = async () => {
      called = true;
      return new Response(null, { status: 200 });
    };

    const client = createCatalogClient({ baseUrl, fetch: fetchFn });
    const catResult = await client.fetchProductsList(
      { category: "invalid/cat" },
      "pl",
    );
    expect(catResult).toEqual({ count: 0, results: [] });
    expect(called).toBe(false);

    const colResult = await client.fetchProductsList(
      { collection: "../coll" },
      "pl",
    );
    expect(colResult).toEqual({ count: 0, results: [] });
    expect(called).toBe(false);
  });

  test("fetchProductsList passes query params, Accept-Language and returns null on 404", async () => {
    let capturedHeaders: Headers | undefined;
    let capturedUrl: string | undefined;

    const fetchFn = async (input: RequestInfo | URL, init?: RequestInit) => {
      capturedUrl = String(input);
      capturedHeaders = new Headers(init?.headers);
      return new Response(null, { status: 404 });
    };

    const client = createCatalogClient({ baseUrl, fetch: fetchFn });
    const result = await client.fetchProductsList(
      { page: 99, pageSize: 12, category: "rings" },
      "pl",
    );

    expect(result).toBeNull();
    expect(capturedUrl).toContain("/products/");
    expect(capturedUrl).toContain("page=99");
    expect(capturedUrl).toContain("pageSize=12");
    expect(capturedUrl).toContain("category=rings");
    expect(capturedUrl).toContain("lang=pl");
    expect(capturedHeaders?.get("accept")).toBe("application/json");
    expect(capturedHeaders?.get("accept-language")).toBe("pl");
  });

  test("fetchProductsList returns paginated list on 200", async () => {
    const mockList = {
      count: 1,
      results: [{ id: "p1", slug: "ring-1", name: "Pierścionek" }],
    } as unknown as PaginatedProductListList;

    const fetchFn = async () =>
      new Response(JSON.stringify(mockList), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });

    const client = createCatalogClient({ baseUrl, fetch: fetchFn });
    const result = await client.fetchProductsList({ page: 1 }, "pl");

    expect(result).toEqual(mockList);
  });

  test("catalog requests omit credentials (public transport)", async () => {
    let capturedInit: RequestInit | undefined;

    const fetchFn = async (_input: RequestInfo | URL, init?: RequestInit) => {
      capturedInit = init;
      return new Response(JSON.stringify({ count: 0, results: [] }), {
        status: 200,
      });
    };

    const client = createCatalogClient({ baseUrl, fetch: fetchFn });
    await client.fetchProductsList({ page: 1 }, "pl");

    expect(capturedInit?.credentials).toBe("omit");
  });

  test("throws a typed CatalogError with the HTTP status on a server error", async () => {
    const fetchFn = async () =>
      new Response("Service Unavailable", { status: 503 });

    const client = createCatalogClient({ baseUrl, fetch: fetchFn });
    const error = await client
      .fetchProductsList({ page: 1 }, "pl")
      .catch((e: unknown) => e);

    expect(error).toBeInstanceOf(CatalogError);
    expect((error as CatalogError).status).toBe(503);
    expect((error as CatalogError).isNetworkError).toBe(false);
  });

  test("wraps a failed fetch in a CatalogError flagged as a network error", async () => {
    const fetchFn = async () => {
      throw new TypeError("Network request failed");
    };

    const client = createCatalogClient({ baseUrl, fetch: fetchFn });
    const error = await client
      .fetchProduct("diamond-ring", "pl")
      .catch((e: unknown) => e);

    expect(error).toBeInstanceOf(CatalogError);
    expect((error as CatalogError).status).toBe(0);
    expect((error as CatalogError).isNetworkError).toBe(true);
  });
});
