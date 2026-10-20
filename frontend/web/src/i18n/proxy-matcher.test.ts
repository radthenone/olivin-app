import { describe, expect, test } from "bun:test";
import { unstable_doesMiddlewareMatch } from "next/experimental/testing/server";

import { config } from "../../proxy";

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

const matches = (url: string) => unstable_doesMiddlewareMatch({ config, url });

describe("language routing matcher", () => {
  test.each(technicalPaths)(
    "leaves %s outside locale routing",
    (path: string) => {
      expect(matches(path)).toBe(false);
    },
  );

  test.each(storefrontPaths)(
    "routes %s through the locale proxy",
    (path: string) => {
      expect(matches(path)).toBe(true);
    },
  );
});
