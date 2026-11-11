import type { ProductVariant } from "@olivin/api/generated/apps/schemas/productVariant";

/**
 * Kategoria dostępności wariantu widziana przez klienta (ADR 0034).
 *
 * Stan magazynowy pokazujemy jako kategorię, a nie liczbę: ostateczną prawdą
 * o dostępności jest koszyk i rezerwacja, więc liczba sztuk na karcie tylko
 * myliłaby przy wyścigu o ostatnią sztukę.
 */
export type AvailabilityCategory = "available" | "lowStock" | "unavailable";

type StockState = Pick<ProductVariant, "isAvailable" | "isLowStock">;

/**
 * Wylicza kategorię dostępności z flag wariantu.
 *
 * Args:
 *     variant: Flagi `isAvailable` i `isLowStock` z API.
 *
 * Returns:
 *     `unavailable`, gdy wariantu nie ma w stanie; `lowStock`, gdy zostały
 *     ostatnie sztuki; inaczej `available`.
 */
export function getAvailabilityCategory(
  variant: StockState,
): AvailabilityCategory {
  if (!variant.isAvailable) {
    return "unavailable";
  }

  return variant.isLowStock ? "lowStock" : "available";
}

/** Klucze komunikatów `@olivin/i18n` dla kategorii dostępności. */
export const availabilityMessageKey = {
  available: "catalog.product.availability.available",
  lowStock: "catalog.product.availability.lowStock",
  unavailable: "catalog.product.availability.unavailable",
} as const satisfies Record<AvailabilityCategory, string>;
