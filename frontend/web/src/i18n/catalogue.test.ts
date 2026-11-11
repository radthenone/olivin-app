import { describe, expect, test } from "bun:test";

import en from "@olivin/i18n/messages/en.json";
import pl from "@olivin/i18n/messages/pl.json";
import { defaultLocale, isLocale, locales, messages } from "@olivin/i18n";

/**
 * Katalog jest źródłem tekstów dla web i mobile. `pl.json` jest źródłem,
 * `en.json` tłumaczeniem — rozjazd kluczy oznacza, że część interfejsu
 * w jednym języku zostanie pusta albo pokaże klucz.
 */
function messageKeys(value: unknown, prefix = ""): string[] {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    return [prefix];
  }

  return Object.entries(value)
    .flatMap(([key, child]) =>
      messageKeys(child, prefix.length > 0 ? `${prefix}.${key}` : key),
    )
    .sort();
}

describe("@olivin/i18n", () => {
  test("en.json covers every key from the pl.json source", () => {
    expect(messageKeys(en)).toEqual(messageKeys(pl));
  });

  test("defines list, category, collection, card and pagination keys in catalog", () => {
    const keys = messageKeys(pl);
    expect(keys).toContain("catalog.category.notFound.title");
    expect(keys).toContain("catalog.collection.notFound.title");
    expect(keys).toContain("catalog.list.productCount");
    expect(keys).toContain("catalog.card.fromPrice");
    expect(keys).toContain("catalog.pagination.previous");
    expect(keys).toContain("catalog.pagination.next");
  });

  test("defines delivery country switch keys", () => {
    const keys = messageKeys(pl);
    expect(keys).toContain("delivery.shipTo");
    expect(keys).toContain("delivery.countries.PL");
    expect(keys).toContain("delivery.countries.DE");
  });

  test("defines variant selection and attribute keys in catalog", () => {
    const keys = messageKeys(pl);
    expect(keys).toContain("catalog.product.attributes.metalColor");
    expect(keys).toContain("catalog.product.attributes.size");
    expect(keys).toContain("catalog.product.attributes.length");
    expect(keys).toContain("catalog.product.attributes.stone");
    expect(keys).toContain("catalog.product.attributeNone");
    expect(keys).toContain("catalog.product.lengthValue");
  });

  test("exposes both locales and uses Polish as the default", () => {
    expect(locales).toEqual(["pl", "en"]);
    expect(defaultLocale).toBe("pl");
  });

  test("recognises only supported locales", () => {
    expect(isLocale("pl")).toBe(true);
    expect(isLocale("en")).toBe(true);
    expect(isLocale("de")).toBe(false);
    expect(isLocale(undefined)).toBe(false);
    expect(isLocale(null)).toBe(false);
  });

  test("returns the catalogue for each supported locale", () => {
    expect(messages.pl).toBe(pl);
    expect(messages.en).toBe(en);
  });
});
