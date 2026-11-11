/**
 * Polyfille dla środowiska Hermes na React Native (ADR 0035).
 *
 * Hermes w starszych wydaniach nie posiadał wbudowanego `Intl.PluralRules`,
 * co prowadziło do problemów z odmianą polskich form liczby mnogiej
 * (one/few/many/other). W razie braku, podpinamy fallback.
 */
export function setupIntlPolyfills(): void {
  if (typeof Intl === "undefined") {
    return;
  }

  // W nowoczesnych wersjach Hermes (React Native 0.86+) Intl.PluralRules
  // jest już wbudowane. Jeśli nie ma, rejestrujemy minimalny fallback zgodny z ICU CLDR dla pl i en.
  if (!("PluralRules" in Intl)) {
    // Prosty polyfill zgodny z regułami CLDR dla pl i en
    class MinimalPluralRules {
      private locale: string;

      constructor(locale = "pl") {
        this.locale = locale.toLowerCase().startsWith("en") ? "en" : "pl";
      }

      select(n: number): "one" | "few" | "many" | "other" {
        if (this.locale === "en") {
          return n === 1 ? "one" : "other";
        }
        // Polski CLDR: 1 -> one; 2-4 (oprócz 12-14) -> few; reszta (0, 5-9, 11-19 itd.) -> many
        if (n === 1) {
          return "one";
        }
        const rem10 = n % 10;
        const rem100 = n % 100;
        if (rem10 >= 2 && rem10 <= 4 && (rem100 < 12 || rem100 > 14)) {
          return "few";
        }
        return "many";
      }
    }

    Object.defineProperty(Intl, "PluralRules", {
      value: MinimalPluralRules,
      writable: true,
      configurable: true,
    });
  }
}
