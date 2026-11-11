import { CatalogNotFound } from "@/components/catalog/catalog-not-found";

/**
 * 404 strony kolekcji. Renderuje się pod prefiksem języka.
 */
export default function CollectionNotFound() {
  return <CatalogNotFound namespace="catalog.collection.notFound" />;
}
