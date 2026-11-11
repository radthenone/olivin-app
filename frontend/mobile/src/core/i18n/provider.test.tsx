import { describe, expect, test } from "bun:test";
import { renderToString } from "react-dom/server";
import { useLocale, useTranslations } from "use-intl";
import { AppIntlProvider } from "./provider";
import { setupIntlPolyfills } from "./polyfills";

function TestConsumer() {
  const t = useTranslations("catalog");
  const locale = useLocale();

  return (
    <div>
      <span data-testid="locale">{locale}</span>
      <span data-testid="title">{t("list.title")}</span>
      <span data-testid="plural-one">{t("list.productCount", { count: 1 })}</span>
      <span data-testid="plural-few">{t("list.productCount", { count: 3 })}</span>
      <span data-testid="plural-many">{t("list.productCount", { count: 5 })}</span>
    </div>
  );
}

describe("AppIntlProvider on mobile", () => {
  test("ensures Intl.PluralRules exists via setupIntlPolyfills", () => {
    setupIntlPolyfills();
    expect(typeof Intl.PluralRules).toBe("function");
  });

  test("renders ICU messages with proper Polish plurals", () => {
    const html = renderToString(
      <AppIntlProvider initialLocale="pl">
        <TestConsumer />
      </AppIntlProvider>,
    );

    expect(html).toContain("Katalog produktów");
    expect(html).toContain("1 produkt");
    expect(html).toContain("3 produkty");
    expect(html).toContain("5 produktów");
  });

  test("renders ICU messages in English when locale is en", () => {
    const html = renderToString(
      <AppIntlProvider initialLocale="en">
        <TestConsumer />
      </AppIntlProvider>,
    );

    expect(html).toContain("Product catalog");
    expect(html).toContain("1 product");
    expect(html).toContain("3 products");
    expect(html).toContain("5 products");
  });
});
