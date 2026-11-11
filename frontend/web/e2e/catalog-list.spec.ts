import { expect, test } from "@playwright/test";

/**
 * Przeglądanie listy produktów, kategorii i kolekcji na webie (#359).
 *
 * Domyślnie katalog odpowiada stub API uruchamiany jako dodatkowy `webServer`
 * Playwrighta.
 */
const liveBackend = process.env.E2E_LIVE_BACKEND === "1";

test.describe("Catalog product list, category and collection pages", () => {
  test("shows product list with category tree navigation and pagination", async ({
    page,
  }) => {
    await page.goto("/pl/products");

    // Nagłówek i drzewo kategorii
    await expect(
      page.getByRole("heading", { level: 1, name: "Katalog produktów" }),
    ).toBeVisible();
    await expect(page.getByRole("navigation", { name: "Kategorie" })).toBeVisible();
    await expect(page.getByRole("link", { name: "Pierścionki", exact: true })).toBeVisible();

    // Kafelki produktów z nazwą i ceną
    await expect(page.getByText("Złoty pierścionek").first()).toBeVisible();
    await expect(page.getByText(/od 2.?500,00.?zł/).first()).toBeVisible();

    // Paginacja
    test.skip(liveBackend, "Paginacja stubu ma z góry znaną liczbę stron.");
    await expect(page.getByText("Strona 1 z 2")).toBeVisible();

    // Przejście na drugą stronę
    const nextButton = page.getByRole("link", { name: "Następna" });
    await expect(nextButton).toBeVisible();
    await nextButton.click();

    await expect(page).toHaveURL(/\/pl\/products\?page=2$/);
    await expect(page.getByText("Strona 2 z 2")).toBeVisible();
  });

  test("navigates into a category and shows only category products", async ({
    page,
  }) => {
    test.skip(liveBackend, "Struktura kategorii dotyczy fixture stubu.");

    await page.goto("/pl/products");
    await page.getByRole("link", { name: "Kolczyki", exact: true }).click();

    await expect(page).toHaveURL(/\/pl\/categories\/kolczyki$/);
    await expect(
      page.getByRole("heading", { level: 1, name: "Kolczyki" }),
    ).toBeVisible();
    await expect(page.getByText("Złote kolczyki")).toBeVisible();
    await expect(page.getByText("Srebrne kolczyki")).toBeVisible();
  });

  test("navigates into a marketing collection and displays its products", async ({
    page,
  }) => {
    test.skip(liveBackend, "Kolekcje dotyczą fixture stubu.");

    await page.goto("/pl/collections/lato-2026");

    await expect(
      page.getByRole("heading", { level: 1, name: "Kolekcja Letnia 2026" }),
    ).toBeVisible();
    await expect(page.getByText("Biżuteria na słoneczne dni.")).toBeVisible();
    await expect(page.getByText("Złoty pierścionek")).toBeVisible();
  });

  test("navigates from a product tile to the product detail page", async ({
    page,
  }) => {
    await page.goto("/pl/products");

    const productTileLink = page.getByRole("link", { name: /Złoty pierścionek/ }).first();
    await expect(productTileLink).toBeVisible();
    await productTileLink.click();

    await expect(page).toHaveURL(/\/pl\/products\/ring$/);
    await expect(
      page.getByRole("heading", { level: 1, name: "Złoty pierścionek" }),
    ).toBeVisible();
  });

  test("shows 404 in the page language for unknown category or collection", async ({
    page,
  }) => {
    const categoryResponse = await page.goto("/pl/categories/nieznana-kategoria");
    expect(categoryResponse?.status()).toBe(404);
    await expect(
      page.getByRole("heading", { level: 1, name: "Nie znaleziono kategorii" }),
    ).toBeVisible();

    const collectionResponse = await page.goto("/pl/collections/nieznana-kolekcja");
    expect(collectionResponse?.status()).toBe(404);
    await expect(
      page.getByRole("heading", { level: 1, name: "Nie znaleziono kolekcji" }),
    ).toBeVisible();
  });

  test("shows the product list in English under /en prefix", async ({
    page,
  }) => {
    await page.goto("/en/products");

    await expect(
      page.getByRole("heading", { level: 1, name: "Product catalog" }),
    ).toBeVisible();
    await expect(
      page.getByRole("navigation", { name: "Categories" }),
    ).toBeVisible();
    await expect(page.getByRole("link", { name: "All products" })).toBeVisible();
  });
});
