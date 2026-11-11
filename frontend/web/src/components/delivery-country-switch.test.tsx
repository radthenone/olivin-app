import { describe, expect, test } from "bun:test";
import { renderToStaticMarkup } from "react-dom/server";
import { NextIntlClientProvider } from "next-intl";

import messages from "@olivin/i18n/messages/pl.json";
import { DeliveryCountrySwitch } from "./delivery-country-switch";

describe("DeliveryCountrySwitch", () => {
  test("renders ship to label and select with EU countries", () => {
    const html = renderToStaticMarkup(
      <NextIntlClientProvider
        locale="pl"
        messages={messages}
        onError={() => {}}
      >
        <DeliveryCountrySwitch initialCountry="PL" />
      </NextIntlClientProvider>,
    );

    expect(html).toContain("Wysyłka do");
    expect(html).toContain("<select");
    expect(html).toContain('id="delivery-country-select"');
    expect(html).toContain("Polska");
    expect(html).toContain("Niemcy");
    expect(html).toContain("Francja");
    // Ensure non-EU countries are not in the select
    expect(html).not.toContain("Stany Zjednoczone");
    expect(html).not.toContain("Wielka Brytania");
  });

  test("renders with selected country", () => {
    const html = renderToStaticMarkup(
      <NextIntlClientProvider
        locale="pl"
        messages={messages}
        onError={() => {}}
      >
        <DeliveryCountrySwitch initialCountry="DE" />
      </NextIntlClientProvider>,
    );

    expect(html).toContain("<select");
    expect(html).toContain('value="DE"');
  });
});
