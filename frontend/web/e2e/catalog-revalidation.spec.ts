import { expect, test } from "@playwright/test";

import { isProductSlug } from "../src/lib/catalog-url";

/**
 * Rewalidacja keszu katalogu na webie (ADR 0034, #358).
 *
 * Endpoint POST /api/revalidate pozwala backendowi unieważniać wpisy kesza
 * (np. po zapisie produktu z tagiem `product:<slug>` lub przeliczeniu cen
 * z tagiem `catalog`). Żądanie wymaga nagłówka `X-Revalidate-Secret` i nie może
 * być przekierowywane na prefiks języka przez middleware.
 */

const liveBackend = process.env.E2E_LIVE_BACKEND === "1";
const revalidateSecret =
  process.env.REVALIDATE_SECRET ?? "dev-revalidate-secret";
const stubPort = Number(process.env.E2E_STUB_PORT) || 3200;
const stubUrl = `http://localhost:${stubPort}`;

test.describe("POST /api/revalidate authorization and routing", () => {
  test("rejects POST /api/revalidate without secret with 401 and no redirect", async ({
    page,
  }) => {
    const response = await page.request.post("/api/revalidate", {
      maxRedirects: 0,
      data: { tags: ["product:ring"] },
    });

    expect(response.status()).toBe(401);
    expect(response.headers()["location"]).toBeUndefined();
  });

  test("rejects POST /api/revalidate with invalid secret with 401 and no redirect", async ({
    page,
  }) => {
    const response = await page.request.post("/api/revalidate", {
      maxRedirects: 0,
      headers: { "x-revalidate-secret": "wrong-secret" },
      data: { tags: ["product:ring"] },
    });

    expect(response.status()).toBe(401);
    expect(response.headers()["location"]).toBeUndefined();
  });

  test("rejects POST /api/revalidate with invalid payload with 400 and no redirect", async ({
    page,
  }) => {
    const response = await page.request.post("/api/revalidate", {
      maxRedirects: 0,
      headers: { "x-revalidate-secret": revalidateSecret },
      data: { tags: [] },
    });

    expect(response.status()).toBe(400);
    expect(response.headers()["location"]).toBeUndefined();
  });
});

test.describe("catalog cache revalidation flow", () => {
  test("updates product card price after stub change and revalidation with product tag", async ({
    page,
    request,
  }) => {
    test.skip(
      liveBackend,
      "Podmiana cen w stubie dotyczy wyłącznie środowiska testowego ze stubem.",
    );

    const slug = "ring";
    if (!isProductSlug(slug)) {
      throw new Error(`Niepoprawny slug produktu: ${slug}`);
    }

    // 1. Sprawdzenie początkowej ceny z kesza karty produktu (2 500,00 zł).
    await page.goto(`/pl/products/${slug}`);
    await expect(page.getByText(/2.?500,00.?zł/)).toBeVisible();

    try {
      // 2. Symulacja przeliczenia / zmiany ceny w katalogu (stub API).
      const updateResponse = await request.post(`${stubUrl}/__test__/fixture`, {
        data: { slug, priceAmount: 320000 },
      });
      expect(updateResponse.ok()).toBe(true);

      // 3. Wysłanie rewalidacji tagu product:<slug> do endpointu webu.
      const revalidateResponse = await page.request.post("/api/revalidate", {
        maxRedirects: 0,
        headers: { "x-revalidate-secret": revalidateSecret },
        data: { tags: [`product:${slug}`] },
      });

      expect(revalidateResponse.status()).toBe(200);
      expect(revalidateResponse.headers()["location"]).toBeUndefined();
      const body = (await revalidateResponse.json()) as {
        revalidated: boolean;
        tags: string[];
      };
      expect(body.revalidated).toBe(true);
      expect(body.tags).toContain(`product:${slug}`);

      // 4. Ponowne załadowanie karty produktu — prezentacja nowej ceny (3 200,00 zł).
      await page.goto(`/pl/products/${slug}`);
      await expect(page.getByText(/3.?200,00.?zł/)).toBeVisible();
    } finally {
      // 5. Przywrócenie stanu początkowego stubu i rewalidacja.
      await request.delete(`${stubUrl}/__test__/fixture`);
      await page.request.post("/api/revalidate", {
        headers: { "x-revalidate-secret": revalidateSecret },
        data: { tags: [`product:${slug}`] },
      });
    }
  });
});
