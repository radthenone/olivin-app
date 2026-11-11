/**
 * Część katalogu bezpieczna w komponentach serwerowych: bez hooków React.
 *
 * Barrel `./index.ts` re-eksportuje hooki wyboru wariantu (`useState`), więc
 * import z niego ciągnie kod klienta do grafu serwerowego i Next odrzuca build.
 */
export {
  CatalogError,
  createCatalogClient,
  isCatalogSlug,
} from "./catalog-client";
export type {
  CatalogClient,
  CatalogClientOptions,
  CatalogCurrency,
  ProductsListFilters,
} from "./catalog-client";

export { uniqueStones } from "./product-stones";

export {
  DELIVERY_COUNTRY_COOKIE_NAME,
  DeliveryCountryEnum,
  EU_DELIVERY_COUNTRIES,
  currencyFromDeliveryCountry,
  isEuDeliveryCountry,
} from "./delivery-country";
export type { DeliveryCountry } from "./delivery-country";
