import { CatalogNotFound } from "@/components/catalog/catalog-not-found";

/**
 * 404 dla rewrite'u z `proxy.ts` (nieznany slug kolekcji).
 */
export default function CollectionNotFoundSegment() {
  return <CatalogNotFound namespace="catalog.collection.notFound" />;
}
