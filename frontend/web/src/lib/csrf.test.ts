import { afterEach, describe, expect, test } from "bun:test";

import { ensureCsrfToken, getCookieValue } from "./csrf";

const originalFetch = globalThis.fetch;

type FakeDocument = { cookie: string };

function withDocument(cookie: string): FakeDocument {
  const document = { cookie };
  (globalThis as { document?: FakeDocument }).document = document;
  return document;
}

/**
 * Klient przeglądarkowy allauth wymaga nagłówka CSRF (#349).
 *
 * Token żyje w ciasteczku `csrftoken`; gdy go nie ma, pierwszy GET sesji
 * allauth zakłada je w odpowiedzi.
 */
describe("CSRF token for browser allauth", () => {
  afterEach(() => {
    globalThis.fetch = originalFetch;
    delete (globalThis as { document?: FakeDocument }).document;
  });

  test("reads a cookie value and ignores similar names", () => {
    const cookie = "NEXT_LOCALE=en; csrftoken=abc123; other=1";

    expect(getCookieValue(cookie, "csrftoken")).toBe("abc123");
    expect(getCookieValue(cookie, "csrftoken_other")).toBeNull();
  });

  test("returns the token already present in the cookie", async () => {
    withDocument("csrftoken=gotowy");
    let requests = 0;
    globalThis.fetch = (async () => {
      requests += 1;
      return new Response("{}", { status: 200 });
    }) as typeof fetch;

    await expect(ensureCsrfToken("http://backend.test/session")).resolves.toBe(
      "gotowy",
    );
    expect(requests).toBe(0);
  });

  test("bootstraps the cookie with a session request when missing", async () => {
    const document = withDocument("");
    const urls: string[] = [];

    globalThis.fetch = (async (input, init) => {
      urls.push(String(input));
      // allauth ustawia ciasteczko w odpowiedzi na GET sesji.
      document.cookie = "csrftoken=z-sesji";
      expect(init?.credentials).toBe("include");
      return new Response("{}", { status: 401 });
    }) as typeof fetch;

    await expect(ensureCsrfToken("http://backend.test/session")).resolves.toBe(
      "z-sesji",
    );
    expect(urls).toEqual(["http://backend.test/session"]);
  });

  test("returns null where there is no document (server render)", async () => {
    await expect(ensureCsrfToken("http://backend.test/session")).resolves.toBe(
      null,
    );
  });
});
