import { describe, expect, test } from "bun:test";

import { formatMoney } from "./index";

/**
 * Formatowanie jest wyłącznie prezentacją: kwota w groszach z API jest dzielona
 * przez 100 dopiero tuż przed `Intl.NumberFormat`; żadne obliczenia nie
 * wykonują się na wyniku dzielenia.
 */
describe("formatMoney", () => {
  test("formats grosze as a Polish złoty amount", () => {
    const formatted = formatMoney({ amount: 123_450, currency: "PLN" }, "pl");

    expect(formatted).toContain("zł");
    expect(formatted).toMatch(/1[\s\u00a0]?234,50/);
  });

  test("uses the locale separators for euro", () => {
    const formatted = formatMoney({ amount: 123_450, currency: "EUR" }, "en");

    expect(formatted).toContain("€");
    expect(formatted).toMatch(/1,234\.50/);
  });

  test("keeps the currency from the API even when the locale differs", () => {
    expect(formatMoney({ amount: 500, currency: "PLN" }, "en")).toContain("PLN");
  });
});
