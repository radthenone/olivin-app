export {
  availabilityMessageKey,
  getAvailabilityCategory,
} from "./availability";
export type { AvailabilityCategory } from "./availability";

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
  VARIANT_ATTRIBUTE_NAMES,
  findMatchingVariant,
  getAttributeDefinitions,
  getInitialSelection,
  isCombinationPossible,
  isOptionAvailable,
  resolveSelection,
  useVariantSelection,
} from "./variant-selection";
export type {
  AttributeDefinition,
  VariantAttributeName,
  VariantSelection,
} from "./variant-selection";
