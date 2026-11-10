import { describe, expect, test } from "bun:test";

import { formatMoney } from "./index";

/**
 * Formatowanie jest wyłącznie prezentacją: grosze przychodzą z API i nigdy nie
 * zamieniają się w liczbę zmiennoprzecinkową przed podziałem (ADR 0009).
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
