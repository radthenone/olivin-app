import { beforeEach, describe, expect, mock, test } from "bun:test";
import { renderToStaticMarkup } from "react-dom/server";
import { NextIntlClientProvider } from "next-intl";

import messages from "@olivin/i18n/messages/pl.json";

const actualNavigation = await import("next/navigation");
const actualAuth = await import("@olivin/features/auth");
const actualCatalog = await import("@olivin/features/catalog");

let mockIsAuthenticated = false;
let savedCookieValue: string | null = null;
let savedProfileValue: string | null = null;
let profileSaveShouldThrow = false;

mock.module("next/navigation", () => ({
  ...actualNavigation,
  useRouter: () => ({ refresh: () => {} }),
}));

mock.module("@olivin/features/auth", () => ({
  ...actualAuth,
  useSession: () => ({ isAuthenticated: mockIsAuthenticated }),
}));

mock.module("@olivin/features/catalog", () => ({
  ...actualCatalog,
  saveDeliveryCountryCookie: (country: string) => {
    savedCookieValue = country;
  },
  saveProfileDeliveryCountry: async (country: string) => {
    if (profileSaveShouldThrow) {
      throw new Error("API error");
    }
    savedProfileValue = country;
  },
}));

const { DeliveryCountrySwitch } = await import("./delivery-country-switch");

describe("DeliveryCountrySwitch", () => {
  beforeEach(() => {
    mockIsAuthenticated = false;
    savedCookieValue = null;
    savedProfileValue = null;
    profileSaveShouldThrow = false;
  });

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
