import { afterEach, beforeEach, describe, expect, test } from "bun:test";

import { defaultLocale } from "@olivin/i18n";

import { webRequest } from "./http";
import { getApiLocale, setApiLocale } from "./request-locale";

const originalFetch = globalThis.fetch;
const originalBackendUrl = process.env.NEXT_PUBLIC_BACKEND_URL;

describe("webRequest Accept-Language", () => {
  beforeEach(() => {
    process.env.NEXT_PUBLIC_BACKEND_URL = "http://backend.test";
    setApiLocale(defaultLocale);
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
    setApiLocale(defaultLocale);

    if (originalBackendUrl === undefined) {
      delete process.env.NEXT_PUBLIC_BACKEND_URL;
    } else {
      process.env.NEXT_PUBLIC_BACKEND_URL = originalBackendUrl;
    }
  });

  test("uses the default locale before the UI sets one", () => {
    expect(getApiLocale()).toBe(defaultLocale);
  });

  test("sends Accept-Language from the same locale as the interface", async () => {
    setApiLocale("en");
    let sentHeaders: Headers | undefined;

    globalThis.fetch = (async (_input, init) => {
      sentHeaders = new Headers(init?.headers);
      return new Response(JSON.stringify({ status: "healthy" }), {
        status: 200,
        headers: { "content-type": "application/json" },
      });
    }) as typeof fetch;

    await webRequest("/health/");

    expect(sentHeaders?.get("accept-language")).toBe("en");
  });

  test("keeps Accept-Language in sync after a locale change", async () => {
    const requests: Array<string | null> = [];

    globalThis.fetch = (async (_input, init) => {
      requests.push(new Headers(init?.headers).get("accept-language"));
      return new Response("{}", {
        status: 200,
        headers: { "content-type": "application/json" },
      });
    }) as typeof fetch;

    setApiLocale("en");
    await webRequest("/health/");
    setApiLocale("pl");
    await webRequest("/health/");

    expect(requests).toEqual(["en", "pl"]);
  });
});
