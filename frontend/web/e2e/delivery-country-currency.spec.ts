import { expect, test } from "@playwright/test";

/**
 * Przełącznik kraju dostawy i waluta z kraju (ADR 0035, #362).
 *
 * Klient spoza Polski wybiera w nagłówku swój kraj Unii i widzi ceny w euro
 * w całym katalogu. Bez wyboru widzi złote. Wybór przetrwa przeładowanie,
 * a zmiana języka nie zmienia waluty.
 */
const liveBackend = process.env.E2E_LIVE_BACKEND === "1";

test.describe("Delivery country switch with currency", () => {
  test("defaults to PLN, switches to EUR on EU country selection, persists reload and ignores language switch", async ({
    page,
  }) => {
    test.skip(liveBackend, "Waluta w stubie dotyczy wyłącznie stubu.");

    // 1. Domyślnie brak wyboru: ceny w złotych na liście produktów
    await page.goto("/pl/products");
    await expect(page.getByText(/od 2.?450,00.?zł/).first()).toBeVisible();

    const countrySelect = page.locator("#delivery-country-select");
    await expect(countrySelect).toBeVisible();
    await expect(countrySelect).toHaveValue("PL");

    // 2. Wybór kraju Unii (Niemcy - DE) przełącza ceny na EUR na liście
    await countrySelect.selectOption("DE");
    await expect(countrySelect).toHaveValue("DE");
    await expect(page.getByText(/€/).first()).toBeVisible();

    // 3. Na karcie produktu cena jest w euro
    await page.goto("/pl/products/ring");
    await expect(page.getByText(/581,50.?€/)).toBeVisible();

    // 4. Wybór przetrwa przeładowanie strony
    await page.reload();
    await expect(countrySelect).toHaveValue("DE");
    await expect(page.getByText(/581,50.?€/)).toBeVisible();

    // 5. Zmiana języka nie zmienia waluty
    await page.goto("/en/products/ring");
    await expect(countrySelect).toHaveValue("DE");
    await expect(page.getByText(/€581\.50/)).toBeVisible();
    await expect(page.getByText("Ship to")).toBeVisible();

    // 6. Przełączenie z powrotem na Polskę przywraca PLN
    await countrySelect.selectOption("PL");
    await expect(countrySelect).toHaveValue("PL");
    // Strona /en/: złote w formacie angielskim (`PLN 2,500.00`), cena aktywnego
    // wariantu leży w regionie aria-live (osobno od ceny grawerunku).
    await expect(
      page.locator('[aria-live="polite"]').getByText(/PLN\s?2,500\.00/),
    ).toBeVisible();
  });
});
