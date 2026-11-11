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
  CATALOG_FINENESSES,
  CATALOG_LENGTHS,
  CATALOG_MATERIALS,
  CATALOG_METAL_COLORS,
  CATALOG_ORDERING_OPTIONS,
  CATALOG_PRICE_MAX,
  CATALOG_SIZES,
  CATALOG_STONES,
  DEFAULT_CATALOG_ORDERING,
  clearCatalogFilters,
  fromProductsListParams,
  hasActiveFilters,
  parseCatalogFilters,
  parseCatalogPrice,
  serializeCatalogFilters,
  toProductsListParams,
  withFilterChange,
} from "./filters";
export type { CatalogFilterState, CatalogOrdering } from "./filters";
