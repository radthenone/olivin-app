import { notFound } from "next/navigation";

/**
 * Cel rewrite'u z `proxy.ts` dla sluga kolekcji, której katalog nie zna.
 */
export default function CollectionNotFoundPage() {
  notFound();
}
