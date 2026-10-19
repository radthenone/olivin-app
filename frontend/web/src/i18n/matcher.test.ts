import { describe, expect, test } from "bun:test";
import { unstable_doesMiddlewareMatch } from "next/experimental/testing/server";

import { localeMatcher, matchesLocaleRouting } from "./matcher";

/**
 * Proxy language routing must never touch technical paths. ADR 0034 depends on
 * it: a 301 on POST /api/revalidate would turn the request into GET and lose
 * cache revalidation silently.
 */
const technicalPaths = [
  "/api",
  "/api/revalidate",
  "/api/health/",
  "/.well-known/assetlinks.json",
  "/robots.txt",
  "/sitemap.xml",
  "/_next/static/chunks/main.js",
  "/favicon.ico",
];

const storefrontPaths = [
  "/",
  "/pl",
  "/en",
  "/pl/health",
  "/en/account",
  "/apiary",
  "/api-docs",
  "/_nextfoo",
];

describe("language routing matcher", () => {
  test.each(technicalPaths)(
    "leaves %s outside locale routing",
    (path: string) => {
      expect(matchesLocaleRouting(path)).toBe(false);
    },
  );

  test.each(storefrontPaths)(
    "routes %s through the locale proxy",
    (path: string) => {
      expect(matchesLocaleRouting(path)).toBe(true);
    },
  );

  test("Next applies the matcher to the same paths as the helper", () => {
    const config = { matcher: localeMatcher };

    for (const path of [...technicalPaths, ...storefrontPaths]) {
      expect({
        path,
        matches: unstable_doesMiddlewareMatch({ config, url: path }),
      }).toEqual({ path, matches: matchesLocaleRouting(path) });
    }
  });
});
