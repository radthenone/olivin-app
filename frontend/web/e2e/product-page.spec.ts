import { expect, test } from "@playwright/test";

/**
 * Karta produktu na webie (#357).
 *
 * Domyślnie katalog odpowiada stub API uruchamiany jako dodatkowy `webServer`
 * Playwrighta, więc test nie potrzebuje Django. `E2E_LIVE_BACKEND=1` kieruje
 * transport serwerowy na prawdziwy backend i wymaga `E2E_PRODUCT_SLUG`.
 */
const liveBackend = process.env.E2E_LIVE_BACKEND === "1";
const liveSlug = process.env.E2E_PRODUCT_SLUG ?? "";
const slug = liveBackend ? liveSlug : "ring";

test.beforeEach(() => {
  test.skip(
    liveBackend && !liveSlug,
    "E2E_LIVE_BACKEND=1 wymaga E2E_PRODUCT_SLUG.",
  );
});

test("shows the cached product card with a PLN price and every availability category", async ({
  page,
}) => {
  await page.goto(`/pl/products/${slug}`);

  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
  await expect(page.getByText("Dostępny", { exact: true })).toBeVisible();

  test.skip(liveBackend, "Szczegóły fixture'u dotyczą wyłącznie stubu.");

  await expect(page.getByText(/2.?500,00.?zł/)).toBeVisible();
  await expect(page.getByText("Ostatnie sztuki", { exact: true })).toBeVisible();
  await expect(page.getByText("Niedostępny", { exact: true })).toBeVisible();
  await expect(page.getByText("Diament", { exact: true })).toBeVisible();
  await expect(page.getByText(/Grawer dostępny/)).toBeVisible();
  await expect(page.getByText("Ocena 4,5 z 5")).toBeVisible();
});

test("shows the product card in the language from the URL prefix", async ({
  page,
}) => {
  test.skip(liveBackend, "Teksty fixture'u dotyczą wyłącznie stubu.");

  await page.goto("/en/products/ring");

  await expect(
    page.getByRole("heading", { level: 1, name: "Gold ring" }),
  ).toBeVisible();
  await expect(page.getByText("Available", { exact: true })).toBeVisible();
  await expect(page.getByText("Last few items", { exact: true })).toBeVisible();
});

test("reads the currency from the cookie without changing the URL", async ({
  page,
}) => {
  test.skip(liveBackend, "Waluta w stubie dotyczy wyłącznie stubu.");

  await page.context().addCookies([
    { name: "currency", value: "EUR", domain: "localhost", path: "/" },
  ]);
  await page.goto("/pl/products/ring");

  await expect(page.getByText(/581,50.?€/)).toBeVisible();
  await expect(page).toHaveURL(/\/pl\/products\/ring$/);
});

test("shows a 404 in the page language for an unknown slug", async ({
  page,
}) => {
  const response = await page.goto("/pl/products/nie-ma-takiego-produktu");

  expect(response?.status()).toBe(404);
  await expect(
    page.getByRole("heading", { level: 1, name: "Nie znaleziono produktu" }),
  ).toBeVisible();
});
