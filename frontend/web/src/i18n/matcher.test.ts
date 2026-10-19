import { describe, expect, test } from "bun:test";

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
  "/_vercel/insights/script.js",
  "/favicon.ico",
];

const storefrontPaths = ["/", "/pl", "/en", "/pl/health", "/en/account"];

describe("language routing matcher", () => {
  test.each(technicalPaths)("leaves %s outside locale routing", (path) => {
    expect(matchesLocaleRouting(path)).toBe(false);
  });

  test.each(storefrontPaths)("routes %s through the locale proxy", (path) => {
    expect(matchesLocaleRouting(path)).toBe(true);
  });

  test("the Next matcher string describes the same paths as the helper", () => {
    const nextMatcher = new RegExp(`^${localeMatcher}$`);

    for (const path of [...technicalPaths, ...storefrontPaths]) {
      expect(nextMatcher.test(path)).toBe(matchesLocaleRouting(path));
    }
  });
});
