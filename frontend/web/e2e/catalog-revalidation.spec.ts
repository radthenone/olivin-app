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
  test("shows the new product name only after revalidation with product tag", async ({
    page,
    request,
  }) => {
    test.skip(
      liveBackend,
      "Podmiana danych w stubie dotyczy wyłącznie środowiska testowego ze stubem.",
    );

    // Slug używany wyłącznie tutaj — product-page.spec.ts korzysta z `ring`,
    // a pliki specyfikacji biegną równolegle na wspólnym stubie.
    const slug = "necklace";
    if (!isProductSlug(slug)) {
      throw new Error(`Niepoprawny slug produktu: ${slug}`);
    }
    const oldName = "Naszyjnik na zamówienie";
    const newName = "Naszyjnik po rewalidacji";
    const heading = (name: string) =>
      page.getByRole("heading", { level: 1, name });

    // 1. Nazwa początkowa trafia do kesza (cena jest dynamiczna, nazwa nie).
    await page.goto(`/pl/products/${slug}`);
    await expect(heading(oldName)).toBeVisible();

    try {
      // 2. Zmiana nazwy w katalogu (stub API).
      const updateResponse = await request.post(`${stubUrl}/__test__/fixture`, {
        data: { slug, name: newName },
      });
      expect(updateResponse.ok()).toBe(true);

      // 3. Kontrola negatywna: bez rewalidacji kesz nadal zwraca starą nazwę.
      await page.goto(`/pl/products/${slug}`);
      await expect(heading(oldName)).toBeVisible();
      await expect(heading(newName)).toHaveCount(0);

      // 4. Rewalidacja tagu product:<slug>.
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

      // 5. Po rewalidacji strona pokazuje nową nazwę.
      await page.goto(`/pl/products/${slug}`);
      await expect(heading(newName)).toBeVisible();
    } finally {
      // 6. Przywrócenie stanu początkowego stubu i rewalidacja.
      await request.delete(`${stubUrl}/__test__/fixture`);
      await page.request.post("/api/revalidate", {
        headers: { "x-revalidate-secret": revalidateSecret },
        data: { tags: [`product:${slug}`] },
      });
    }
  });
});
