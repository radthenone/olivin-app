import { describe, expect, test } from "bun:test";

import {
  EU_DELIVERY_COUNTRIES,
  currencyFromDeliveryCountry,
  isEuDeliveryCountry,
} from "./delivery-country";

describe("delivery-country", () => {
  describe("currencyFromDeliveryCountry", () => {
    test("returns PLN when country is empty, undefined or null", () => {
      expect(currencyFromDeliveryCountry(undefined)).toBe("PLN");
      expect(currencyFromDeliveryCountry(null)).toBe("PLN");
      expect(currencyFromDeliveryCountry("")).toBe("PLN");
    });

    test("returns PLN when country is Poland (PL)", () => {
      expect(currencyFromDeliveryCountry("PL")).toBe("PLN");
    });

    test("returns EUR for other EU member states", () => {
      expect(currencyFromDeliveryCountry("DE")).toBe("EUR");
      expect(currencyFromDeliveryCountry("FR")).toBe("EUR");
      expect(currencyFromDeliveryCountry("IT")).toBe("EUR");
      expect(currencyFromDeliveryCountry("ES")).toBe("EUR");
      expect(currencyFromDeliveryCountry("CZ")).toBe("EUR");
      expect(currencyFromDeliveryCountry("SE")).toBe("EUR");
    });

    test("returns PLN for unknown or non-EU countries", () => {
      expect(currencyFromDeliveryCountry("US")).toBe("PLN");
      expect(currencyFromDeliveryCountry("GB")).toBe("PLN");
      expect(currencyFromDeliveryCountry("XYZ")).toBe("PLN");
    });
  });

  describe("isEuDeliveryCountry", () => {
    test("identifies EU countries correctly", () => {
      expect(isEuDeliveryCountry("PL")).toBe(true);
      expect(isEuDeliveryCountry("DE")).toBe(true);
      expect(isEuDeliveryCountry("US")).toBe(false);
      expect(isEuDeliveryCountry("")).toBe(false);
      expect(isEuDeliveryCountry(undefined)).toBe(false);
    });
  });

  describe("EU_DELIVERY_COUNTRIES", () => {
    test("contains exactly 27 EU member states", () => {
      expect(EU_DELIVERY_COUNTRIES).toHaveLength(27);
      expect(EU_DELIVERY_COUNTRIES).toContain("PL");
      expect(EU_DELIVERY_COUNTRIES).toContain("DE");
      expect(EU_DELIVERY_COUNTRIES).toContain("FR");
    });
  });
});
