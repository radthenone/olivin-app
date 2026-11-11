import type { ProductVariant } from "@olivin/api/generated/apps/schemas";

/**
 * Rodzaje kamieni występujące w wariantach produktu, bez powtórzeń i w
 * kolejności pierwszego wystąpienia.
 *
 * Args:
 *     variants: Warianty produktu z API katalogu.
 *
 * Returns:
 *     Unikalne rodzaje kamieni; pusta lista, gdy produkt nie ma kamieni.
 */
export function uniqueStones(
  variants: readonly Pick<ProductVariant, "stone">[],
): ProductVariant["stone"][] {
  return [...new Set(variants.map((variant) => variant.stone))].filter(Boolean);
}
