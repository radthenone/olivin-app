import { CatalogNotFound } from "@/components/catalog/catalog-not-found";

/**
 * 404 strony kategorii. Renderuje się pod prefiksem języka.
 */
export default function CategoryNotFound() {
  return <CatalogNotFound namespace="catalog.category.notFound" />;
}
