import { describe, expect, test } from "bun:test";
import { buildHeaders } from "./headers";
import { getActiveLocale, setActiveLocale } from "../i18n/locale";

describe("mobile buildHeaders", () => {
  test("includes Accept-Language matching active interface locale", async () => {
    setActiveLocale("pl");
    expect(getActiveLocale()).toBe("pl");

    const headersPl = await buildHeaders({ url: "/products/" });
    expect(headersPl.get("Accept-Language")).toBe("pl");

    setActiveLocale("en");
    expect(getActiveLocale()).toBe("en");

    const headersEn = await buildHeaders({ url: "/products/" });
    expect(headersEn.get("Accept-Language")).toBe("en");

    // Przywracamy domyślny
    setActiveLocale("pl");
  });

  test("explicit Accept-Language in request config overrides active locale", async () => {
    setActiveLocale("pl");
    const headers = await buildHeaders({
      url: "/products/",
      headers: { "Accept-Language": "en" },
    });
    expect(headers.get("Accept-Language")).toBe("en");
  });
});
