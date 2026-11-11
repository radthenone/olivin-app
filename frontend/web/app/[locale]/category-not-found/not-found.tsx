import { CatalogNotFound } from "@/components/catalog/catalog-not-found";

/**
 * 404 dla rewrite'u z `proxy.ts` (nieznany slug kategorii).
 */
export default function CategoryNotFoundSegment() {
  return <CatalogNotFound namespace="catalog.category.notFound" />;
}
