export {
  availabilityMessageKey,
  getAvailabilityCategory,
} from "./availability";
export type { AvailabilityCategory } from "./availability";

export * from "./server";

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
