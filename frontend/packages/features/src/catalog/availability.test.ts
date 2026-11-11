import { describe, expect, test } from "bun:test";

import { getAvailabilityCategory } from "./availability";

/**
 * Kategoria dostępności to jedyna prawda, którą interfejs pokazuje klientowi:
 * „dostępny”, „ostatnie sztuki” albo „niedostępny” (ADR 0034).
 */
describe("getAvailabilityCategory", () => {
  test("marks an available variant with plenty of stock as available", () => {
    expect(
      getAvailabilityCategory({ isAvailable: true, isLowStock: false }),
    ).toBe("available");
  });

  test("marks a positive but small stock as low stock", () => {
    expect(
      getAvailabilityCategory({ isAvailable: true, isLowStock: true }),
    ).toBe("lowStock");
  });

  test("marks a variant without stock as unavailable", () => {
    expect(
      getAvailabilityCategory({ isAvailable: false, isLowStock: false }),
    ).toBe("unavailable");
  });

  test("unavailable wins over a stale low-stock flag", () => {
    expect(
      getAvailabilityCategory({ isAvailable: false, isLowStock: true }),
    ).toBe("unavailable");
  });
});
