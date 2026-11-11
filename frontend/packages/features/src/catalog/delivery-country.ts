import { DeliveryCountryEnum } from "@olivin/api/generated/apps/schemas";

/** Kraj dostawy w obrębie Unii Europejskiej (ADR 0035). */
export type DeliveryCountry = DeliveryCountryEnum;

export { DeliveryCountryEnum };

/** Nazwa ciasteczka z wybranym krajem dostawy. */
export const DELIVERY_COUNTRY_COOKIE_NAME = "delivery_country";

/** Lista wszystkich 27 państw członkowskich Unii Europejskiej. */
export const EU_DELIVERY_COUNTRIES: readonly DeliveryCountry[] =
  Object.values(DeliveryCountryEnum);

const EU_COUNTRY_SET = new Set<string>(EU_DELIVERY_COUNTRIES);

/**
 * Sprawdza, czy kod kraju należy do Unii Europejskiej.
 *
 * Args:
 *     country: Kod kraju ISO 3166-1 alpha-2.
 *
 * Returns:
 *     `true`, jeśli kraj należy do UE.
 */
export function isEuDeliveryCountry(
  country: unknown,
): country is DeliveryCountry {
  return typeof country === "string" && EU_COUNTRY_SET.has(country);
}

/**
 * Wyznacza walutę katalogu z kraju dostawy (ADR 0035).
 *
 * Pusty kraj albo Polska daje PLN. Inny kraj Unii Europejskiej daje EUR.
 * Kraje spoza Unii (lub niepoprawne) zwracają domyślnie PLN.
 *
 * Args:
 *     country: Kod kraju dostawy.
 *
 * Returns:
 *     Waluta katalogu (`PLN` albo `EUR`).
 */
export function currencyFromDeliveryCountry(
  country?: DeliveryCountry | string | null,
): "PLN" | "EUR" {
  if (!country || country === "PL" || !isEuDeliveryCountry(country)) {
    return "PLN";
  }
  return "EUR";
}
