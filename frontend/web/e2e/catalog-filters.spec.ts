import { expect, test } from "@playwright/test";

/**
 * Filtry, wyszukiwanie i sortowanie katalogu na webie (#360).
 *
 * Testy przeglądarkowe weryfikują odbicie filtrów w adresie URL, obsługę
 * historii przeglądarki (przycisk „wstecz”), bezpośrednie wejście z linku
 * z filtrami oraz pusty wynik z czyszczeniem jednym ruchem.
 */
const liveBackend = process.env.E2E_LIVE_BACKEND === "1";

test.describe("Web catalog filters, search and sorting in URL (#360)", () => {
  test("filters by keyword search and reflects in URL", async ({ page }) => {
    test.skip(liveBackend, "Fixture stubu mają z góry znane nazwy produktów.");

    await page.goto("/pl/products");

    const searchInput = page.getByRole("searchbox", {
      name: "Szukaj w katalogu",
    });
    await expect(searchInput).toBeVisible();

    await searchInput.fill("złoty pierścionek");
    await page.getByRole("button", { name: "Szukaj" }).click();

    await expect(page).toHaveURL(
      /search=z%C5%82oty\+pier%C5%9Bcionek|search=z%C5%82oty\+pier%C5%9Bcionek/,
    );
    const main = page.getByRole("main");
    await expect(main.getByText("Złoty pierścionek")).toBeVisible();
  });

  test("filters by material attribute and reflects in URL", async ({
    page,
  }) => {
    test.skip(liveBackend, "Fixture stubu mają określone kruszce.");

    await page.goto("/pl/products");

    const materialSelect = page.getByLabel("Kruszec");
    await expect(materialSelect).toBeVisible();

    await materialSelect.selectOption("silver");

    await expect(page).toHaveURL(/material=silver/);
    const main = page.getByRole("main");
    await expect(main.getByText("Srebrne kolczyki")).toBeVisible();
    await expect(main.getByText("Złoty pierścionek")).not.toBeVisible();
  });

  test("sorts products and reflects ordering parameter in URL", async ({
    page,
  }) => {
    test.skip(liveBackend, "Kolejność w stubie odpowiada cenom.");

    await page.goto("/pl/products");

    const sortSelect = page.getByLabel("Sortowanie");
    await expect(sortSelect).toBeVisible();

    await sortSelect.selectOption("price");

    await expect(page).toHaveURL(/ordering=price/);
  });

  test("filter change resets pagination back to page 1", async ({ page }) => {
    test.skip(liveBackend, "Stronicowanie dotyczy 16 fixture w stubie.");

    await page.goto("/pl/products?page=2");
    await expect(page).toHaveURL(/page=2/);

    const materialSelect = page.getByLabel("Kruszec");
    await materialSelect.selectOption("gold");

    await expect(page).toHaveURL(/material=gold/);
    // page=2 powinno zostać usunięte z adresu
    expect(page.url()).not.toContain("page=2");
  });

  test("browser back button restores previous filter state", async ({
    page,
  }) => {
    test.skip(liveBackend, "Wymaga deterministycznych stanów stubu.");

    await page.goto("/pl/products");

    const materialSelect = page.getByLabel("Kruszec");
    await materialSelect.selectOption("silver");
    await expect(page).toHaveURL(/material=silver/);

    await page.goBack();
    expect(page.url()).not.toContain("material=silver");
  });

  test("loads filtered state directly from URL link", async ({ page }) => {
    test.skip(liveBackend, "Dotyczy fixture stubu.");

    await page.goto("/pl/products?material=silver");

    const materialSelect = page.getByLabel("Kruszec");
    await expect(materialSelect).toHaveValue("silver");

    const main = page.getByRole("main");
    await expect(main.getByText("Srebrne kolczyki")).toBeVisible();
    await expect(main.getByText("Złoty pierścionek")).not.toBeVisible();
  });

  test("shows empty message with one-click filter clear when no products match", async ({
    page,
  }) => {
    test.skip(liveBackend, "Niemożliwy filtr dotyczy stubu.");

    await page.goto("/pl/products?search=fraza-ktorej-nie-ma-w-katalogu");

    const main = page.getByRole("main");
    await expect(
      main.getByText("Brak produktów spełniających wybrane kryteria."),
    ).toBeVisible();

    const clearButton = main.getByRole("link", { name: "Wyczyść filtry" });
    await expect(clearButton).toBeVisible();

    await clearButton.click();

    await expect(page).toHaveURL(/\/pl\/products$/);
    await expect(main.getByText("Złoty pierścionek")).toBeVisible();
  });

  test("clearing filters and browser back reset search and price fields", async ({
    page,
  }) => {
    test.skip(liveBackend, "Fixture stubu mają z góry znane nazwy produktów.");

    await page.goto("/pl/products");

    const searchInput = page.getByRole("searchbox", {
      name: "Szukaj w katalogu",
    });
    const priceMin = page.locator("#filter-price-min");

    await searchInput.fill("pierścionek");
    await page.getByRole("button", { name: "Szukaj" }).click();
    await expect(page).toHaveURL(/search=/);

    await priceMin.fill("100");
    await page.getByRole("button", { name: "Zastosuj filtry" }).click();
    await expect(page).toHaveURL(/priceMin=100/);

    await page
      .locator("aside")
      .getByRole("link", { name: "Wyczyść filtry" })
      .click();
    await expect(page).toHaveURL(/\/pl\/products$/);
    await expect(searchInput).toHaveValue("");
    await expect(priceMin).toHaveValue("");

    // „Wstecz” odtwarza adres z filtrami, a pola odzwierciedlają ten adres.
    await page.goBack();
    await expect(page).toHaveURL(/priceMin=100/);
    await expect(searchInput).toHaveValue("pierścionek");
    await expect(priceMin).toHaveValue("100");

    await page.goBack();
    await expect(page).not.toHaveURL(/priceMin=/);
    await expect(priceMin).toHaveValue("");

    await page.goBack();
    await expect(page).not.toHaveURL(/search=/);
    await expect(searchInput).toHaveValue("");
  });

  test("ignores non-finite prices and control characters from the URL", async ({
    page,
  }) => {
    test.skip(liveBackend, "Fixture stubu mają z góry znane nazwy produktów.");

    await page.goto("/pl/products?priceMin=Infinity&priceMax=1e999&search=%00");

    const main = page.getByRole("main");
    await expect(main.getByText("Złoty pierścionek")).toBeVisible();
    await expect(page.locator("#filter-price-min")).toHaveValue("");
  });
});
